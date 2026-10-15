"""Run cases x defense arm, judge, write traces + summary.

  python run_cases.py --dry-run                # scripted model, pipeline test
  python run_cases.py --model Qwen/Qwen2.5-7B-Instruct-AWQ --arms all
"""

import argparse
import json
from pathlib import Path

import agent as agent_mod
import defenses
from cases import load_cases
from judge import aggregate, judge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--arms", default="all", help="comma list or 'all'")
    ap.add_argument("--out-dir", type=Path, default=Path("../results"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    arms = defenses.ARMS if args.arms == "all" else args.arms.split(",")
    cases = load_cases()
    model = agent_mod.ScriptedModel(None) if args.dry_run else agent_mod.LocalModel(args.model)

    rows = []
    for case in cases:
        for arm in arms:
            trace = agent_mod.run_agent(case, arm, model, defenses)
            trace["judge"] = judge(trace, case)
            rows.append(trace)
            print(json.dumps({
                "case": case["case_id"], "arm": arm,
                **trace["judge"], "final": trace["final"][:80],
            }, ensure_ascii=False))

    tag = "dryrun" if args.dry_run else (args.model or "model").split("/")[-1]
    (args.out_dir / f"traces_{tag}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in rows)
    )
    summary = aggregate(rows)
    (args.out_dir / f"metrics_{tag}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
