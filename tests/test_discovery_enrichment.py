import unittest
from tools.discovery_enrichment import suggest


class DiscoveryEnrichmentTests(unittest.TestCase):
    def test_only_authored_interface_facts_and_no_redundant_offer(self):
        component = {"id": "test.fill", "implements": ["fill/1"]}
        meter = {"id": "test.meter", "kind": "composition",
                 "slots": {"fill": {"accepts": "fill/1", "options": ["test.fill"]}}}
        pack = {"assets": [component, meter], "interfaces": {"fill/1": {}}}
        result = suggest(pack)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["review"], "required")
        meter["concept_id"] = "test.meter.concept"
        pack["concepts"] = [{"id": meter["concept_id"], "discovery_offers": {"fill": result[0]["candidate"]}}]
        self.assertEqual(suggest(pack), [])
        pack["concepts"][0]["discovery_offers"]["fill"] = {"role": "different", "requirements": []}
        self.assertEqual(suggest(pack)[0]["review"], "conflict")
        component["implements"] = []
        self.assertEqual(suggest(pack), [])

    def test_state_sets_require_review_and_do_not_infer_axes(self):
        p = {"assets": [{"id": "test.one"}, {"id": "test.two"},
                        {"id": "test.states", "kind": "state_set", "states": {"a": "test.one", "b": "test.two"}, "default_state": "a"}]}
        rows = suggest(p)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "state-representation-review")
        self.assertNotIn("candidate", rows[0])
        p["assets"][-1]["concept_id"] = "test.concept"
        self.assertEqual(suggest(p), [])
