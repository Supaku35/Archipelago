import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plan_chest_locations as p


def entry(label='Chest', colour='Brown'):
    return {'area':'Area','label':label,'colour':colour,'contents':'Item x1',
            'record_classification':'user_reported_chest','access':{'status':'initially_accessible'},
            'opening_evidence':{'previous_tick':0,'open_tick':999999999}}


def scan():
    return ('OT0AP_CHEST_SCAN_V1\ncaptured_at\t123\nsave_name\tsave A\nmode\tbaseline\n'
            'reward_status\truntime_candidates_not_vanilla_verified\n'
            'treasure_id\topen_tick\tstate\tprevious_tick\tchange\tcandidate_reward_ids\treward_details\n'
            '1\t999999999\topened\t\tbaseline\t1\titem\n'
            '2\t0\tunopened\t\tbaseline\t2\titem\n'
            '3\t5\tunknown\t\tbaseline\t3\titem\nEND\n').encode()


class LocationPlanTests(unittest.TestCase):
    def test_real_catalog_and_legacy_mapping(self):
        plan=p.build_plan(p.load_catalog(p.DEFAULT_CATALOG),p.current_locations())
        self.assertEqual(plan['summary'],{'selected':178,'draft_only':10,'excluded':198})
        legacy=next(r for r in plan['locations'] if r['game_treasure_id']==70117)
        self.assertEqual((legacy['name'],legacy['ap_location_id']),('Cerulean Caverns - Southwest Cliff Chest',10070117))
        self.assertTrue(all(not r['ap_logic_verified'] for r in plan['locations']))
        self.assertFalse(plan['live_submission_authorized'])
        self.assertEqual(len({r['ap_location_id'] for r in plan['locations']}),178)

    def test_selection_never_uses_completion_as_access(self):
        cat={'schema_version':1,'chests':{'1':entry('One'),'2':entry('Blue','Blue'),'3':entry('Candidate'),'4':entry('Blocked')}}
        cat['chests']['3']['record_classification']='unclassified_scan_record'
        cat['chests']['4']['access']['status']='unknown'
        before=copy.deepcopy(cat)
        result=p.build_plan(cat,{})
        self.assertEqual([r['game_treasure_id'] for r in result['locations']],[1])
        self.assertEqual(cat,before)

    def test_ids_survive_growth_and_reordering(self):
        cat={'schema_version':1,'chests':{'10':entry('Ten'),'20':entry('Twenty')}}
        first={x['game_treasure_id']:x['ap_location_id'] for x in p.build_plan(cat,{})['locations']}
        cat['chests']['1']=entry('One')
        cat['chests']['10']['colour']='Blue'
        second=p.build_plan(cat,{})
        self.assertEqual(next(x['ap_location_id'] for x in second['locations'] if x['game_treasure_id']==20),first[20])

    def test_collisions_and_missing_legacy_are_rejected(self):
        cat={'schema_version':1,'chests':{'1':entry(),'2':entry()}}
        with self.assertRaises(ValueError):p.build_plan(cat,{})
        cat['chests']['2']['label']='Other'
        with self.assertRaises(ValueError):p.build_plan(cat,{1:('Legacy',p.DRAFT_BASE+2)})
        with self.assertRaises(ValueError):p.build_plan(cat,{3:('Missing',10000001)})
        cat['chests']['01']=entry('Alias')
        with self.assertRaises(ValueError):p.build_plan(cat,{})

    def test_snapshot_states_are_separate_and_incomplete_is_not_unopened(self):
        cat={'schema_version':1,'chests':{str(i):entry(str(i)) for i in range(1,5)}}
        plan=p.build_plan(cat,{})
        result=p.compare_scan(plan,scan(),'snapshot.tsv')
        for state,ident in [('opened',1),('unopened',2),('unknown',3),('missing',4)]:
            self.assertEqual([x['game_treasure_id'] for x in result[state]],[ident])
        self.assertEqual(result['save_name'],'save A')

    def test_failed_and_incomplete_captures_are_rejected(self):
        plan=p.build_plan({'schema_version':1,'chests':{}},{})
        for data in [scan().replace(b'runtime_candidates_not_vanilla_verified',b'unavailable: error'),scan().replace(b'END\n',b'')]:
            with self.assertRaises(ValueError):p.compare_scan(plan,data,'bad.tsv')

    def test_cli_is_offline_and_protects_inputs(self):
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()),patch.dict('os.environ',{},clear=True):
            path=Path(folder)/'plan.json'
            before=p.DEFAULT_CATALOG.read_bytes()
            p.main(['--output',str(path)])
            self.assertEqual(json.loads(path.read_text())['summary']['selected'],178)
            self.assertEqual(p.DEFAULT_CATALOG.read_bytes(),before)
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                p.main(['--output',str(p.DEFAULT_CATALOG)])
            self.assertEqual(p.DEFAULT_CATALOG.read_bytes(),before)

if __name__=='__main__':unittest.main()

