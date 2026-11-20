"""Pin the old-room sender even when future world IDs change."""
import asyncio
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ap_connection as ap
import submit_two_chest as sender
from watch_chests import WatchEvents


class Room:
    def __init__(self, checked=(), *, wrong_seed=False, wrong_mapping=False, confirmation=None):
        self.sent = []
        rows = sender.SLOT_DATA['locations']
        slot = dict(sender.SLOT_DATA)
        if wrong_mapping:
            slot['locations'] = [dict(rows[0]), dict(rows[1], ap_location_id=10070115)]
        self.messages = [
            {'cmd':'RoomInfo', 'seed_name':'other' if wrong_seed else sender.SEED, 'games':[ap.GAME]},
            {'cmd':'DataPackage', 'data':{'games':{ap.GAME:{
                'location_name_to_id':{r['name']:r['ap_location_id'] for r in rows},
                'item_name_to_id':{'Small Shield':10000002}}}}},
            {'cmd':'Connected', 'team':0, 'slot':1, 'slot_info':{'1':{'name':sender.PLAYER,'game':ap.GAME}},
             'slot_data':slot, 'checked_locations':list(checked),
             'missing_locations':sorted({10000001,10170115}-set(checked))},
            {'cmd':'RoomUpdate', 'checked_locations':[10170115] if confirmation is None else confirmation},
        ]

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def recv(self): return json.dumps([self.messages.pop(0)])
    async def send(self, data): self.sent.extend(json.loads(data))


def evidence():
    e = WatchEvents('token', [70115], live=True)
    e.accept(b'OT0AP_LIVE_WATCH_V1\ntoken\nsave A\n70115\ncomplete\n70115=checked\ndetail\nEND\n')
    return e


class SubmissionTests(unittest.TestCase):
    def run_sender(self, rooms, result):
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(StringIO()), patch.object(
                ap, 'connect', side_effect=rooms), patch.object(sender, 'observe_watch', return_value=result) as watch:
            asyncio.run(sender.run(70115, Path(folder)))
            return watch.call_count

    def test_submit_and_skip(self):
        second = Room()
        self.assertEqual(self.run_sender([Room(),second], evidence()), 1)
        self.assertEqual(second.sent[-1], {'cmd':'LocationChecks','locations':[10170115]})
        self.assertEqual(self.run_sender([Room([10170115])], None), 0)

    def test_cancel_or_concurrent_check(self):
        for rooms, result in [([Room()],None), ([Room(),Room([10170115])],evidence())]:
            self.run_sender(rooms,result)
            self.assertFalse(any(p['cmd']=='LocationChecks' for room in rooms for p in room.sent))

    def test_revalidate_after_observation(self):
        for second in [Room(wrong_seed=True),Room(wrong_mapping=True)]:
            with self.assertRaises(RuntimeError):
                self.run_sender([Room(),second],evidence())
            self.assertFalse(any(p['cmd']=='LocationChecks' for p in second.sent))

    def test_bad_confirmation_does_not_resend(self):
        second = Room(confirmation=[10070115])
        with self.assertRaises(RuntimeError):
            self.run_sender([Room(),second],evidence())
        self.assertEqual(sum(p['cmd']=='LocationChecks' for p in second.sent),1)

    def test_dry_event_rejected(self):
        with self.assertRaises(RuntimeError):
            WatchEvents('token',[70115],live=True).accept(
                b'OT0AP_WATCH_V2\ntoken\nsave A\n70115\ncomplete\n70115=checked\ndetail\nEND\n')
