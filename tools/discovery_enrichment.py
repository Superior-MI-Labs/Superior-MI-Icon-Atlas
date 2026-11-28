#!/usr/bin/env python3
"""Read-only discovery enrichment suggestions from authored facts.

No guessing from names, no writes, and no inferred rights or gameplay data.
Review candidate output before changing canonical manifests.
"""
import argparse
import hashlib
import json
from pathlib import Path


def suggest(manifest):
    assets = manifest["assets"]
    by_id = {a["id"]: a for a in assets}
    if len(by_id) != len(assets):
        raise ValueError("Duplicate asset identity")
    existing = {c["id"]: c for c in manifest.get("concepts", [])}
    suggestions = []
    for a in assets:
        if a.get("kind") == "composition":
            for key, slot in a.get("slots", {}).items():
                interface = slot["accepts"]
                options = slot["options"]
                if interface not in manifest.get("interfaces", {}) or not options or not all(
                    interface in by_id.get(option, {}).get("implements", []) for option in options
                ):
                    continue
                offer = {"role": "slot." + key + ".candidate",
                         "requirements": [{"scope": "representation", "op": "interface.has", "key": interface}]}
                # Use only IDs legal in the existing concept discovery vocabulary.
                import re
                if not re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", key) or len(offer["role"]) > 128:
                    continue
                declared = existing.get(a.get("concept_id"), {}).get("discovery_offers", {}).get(key)
                if declared == offer:
                    continue
                suggestions.append({"kind": "offer", "asset_id": a["id"], "offer_id": key,
                                    "candidate": offer, "evidence": {"slot": key, "interface": interface, "options": options},
                                    "review": "conflict" if declared is not None else "required"})
        if a.get("kind") == "state_set" and not a.get("concept_id"):
            states = a.get("states", {})
            if states and a.get("default_state") in states and all(x in by_id for x in states.values()):
                suggestions.append({"kind": "state-representation-review", "asset_id": a["id"],
                                    "evidence": {"states": states, "default_state": a["default_state"]},
                                    "review": "required", "note": "Confirm shared concept, axis and representation roles; do not infer them from names."})
    return suggestions


def inspect(path):
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if manifest.get("schema") != "smi-visual-pack/1":
        raise ValueError("Expected smi-visual-pack/1")
    return {"manifest": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "pack_id": manifest["pack_id"], "suggestions": suggest(manifest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps([inspect(path) for path in args.manifest], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
