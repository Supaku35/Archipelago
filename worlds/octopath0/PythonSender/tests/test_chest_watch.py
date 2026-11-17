import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import watch_chests as w


def event(status='watching', states='70115=unopened,70117=checked', save='save', token='a'*32, ids='70115,70117'):
    return '\n'.join(['OT0AP_WATCH_V2', token, save, ids, status, states, 'detail', 'END', '']).encode()


class WatchTests(unittest.TestCase):
    def test_preview_once_then_complete(self):
        watch = w.WatchEvents('a'*32, [70117, 70115])
        self.assertEqual(watch.accept(event())[2], [70117])
        self.assertEqual(watch.accept(event())[2], [])
        self.assertEqual(watch.accept(event('complete', '70115=checked,70117=checked'))[2], [70115])
        self.assertTrue(watch.finished)
        self.assertEqual(w.DRAFT_LOCATIONS[70117]['ap_location_id'], 10000001)
        self.assertEqual(w.DRAFT_LOCATIONS[70115]['ap_location_id'], 10170115)

    def test_missing_unknown_do_not_check(self):
        watch = w.WatchEvents('a'*32, [70115, 70117])
        self.assertEqual(watch.accept(event(states='70115=missing,70117=unknown'))[2], [])

    def test_bad_events(self):
        for raw in [event(token='b'*32), event(ids='70117,70115'), event(save='unknown'),
                    event('complete'), event(states='70115=checked,70117=checked'),
                    event(states='70115=missing'), event(states='70115=other,70117=checked'), b'x'*8193]:
            with self.subTest(raw=raw[:80]), self.assertRaises(RuntimeError):
                w.WatchEvents('a'*32, [70115,70117]).accept(raw)

    def test_save_change_and_regression(self):
        for raw in [event(save='other'), event(states='70115=unopened,70117=unopened')]:
            watch = w.WatchEvents('a'*32, [70115,70117]); watch.accept(event())
            with self.assertRaises(RuntimeError): watch.accept(raw)

    def test_terminal_no_preview(self):
        for status in ['stopped', 'blocked', 'error']:
            watch = w.WatchEvents('a'*32, [70115,70117])
            self.assertEqual(watch.accept(event(status, 'unknown'))[2], [])
            self.assertTrue(watch.finished)

    def test_ids(self):
        for ids in [[], [70115,70115], [99], [True], ['70117']]:
            with self.assertRaises(ValueError): w.validate_ids(ids)
        self.assertEqual(w.validate_ids([70117]), (70117,))

    def test_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            def publish(path, query):
                path.write_text(query)
                token=query.splitlines()[1]
                (folder/f'{token}.watch.0').write_bytes(event(token=token))
                (folder/f'{token}.watch.1').write_bytes(event(token=token))
                (folder/f'{token}.watch.2').write_bytes(event('complete','70115=checked,70117=checked',token=token))
            out=io.StringIO()
            with patch.object(w,'publish',publish), patch.object(w.time,'sleep'), contextlib.redirect_stdout(out):
                w.run_watch(folder,600,[70115,70117])
            self.assertEqual(out.getvalue().count('"cmd": "LocationChecks"'),2)
            self.assertFalse((folder/'last_request.txt').exists())


if __name__ == '__main__': unittest.main()
