"""Audit existing configurations without loading models or launching experiments.

Run from the manuscript repository: python3 motivation_method/audit_protocols.py --workspace ..
The published score snapshot is read only. Raw arguments and missing metadata are preserved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
TASKS = ['cola', 'mnli', 'mrpc', 'qnli', 'qqp', 'rte', 'sst2', 'stsb']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--verify-caches', action='store_true', help='CPU-only torch check of cached T5 sample indices and tokens')
    args = p.parse_args()
    root = args.workspace.resolve()
    sources, runs = {}, []

    def read(path):
        path = Path(path)
        if path.is_absolute():
            path = path.relative_to(root)
        raw = (root / path).read_bytes()
        sources[str(path)] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
        return json.loads(raw)

    published = json.loads((HERE / 'data/verified_results.json').read_text())
    paper_sources = {s['path'] for s in published['sources']}
    for path in sorted((root / 'experiments/nlp_runs/merged').glob('*.log.json')):
        if not any(s in path.name for s in ('coexist', 'featcal')):
            continue
        log = read(path)
        a = log['args']
        name = path.name.removesuffix('.log.json')
        result_path = 'experiments/nlp_runs/results/' + name + '.json'
        result = read(result_path) if (root / result_path).exists() else None
        complete = result is not None and all(t in result for t in TASKS)
        is_cm = a.get('method', '').startswith('coexist')
        inferred = {}
        if is_cm and 'target_alpha' not in a:
            inferred['target_alpha'] = '0; legacy implementation before the optional target extension'
        if is_cm and 'freeze_head' not in a:
            inferred['freeze_head'] = 'false; legacy head solve, not an explicit logged argument'
        if is_cm and a.get('alpha') is None and a.get('init') == 'iso_c':
            inferred['init_scale'] = '1.3; merge_t5.py method default'
        runs.append({
            'id': name, 'family': 'T5', 'setting': 'large' if name.startswith('t5l_') else 'base',
            'implementation': 'nlp/merge_t5.py' if is_cm else 'nlp/featcal_t5.py',
            'method': 'CM' if is_cm else 'FeatCal port', 'seed': a['seed'], 'seed_evidence': 'logged',
            'target_interpolation': a.get('target_alpha', 0) if is_cm else None,
            'featcal_interpolation': None if is_cm else a['alpha'],
            'stats_samples_per_task': a['n'], 'holdout_samples_per_task': a.get('holdout', 0),
            'max_rounds': a.get('rounds', 1), 'cg_iterations': a.get('cg'),
            'solver_initialization': 'current model' if is_cm else 'direct linear solve; no CG',
            'raw_args': a, 'inferred_defaults': inferred,
            'complete_evaluation': complete, 'in_published_snapshot': result_path in paper_sources,
            'score': statistics.mean(result[t]['value'] for t in TASKS) if complete else None,
            'result_source': result_path if result else None, 'config_source': str(path.relative_to(root)),
        })

    # Include every CM workbench sensitivity record, not just favorable/published points.
    main_sources = {c['cm_prototype']['source'] for c in published['vision']['cells']}
    for path in sorted((root / 'wb/results_ablation').glob('*.json')):
        try:
            content = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(content, dict):
            continue
        for name, record in content.items():
            if not isinstance(record, dict) or record.get('args', {}).get('gkind') != 'chi2':
                continue
            read(path)
            a = record['args']
            hist = [h for h in record.get('hist', []) if isinstance(h.get('round'), int)]
            complete = bool(hist and hist[-1]['round'] == a['rounds'])
            selected = min((h for h in hist if h.get('hold_kl') is not None),
                           key=lambda h: (h['hold_kl'], h['round']), default=None)
            rel = str(path.relative_to(root))
            runs.append({'id': name, 'family': 'CLIP', 'setting': a['arch'] + '/' + str(a['tasks']),
                         'implementation': 'workbench', 'method': 'CM', 'seed': a['seed'],
                         'seed_evidence': 'logged', 'target_interpolation': 0,
                         'featcal_interpolation': None, 'stats_samples_per_task': a['n'],
                         'holdout_samples_per_task': a['n'] if a['holdout'] else 0,
                         'max_rounds': a['rounds'], 'cg_iterations': a['cg'], 'raw_args': a,
                         'solver_initialization': 'expert weight average (mats_bfm default)',
                         'complete_evaluation': complete, 'in_published_snapshot': rel in paper_sources,
                         'systematic_main_cell': rel in main_sources,
                         'score': selected['avg'] if complete and selected else None,
                         'config_source': rel, 'result_source': rel})

    formal = published['vision']['formal']
    for r in formal['runs']:
        d = read(r['source'])
        m = d['methods']['coexist-merge']
        a = m['selected_hyperparameters']
        runs.append({'id': Path(r['source']).stem, 'family': 'CLIP', 'setting': 'ViT-B-32/8',
                     'implementation': 'formal', 'method': 'CM', 'seed': r['seed'],
                     'seed_evidence': 'logged', 'target_interpolation': 0,
                     'featcal_interpolation': None, 'stats_samples_per_task': a['calibration_samples_per_task'],
                     'holdout_samples_per_task': a['holdout_samples_per_task'],
                     'max_rounds': 4, 'cg_iterations': 100, 'raw_args': a,
                     'solver_initialization': 'current model',
                     'budget_evidence': d['configuration_source'], 'complete_evaluation': True,
                     'in_published_snapshot': True, 'config_source': r['source'], 'result_source': r['source'],
                     'score': r['metrics']['absolute_accuracy_mean']})

    # Old LLM logs predate --seed. Historical commit 43d4206 shows the old call used
    # calib.texts without a seed argument; wb/llm/calib.py defaults to 42, not zero.
    llm_rows = []
    for r in published['llm']:
        checkpoint = Path(r['GSM8K_after_source']).parts[2].removeprefix('gsm8k_')
        llm_rows.append((checkpoint, r['GSM8K_after_source'], r))
    for seed in [1, 2]:
        checkpoint = f'L1_coexist_isoc_s{seed}'
        matches = sorted((root / 'assets/lmeval' / ('gsm8k_' + checkpoint)).glob('*/results_*.json'))
        assert len(matches) == 1, checkpoint
        llm_rows.append((checkpoint, str(matches[0].relative_to(root)), None))
    for checkpoint, result_path, row in llm_rows:
        config_path = f'assets/ckpt/merged/{checkpoint}/ink_hist.json'
        d, result = read(config_path), read(result_path)
        a = d['args']
        runs.append({'id': checkpoint, 'family': 'LLM', 'setting': a['model'],
                     'implementation': 'wb/llm/ink_llm.py', 'method': 'CM',
                     'seed': a.get('seed', 42),
                     'seed_evidence': 'logged' if 'seed' in a else 'historical default; git commit 43d4206 and calib.texts default',
                     'target_interpolation': 0, 'featcal_interpolation': None,
                     'stats_samples_per_task': a['n'], 'holdout_samples_per_task': a['n'],
                     'max_rounds': a['rounds'], 'cg_iterations': a['cg'], 'raw_args': a,
                     'solver_initialization': 'expert weight average (mats_bfm default)',
                     'complete_evaluation': True, 'evaluation_scope': 'GSM8K; see available_metrics',
                     'available_metrics': ['GSM8K'] + ([k for k in ['IFEval', 'multilingual'] if row[k + '_after'] is not None] if row else []),
                     'in_published_snapshot': row is not None,
                     'score': 100 * result['results']['gsm8k']['exact_match,flexible-extract'],
                     'evaluation_config': result['config'], 'evaluation_git_hash': result.get('git_hash'),
                     'config_source': config_path, 'result_source': result_path})

    # Paired target study: use the intersection, never compare different-size means.
    groups = {}
    by_id = {r['id']: r for r in runs}
    for key in ['cm', 'featcal', 'cm_target03', 'cm_target06']:
        row = next(r for r in published['t5']['rows'] if r['key'] == key)
        ids = [Path(s).stem for s in row['base']['sources']]
        group = [by_id[i] for i in ids]
        assert all(r['complete_evaluation'] for r in group)
        groups[key] = {'seeds': [r['seed'] for r in group], 'run_ids': ids,
                       'values': [r['score'] for r in group]}
        assert all(abs(x - y) < 1e-10 for x, y in zip(groups[key]['values'], row['base']['values']))
    shared = sorted(set.intersection(*(set(g['seeds']) for g in groups.values())))
    assert shared == [0, 1, 2]
    for group in groups.values():
        vals = dict(zip(group['seeds'], group['values']))
        v = [vals[s] for s in shared]
        group['paired_seeds'] = shared
        group['paired_mean'] = statistics.mean(v)
        group['paired_sample_sd'] = statistics.stdev(v)

    # Verify the CM sweeps differ only in the named intervention, apart from legacy
    # omitted defaults, output paths, seeds, and completed/selected round outcomes.
    cm_ids = sum((groups[k]['run_ids'] for k in ['cm', 'cm_target03', 'cm_target06']), [])
    comparisons = []
    for name in cm_ids:
        a = by_id[name]['raw_args']
        assert (a['n'], a['holdout'], a['rounds'], a['cg'], a['seed']) == (256, 256, 4, 100, by_id[name]['seed'])
        assert a['init'] == 'iso_c' and a['alpha'] is None and not a.get('freeze_head', False)
        assert not a['no_line_search']
        comparisons.append(name)

    cache_checks = []
    if args.verify_caches:
        import torch
        for size, folder in [('base', 'cache'), ('large', 'cache_large')]:
            for seed in range(5 if size == 'base' else 1):
                for task in TASKS:
                    cal = Path('experiments/nlp_runs', folder, f'{task}__train__calib_n256_seed{seed}.pt')
                    both = cal.with_name(f'{task}__train__calib_n512_seed{seed}.pt')
                    x = torch.load(root / cal, map_location='cpu', weights_only=False)
                    y = torch.load(root / both, map_location='cpu', weights_only=False)
                    ids, all_ids = x['index'].tolist(), y['index'].tolist()
                    assert ids == all_ids[:256] and not set(ids).intersection(all_ids[256:])
                    assert torch.equal(x['input_ids'], y['input_ids'][:256])
                    cache_checks.append({'size': size, 'seed': seed, 'task': task,
                                         'same_statistics_indices_and_tokens': True,
                                         'disjoint_holdout': True,
                                         'statistics_index_sha256': hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
                                         'holdout_index_sha256': hashlib.sha256(json.dumps(all_ids[256:]).encode()).hexdigest(),
                                         'calibration_cache': str(cal), 'calibration_and_holdout_cache': str(both)})
        (HERE / 'data/calibration_cache_audit.json').write_text(json.dumps(cache_checks, indent=2) + '\n')

    for rel in ['nlp/merge_t5.py', 'nlp/featcal_t5.py', 'nlp/glue_data.py', 'nlp/kfac_targets.py',
                'wb/run_iter.py', 'wb/wbench/merge_data.py', 'wb/llm/ink_llm.py', 'wb/llm/calib.py',
                'github/configurations/clip-vit-base-patch32-eight-tasks.yaml']:
        sources[rel] = {'path': rel, 'sha256': hashlib.sha256((root / rel).read_bytes()).hexdigest(),
                        'role': 'audit-time code/configuration; not a claim of historical run commit identity'}

    output = {'date': '2026-09-16', 'scope': 'existing CM runs and T5 FeatCal ports; no GPU runs',
              'published_snapshot_sha256': hashlib.sha256((HERE / 'data/verified_results.json').read_bytes()).hexdigest(),
              'runs': runs, 't5_seed_cohorts': groups, 't5_common_seed_intersection': shared,
              't5_cm_core_configuration_checks': comparisons,
              'sources': list(sources.values())}
    (HERE / 'data/protocol_audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    fields = ['id', 'family', 'setting', 'implementation', 'method', 'seed', 'seed_evidence',
              'target_interpolation', 'featcal_interpolation', 'stats_samples_per_task',
              'holdout_samples_per_task', 'max_rounds', 'cg_iterations', 'solver_initialization', 'complete_evaluation',
              'in_published_snapshot', 'score', 'config_source', 'result_source']
    with (HERE / 'data/protocol_runs.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        writer.writerows(runs)

    gaps = []
    seeds = [0, 1, 2, 3, 4]
    for col in published['vision']['columns']:
        gaps.append({'family': 'CLIP', 'setting': col['architecture'] + '/' + str(col['tasks']),
                     'implementation': 'workbench', 'method': 'CM + Iso-C',
                     'completed_seeds': [0], 'missing_seeds': [1, 2, 3, 4],
                     'strict_aligned_protocol': 'all five seeds require new runs if CG initialization changes to current model',
                     'status': 'not_launched; freeze code and asset/split fingerprints before reuse'})
    gaps.append({'family': 'CLIP', 'setting': 'ViT-B-32/8', 'implementation': 'formal',
                 'method': 'CM + Iso-C', 'completed_seeds': [0, 1, 2, 3], 'missing_seeds': [4],
                 'status': 'not_launched; separate cohort, not pooled with workbench'})
    for size in ['base', 'large']:
        for key in ['cm', 'featcal', 'cm_target03', 'cm_target06']:
            complete = groups[key]['seeds'] if size == 'base' else ([0] if key != 'cm_target06' else [])
            gaps.append({'family': 'T5', 'setting': size, 'method': key,
                         'completed_seeds': complete, 'missing_seeds': [s for s in seeds if s not in complete],
                         'status': 'not_launched' if len(complete) < 5 else 'existing_default_pipeline_cohort_complete',
                         'note': 'large target 0.6 seed 0 has merge log but no complete evaluation' if size == 'large' and key == 'cm_target06' else 'data-budget comparison remains separately labeled'})
    for row in published['llm']:
        completed = [1, 2] if row['model'] == 'Llama-3.2-3B' and row['start'] == 'Iso-C' else []
        gaps.append({'family': 'LLM', 'setting': row['model'], 'method': 'CM + ' + row['start'],
                     'completed_seeds_GSM8K': completed, 'historical_seed': 42,
                     'missing_seeds_GSM8K': [s for s in seeds if s not in completed],
                     'missing_seeds_full_five_domain_evaluation': seeds,
                     'strict_aligned_protocol': 'all five seeds require new runs if CG initialization changes to current model',
                     'status': 'not_launched; verify upstream checkpoint seed; rebuild data-driven upstream per seed'})
    policy = {'version': 'audit-followup-v1', 'date': '2026-09-16', 'status': 'plan_only_no_jobs_launched',
              'not_retrospective_preregistration': True, 'seeds': seeds,
              'default_cm': {'initialization': 'Iso-C', 'init_scale': 1.3, 'target_interpolation': 0,
                             'statistics_samples_per_task_or_domain': 256, 'holdout_samples_per_task_or_domain': 256,
                             'max_rounds': 4, 'cg_max_iterations': 100, 'input_shrinkage': 0,
                             'cg_initialization': 'current model; requires solver change for legacy workbench/LLM before execution',
                             'output_shrinkage': 'automatic', 'remeasure_each_round': True,
                             'selection': 'held-out teacher KL only'},
              'registered_family_adaptations': {
                  'CLIP_workbench': 'historical expert-mean CG and old block refinement; archive only if switching to the strict aligned profile',
                  'CLIP_formal': 'explicit zero candidate, formal block search; separate cohort',
                  'T5': 'teacher-forced teacher answers, global search, input-only lm_head solve',
                  'LLM': 'teacher top-128, length 1024, global search/rejection, base embeddings/lm_head, Gemma eager attention; old expert-mean CG must be changed for strict alignment'},
              't5_target_ablation': {'target_interpolation_candidates': [0, 0.3, 0.6], 'seeds': seeds,
                                     'settings': ['base', 'large'], 'role': 'separate_extension_not_default_CM'},
              'pairing_requirements': ['same checkpoint and expert fingerprints', 'same task list and split manifests',
                                       'same statistics and disjoint holdout IDs per seed', 'same tokenizer and eval revision',
                                       'same method configuration except named intervention', 'matched upstream seed for data-driven starts',
                                       'candidate selection cannot use final evaluation scores'],
              'budget_reporting': 'Report unique samples, calibration passes, selection budget and compute separately; no claim that original FeatCal used the CM holdout.',
              'existing_run_reuse_gate': 'Missing seeds are necessary, not sufficient: historical runs can join only after code/config/data fingerprint equivalence is checked.',
              'coverage_semantics': 'completed/missing seed lists describe historical protocols; they are not completed runs of the proposed strict profile.',
              'implementation_work_required': ['Unify CG initialization to current model in workbench and LLM before strict-profile runs.',
                                               'Freeze and record global/block candidate grids, rejection tolerances, precision, teacher and output-head policy per family.',
                                               'Do not retrofit changed solver settings onto already measured scores.'],
              'groups': gaps,
              'remaining_scope': ['Inventory and repeat other stochastic baselines under the same seeds; do not duplicate deterministic baselines.',
                                  'Initialization/stacking/sensitivity groups require paired repetitions; current single-seed records are exploratory.',
                                  'CLIP/LLM target interpolation extension is not implemented/validated as a reported result.',
                                  'Common-start and equal-total-data-budget FeatCal comparisons need separate controlled runs; current default-pipeline scores do not fill these slots.']}
    (HERE / 'data/alignment_plan.json').write_text(json.dumps(policy, ensure_ascii=False, indent=2) + '\n')
    print(f'Audited {len(runs)} runs and {len(sources)} sources. No models loaded or experiments run.')


if __name__ == '__main__':
    main()
