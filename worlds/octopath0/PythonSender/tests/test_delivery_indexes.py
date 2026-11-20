"""Offline history and sequential coordinator tests; no server/game writes."""
import asyncio
import contextlib
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ap_history as h
import deliver_ap_item as d
from bridge_io import BridgeCancelled
from test_cleanup_helpers import FakeSocket

class IndexTests(unittest.TestCase):
    def setUp(self):
        self.history = [dict(h.EXPECTED_ITEM, location=-1-i) for i in range(3)]

    def test_history_and_partial_plan(self):
        self.assertEqual(h.validate_history({"index":0,"items":[]}), [])
        self.assertEqual(h.plan_pending(self.history, 1), list(enumerate(self.history[1:],1)))
        self.assertEqual(h.plan_pending(self.history, 3), [])
        for index in [-1,4,True]:
            with self.assertRaises(RuntimeError):h.plan_pending(self.history,index)
        with self.assertRaises(RuntimeError):
            h.plan_pending(self.history+[dict(h.EXPECTED_ITEM,item=99)],0)

    def test_conflicting_snapshots_rejected(self):
        ws=FakeSocket([[{"cmd":"ReceivedItems","index":0,"items":self.history},
                        {"cmd":"ReceivedItems","index":0,"items":self.history[:1]}]])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            asyncio.run(h.inspect_history(ws,{10000001}))

    def command(self, progress=0, fail_at=None, failure=None, replay=False):
        events=[]
        async def history(*, revised):
            assert not revised
            return self.history
        def publish(path,text):events.append(("send",int(text.splitlines()[6])))
        def wait(*args,**kwargs):
            index=events[-1][1];events.append(("wait",index))
            if index==fail_at:raise failure
            return (progress if replay else index+1,"save A")
        binding=dict(seed=d.SEED,team=0,slot=1,next_index=progress,token="a"*32,save_name="save A")
        with patch.object(d,"read_verified_history",history), patch.object(d,"request_save_binding",return_value=binding), patch.object(d,"publish",publish), patch.object(d,"wait_for_bridge_response",wait), patch.dict(os.environ,LOCALAPPDATA="unused"), contextlib.redirect_stdout(io.StringIO()) as out:
            code=d.run_cli(["--replay-index-zero"] if replay else [])
        return code,events,out.getvalue()

    def test_full_and_partial_catchup(self):
        for start in [0,1,3]:
            code,events,out=self.command(start)
            self.assertEqual(code,0)
            self.assertEqual(events,[(kind,i) for i in range(start,3) for kind in ["send","wait"]])
            self.assertIn("Ctrl+F3",out)

    def test_replay_zero_preserves_later_progress(self):
        code,events,out=self.command(3,replay=True)
        self.assertEqual(code,0);self.assertEqual(events,[("send",0),("wait",0)])
        self.assertIn("next index=3",out)

    def test_revised_runs_publish_one_index_with_revised_identity(self):
        history = [dict(item=10110001, location=source, player=1, flags=1)
                   for source in (10070115, 10070117)]
        for progress, replay, expected in ((0, False, 0), (1, False, 1), (2, False, None), (2, True, 0)):
            args = ["--profile", "revised"]
            if replay:
                args.append("--replay-index-zero")
            binding = dict(seed=d.REVISED_SEED, team=0, slot=1, next_index=progress,
                           token="a"*32, save_name="save A")
            with patch.object(d, "read_verified_history", return_value=history) as read, patch.object(
                    d, "request_save_binding", return_value=binding) as authorize, patch.object(
                    d, "publish") as publish, patch.object(d, "wait_for_bridge_response",
                    return_value=(progress if replay else progress+1, "save A")), patch.dict(
                    os.environ, LOCALAPPDATA="unused"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(d.run_cli(args), 0)
                read.assert_awaited_once_with(revised=True)
                authorize.assert_called_once_with("authorize", revised=True)
                if expected is None:
                    publish.assert_not_called()
                else:
                    publish.assert_called_once()
                    fields = publish.call_args.args[1].splitlines()
                    self.assertEqual(fields[2:], [binding["token"], d.REVISED_SEED, "0", "1",
                                                  str(expected), "10110001", "END"])

    def test_cancel_and_failure_after_first_delivery_stop_stream(self):
        for error in [BridgeCancelled("cancelled"),RuntimeError("blocked"),TimeoutError("timeout")]:
            code,events,out=self.command(fail_at=1,failure=error)
            self.assertEqual(code,1)
            self.assertEqual(events,[("send",0),("wait",0),("send",1),("wait",1)])
            if isinstance(error,BridgeCancelled):self.assertIn("Earlier deliveries",out)
            else:self.assertIn("Delivery outcome is not confirmed",out)

if __name__ == "__main__":unittest.main()

