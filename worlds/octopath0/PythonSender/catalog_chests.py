"""Offline chest catalog editor. Never connects to AP or publishes bridge requests."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / 'data' / 'chest_catalog.json'
COLUMNS = ['treasure_id', 'open_tick', 'state', 'previous_tick', 'change',
           'candidate_reward_ids', 'reward_details']


def bridge_folder():
    root = os.environ.get('LOCALAPPDATA')
    if not root:
        raise RuntimeError('LOCALAPPDATA is unavailable.')
    return Path(root) / 'OctopathArchipelagoBridge'


def state_for(tick):
    return 'missing' if tick is None else 'unopened' if tick == 0 else 'opened' if tick == 999999999 else 'unknown'


def parse_scan(data):
    if len(data) > 8_000_000:
        raise ValueError('Scan exceeds the diagnostic size limit.')
    lines = data.decode('utf-8').splitlines()
    if len(lines) < 7 or lines[0] != 'OT0AP_CHEST_SCAN_V1' or lines[-1] != 'END':
        raise ValueError('Incomplete or unsupported scan file.')
    metadata = {}
    for line, key in zip(lines[1:5], ['captured_at', 'save_name', 'mode', 'reward_status']):
        name, sep, value = line.partition('\t')
        if name != key or not sep or not value:
            raise ValueError('Invalid scan metadata.')
        metadata[key] = value
    if not metadata['captured_at'].isdigit() or metadata['mode'] not in {'baseline', 'comparison'}:
        raise ValueError('Invalid scan time/mode.')
    reader = csv.DictReader(io.StringIO('\n'.join(lines[5:-1])), delimiter='\t', quoting=csv.QUOTE_NONE)
    if reader.fieldnames != COLUMNS:
        raise ValueError('Unexpected scan columns.')
    records = {}
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('Malformed scan row.')
        if not row['treasure_id'].isdigit():
            raise ValueError('Invalid treasure ID.')
        ident = int(row['treasure_id'])
        if ident in records or not 0 <= ident <= 999999999:
            raise ValueError('Duplicate or invalid treasure ID.')
        tick = int(row['open_tick']) if row['open_tick'] else None
        before = int(row['previous_tick']) if row['previous_tick'] else None
        if row['state'] != state_for(tick):
            raise ValueError('Completion state disagrees with raw OpenTick.')
        expected = ('baseline' if metadata['mode'] == 'baseline' else
                    'removed' if tick is None else 'added' if before is None else
                    'unchanged' if tick == before else 'changed')
        if row['change'] != expected or (metadata['mode'] == 'baseline' and (before is not None or tick is None)):
            raise ValueError('Change classification disagrees with the snapshot.')
        rewards = [int(x) for x in row['candidate_reward_ids'].split(',') if x]
        if any(x < 0 for x in rewards):
            raise ValueError('Invalid candidate reward ID.')
        records[ident] = dict(open_tick=tick, state=row['state'], previous_tick=before,
                             change=row['change'], candidate_reward_ids=rewards,
                             runtime_reward_details=row['reward_details'])
    if len(records) > 20000:
        raise ValueError('Too many scan records.')
    return metadata, records


def load_catalog(path):
    if not path.exists():
        return {'schema_version': 1, 'chests': {}}
    catalog = json.loads(path.read_text(encoding='utf-8'))
    if catalog.get('schema_version') != 1 or not isinstance(catalog.get('chests'), dict):
        raise ValueError('Unsupported catalog; nothing overwritten.')
    for ident, row in catalog['chests'].items():
        if not ident.isdigit() or not isinstance(row, dict):
            raise ValueError('Malformed catalog; nothing overwritten.')
    return catalog


def save_catalog(path, catalog):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(catalog, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def import_scan(catalog, data, filename):
    metadata, records = parse_scan(data)  # Validate all rows before changing the catalog.
    digest = hashlib.sha256(data).hexdigest()
    changed = []
    for ident, observation in records.items():
        key = str(ident)
        entry = catalog['chests'].setdefault(key, {'area': '', 'label': '', 'contents': '',
                                                 'notes': '', 'mapping_status': 'candidate'})
        evidence = dict(observation, captured_at=int(metadata['captured_at']),
                        source_scan=filename, scan_sha256=digest, reward_status=metadata['reward_status'])
        entry['last_observation'] = evidence
        # Opening evidence survives later imports of older/unopened saves.
        if observation['state'] == 'opened' and observation['change'] in {'added', 'changed'}:
            entry['opening_evidence'] = evidence
        if observation['change'] in {'added', 'changed', 'removed'}:
            changed.append((ident, observation))
    catalog['last_import'] = {'file': filename, 'sha256': digest, 'captured_at': int(metadata['captured_at'])}
    return metadata, changed, len(records)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--import-latest', action='store_true')
    action.add_argument('--scan', type=Path, help='Import a specific exported scan instead of the latest.')
    action.add_argument('--list', action='store_true')
    action.add_argument('--label-id', type=int)
    for field in ['area', 'label', 'contents', 'notes']:
        parser.add_argument('--' + field)
    args = parser.parse_args(argv)
    if args.label_id is None and any(getattr(args, field) is not None for field in ['area','label','contents','notes']):
        parser.error('Label fields require --label-id.')
    if args.prepare:
        folder = bridge_folder()
        folder.mkdir(parents=True, exist_ok=True)
        print(f'Scan folder ready: {folder}')
        print('Stop coordinators, Ctrl+F3, then Ctrl+F10 and Ctrl+F9 in exploration.')
        return
    catalog = load_catalog(args.catalog)
    if args.import_latest or args.scan:
        scans = sorted(bridge_folder().glob('chest-scan-*.tsv')) if args.import_latest else []
        if args.import_latest and not scans:
            raise ValueError('No exported scans. Run --prepare, then capture with Ctrl+F9.')
        path = scans[-1] if args.import_latest else args.scan
        data = path.read_bytes()
        metadata, changed, count = import_scan(catalog, data, path.name)
        save_catalog(args.catalog, catalog)
        print(f'Imported {count} observed IDs from {path}; mode={metadata["mode"]}.')
        print(f'Capture time (Unix): {metadata["captured_at"]}; save: {metadata["save_name"]}')
        for ident, row in changed:
            print(f'ID={ident}: {row["previous_tick"]} -> {row["open_tick"]}; {row["state"]}; {row["change"]}')
            print('  Runtime reward candidates: ' + (row['runtime_reward_details'] or 'unavailable'))
        if not changed:
            print('No changed records (or this is a baseline). No chest label inferred.')
        print('Labels preserved. Runtime rewards may be modified by suppression; enter actual contents separately.')
    elif args.label_id is not None:
        key = str(args.label_id)
        if key not in catalog['chests']:
            raise ValueError('ID not in catalog. Import the scan first.')
        for field in ['area', 'label', 'contents', 'notes']:
            value = getattr(args, field)
            if value is not None:
                catalog['chests'][key][field] = value
        save_catalog(args.catalog, catalog)
        print(f'Updated ID {key}: {catalog["chests"][key].get("label", "")}')
    else:
        for ident, entry in sorted(catalog['chests'].items(), key=lambda pair:int(pair[0])):
            obs = entry.get('last_observation', {})
            print(f'{ident}: {entry.get("area", "")} | {entry.get("label", "")} | '
                  f'{entry.get("contents", "")} | last state={obs.get("state", "not scanned")}')
    print(f'Catalog: {args.catalog}')
    print('Discovery only: no AP locations activated, checks sent, rewards changed, or delivery authorized.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f'Catalog error: {exc}')
