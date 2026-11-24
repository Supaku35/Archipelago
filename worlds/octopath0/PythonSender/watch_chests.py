"""Explicit-set chest observation and draft payload previews; never connects to AP."""
import argparse
import json
import os
from pathlib import Path
import time
import uuid

from bridge_io import publish
from chest_checks import PROTOTYPE_LOCATIONS

DRAFT_LOCATIONS = {
    70117: PROTOTYPE_LOCATIONS['treasure', 70117],
    70115: {'name': 'Wishvale Trail - West near Squirrel',
            'ap_location_id': 10100000 + 70115},
}


def validate_ids(ids):
    ids = tuple(ids)
    if not ids or len(ids) > 2 or any(type(i) is not int or i not in DRAFT_LOCATIONS for i in ids):
        raise ValueError('Choose treasure 70115 and/or 70117.')
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate treasure IDs are not allowed.')
    return tuple(sorted(ids))


class WatchEvents:
    def __init__(self, request_id, ids, *, live=False):
        self.header = "OT0AP_LIVE_WATCH_V1" if live else "OT0AP_WATCH_V2"
        self.request_id = request_id
        self.ids = validate_ids(ids)
        self.save = None
        self.checked = set()
        self.finished = False

    def accept(self, raw):
        if self.finished:
            raise RuntimeError('Watch already finished.')
        if len(raw) > 8192:
            raise RuntimeError('Watch event exceeds the size limit.')
        lines = raw.decode('utf-8').splitlines()
        if (len(lines) != 8 or lines[0] != self.header
                or lines[1] != self.request_id
                or lines[3] != ','.join(map(str, self.ids)) or lines[7] != 'END'):
            raise RuntimeError('Invalid or mismatched watch event.')
        save, status, observation = lines[2], lines[4], lines[5]
        if status not in {'watching', 'complete', 'stopped', 'blocked', 'error'}:
            raise RuntimeError('Invalid watch status.')
        if self.save is not None and save != self.save:
            raise RuntimeError('Watch changed its bound-save identity.')
        if status in {'stopped', 'blocked', 'error'}:
            if observation != 'unknown':
                raise RuntimeError('Invalid terminal watch observation.')
            self.finished = True
            return status, {}, [], lines[6]
        if save in {'', 'unknown', 'nil'}:
            raise RuntimeError('Watch lacks a save identity.')
        parts = observation.split(',')
        states = {}
        if len(parts) != len(self.ids):
            raise RuntimeError('Incomplete watch sample.')
        for id, part in zip(self.ids, parts):
            pair = part.split('=')
            if len(pair) != 2 or pair[0] != str(id) or pair[1] not in {'checked', 'unopened', 'unknown', 'missing'}:
                raise RuntimeError('Invalid watch observation.')
            states[id] = pair[1]
        checked = {id for id, state in states.items() if state == 'checked'}
        if (status == 'complete') != (checked == set(self.ids)):
            raise RuntimeError('Watch completion disagrees with its observations.')
        if not self.checked.issubset(checked):
            raise RuntimeError('Previously checked chest regressed; inspect the save before restarting.')
        newly_checked = sorted(checked - self.checked)
        self.save, self.checked = save, checked
        self.finished = status == 'complete'
        return status, states, newly_checked, lines[6]


def observe_watch(folder, timeout, ids, *, live=False, bound_seed=None):
    ids = validate_ids(ids)
    request_id = uuid.uuid4().hex
    events = WatchEvents(request_id, ids, live=live)
    header = 'OT0AP_LIVE_WATCH_QUERY_V1' if live else 'OT0AP_WATCH_QUERY_V2'
    fields = [header, request_id, str(len(ids)), *map(str, ids)]
    if bound_seed is not None:
        if not live or len(ids) != 1:
            raise ValueError('Bound watches require a single live chest.')
        fields = ['OT0AP_BOUND_WATCH_V1', request_id, bound_seed, '0', '1', str(ids[0])]
    query = '\n'.join([*fields, 'END', ''])
    publish(folder / 'inbox.txt', query)
    if live:
        print('LIVE: Ctrl+F7 authorizes submitting the selected chest, including if already open.', flush=True)
    else:
        print('DRY RUN ONLY: preview uses the original two-chest seed IDs. No checks sent.', flush=True)
    print('Ctrl+F3 to disarm, then Ctrl+F7 on the intended save. Ctrl+F3 stops the watch.', flush=True)
    print('Already-open chests count as checked. Observations are in memory, not proof of a disk save.', flush=True)
    deadline, sequence = time.monotonic() + timeout, 0
    while True:
        if (folder / 'inbox.txt').read_text(encoding='utf-8') != query:
            raise RuntimeError('Inbox replaced. Watch stopped in Python; press Ctrl+F3 in-game.')
        try:
            with (folder / f'{request_id}.watch.{sequence}').open('rb') as handle:
                raw = handle.read(8193)
        except FileNotFoundError:
            raw = None
        if raw is not None:
            status, states, newly_checked, detail = events.accept(raw)
            print(f'Watch={status}; save={events.save or "unbound"}; {states}; {detail}', flush=True)
            for id in ([] if live else newly_checked):
                location = DRAFT_LOCATIONS[id]
                print(f"DRY RUN: {location['name']} -> AP location {location['ap_location_id']}", flush=True)
                print(json.dumps([{'cmd': 'LocationChecks', 'locations': [location['ap_location_id']]}]), flush=True)
            sequence += 1
            if status in {'blocked', 'error'}:
                raise RuntimeError(detail)
            if events.finished:
                if not live:
                    print('Watch ended. No location checks were sent.', flush=True)
                return events if status == 'complete' else None
        if time.monotonic() >= deadline:
            raise RuntimeError('Watch timed out. Press Ctrl+F3 to stop the in-game watch.')
        time.sleep(0.5)


def run_watch(folder, timeout, ids=(70117,)):
    observe_watch(folder, timeout, ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--treasure-ids', nargs='+', type=int, default=[70117])
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    try:
        ids = validate_ids(args.treasure_ids)
    except ValueError as exc:
        parser.error(str(exc))
    if args.timeout < 1:
        parser.error('--timeout must be positive.')
    root = os.environ.get('LOCALAPPDATA')
    if not root:
        raise RuntimeError('LOCALAPPDATA is unavailable.')
    folder = Path(root) / 'OctopathArchipelagoBridge'
    folder.mkdir(parents=True, exist_ok=True)
    run_watch(folder, args.timeout, ids)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        raise SystemExit(f'Watch stopped: {exc}. Press Ctrl+F3 if a watch remains active. No checks sent.')
