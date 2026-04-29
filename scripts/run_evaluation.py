#!/usr/bin/env python3
"""
run_evaluation.py
-----------------
CLI script to run ClinicalSafetyBench evaluations.

Examples:
    python scripts/run_evaluation.py --model gpt-4o
    python scripts/run_evaluation.py --model gpt-4o --country kenya
    python scripts/run_evaluation.py --all
    python scripts/run_evaluation.py --model gpt-4o --dry-run
"""
import sys, json, logging, argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from rich.console import Console
from rich.table   import Table
console = Console()

MODELS    = ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"]
COUNTRIES = ["kenya", "rwanda", "nigeria"]


def parse_args():
    p = argparse.ArgumentParser(description="Run ClinicalSafetyBench evaluations.")
    p.add_argument("--model",     "-m", help="Model ID to evaluate")
    p.add_argument("--country",   "-c", help="Country dataset (kenya/rwanda/nigeria)")
    p.add_argument("--condition",       help="Filter by clinical condition")
    p.add_argument("--all",       "-a", action="store_true", help="Run all models")
    p.add_argument("--dry-run",         action="store_true", help="Print without calling APIs")
    p.add_argument("--output",    "-o", default=str(ROOT / "results"), help="Output directory")
    p.add_argument("--log-level",       default="INFO")
    return p.parse_args()


def main():
    args   = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    from clinicalsafetybench.benchmark import BenchmarkLoader
    from clinicalsafetybench.evaluator import Evaluator
    from clinicalsafetybench.models    import get_adapter
    from clinicalsafetybench.scoring.metrics import compute_metrics

    models = MODELS if args.all else ([args.model] if args.model else None)
    if not models:
        console.print("[red]Specify --model MODEL_ID or --all[/red]")
        sys.exit(1)

    loader  = BenchmarkLoader(ROOT / "data")
    prompts = loader.load_all()
    if args.country:
        prompts = [p for p in prompts if p.country == args.country.lower()]
    if args.condition:
        prompts = [p for p in prompts if p.condition == args.condition]

    console.print(f"\n[bold blue]ClinicalSafetyBench Evaluation[/bold blue]")
    console.print(f"  Prompts : {len(prompts)}")
    console.print(f"  Models  : {', '.join(models)}")
    if args.dry_run:
        console.print("\n[yellow]DRY RUN — no API calls will be made[/yellow]")
        for p in prompts[:5]:
            console.print(f"  [dim]{p.id}[/dim]  {p.scenario[:100]}...")
        return

    run_id     = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    # symlink "latest" → this run
    latest = Path(args.output) / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(run_id)

    all_results = []

    for model_id in models:
        console.print(f"\n[bold]▶ {model_id}[/bold]")
        try:
            adapter   = get_adapter(model_id)
            evaluator = Evaluator(adapter)
            scored    = evaluator.run(prompts)
        except EnvironmentError as exc:
            console.print(f"  [red]Skipped: {exc}[/red]")
            continue

        out_file = output_dir / f"{model_id.replace('/', '_')}.jsonl"
        with open(out_file, "w") as fh:
            for sr in scored:
                d = sr.to_dict()
                all_results.append(d)
                fh.write(json.dumps(d) + "\n")

        m       = compute_metrics([s.to_dict() for s in scored])
        passes  = m["passed"]
        total   = m["total"]
        gar     = f"{m['guideline_adherence_rate']*100:.1f}%"
        console.print(f"  ✓ {passes}/{total} passed · GAR {gar} · saved → {out_file}")

    if all_results:
        combined = output_dir / "combined.jsonl"
        with open(combined, "w") as fh:
            for r in all_results:
                fh.write(json.dumps(r) + "\n")
        console.print(f"\n[green]All results saved to {output_dir}[/green]")
        console.print(f"Run report: python scripts/generate_report.py --results {output_dir}")


if __name__ == "__main__":
    main()
