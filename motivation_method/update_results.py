"""Import measured IF-Merge results and render paper tables, without running models.

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
START_LABELS = {'iso_c': 'Iso-C', 'isoc': 'Iso-C', 'average': 'WeightAvg',
                'ta': 'Task Arithmetic', 'tsv_m': 'TSV-M', 'regmean': 'RegMean',
                'zeroshot': 'Zero-shot', 'unflattened_matched': '未拉平控制'}
LLM_START_LABELS = {'Soup': 'Model Soup', 'TA': 'Task Arith. 0.4',
                    'TIES': 'TIES 0.3/0.4', 'TSV-M': 'TSV-M',
                    'RegMean 0.5': 'RegMean 0.5', 'Iso-C': 'Iso-C 1.3'}
VISION_METHODS = [
    ('ft', 'Individual FT'), ('zeroshot', 'Zero-shot'),
    ('average', 'WeightAvg'), ('ta', 'Task Arith.'), ('ties', 'TIES'),
    ('consensus', 'Consensus TA'), ('iso_c', 'Iso-C'), ('iso_cts', 'Iso-CTS'),
    ('tsv_m', 'TSV-M'), ('regmean', 'RegMean'), ('wudi', 'WUDI'),
    ('lines', 'LiNeS (Iso-C)'), ('com', 'CoM'), ('esm', 'ESM'),
    ('svc', 'SVC (Iso-CTS)'), ('svc_on_esm', 'SVC (ESM)'),
    ('cm_prototype', '\method{} + Iso-C'),
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
            selected = min((h for h in hist if h.get('hold_kl') is not None), key=lambda h: (h['hold_kl'], h['round']))
            starts.append({'key': key, 'before': hist[0]['avg'], 'after': hist[-1]['avg'],
                           'selected_accuracy': selected['avg'], 'selected_round': selected['round'],
                           'seed': r['args']['seed'], 'source': source})
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
        completion_source = 'docs/experiment_inventory/2026-09-16/remote_snapshot/reports/latex/cm_multistart_motivation/data/original/completion.json'
        completion = self.read(completion_source)
        paired_starts = []
        for key in ['isoc', 'average', 'regmean', 'unflattened_matched']:
            r = completion['final_results'][key]
            assert abs(stats.mean(r['per_task_test_accuracy'].values()) - r['mean_test_accuracy']) < 1e-8
            paired_starts.append({'key': key, 'accuracy': r['mean_test_accuracy'],
                                  'per_task': r['per_task_test_accuracy'], 'seed': completion['seed'],
                                  'selected_round': r['selected_round'], 'source': completion_source,
                                  'source_commit': completion['source_commit']})
        sensitivity = []
        paths = sorted({p for pattern in ['abl_budget_coexist_*.json', 'abl_scale_*.json', 'abl_hp_coexist_isoalpha*.json']
                        for p in (self.workspace / 'wb/results_ablation').glob(pattern)})
        for p in paths:
            source = str(p.relative_to(self.workspace))
            for tag, r in self.read(source).items():
                a = r.get('args', {})
                if a.get('gkind') != 'chi2':
                    continue
                hist = [h for h in r['hist'] if isinstance(h.get('round'), int)]
                selected = min((h for h in hist if h.get('hold_kl') is not None), key=lambda h: (h['hold_kl'], h['round']))
                sensitivity.append({'tag': tag, 'key': a['init'], 'init_scale': a.get('init_alpha'),
                                    'round_budget': a['rounds'], 'completed_rounds': hist[-1]['round'],
                                    'seed': a['seed'], 'before': hist[0]['avg'], 'selected_accuracy': selected['avg'],
                                    'selected_round': selected['round'], 'last_accuracy': hist[-1]['avg'], 'source': source})
        return {'columns': columns, 'cells': cells, 'formal': formal, 'starts': starts,
                'paired_starts': paired_starts, 'start_sensitivity': sensitivity,
                'default_initialization': 'Iso-C', 'default_initialization_scale': 1.3}

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
            ('cm', '\method{} + Iso-C', ['t5_coexist_n256'] + [f't5_coexist_seed{i}' for i in range(1, 5)], ['t5l_coexist']),
            ('cm_target03', '\method{} + Iso-C（目标插值 0.3）', ['t5_coexist_tgt0.3'] + [f't5_coexist_tgt0.3_seed{i}' for i in range(1, 4)], ['t5l_coexist_tgt0.3']),
            ('cm_target06', '\method{} + Iso-C（目标插值 0.6）', ['t5_coexist_tgt0.6'] + [f't5_coexist_tgt0.6_seed{i}' for i in range(1, 3)], None),
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
        for label, before_b, original_b, extension_b, before_l, original_l in [
            ('Iso-C', 't5_iso_c1.3', 't5_coexist_n256', 't5_coexist_tgt0.3', 't5l_iso_c1.3', 't5l_coexist'),
            ('FeatCal (TA)', 't5_featcal', 't5_coexist_from_featcal', 't5_stack_tgt0.3_from_featcal', 't5l_featcal', 't5l_stack_coexist_from_featcal'),
            ('RegMean', 't5_regmean0.9', 't5_coexist_from_regmean0.9', 't5_stack_tgt0.3_from_regmean0.9', 't5l_regmean0.9', None),
            ('TSV-M', 't5_tsv_m', None, 't5_stack_tgt0.3_from_tsv_m', 't5l_tsv_m', 't5l_stack_coexist_from_tsv_m'),
            ('Task Arithmetic', 't5_ta0.3', None, 't5_stack_tgt0.3_from_ta0.3', 't5l_ta0.3', None),
        ]:
            groups = {key: group([name]) if name else None for key, name in zip(
                ['base_before', 'base_original', 'base_target03', 'large_before', 'large_original'],
                [before_b, original_b, extension_b, before_l, original_l])}
            starts.append({'label': label, **groups})
        postprocessing = [{'setting': setting, 'cm_variant': variant, 'result': group([name])}
                          for setting, variant, name in [('base', 'original', 't5_featcal_on_coexist'),
                                                         ('base', 'target0.3', 't5_stack_featcal_on_tgt0.3'),
                                                         ('large', 'original', 't5l_stack_featcal_on_coexist')]]
        return {'rows': rows, 'partial_base': partial, 'partial_expert': partial_expert, 'starts': starts,
                'featcal_after_cm': postprocessing, 'default_initialization': 'Iso-C', 'default_initialization_scale': 1.3}

    def llm(self):
        rows = self.read('docs/experiment_inventory/2026-09-16/llm_hotplug.csv')
        for r in rows:
            checkpoint = Path(r['GSM8K_after_source']).parts[2].removeprefix('gsm8k_')
            config_source = f'assets/ckpt/merged/{checkpoint}/ink_hist.json'
            args = self.read(config_source)['args']
            r['calibration_seed'] = args.get('seed', 42)
            r['calibration_seed_evidence'] = ('logged' if 'seed' in args else
                'historical default: commit 43d4206 added explicit seed; prior calib.texts default was 42')
            r['merge_config_source'] = config_source
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


def render_initialization_catalog(data):
    """Keep initialization studies discoverable without mixing their protocols."""
    vision = data['vision']
    formal = vision['formal']
    ft = formal['expert']['absolute_accuracy_mean']
    wb_ft = vision['cells'][0]['ft']['accuracy']
    records = []

    def add(family, setting, protocol, initialization, score, sources, *,
            seeds='0', n=1, variant='original', before=None, last=None,
            ft_reference=None, init_scale=None, round_budget=None):
        records.append({'family': family, 'setting': setting, 'protocol': protocol,
                        'initialization': initialization, 'cm_variant': variant,
                        'seed_count': n, 'seeds': seeds, 'init_scale': init_scale,
                        'round_budget': round_budget, 'initial_score': before,
                        'reported_score': score, 'last_round_score': last,
                        'individual_ft': ft_reference,
                        'delta_vs_ft_pp': score - ft_reference if ft_reference is not None else None,
                        'sources': ';'.join(sources)})

    add('CLIP', 'ViT-B/32 / 8', 'benchmark repeated calibration', 'Iso-C',
        formal['mean'], [r['source'] for r in formal['runs']],
        seeds=','.join(str(r['seed']) for r in formal['runs']), n=formal['n'], ft_reference=ft, init_scale=1.3)
    for r in vision['paired_starts']:
        add('CLIP', 'ViT-B/32 / 8', 'benchmark paired initialization study', START_LABELS[r['key']],
            r['accuracy'], [r['source']], seeds=str(r['seed']), ft_reference=ft, round_budget=4)
    for r in vision['starts']:
        add('CLIP', 'ViT-B/32 / 8', 'workbench paired initialization study', START_LABELS[r['key']],
            r['selected_accuracy'], [r['source']], seeds=str(r['seed']), before=r['before'],
            last=r['after'], ft_reference=wb_ft, round_budget=4)
    for r in vision['start_sensitivity']:
        add('CLIP', 'ViT-B/32 / 8', r['tag'], START_LABELS[r['key']], r['selected_accuracy'], [r['source']],
            seeds=str(r['seed']), before=r['before'], last=r['last_accuracy'], ft_reference=wb_ft,
            init_scale=r['init_scale'], round_budget=r['round_budget'])
    for r in data['t5']['starts']:
        for key, size, variant in [('base_original', 'base', 'original'),
                                    ('base_target03', 'base', 'target interpolation 0.3'),
                                    ('large_original', 'large', 'original')]:
            if r[key] is not None:
                before = r[size + '_before']
                add('T5', size, 'paired initialization study', r['label'], r[key]['mean'], r[key]['sources'],
                    variant=variant, before=before['mean'] if before else None)
    for r in data['llm']:
        add('LLM', r['model'], 'paired initialization study; GSM8K', LLM_START_LABELS[r['start']],
            r['GSM8K_after'], [r['GSM8K_before_source'], r['GSM8K_after_source'], r['merge_config_source']],
            seeds=str(r['calibration_seed']), before=r['GSM8K_before'])
    with (HERE / 'data/cm_initializations.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)

    def md_table(headers, values):
        return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] + [
            '| ' + ' | '.join(str(v) for v in vs) + ' |' for vs in values] + ['']

    def score(group):
        return f'{group["mean"]:.2f}' if group else '—'

    lines = ['# IF-Merge 起点实验清单', '',
             '由 update_results.py 从核验快照生成。IF-Merge + X 表示先用 X 初始化，再运行 IF-Merge。'
             '主配置是 **IF-Merge + Iso-C**，CLIP 与 T5 默认初始化尺度为 1.3。', '',
             '“原型 / 正式”是实现记录的来源；“4 seeds”是四次校准随机种子的重复，均不是新的方法名。'
             '不同实现、目标设定和轮数分别比较。Delta 使用百分点，负值表示低于 Individual FT。', '',
             '## CLIP：固定基准实现，ViT-B/32 八任务', '',
             '四种子主实验与单种子起点研究是独立运行记录。后者按留出集选中第 4 轮。', '']
    lines += md_table(['配置', 'seeds', 'test 宏平均', 'Delta vs. FT'],
                     [['Individual FT', '—', f'{ft:.2f}', '0.00']] +
                     [['IF-Merge + ' + START_LABELS[r['key']], 1, f'{r["accuracy"]:.2f}', f'{r["accuracy"]-ft:+.2f}']
                      for r in vision['paired_starts']] +
                     [['IF-Merge + Iso-C（主实验）', formal['n'], f'{formal["mean"]:.3f}（样本标准差 {formal["sample_sd"]:.3f}）', f'{formal["mean"]-ft:+.2f}']])
    lines += ['## CLIP：工作台同配置换起点，ViT-B/32 八任务', '',
              '均为 seed 0、四轮预算；正文规模表使用留出集选轮后的结果。末轮分数单列供追溯。', '']
    lines += md_table(['配置', '起点', '留出选轮', '末轮', 'Delta vs. FT'],
                     [['IF-Merge + ' + START_LABELS[r['key']], f'{r["before"]:.2f}', f'{r["selected_accuracy"]:.2f}',
                       f'{r["after"]:.2f}', f'{r["selected_accuracy"]-wb_ft:+.2f}'] for r in vision['starts']])
    lines += ['## T5：同一 seed 0 的起点对照', '',
              'FeatCal 起点先由 Task Arithmetic 合并再进行 FeatCal。原始目标与目标插值是不同 IF-Merge 配置。'
              '缺测留空；缺少完整的 Individual FT 对角参考，因此不推算八任务 FT 差距。', '']
    lines += md_table(['配置', 'base 起点', 'base 原始目标', 'base 插值 0.3', 'large 起点', 'large 原始目标'],
                     [['IF-Merge + ' + r['label']] + [score(r[k]) for k in ['base_before', 'base_original', 'base_target03', 'large_before', 'large_original']]
                      for r in data['t5']['starts']])
    lines += ['另有相反顺序的后处理：先 IF-Merge，再 FeatCal；这些不计作 IF-Merge 初始化实验。', '']
    lines += md_table(['模型', '前序 IF-Merge 配置', '再做 FeatCal 的八任务分数'],
                     [[r['setting'], r['cm_variant'], score(r['result'])] for r in data['t5']['featcal_after_cm']])
    lines += ['## LLM：已完成的十组起点对照', '',
              '十组的校准种子均为 42（旧日志未显式记录时，由历史默认调用确认），不是 seed 0。'
              '下面是 GSM8K；IFEval 及 Llama 三域结果见论文正文和完整快照。起点增益与 FT 差距不是同一指标。'
              '版本、目标插值和五种子补齐规范见 [协议对齐清单](PROTOCOL_ALIGNMENT.md)。', '']
    lines += md_table(['模型', '配置', '起点', 'IF-Merge 后', '起点增益'],
                     [[r['model'], 'IF-Merge + ' + LLM_START_LABELS[r['start']], f'{r["GSM8K_before"]:.2f}',
                       f'{r["GSM8K_after"]:.2f}', f'{r["GSM8K_difference_pp"]:+.2f}'] for r in data['llm']])
    lines += ['另外找到 Llama 的 RegMean 0.9 合并命令及完成标记，未找到可配对的完整评测，故不填成绩。'
              '命令记录为 experiments/github_runs/logs/llm_coexist_from_regmean0.9.cmd.sh。', '',
              '## CLIP：起点尺度与轮数补充', '',
              '这是参数敏感性记录，不作为新的起点方法，也不混入四轮默认对照。', '']
    lines += md_table(['记录', '起点', '尺度', '轮数预算', '留出选轮分数', '末轮分数'],
                     [[r['tag'], START_LABELS[r['key']], r['init_scale'] if r['init_scale'] is not None else '默认', r['round_budget'],
                       f'{r["selected_accuracy"]:.2f}', f'{r["last_accuracy"]:.2f}'] for r in vision['start_sensitivity']])
    lines += ['## 逐项来源', '',
              '[CSV 清单](data/cm_initializations.csv) 保存每项配置、完整精度数值、种子和来源文件；'
              '[核验快照](data/verified_results.json) 保存逐任务结果与输入文件 SHA-256。'
              '来源路径相对实验工作区，历史文件名不代表另一个方法。', '']
    (HERE / 'INITIALIZATIONS.md').write_text('\n'.join(lines), encoding='utf-8')
    return len(records)


def render(data):
    vision = data['vision']
    formal = vision['formal']
    ft = formal['expert']['absolute_accuracy_mean']
    lines = [r'\begin{table}[!htbp]', r'\centering',
             r'\caption{CLIP 规模实验（单种子，\%）。主配置统一为 \method{} + Iso-C。单元格为任务宏平均准确率，下标为逐任务相对本环境专家的归一化均值。Delta 行为 \method{} 相对本列 Individual FT 的百分点差；负值表示低于 FT。--- 为缺测。}',
             r'\label{tab:ink-vision-summary}', r'\setlength{\tabcolsep}{2pt}', r'\renewcommand{\arraystretch}{1.12}',
             r'\resizebox{\textwidth}{!}{\begin{tabular}{@{}lccc|ccc|ccc@{}}', r'\toprule',
             row([r'\multirow{2}{*}{Method}', r'\multicolumn{3}{c}{ViT-B/32}', r'\multicolumn{3}{c}{ViT-B/16}', r'\multicolumn{3}{c}{ViT-L/14}']),
             r'\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(l){8-10}', row([''] + ['8 tasks', '14 tasks', '20 tasks'] * 3), r'\midrule']
    missing = []
    incomplete = [(key, label) for key, label in VISION_METHODS if any(key not in cell for cell in vision['cells'])]
    for key, label in VISION_METHODS:
        if any(key == k for k, _ in incomplete):
            missing.extend({'method': label, **column} for column, cell in zip(vision['columns'], vision['cells']) if key not in cell)
            continue
        if key == 'cm_prototype':
            lines.append(r'\rowcolor{black!8}')
            label = '\method{} + Iso-C'
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
    lines += [row(['Delta vs. FT'] + [f'{cell["cm_prototype"]["accuracy"]-cell["ft"]["accuracy"]:+.2f}' for cell in vision['cells']]),
              r'\bottomrule', r'\end{tabular}}', r'\par\smallskip',
              r'{\footnotesize \method{} + X 表示先用 X 初始化，再运行 \method{}。\method{} 的 Iso-C 初始化尺度固定为 1.3，按无标签留出 KL 选轮；外部基线各自按 validation 选参。本表仅纳入九格均有宏平均结果的规模实验，来源为工作台实现。固定基准实现的四种子与换起点实验单列于表~\ref{tab:clip-initializations}；覆盖未齐的 ESM、SVC (ESM) 移至附录表~\ref{tab:clip-scaling}。L/14 二十任务的三项谱方法只有日志宏平均，故其归一化下标留空。}', r'\end{table}']
    write_table('vision_summary', lines)

    lines = [r'\begin{table}[!htbp]', r'\centering\small',
             r'\caption{CLIP ViT-B/32 八任务：\method{} 的不同起点与主配置。种子数单列，不属于方法名称。Delta 为相对 Individual FT 的百分点差。}',
             r'\label{tab:clip-initializations}', r'\begin{tabular}{@{}lrrr@{}}', r'\toprule',
             row(['配置', 'seeds', 'test 宏平均', 'Delta vs. FT']), r'\midrule',
             row(['Individual FT', '---', f'{ft:.2f}', '0.00']),
             r'\multicolumn{4}{l}{\textit{同一 seed 0 的换起点对照}} \\']
    for r in vision['paired_starts']:
        lines.append(row(['\method{} + ' + START_LABELS[r['key']], '1', f'{r["accuracy"]:.2f}', f'{r["accuracy"]-ft:+.2f}']))
    lines += [r'\midrule', r'\rowcolor{black!8}', row(['\method{} + Iso-C（主实验）', str(formal['n']), tex_score(formal, 3), f'{formal["mean"]-ft:+.2f}']),
              r'\bottomrule', r'\end{tabular}', r'\par\smallskip',
              r'{\footnotesize 起点对照来自独立的四起点研究，未拉平起点为控制实验。下方单列主配置四次校准重复的均值及样本标准差。Delta 由未舍入分数计算。工作台还覆盖 TSV-M、Task Arithmetic 与 Zero-shot 起点，完整记录见表~\ref{tab:clip-starts}。}', r'\end{table}']
    write_table('clip_initializations', lines)

    base_rows = {r['key']: r for r in data['t5']['rows']}
    lines = [r'\begin{table}[!htbp]', r'\centering',
             r'\caption{Flan-T5-base 八专家一次性合并后的 GLUE validation 实测结果（FusionBench 口径）。前七任务为生成答案 exact match，STSB 为 Spearman；末列为八任务宏平均。}',
             r'\label{tab:ink-t5-results}', r'\setlength{\tabcolsep}{3pt}', r'\renewcommand{\arraystretch}{1.14}',
             r'\resizebox{\textwidth}{!}{\begin{tabular}{@{}lrrrrrrrr|c@{}}', r'\toprule',
             row(['Method', 'CoLA', 'MNLI', 'MRPC', 'QNLI', 'QQP', 'RTE', 'SST2', 'STSB', '平均']), r'\midrule',
             row(['Individual FT'] + [f'{data["t5"]["partial_expert"]["per_task"][t]:.2f}' if t in data['t5']['partial_expert']['per_task'] else '---' for t in GLUE] + ['---']),
             row(['Zero-shot'] + [f'{data["t5"]["partial_base"]["per_task"][t]:.2f}' if t in data['t5']['partial_base']['per_task'] else '---' for t in GLUE] + ['---']), r'\midrule']
    for r in data['t5']['rows']:
        if r['key'].startswith('cm_target'):
            continue
        if r['key'].startswith('cm'):
            lines.append(r'\rowcolor{black!8}')
        g = r['base']
        lines.append(row([r['label']] + [f'{g["per_task"][t]:.2f}' for t in GLUE] + [tex_score(g)]))
        if r['key'].startswith('cm'):
            expert = data['t5']['partial_expert']['per_task']
            lines.append(row(['Delta vs. FT'] + [f'{g["per_task"][t]-expert[t]:+.2f}' if t in expert else '---' for t in GLUE] + ['---']))
    lines += [r'\bottomrule', r'\end{tabular}}', r'\par\smallskip',
              r'{\footnotesize \method{} 使用原始目标，目标插值另见表~\ref{tab:t5-target-paired}。FeatCal 与 \method{} 均为 seed 0--4，误差为八任务均值的样本标准差；其它基线为单次记录。两方法统计样本相同，\method{} 另用每任务 256 条留出数据，且默认起点不同；本表比较默认流程，不声明相同总数据预算。Delta 相对实测 FT，负值表示低于 FT；独立专家仅有 CoLA 对角参考，其余留空。}', r'\end{table}']
    write_table('t5_results', lines)

    lines = [r'\begin{table}[htbp]', r'\centering\small',
             r'\caption{T5-base 目标插值消融：三行统一使用已完成的配对 seed 0、1、2。其它 \method{} 配置相同；误差为样本标准差。}',
             r'\label{tab:t5-target-paired}', r'\begin{tabular}{@{}lcc@{}}', r'\toprule',
             row(['\method{} 目标版本', 'seeds', '八任务宏平均']), r'\midrule']
    for key, label in [('cm', '原始目标'), ('cm_target03', '目标插值 0.3'), ('cm_target06', '目标插值 0.6')]:
        group = base_rows[key]['base']
        assert all(Path(s).stem.endswith(f'_seed{i}') for i, s in enumerate(group['sources'][1:3], 1))
        lines.append(row([label, '0, 1, 2', tex_score(summary(group['values'][:3]))]))
    lines += [r'\bottomrule', r'\end{tabular}', r'\par\smallskip',
              r'{\footnotesize 共同配置：Iso-C 1.3 起点，每任务统计 256、独立留出 256，四轮预算，CG 100 步，留出教师 KL 选步与选轮。完整 5/4/3 次记录保留在表~\ref{tab:t5-main}，不混成同一重复集合；两种扩展尚未补齐五种子。}', r'\end{table}']
    write_table('t5_target_paired', lines)

    lines = [r'\begin{table}[!htbp]', r'\centering\small',
             r'\caption{CLIP ViT-B/32 八任务：主配置 \method{} + Iso-C 与外部参照（\%）。采用固定基准实现，\method{} 为四种子均值及样本标准差，外部方法为已归档单次结果。}',
             r'\label{tab:clip-main}', r'\begin{tabular}{@{}lcc@{}}', r'\toprule', row(['方法', 'seeds', 'test 宏平均']), r'\midrule',
             row(['Individual FT', '---', f'{ft:.2f}'])]
    for key, label in VISION_METHODS:
        if key not in ['ft', 'cm_prototype']:
            lines.append(row([label, '1', f'${vision["cells"][0][key]["accuracy"]:.2f}$']))
    lines += [r'\rowcolor{black!8}', row(['\method{} + Iso-C', str(formal['n']), tex_score(formal, 3)]),
              row(['Delta vs. FT', '---', f'{formal["mean"]-ft:+.2f}']), r'\bottomrule', r'\end{tabular}', r'\end{table}']
    write_table('clip_main', lines)
    lines = [r'\begin{table}[!htbp]', r'\centering\small', r'\caption{规模实验补充（单种子）：\method{} + Iso-C 的起点收益、FT 差距及覆盖未齐的外部基线。--- 为缺测。}',
             r'\label{tab:clip-scaling}', r'\resizebox{\textwidth}{!}{\begin{tabular}{@{}l' + 'r' * (4 + len(incomplete)) + r'@{}}', r'\toprule',
             row(['设定', 'Iso-C 起点', '\method{} + Iso-C', '起点增益', 'Delta vs. FT'] + [label for _, label in incomplete]), r'\midrule']
    for c, cell in zip(vision['columns'], vision['cells']):
        r = cell['cm_prototype']
        lines.append(row([f'{c["architecture"]} / {c["tasks"]}', f'{r["initial_accuracy"]:.2f}', f'{r["accuracy"]:.2f}', f'{r["accuracy"]-r["initial_accuracy"]:+.2f}', f'{r["accuracy"]-cell["ft"]["accuracy"]:+.2f}'] +
                         [f'{cell[key]["accuracy"]:.2f}' if key in cell else '---' for key, _ in incomplete]))
    lines += [r'\bottomrule', r'\end{tabular}}', r'\end{table}']
    write_table('clip_scaling', lines)
    lines = [r'\begin{table}[!htbp]', r'\centering\small',
             r'\caption{Flan-T5 全部已有重复记录。上半表为默认流程，下半表为覆盖未齐的目标扩展；并非全表等种子、等预算比较。误差为样本标准差，large 各行均为 seed 0。}',
             r'\label{tab:t5-main}', r'\begin{tabular}{@{}lccc@{}}', r'\toprule', row(['方法', 'base', 'base seeds', 'large']), r'\midrule']
    for r in data['t5']['rows']:
        if r['key'] == 'cm_target03':
            lines.extend([r'\midrule', r'\multicolumn{4}{l}{\textit{扩展的全部记录；配对比较见表~\ref{tab:t5-target-paired}}} \\'])
        if r['key'].startswith('cm'):
            lines.append(r'\rowcolor{black!8}')
        lines.append(row([r['label'], tex_score(r['base']), str(r['base']['n']), tex_score(r['large'])]))
    lines += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    write_table('t5_main', lines)
    lines = [r'\begin{tabular}{@{}llcc@{}}', r'\toprule', row(['设定', '方法版本', '参照分数', '\method{}']), r'\midrule',
             row(['CLIP ViT-B/32', '\method{} + Iso-C / ESM', f'{vision["cells"][0]["esm"]["accuracy"]:.2f}', tex_score(formal)])]
    for size in ['base', 'large']:
        for key in ['cm']:
            lines.append(row(['T5-' + size, base_rows[key]['label'] + ' / FeatCal', tex_score(base_rows['featcal'][size]), tex_score(base_rows[key][size])]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('main_summary', lines)

    labels = LLM_START_LABELS
    for family, name, order in [('Llama-3.2-3B', 'llama_full', ['Iso-C', 'TSV-M', 'Soup', 'TA', 'TIES', 'RegMean 0.5']),
                                 ('Gemma-2-2B', 'gemma_full', ['Soup', 'TA', 'TIES', 'TSV-M'])]:
        is_llama = family.startswith('Llama')
        lines = [r'\begin{tabular}{@{}lrrrr' + ('rrr' if is_llama else 'r') + r'@{}}', r'\toprule',
                 row(['\method{} 配置', r'\multicolumn{3}{c}{GSM8K}', r'\multicolumn{2}{c}{IFEval}'] + ([r'\multicolumn{2}{c}{三域宏平均}'] if is_llama else [])),
                 r'\cmidrule(lr){2-4}\cmidrule(lr){5-6}' + (r'\cmidrule(l){7-8}' if is_llama else ''),
                 row(['', '起点', '+ \method{}', '差值', '起点', '+ \method{}'] + (['起点', '+ \method{}'] if is_llama else [])), r'\midrule']
        for start in order:
            r = next(r for r in data['llm'] if r['model'] == family and r['start'] == start)
            values = [f'{r[k]:.2f}' for k in ['GSM8K_before', 'GSM8K_after']] + [f'{r["GSM8K_difference_pp"]:+.2f}']
            values += [f'{r[k]:.2f}' for k in ['IFEval_before', 'IFEval_after'] + (['three_domain_before', 'three_domain_after'] if is_llama else [])]
            lines.append(row(['\method{} + ' + labels[start]] + values))
        lines += [r'\bottomrule', r'\end{tabular}']
        write_table(name, lines)
    lines = [r'\begin{tabular}{@{}llrrrr@{}}', r'\toprule',
             row(['模型', '\method{} 配置', r'\multicolumn{2}{c}{GSM8K}', r'\multicolumn{2}{c}{IFEval}']), r'\cmidrule(lr){3-4}\cmidrule(l){5-6}',
             row(['', '', '起点', '+ \method{}', '起点', '+ \method{}']), r'\midrule']
    for family, start in [('Llama-3.2-3B', 'Iso-C'), ('Llama-3.2-3B', 'TSV-M'), ('Llama-3.2-3B', 'RegMean 0.5'), ('Gemma-2-2B', 'Soup')]:
        r = next(r for r in data['llm'] if r['model'] == family and r['start'] == start)
        lines.append(row([family, '\method{} + ' + labels[start]] + [f'{r[k]:.2f}' for k in ['GSM8K_before', 'GSM8K_after', 'IFEval_before', 'IFEval_after']]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('llm_summary', lines)
    lines = [r'\begin{tabular}{@{}lrrrr@{}}', r'\toprule', row(['配置', '起点分', '留出选轮', '末轮', 'Delta vs. FT']), r'\midrule']
    for r in vision['starts']:
        lines.append(row(['\method{} + ' + START_LABELS[r['key']], f'{r["before"]:.2f}', f'{r["selected_accuracy"]:.2f}', f'{r["after"]:.2f}',
                          f'{r["selected_accuracy"]-vision["cells"][0]["ft"]["accuracy"]:+.2f}']))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('clip_starts', lines)
    lines = [r'\begin{tabular}{@{}lccccc@{}}', r'\toprule',
             row(['配置', r'\multicolumn{3}{c}{T5-base}', r'\multicolumn{2}{c}{T5-large}']),
             r'\cmidrule(lr){2-4}\cmidrule(l){5-6}', row(['', '起点', '\method{} 原始目标', '\method{} 插值 0.3', '起点', '\method{} 原始目标']), r'\midrule']
    for r in data['t5']['starts']:
        lines.append(row(['\method{} + ' + r['label']] + [tex_score(r[key]) for key in ['base_before', 'base_original', 'base_target03', 'large_before', 'large_original']]))
    lines += [r'\bottomrule', r'\end{tabular}']
    write_table('t5_starts', lines)
    # Keep the earlier machine-readable entry useful, but source every number
    # from the checked snapshot instead of the supplied, rounded prose table.
    compact = {
        'source_file': 'data/verified_results.json',
        'source_sha256': hashlib.sha256((HERE / 'data/verified_results.json').read_bytes()).hexdigest(),
        'status': 'Measured IF-Merge results, named by initialization. Implementation provenance, seeds and target variants are separate metadata. No model reruns.',
        'default_cm_initialization': {'clip': 'Iso-C', 't5': 'Iso-C', 'scale': 1.3},
        'clip_main': [['方法', 'test 宏平均']] + [[label, round(vision['cells'][0][key]['accuracy'], 2)] for key, label in VISION_METHODS if key != 'cm_prototype'],
        'clip_formal': {k: formal[k] for k in ['mean', 'sample_sd', 'n', 'values', 'normalized']},
        'clip_formal_delta_vs_ft_pp': formal['mean'] - ft,
        'clip_paired_initializations': vision['paired_starts'],
        'clip_workbench_initializations': vision['starts'],
        'clip_scaling': [{'architecture': c['architecture'], 'tasks': c['tasks'], **{k: cell['cm_prototype'][k] for k in ['initial_accuracy', 'accuracy', 'normalized', 'selection']}}
                         for c, cell in zip(vision['columns'], vision['cells'])],
        't5_main': data['t5']['rows'],
        't5_initializations': data['t5']['starts'],
        'llama': [r for r in data['llm'] if r['model'].startswith('Llama')],
        'gemma': [r for r in data['llm'] if r['model'].startswith('Gemma')],
    }
    initialization_records = render_initialization_catalog(data)
    dump(HERE / 'data/main_results.json', compact)
    checks = json.loads((HERE / 'data/source_checks.json').read_text())
    checks['main_results_evidence_level'] = compact['status']
    checks['measured_result_sources'] = len(data['sources'])
    for name in ['data/main_results.json', 'data/verified_results.json', 'data/cm_initializations.csv']:
        checks['files'][name] = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    dump(HERE / 'data/source_checks.json', checks)
    dump(HERE / 'data/result_validation.json', {
        'status': 'passed', 'model_runs': 0, 'source_files': len(data['sources']),
        'clip_prototype_cells': 9, 'clip_formal_seeds': formal['n'],
        'clip_formal_delta_vs_ft_pp': formal['mean'] - ft,
        'clip_paired_initializations': len(vision['paired_starts']),
        'clip_workbench_initializations': len(vision['starts']),
        'initialization_catalog_records': initialization_records,
        'vision_methods_moved_to_appendix': [label for _, label in incomplete],
        't5_base_seeds': {r['key']: r['base']['n'] for r in data['t5']['rows']},
        't5_target_comparison_seeds': [0, 1, 2],
        'llm_main_calibration_seeds': sorted(set(r['calibration_seed'] for r in data['llm'])),
        'llm_pairs': len(data['llm']), 'llm_positive_gsm8k_pairs': sum(r['GSM8K_difference_pp'] > 0 for r in data['llm']),
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
        data = {'audit_date': '2026-09-16', 'scope': 'IF-Merge, explicitly labeled IF-Merge variants, and external reference methods',
                'vision': importer.clip(), 't5': importer.t5(), 'llm': importer.llm()}
        data['sources'] = sorted(importer.sources.values(), key=lambda r: r['path'])
        dump(HERE / 'data/verified_results.json', data)
    else:
        data = json.loads((HERE / 'data/verified_results.json').read_text())
    render(data)
    print(f'Rendered result tables and initialization catalog from {len(data["sources"])} evidence source files; no model runs.')


if __name__ == '__main__':
    main()
