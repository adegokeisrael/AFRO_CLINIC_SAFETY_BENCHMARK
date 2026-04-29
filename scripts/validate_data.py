#!/usr/bin/env python3
"""
validate_data.py
----------------
Validate that all .jsonl data files parse correctly and match the schema.

Examples:
    python scripts/validate_data.py
    python scripts/validate_data.py --country kenya
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console
from rich.table   import Table
console = Console()

REQUIRED_FIELDS   = {"id","country","condition","severity","guideline_source",
                     "scenario","ground_truth","failure_modes_to_watch","failure_definitions"}
REQUIRED_GT       = {"first_line_drug","dosage","additional","referral"}
VALID_FAILURE_MODES = {"dosage_error","hallucinated_referral",
                       "guideline_contradiction","language_misinterpretation"}


def validate_file(path: Path) -> list[str]:
    errors = []
    seen_ids: set[str] = set()
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {lineno}: JSON parse error: {e}")
                continue

            missing = REQUIRED_FIELDS - set(rec.keys())
            if missing:
                errors.append(f"Line {lineno} [{rec.get('id','?')}]: missing fields {missing}")

            gt_missing = REQUIRED_GT - set(rec.get("ground_truth", {}).keys())
            if gt_missing:
                errors.append(f"Line {lineno} [{rec.get('id','?')}]: missing ground_truth fields {gt_missing}")

            for fm in rec.get("failure_modes_to_watch", []):
                if fm not in VALID_FAILURE_MODES:
                    errors.append(f"Line {lineno} [{rec.get('id','?')}]: invalid failure mode '{fm}'")

            pid = rec.get("id","")
            if pid in seen_ids:
                errors.append(f"Line {lineno}: duplicate ID '{pid}'")
            seen_ids.add(pid)

            if not rec.get("scenario","").strip():
                errors.append(f"Line {lineno} [{pid}]: empty scenario")
            if not rec.get("guideline_source","").strip():
                errors.append(f"Line {lineno} [{pid}]: empty guideline_source")

    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country", help="Validate one country only")
    args = parse_args() if False else p.parse_args()

    data_dir = ROOT / "data"
    if args.country:
        files = [data_dir / args.country / "prompts.jsonl"]
    else:
        files = list(data_dir.glob("*/prompts.jsonl"))

    if not files:
        console.print("[red]No data files found.[/red]")
        sys.exit(1)

    total_errors = 0
    t = Table("File", "Prompts", "Status", title="Validation Results")

    for f in sorted(files):
        if not f.exists():
            console.print(f"[yellow]SKIP[/yellow] {f} (not found)")
            continue
        errors  = validate_file(f)
        prompts = sum(1 for line in open(f) if line.strip())
        status  = "[green]✓ PASS[/green]" if not errors else f"[red]✗ {len(errors)} error(s)[/red]"
        t.add_row(str(f.relative_to(ROOT)), str(prompts), status)
        total_errors += len(errors)
        for e in errors:
            console.print(f"  [red]{e}[/red]")

    console.print(t)

    if total_errors:
        console.print(f"\n[red]Validation FAILED — {total_errors} error(s)[/red]")
        sys.exit(1)
    else:
        console.print("\n[green]All data files valid ✓[/green]")


if __name__ == "__main__":
    main()
