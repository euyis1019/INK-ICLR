"""Import measured CM results and render paper tables, without running models.

Import from the experiment workspace:
    python3 motivation_method/update_results.py --workspace ..
Render the checked-in, portable snapshot:
    python3 motivation_method/update_results.py
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import statistics as stats

HERE = Path(__file__).resolve().parent
GLUE = ['cola', 'mnli', 'mrpc', 'qnli', 'qqp', 'rte', 'sst2', 'stsb']
ARCHS = ['ViT-B-32', 'ViT-B-16', 'ViT-L-14']
VISION_METHODS = [
    ('ft', 'Individual FT'), ('zeroshot', 'Zero-shot'),
    ('average', 'Weight Avg.'), ('ta', 'Task Arith.'), ('ties', 'TIES'),
    ('consensus', 'Consensus TA'), ('iso_c', 'Iso-C'), ('iso_cts', 'Iso-CTS'),
    ('tsv_m', 'TSV-M'), ('regmean', 'RegMean'), ('wudi', 'WUDI'),
    ('lines', 'LiNeS (Iso-C)'), ('com', 'CoM'), ('esm', 'ESM'),
    ('svc', 'SVC (Iso-CTS)'), ('svc_on_esm', 'SVC (ESM)'),
    ('cm_prototype', r'\method{}（原型）'),
]


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def summary(values):
    return {'mean': stats.mean(values), 'sample_sd': stats.stdev(values) if len(values) > 1 else None,
            'n': len(values), 'values': values}


class Importer:
    def __init__(self, workspace):
        self.workspace = workspace
        self.sources = {}

    def read(self, relative):
        raw = (self.workspace / relative).read_bytes()
        self.sources[relative] = {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        if relative.endswith('.csv'):
            return list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
        return json.loads(raw)

    def clip(self):
        # Parse only the literal task list; never import the GPU/model package.
        assets = self.workspace / 'wb/wbench/assets.py'
        task_list = next(ast.literal_eval(node.value) for node in ast.parse(assets.read_text()).body
                         if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ALL20' for t in node.targets))
        columns, cells, starts = [], [], []
        com_source = 'wb/results_com.json'
        com = self.read(com_source)
        for arch in ARCHS:
            gate_source = f'wb/results_gate_{arch}_20.json'
            gate = self.read(gate_source)[arch]
            for n in [8, 14, 20]:
                tasks = task_list[:n]
                columns.append({'architecture': arch, 'tasks': n})
                cell = {}

                def record(report, source, selection, denominator=None):
                    per = report['per_task']
                    if per is None:
                        return {'accuracy': report['avg'], 'normalized': None, 'per_task': None,
                                'source': source, 'selection': selection,
                                'note': 'Aggregate recovered from log; per-task test scores unavailable. No normalized value inferred.'}
                    assert set(per) == set(tasks), (source, set(per), tasks)
                    assert abs(stats.mean(per.values()) - report['avg']) < 1e-7, source
                    den = denominator or {t: gate[t]['ft'] for t in tasks}
                    return {'accuracy': report['avg'], 'normalized': stats.mean(100 * per[t] / den[t] for t in tasks),
                            'per_task': per, 'source': source, 'selection': selection,
                            'normalization_source': gate_source}

                for key, field in [('ft', 'ft'), ('zeroshot', 'zeroshot')]:
                    per = {t: gate[t][field] for t in tasks}
                    cell[key] = record({'avg': stats.mean(per.values()), 'per_task': per}, gate_source, 'fixed anchor')
                source = f'wb/results_bl_{arch}_{n}_val.json'
                for key, r in self.read(source).items():
                    assert r['select_split'] == 'val' and r['report']['split'] == 'test'
                    cell[key.split('@')[0]] = record(r['report'], source, f'{key}; validation-selected scale {r["best_alpha"]}')
                source = f'wb/results_dm_{arch}_{n}_val.json'
                candidates = [(key, r) for key, by_n in self.read(source).items() for budget, r in by_n.items()
                              if budget == '256' and r.get('report')]
                key, r = max(candidates, key=lambda x: x[1]['avg'])
                assert r['select_split'] == 'val' and r['report']['split'] == 'test'
                cell['regmean'] = record(r['report'], source, f'validation-selected {key}; 256 images/task')
                r = com[f'com_{arch}_{n}']
                assert r['args']['rounds'] == 1 and r['args']['split'] == 'test'
                h = next(h for h in r['hist'] if h['round'] == 1)
                cell['com'] = record(h, com_source, 'fixed one-round CoM; no test selection')
                for family in ['esm', 'svc', 'svcon']:
                    source = f'wb/results_{family}_{arch}_{n}' + ('_val.json' if family == 'svc' else '.json')
                    if not (self.workspace / source).exists():
                        continue
                    records = self.read(source)
                    if family == 'svc':
                        candidates = [(key, r) for key, r in records.items() if key.startswith('svc@base=iso_cts;') and r.get('report')]
                        if not candidates:
                            continue
                        key, r = max(candidates, key=lambda x: x[1]['best']['avg'])
                    elif family == 'svcon':
                        if 'svc(ESM)' not in records or not records['svc(ESM)'].get('report'):
                            continue
                        key, r = 'svc(ESM)', records['svc(ESM)']
                    else:
                        key, r = 'esm@n=32', records['esm@n=32']
                        if not r.get('report'):
                            continue
                    assert r['select_split'] == 'val' and r['report']['split'] == 'test'
                    cell['svc_on_esm' if family == 'svcon' else family] = record(r['report'], source, f'validation-selected {key}')
                tag = 'abl_init_coexist_iso_c' if (arch, n) == ('ViT-B-32', 8) else f'grid_coexist_{arch}_{n}'
                source = f'wb/results_ablation/{tag}.json'
                r = self.read(source)[tag]
                hist = [h for h in r['hist'] if isinstance(h.get('round'), int)]
                assert hist[-1]['round'] == r['args']['rounds'] and r['args']['gkind'] == 'chi2'
                chosen = min((h for h in hist if h.get('hold_kl') is not None), key=lambda h: (h['hold_kl'], h['round']))
                cell['cm_prototype'] = record(chosen, source, f'held-out teacher KL; round {chosen["round"]}; seed 0')
                cell['cm_prototype']['initial_accuracy'] = hist[0]['avg']
                cells.append(cell)
        for key in ['iso_c', 'tsv_m', 'regmean', 'zeroshot', 'average', 'ta']:
            source = f'wb/results_ablation/abl_init_coexist_{key}.json'
            r = self.read(source)[f'abl_init_coexist_{key}']
            hist = [h for h in r['hist'] if isinstance(h.get('round'), int)]
            assert hist[-1]['round'] == r['args']['rounds']
            starts.append({'key': key, 'before': hist[0]['avg'], 'after': hist[-1]['avg'], 'source': source})
        runs, expert = [], None
        for run in ['coexist_inkrl_seed0', 'coexist_inkrl_seed1', 'coexist_main_seed2', 'coexist_main_seed3']:
            source = f'experiments/github_runs/results/{run}.json'
            d = self.read(source)
            r = d['methods']['coexist-merge']['test_metrics']
            e = d['methods']['individual-finetuned-experts']['test_metrics']
            if expert is None:
                expert = e
            assert e == expert
            assert abs(stats.mean(r['per_task_absolute_accuracy'].values()) - r['absolute_accuracy_mean']) < 1e-7
            assert abs(stats.mean(100 * v / e['per_task_absolute_accuracy'][t] for t, v in r['per_task_absolute_accuracy'].items()) - r['normalized_accuracy_mean']) < 1e-7
            runs.append({'seed': d['protocol']['random_seed'], 'source': source, 'metrics': r})
        assert sorted(r['seed'] for r in runs) == [0, 1, 2, 3]
        formal = summary([r['metrics']['absolute_accuracy_mean'] for r in runs])
        formal.update(normalized=stats.mean(r['metrics']['normalized_accuracy_mean'] for r in runs), runs=runs, expert=expert)
        return {'columns': columns, 'cells': cells, 'formal': formal, 'starts': starts}

    def t5(self):
        rows = []

        def group(names):
            if not names:
                return None
            records, sources = [], []
            for name in names:
                source = f'experiments/nlp_runs/results/{name}.json'
                d = self.read(source)
                assert all(t in d for t in GLUE)
                assert d['protocol'] == 'fusionbench-flan-t5-glue'
                assert all(d[t]['metric'] == ('spearman_rho' if t == 'stsb' else 'exact_match') for t in GLUE)
                assert abs(stats.mean(d[t]['value'] for t in GLUE) - d['average']) < 1e-7
                records.append(d)
                sources.append(source)
            result = summary([d['average'] for d in records])
            result.update(per_task={t: stats.mean(d[t]['value'] for d in records) for t in GLUE}, sources=sources)
            return result

        for key, label, base, large in [
            ('average', 'Weight Avg.', ['t5_average'], ['t5l_average']),
            ('ta', 'Task Arith.', ['t5_ta0.3'], ['t5l_ta0.3']),
            ('ties', 'TIES', ['t5_ties0.3'], ['t5l_ties0.3']),
            ('iso_c', 'Iso-C 1.3', ['t5_iso_c1.3'], ['t5l_iso_c1.3']),
            ('tsv_m', 'TSV-M', ['t5_tsv_m'], ['t5l_tsv_m']),
            ('regmean', 'RegMean 0.9', ['t5_regmean0.9'], ['t5l_regmean0.9']),
            ('featcal', 'TA + FeatCal（移植）', ['t5_featcal'] + [f't5_featcal_seed{i}' for i in range(1, 5)], ['t5l_featcal']),
            ('cm', r'\method{}（原版）', ['t5_coexist_n256'] + [f't5_coexist_seed{i}' for i in range(1, 5)], ['t5l_coexist']),
            ('cm_target03', r'\method{}（目标插值 0.3）', ['t5_coexist_tgt0.3'] + [f't5_coexist_tgt0.3_seed{i}' for i in range(1, 4)], ['t5l_coexist_tgt0.3']),
            ('cm_target06', r'\method{}（目标插值 0.6）', ['t5_coexist_tgt0.6'] + [f't5_coexist_tgt0.6_seed{i}' for i in range(1, 3)], None),
        ]:
            rows.append({'key': key, 'label': label, 'base': group(base), 'large': group(large)})
        partial_source = 'experiments/nlp_runs/results/eval_base_4tasks.json'
        d = self.read(partial_source)
        partial = {'per_task': {t: d[t]['value'] for t in GLUE if t in d}, 'source': partial_source}
        expert_source = 'experiments/nlp_runs/results/eval_expert_cola.json'
        expert = self.read(expert_source)
        assert expert['model'].endswith('tanganke__flan-t5-base_glue-cola')
        partial_expert = {'per_task': {'cola': expert['cola']['value']}, 'source': expert_source,
                          'note': 'Only the CoLA expert on CoLA is a diagonal expert reference. Other tasks in this file evaluate the same CoLA expert.'}
        starts = []
        for label, before_b, after_b, before_l, after_l in [
            ('Iso-C 1.3', 't5_iso_c1.3', 't5_coexist_tgt0.3', 't5l_iso_c1.3', 't5l_coexist'),
            ('TA + FeatCal', 't5_featcal', 't5_stack_tgt0.3_from_featcal', 't5l_featcal', 't5l_stack_coexist_from_featcal'),
            ('RegMean 0.9', 't5_regmean0.9', 't5_stack_tgt0.3_from_regmean0.9', None, None),
            ('TSV-M', 't5_tsv_m', 't5_stack_tgt0.3_from_tsv_m', 't5l_tsv_m', 't5l_stack_coexist_from_tsv_m'),
            ('Task Arith. 0.3', 't5_ta0.3', 't5_stack_tgt0.3_from_ta0.3', None, None),
        ]:
            starts.append({'label': label, 'groups': [group([x]) if x else None for x in [before_b, after_b, before_l, after_l]]})
        return {'rows': rows, 'partial_base': partial, 'partial_expert': partial_expert, 'starts': starts}

    def llm(self):
        rows = self.read('docs/experiment_inventory/2026-09-16/llm_hotplug.csv')
        for r in rows:
            for name in ['GSM8K', 'IFEval', 'multilingual']:
                for side in ['before', 'after']:
                    source = r[f'{name}_{side}_source']
                    if not source:
                        r[f'{name}_{side}'] = None
                        continue
                    values = self.read(source)['results']
                    if name == 'GSM8K':
                        score = 100 * values['gsm8k']['exact_match,flexible-extract']
                    elif name == 'IFEval':
                        score = 100 * values['ifeval']['prompt_level_strict_acc,none']
                    else:
                        scores = [100 * values[f'{task}_{lang}'][metric]
                                  for task, metric in [('arc', 'acc_norm,none'), ('hellaswag', 'acc_norm,none'), ('m_mmlu', 'acc,none')]
                                  for lang in ['fr', 'es', 'de', 'ru']]
                        score = stats.mean(scores)
                    assert abs(score - float(r[f'{name}_{side}'])) < 1e-8
                    r[f'{name}_{side}'] = score
                r[f'{name}_difference_pp'] = r[f'{name}_after'] - r[f'{name}_before'] if r[f'{name}_before'] is not None else None
            for side in ['before', 'after']:
                r[f'three_domain_{side}'] = stats.mean(r[f'{m}_{side}'] for m in ['GSM8K', 'IFEval', 'multilingual']) if r[f'multilingual_{side}'] is not None else None
            r['three_domain_difference_pp'] = r['three_domain_after'] - r['three_domain_before'] if r['three_domain_before'] is not None else None
        assert len(rows) == 10 and sum(r['GSM8K_difference_pp'] > 0 for r in rows) == 9
        return rows


def tex_score(record, precision=2):
    if record is None:
        return '---'
    value = f'{record["mean"]:.{precision}f}'
    if record['sample_sd'] is not None:
        value += rf'\pm {record["sample_sd"]:.{precision}f}'
    return '$' + value + '$'


def write_table(name, lines):
    text = '% Generated by motivation_method/update_results.py from data/verified_results.json.\n'
    (HERE / 'tables' / (name + '.tex')).write_text(text + '\n'.join(lines) + '\n', encoding='utf-8')


def row(values):
    return ' & '.join(values) + r' \\'


def render(data):
    vision = data['vision']
    lines = [r'\begin{table}[!htbp]', r'\centering',
             r'\caption{CLIP 实测结果（\%）。单元格为任务宏平均准确率，下标为逐任务相对本环境专家的归一化均值。上半表为工作台；正式 CM 单独列出。--- 为缺测。}',
             r'\label{tab:ink-vision-summary}', r'\setlength{\tabcolsep}{2pt}', r'\renewcommand{\arraystretch}{1.12}',
             r'\resizebox{\textwidth}{!}{\begin{tabular}{@{}lccc|ccc|ccc@{}}', r'\toprule',
             row([r'\multirow{2}{*}{Method}', r'\multicolumn{3}{c}{ViT-B/32}', r'\multicolumn{3}{c}{ViT-B/16}', r'\multicolumn{3}{c}{ViT-L/14}']),
             r'\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(l){8-10}', row([''] + ['8 tasks', '14 tasks', '20 tasks'] * 3), r'\midrule']
    missing = []
    for key, label in VISION_METHODS:
        if key == 'cm_prototype':
            lines.append(r'\rowcolor{black!8}')
            label = 'CM（原型）'
        scores = []
        for column, cell in zip(vision['columns'], vision['cells']):
            r = cell.get(key)
            scores.append((f'${r["accuracy"]:.2f}_{{({r["normalized"]:.2f})}}$' if r['normalized'] is not None
                           else rf'${r["accuracy"]:.2f}_{{(\text{{---}})}}$') if r else '---')
            if r is None:
                missing.append({'method': label, **column})
        lines.append(row([label] + scores))
        if key == 'ft':
            lines.append(r'\midrule')
    formal = vision['formal']
    lines += [r'\midrule', r'\rowcolor{black!8}', row(['CM（正式，4 seeds）', f'${formal["mean"]:.2f}_{{({formal["normalized"]:.2f})}}$'] + ['---'] * 8),
              r'\bottomrule', r'\end{tabular}}', r'\par\smallskip',
              r'{\footnotesize 工作台 CM 九格均为单种子，按无标签留出 KL 选轮；可调基线按有标签 validation 选参。L/14 二十任务的 Iso-C、Iso-CTS、TSV-M 仅恢复了日志中的两位小数宏平均，故归一化下标留空。正式 CM 为 $87.059\pm0.021$，使用正式运行中的专家作归一化分母；其余行使用工作台闸门专家。两版不拼成一行。}', r'\end{table}']
    write_table('vision_summary', lines)

    base_rows = {r['key']: r for r in data['t5']['rows']}
    lines = [r'\begin{table}[!htbp]', r'\centering',
             r'\caption{Flan-T5-base 八专家一次性合并后的 GLUE validation 实测结果（FusionBench 口径）。前七任务为生成答案 exact match，STSB 为 Spearman；末列为八任务宏平均。}',
             r'\label{tab:ink-t5-results}', r'\setlength{\tabcolsep}{3pt}', r'\renewcommand{\arraystretch}{1.14}',
             r'\resizebox{\textwidth}{!}{\begin{tabular}{@{}lrrrrrrrr|c@{}}', r'\toprule',
             row(['Method', 'CoLA', 'MNLI', 'MRPC', 'QNLI', 'QQP', 'RTE', 'SST2', 'STSB', '平均']), r'\midrule',
             row(['Individual FT'] + [f'{data["t5"]["partial_expert"]["per_task"][t]:.2f}' if t in data['t5']['partial_expert']['per_task'] else '---' for t in GLUE] + ['---']),
             row(['Zero-shot'] + [f'{data["t5"]["partial_base"]["per_task"][t]:.2f}' if t in data['t5']['partial_base']['per_task'] else '---' for t in GLUE] + ['---']), r'\midrule']
    for r in data['t5']['rows']:
        if r['key'].startswith('cm'):
            lines.append(r'\rowcolor{black!8}')
        g = r['base']
        lines.append(row([r['label']] + [f'{g["per_task"][t]:.2f}' for t in GLUE] + [tex_score(g)]))
    lines += [r'\bottomrule', r'\end{tabular}}', r'\par\smallskip',
              r'{\footnotesize 多种子逐任务列为种子均值；末列误差为各次八任务均值的样本标准差。FeatCal 与原版 CM 各 5 seeds，目标插值 0.3 为 4 seeds，0.6 为 3 seeds；其他合并行为单种子。Zero-shot 仅测四任务，独立专家仅有 CoLA 对角结果，均不补八任务平均；未完成 T5 适配的视觉基线不列入本表。}', r'\end{table}']
    write_table('t5_results', lines)

    lines = [r'\begin{table}[!htbp]', r'\centering\small',
             r'\caption{CLIP ViT-B/32 八任务：正式 CM 与同任务外部复现参照（\%）。CM 为四种子均值及样本标准差，外部方法为已归档单次结果。}',
             r'\label{tab:clip-main}', r'\begin{tabular}{@{}lc@{}}', r'\toprule', row(['方法', 'test 宏平均']), r'\midrule']
    for key, label in VISION_METHODS:
        if key not in ['ft', 'cm_prototype']:
            lines.append(row([label, f'${vision["cells"][0][key]["accuracy"]:.2f}$']))
    lines += [r'\rowcolor{black!8}', row([r'\method{}（正式，4 seeds）', tex_score(formal, 3)]), r'\midrule',
              row(['正式环境单任务专家', f'${formal["expert"]["absolute_accuracy_mean"]:.2f}$']), r'\bottomrule', r'\end{tabular}', r'\end{table}']
    write_table('clip_main', lines)
    lines = [r'\begin{table}[!htbp]', r'\centering\small', r'\caption{CM 工作台九格（单种子）：固定 Iso-C 起点到留出 KL 选定轮。}',
             r'\label{tab:clip-scaling}', r'\begin{tabular}{@{}lrrr@{}}', r'\toprule', row(['设定', '起点', 'CM 原型', '差值']), r'\midrule']
    for c, cell in zip(vision['columns'], vision['cells']):
        r = cell['cm_prototype']
        lines.append(row([f'{c["architecture"]} / {c["tasks"]}', f'{r["initial_accuracy"]:.2f}', f'{r["accuracy"]:.2f}', f'{r["accuracy"]-r["initial_accuracy"]:+.2f}']))
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    write_table('clip_scaling', lines)
    lines = [r'\begin{table}[!htbp]', r'\centering\small',
             r'\caption{Flan-T5 GLUE 八任务实测宏平均。原版与目标插值扩展分行；所有误差为样本标准差。large 各行均为单种子。}',
             r'\label{tab:t5-main}', r'\begin{tabular}{@{}lccc@{}}', r'\toprule', row(['方法', 'base', 'base seeds', 'large']), r'\midrule']
    for r in data['t5']['rows']:
        if r['key'].startswith('cm'):
            lines.append(r'\rowcolor{black!8}')
        lines.append(row([r['label'], tex_score(r['base']), str(r['base']['n']), tex_score(r['large'])]))
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    write_table('t5_main', lines)
    lines = [r'\begin{tabular}{@{}llcc@{}}', r'\toprule', row(['设定', '方法版本', '参照分数', 'CM']), r'\midrule',
             row(['CLIP ViT-B/32', '正式 CM / ESM', f'{vision["cells"][0]["esm"]["accuracy"]:.2f}', tex_score(formal)])]
    for size in ['base', 'large']:
        for key in ['cm', 'cm_target03']:
            lines.append(row(['T5-' + size, base_rows[key]['label'] + ' / FeatCal', tex_score(base_rows['featcal'][size]), tex_score(base_rows[key][size])]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('main_summary', lines)

    labels = {'Soup': 'Model Soup', 'TA': 'Task Arith. 0.4', 'TIES': 'TIES 0.3/0.4', 'TSV-M': 'TSV-M', 'RegMean 0.5': 'RegMean 0.5', 'Iso-C': 'Iso-C 1.3'}
    for family, name, order in [('Llama-3.2-3B', 'llama_full', ['Iso-C', 'TSV-M', 'Soup', 'TA', 'TIES', 'RegMean 0.5']),
                                 ('Gemma-2-2B', 'gemma_full', ['Soup', 'TA', 'TIES', 'TSV-M'])]:
        is_llama = family.startswith('Llama')
        lines = [r'\begin{tabular}{@{}lrrrr' + ('rrr' if is_llama else 'r') + r'@{}}', r'\toprule',
                 row(['起点', r'\multicolumn{3}{c}{GSM8K}', r'\multicolumn{2}{c}{IFEval}'] + ([r'\multicolumn{2}{c}{三域宏平均}'] if is_llama else [])),
                 r'\cmidrule(lr){2-4}\cmidrule(lr){5-6}' + (r'\cmidrule(l){7-8}' if is_llama else ''),
                 row(['', '起点', '+ CM', '差值', '起点', '+ CM'] + (['起点', '+ CM'] if is_llama else [])), r'\midrule']
        for start in order:
            r = next(r for r in data['llm'] if r['model'] == family and r['start'] == start)
            values = [f'{r[k]:.2f}' for k in ['GSM8K_before', 'GSM8K_after']] + [f'{r["GSM8K_difference_pp"]:+.2f}']
            values += [f'{r[k]:.2f}' for k in ['IFEval_before', 'IFEval_after'] + (['three_domain_before', 'three_domain_after'] if is_llama else [])]
            lines.append(row([labels[start]] + values))
        lines += [r'\bottomrule', r'\end{tabular}']
        write_table(name, lines)
    lines = [r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
             row(['模型', '起点', r'\multicolumn{2}{c}{GSM8K}', r'\multicolumn{2}{c}{IFEval}']), r'\cmidrule(lr){3-4}\cmidrule(l){5-6}',
             row(['', '', '起点', '+ CM', '起点', '+ CM']), r'\midrule']
    for family, start in [('Llama-3.2-3B', 'Iso-C'), ('Llama-3.2-3B', 'TSV-M'), ('Llama-3.2-3B', 'RegMean 0.5'), ('Gemma-2-2B', 'Soup')]:
        r = next(r for r in data['llm'] if r['model'] == family and r['start'] == start)
        lines.append(row([family, labels[start]] + [f'{r[k]:.2f}' for k in ['GSM8K_before', 'GSM8K_after', 'IFEval_before', 'IFEval_after']]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('llm_summary', lines)
    lines = [r'\begin{tabular}{@{}lcc@{}}', r'\toprule', row(['起点', '起点分', '+ CM 原型（末轮）']), r'\midrule']
    start_labels = dict(VISION_METHODS)
    for r in vision['starts']:
        lines.append(row([start_labels[r['key']], f'{r["before"]:.2f}', f'{r["after"]:.2f}']))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('clip_starts', lines)
    lines = [r'\begin{tabular}{@{}lcccc@{}}', r'\toprule', row(['起点', 'base 起点', '+ CM 插值 0.3', 'large 起点', '+ CM 原版']), r'\midrule']
    for r in data['t5']['starts']:
        lines.append(row([r['label']] + [tex_score(g) for g in r['groups']]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('t5_starts', lines)
    # Keep the earlier machine-readable entry useful, but source every number
    # from the checked snapshot instead of the supplied, rounded prose table.
    compact = {
        'source_file': 'data/verified_results.json',
        'source_sha256': hashlib.sha256((HERE / 'data/verified_results.json').read_bytes()).hexdigest(),
        'status': 'Read-only audit of measured logs; formal/prototype/extension versions are separate. No model reruns.',
        'clip_main': [['方法', 'test 宏平均']] + [[label, round(vision['cells'][0][key]['accuracy'], 2)] for key, label in VISION_METHODS if key != 'cm_prototype'],
        'clip_formal': {k: formal[k] for k in ['mean', 'sample_sd', 'n', 'values', 'normalized']},
        'clip_scaling': [{'architecture': c['architecture'], 'tasks': c['tasks'], **{k: cell['cm_prototype'][k] for k in ['initial_accuracy', 'accuracy', 'normalized', 'selection']}}
                         for c, cell in zip(vision['columns'], vision['cells'])],
        't5_main': data['t5']['rows'],
        'llama': [r for r in data['llm'] if r['model'].startswith('Llama')],
        'gemma': [r for r in data['llm'] if r['model'].startswith('Gemma')],
    }
    dump(HERE / 'data/main_results.json', compact)
    checks = json.loads((HERE / 'data/source_checks.json').read_text())
    checks['main_results_evidence_level'] = compact['status']
    checks['measured_result_sources'] = len(data['sources'])
    for name in ['data/main_results.json', 'data/verified_results.json']:
        checks['files'][name] = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    dump(HERE / 'data/source_checks.json', checks)
    dump(HERE / 'data/result_validation.json', {
        'status': 'passed', 'model_runs': 0, 'source_files': len(data['sources']),
        'clip_prototype_cells': 9, 'clip_formal_seeds': formal['n'],
        't5_base_seeds': {r['key']: r['base']['n'] for r in data['t5']['rows']},
        'llm_pairs': len(data['llm']), 'llm_positive_gsm8k_pairs': 9,
        'missing_vision_baseline_cells': missing,
        'missing_formal_clip_scale_cells': 8,
        'missing_normalized_values': [{'architecture': c['architecture'], 'tasks': c['tasks'], 'method': key}
                                      for c, cell in zip(vision['columns'], vision['cells']) for key, r in cell.items() if r['normalized'] is None],
        't5_zero_shot_tasks': list(data['t5']['partial_base']['per_task']),
        't5_expert_diagonal_tasks': list(data['t5']['partial_expert']['per_task']),
        'notes': ['No synthetic scores or errors.', 'Differences computed before rounding.',
                  'T5 full averages require eight tasks.', 'Source paths retain historical filenames; no historical-method result rows.']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    if args.workspace:
        importer = Importer(args.workspace.resolve())
        data = {'audit_date': '2026-09-16', 'scope': 'CM, explicitly labeled CM variants, and external reference methods',
                'vision': importer.clip(), 't5': importer.t5(), 'llm': importer.llm()}
        data['sources'] = sorted(importer.sources.values(), key=lambda r: r['path'])
        dump(HERE / 'data/verified_results.json', data)
    else:
        data = json.loads((HERE / 'data/verified_results.json').read_text())
    render(data)
    print(f'Rendered 11 tables from {len(data["sources"])} measured source files; no model runs.')


if __name__ == '__main__':
    main()
