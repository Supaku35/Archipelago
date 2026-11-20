"""Offline draft location plan. Does not generate worlds, contact AP, or access the game bridge."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from catalog_chests import DEFAULT_CATALOG, load_catalog, parse_scan, save_catalog

# New seed IDs follow the catalog convention.
# Treasure IDs determine IDs; filtering/reordering never renumbers other chests.
DRAFT_BASE = 10_000_000
MAX_TREASURE_ID = 99_999
WORLD_LOCATIONS = Path(__file__).resolve().parents[1] / 'locations.py'


def current_locations():
    # Load only the standalone constants file, without importing worlds or AP.
    values = runpy.run_path(str(WORLD_LOCATIONS))
    rows = values['CHEST_CATALOG']
    existing = {treasure_id: (name, ap_id) for _, name, ap_id, treasure_id in rows}
    if len(existing) != len(rows) or values['location_name_to_id'] != {
        name: ap_id for name, ap_id in existing.values()
    }:
        raise ValueError('Inconsistent catalog chest mappings.')
    return existing


def build_plan(catalog, existing):
    if catalog.get('schema_version') != 1 or not isinstance(catalog.get('chests'), dict):
        raise ValueError('Unsupported catalog.')
    locations, excluded = [], []
    used_ids, used_names, treasure_ids = set(), set(), set()
    for key, entry in sorted(catalog['chests'].items(), key=lambda pair: int(pair[0])):
        if not key.isdigit() or not 0 <= int(key) <= MAX_TREASURE_ID:
            raise ValueError('Treasure ID outside draft allocation range: ' + key)
        ident = int(key)
        if ident in treasure_ids:
            raise ValueError('Duplicate numeric treasure ID: ' + key)
        treasure_ids.add(ident)
        area, label = entry.get('area', '').strip(), entry.get('label', '').strip()
        name = area + ' - ' + label
        reason = None
        if entry.get('record_classification') != 'user_reported_chest':
            reason = 'unclassified_record'
        elif entry.get('colour') == 'Blue':
            reason = 'blue_chest_access_unresolved'
        elif entry.get('access', {}).get('status') != 'initially_accessible':
            reason = 'starting_access_not_reported'
        elif entry.get('colour') not in ('Brown', 'Red') or not area or not label:
            reason = 'incomplete_label_or_colour'
        if reason:
            excluded.append({'game_treasure_id': ident, 'catalog_name': name, 'reason': reason})
            continue
        ap_name, ap_id = existing.get(ident, (name, DRAFT_BASE + ident))
        if type(ap_id) is not int or ap_id in used_ids or ap_name in used_names:
            raise ValueError('Duplicate or invalid proposed AP mapping: ' + name)
        used_ids.add(ap_id)
        used_names.add(ap_name)
        evidence = entry.get('opening_evidence', {})
        observed = evidence.get('previous_tick') == 0 and evidence.get('open_tick') == 999999999
        locations.append({
            'game_treasure_id': ident, 'ap_location_id': ap_id, 'name': ap_name,
            'catalog_name': name, 'area': area, 'colour': entry['colour'],
            'mapping_state': 'catalogued' if ident in existing else 'draft_only',
            'reported_contents': entry.get('contents', ''),
            'access_basis': 'user_reported_initial_access', 'ap_logic_verified': False,
            'completion_evidence': 'opening_transition_observed' if observed else
                'prior_manual_verification' if entry.get('mapping_status') == 'manually_verified' else 'needs_review',
        })
    selected = {row['game_treasure_id'] for row in locations}
    if set(existing) - selected:
        raise ValueError('Plan would exclude a catalogued location.')
    for entry in catalog.get('unidentified_chests', []):
        excluded.append({'game_treasure_id': None,
                         'catalog_name': entry.get('area', '') + ' - ' + entry.get('label', ''),
                         'reason': 'blue_chest_access_unresolved' if entry.get('colour') == 'Blue' else 'unfinished_placeholder'})
    return {'schema_version': 1, 'kind': 'offline_draft_location_plan',
            'live_submission_authorized': False,
            'allocation': {'draft_base': DRAFT_BASE, 'formula': 'draft_base + game_treasure_id',
                           'maximum_treasure_id': MAX_TREASURE_ID, 'existing_ids_and_names_preserved': True},
            'summary': {'selected': len(locations), 'draft_only': sum(x['mapping_state'] == 'draft_only' for x in locations),
                        'excluded': len(excluded)},
            'locations': locations, 'excluded': excluded}


def compare_scan(plan, data, filename):
    metadata, records = parse_scan(data)
    if metadata['reward_status'] != 'runtime_candidates_not_vanilla_verified':
        raise ValueError('Capture has unavailable reward evidence; quarantine it instead of using this plan.')
    result = {'source_scan': filename, 'scan_sha256': hashlib.sha256(data).hexdigest(),
              'captured_at': int(metadata['captured_at']), 'save_name': metadata['save_name'],
              'scope': 'Saved snapshot only; not current gameplay or proof of disk persistence.',
              'opened': [], 'unopened': [], 'unknown': [], 'missing': []}
    for location in plan['locations']:
        ident = location['game_treasure_id']
        row = records.get(ident)
        state = row['state'] if row else 'missing'
        result[state].append({'game_treasure_id': ident, 'ap_location_id': location['ap_location_id']})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--scan', type=Path, help='Optional existing TSV; no live game reads.')
    parser.add_argument('--output', type=Path, help='Optional JSON report; otherwise print JSON.')
    args = parser.parse_args(argv)
    if args.output and args.output.resolve() in {args.catalog.resolve(), WORLD_LOCATIONS.resolve(),
                                                args.scan.resolve() if args.scan else args.catalog.resolve()}:
        parser.error('Output must not overwrite the catalog, world mappings, or input scan.')
    plan = build_plan(load_catalog(args.catalog), current_locations())
    plan['catalog_sha256'] = hashlib.sha256(args.catalog.read_bytes()).hexdigest()
    if args.scan:
        plan['snapshot'] = compare_scan(plan, args.scan.read_bytes(), args.scan.name)
    if args.output:
        save_catalog(args.output, plan)
        print(f"Draft plan saved: {args.output}; {plan['summary']['selected']} locations, {plan['summary']['excluded']} excluded.")
        print('No AP checks submitted, worlds generated, rewards suppressed, or delivery authorized.')
    else:
        print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f'Location plan error: {exc}')

