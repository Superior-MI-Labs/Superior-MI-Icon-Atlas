import json, unittest, tempfile
from pathlib import Path
from tools.build_site import build,ROOT
from atlasctl import validate

class ReleaseTests(unittest.TestCase):
 def test_geometry_and_integrity(self):self.assertEqual(validate(),[])
 def test_all_ids_unique(self):
  m=json.loads((ROOT/'manifest.json').read_text());self.assertEqual(len(m['icons']),1920);self.assertEqual(len(m['sheets']),10)
  self.assertEqual(len({i['id'] for i in m['icons']}),1920)
 def test_website(self):
  with tempfile.TemporaryDirectory() as tmp:
   self.assertEqual(build(Path(tmp)),1920)
   self.assertTrue((Path(tmp)/'index.html').exists())
   self.assertTrue((Path(tmp)/'sheets/nature/atlas.png').exists())
   s=(Path(tmp)/'catalog-data.js').read_text()
   self.assertIn('icons.concept.programming.r00c00',s)
if __name__=='__main__':unittest.main()
