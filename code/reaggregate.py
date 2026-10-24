"""Re-judge saved traces with the current judge (dedupe by case+arm, keep last)."""
import json
import sys
from pathlib import Path

from cases import load_cases
from judge import aggregate, judge

R = Path(__file__).resolve().parent.parent / "results"
case_by_id = {c["case_id"]: c for c in load_cases()}

for tag in sys.argv[1:]:
    path = R / f"traces_{tag}.jsonl"
    if not path.exists():
        print(f"{tag}: no traces"); continue
    rows, seen = [], {}
    for line in open(path):
        t = json.loads(line)
        seen[(t["case_id"], t["arm"])] = t  # keep last occurrence
    for (cid, arm), t in seen.items():
        t["judge"] = judge(t, case_by_id[cid])
        rows.append(t)
    summary = aggregate(rows)
    out = R / f"metrics_{tag}_rejudged.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"== {tag} ({len(rows)} traces) ==")
    for k, v in summary.items():
        print(f"  {k}: task={v['task_success']:.2f} inj={v['injection_success']:.2f} "
              f"refusal={v['over_refusal']:.2f} tip={v['tip_followed']}")
