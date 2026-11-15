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
import catalog_chests as c


def scan(tick='999999999', previous='0', change='changed', state='opened'):
    return ('OT0AP_CHEST_SCAN_V1\ncaptured_at\t123\nsave_name\tsave A\nmode\tcomparison\n'
            'reward_status\truntime_candidates_not_vanilla_verified\n'+'\t'.join(c.COLUMNS)+'\n'+
            f'70115\t{tick}\t{state}\t{previous}\t{change}\t70115\treward=70115 id=130170 qty=0\nEND\n').encode()


class CatalogTests(unittest.TestCase):
    def test_state_rules(self):
        self.assertEqual([c.state_for(x) for x in [0,999999999,12,-1,None]],
                         ['unopened','opened','unknown','unknown','missing'])

    def test_import_preserves_labels_and_separates_runtime_rewards(self):
        cat={'schema_version':1,'chests':{'70115':{'label':'Near squirrel','contents':'Fire Soulstone x1','mapping_status':'manually_verified'}}}
        _, changed, count=c.import_scan(cat,scan(),'scan.tsv')
        self.assertEqual((len(changed),count),(1,1))
        self.assertEqual(cat['chests']['70115']['contents'],'Fire Soulstone x1')
        self.assertIn('qty=0',cat['chests']['70115']['last_observation']['runtime_reward_details'])
        evidence=copy.deepcopy(cat['chests']['70115']['opening_evidence'])
        c.import_scan(cat,scan('0','0','unchanged','unopened'),'older-save.tsv')
        self.assertEqual(cat['chests']['70115']['opening_evidence'],evidence)
        self.assertEqual(cat['chests']['70115']['label'],'Near squirrel')

    def test_candidates_are_not_activated(self):
        cat={'schema_version':1,'chests':{}}
        c.import_scan(cat,scan(),'scan.tsv')
        row=cat['chests']['70115']
        self.assertEqual(row['mapping_status'],'candidate')
        self.assertEqual(row['label'],'')
        self.assertNotIn('ap_location_id',row)

    def test_invalid_file_does_not_mutate_catalog(self):
        for data in [scan().replace(b'END\n',b''),scan(state='unopened'),scan(change='added'),
                     scan().replace(b'END\n',scan().splitlines()[-2]+b'\nEND\n')]:
            cat={'schema_version':1,'chests':{}}
            with self.subTest(data=data),self.assertRaises(ValueError):c.import_scan(cat,data,'bad.tsv')
            self.assertEqual(cat,{'schema_version':1,'chests':{}})

    def test_unknown_and_missing(self):
        for tick,before,change,state in [('12','0','changed','unknown'),('','0','removed','missing'),('999999999','','added','opened')]:
            _,rows=c.parse_scan(scan(tick,before,change,state))
            self.assertEqual(rows[70115]['state'],state)

    def test_failed_replace_preserves_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.json';path.write_text('original')
            with patch.object(c.os,'replace',side_effect=OSError('injected')),self.assertRaises(OSError):
                c.save_catalog(path,{'schema_version':1,'chests':{}})
            self.assertEqual(path.read_text(),'original')
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])

    def test_cli_import_and_label(self):
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            path=Path(folder)/'catalog.json';source=Path(folder)/'scan.tsv';source.write_bytes(scan())
            c.main(['--catalog',str(path),'--scan',str(source)])
            c.main(['--catalog',str(path),'--label-id','70115','--area','Wishvale Trail','--label','Squirrel chest','--contents','Fire Soulstone x1'])
            c.main(['--catalog',str(path),'--scan',str(source)])
            self.assertEqual(json.loads(path.read_text())['chests']['70115']['label'],'Squirrel chest')
            with self.assertRaises(ValueError):c.main(['--catalog',str(path),'--label-id','999'])

if __name__=='__main__':unittest.main()
