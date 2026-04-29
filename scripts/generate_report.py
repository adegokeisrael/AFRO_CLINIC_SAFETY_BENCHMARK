#!/usr/bin/env python3
"""
generate_report.py
------------------
Generate an HTML report from saved evaluation results.

Examples:
    python scripts/generate_report.py --results results/latest/
    python scripts/generate_report.py --results results/20260429_120000/ --output my_report.html
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console
console = Console()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--results", "-r", required=True, type=Path,
                   help="Directory containing .jsonl result files")
    p.add_argument("--output",  "-o", default=None,
                   help="Output HTML file (default: results_dir/report.html)")
    return p.parse_args()


def main():
    args        = parse_args()
    results_dir = Path(args.results)
    output      = Path(args.output) if args.output else results_dir / "report.html"

    if not results_dir.exists():
        console.print(f"[red]Results directory not found: {results_dir}[/red]")
        sys.exit(1)

    jsonl_files = list(results_dir.glob("*.jsonl"))
    if not jsonl_files:
        console.print(f"[red]No .jsonl files found in {results_dir}[/red]")
        sys.exit(1)

    all_results = []
    for f in jsonl_files:
        if f.name == "combined.jsonl":
            continue
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    all_results.append(json.loads(line))

    if not all_results:
        console.print("[red]No results loaded.[/red]")
        sys.exit(1)

    console.print(f"Loaded {len(all_results)} results from {len(jsonl_files)} file(s)")

    from clinicalsafetybench.reporting.report_generator import ReportGenerator
    from clinicalsafetybench.scoring.metrics            import compute_metrics

    gen = ReportGenerator()
    gen.generate(all_results, output)

    m = compute_metrics(all_results)
    console.print(f"\n[bold]Summary[/bold]")
    console.print(f"  Total   : {m['total']}")
    console.print(f"  Passed  : {m['passed']}")
    console.print(f"  GAR     : {m['guideline_adherence_rate']*100:.1f}%")
    console.print(f"  DAR     : {m['dosage_accuracy_rate']*100:.1f}%")
    console.print(f"  RHR     : {m['hallucination_rate']*100:.1f}%")
    console.print(f"  OSS     : {m['overall_safety_score']*100:.1f}%")
    console.print(f"\n[green]Report saved → {output}[/green]")


if __name__ == "__main__":
    main()
