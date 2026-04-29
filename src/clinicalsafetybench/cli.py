"""
cli.py — Command-line entry points for ClinicalSafetyBench.

Usage
-----
    csb-eval  --model gpt-4o --country kenya
    csb-eval  --all
    csb-report --results results/latest/
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()
console = Console()
app_eval   = typer.Typer(name="csb-eval",   help="Run ClinicalSafetyBench evaluations.")
app_report = typer.Typer(name="csb-report", help="Generate reports from saved results.")


# ── helpers ───────────────────────────────────────────────────────────────────

def _resolve_models(model: Optional[str], all_models: bool) -> List[str]:
    defaults = ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"]
    if all_models:
        return defaults
    if model:
        return [model]
    console.print("[yellow]No model specified. Use --model or --all.[/yellow]")
    raise typer.Exit(1)


def _resolve_countries(country: Optional[str], all_countries: bool) -> List[str]:
    supported = ["kenya", "rwanda", "nigeria"]
    if all_countries:
        return supported
    if country:
        if country not in supported:
            console.print(f"[red]Unknown country '{country}'. Choose from: {supported}[/red]")
            raise typer.Exit(1)
        return [country]
    return supported  # default: all


# ── eval command ──────────────────────────────────────────────────────────────

@app_eval.command()
def evaluate(
    model: Optional[str] = typer.Option(None,  "--model",   "-m", help="Model ID (e.g. gpt-4o)"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Country dataset (kenya/rwanda/nigeria)"),
    all_models: bool       = typer.Option(False,"--all",    "-a", help="Run all registered models"),
    condition: Optional[str]= typer.Option(None,"--condition",    help="Filter by condition"),
    output_dir: Path       = typer.Option(Path("results"), "--output", "-o"),
    dry_run: bool          = typer.Option(False, "--dry-run", help="Print prompts without calling APIs"),
):
    """Run the benchmark and save results as JSONL."""
    from clinicalsafetybench.benchmark import BenchmarkLoader
    from clinicalsafetybench.evaluator import Evaluator
    from clinicalsafetybench.models    import get_adapter

    models    = _resolve_models(model, all_models)
    countries = _resolve_countries(country, False)

    loader   = BenchmarkLoader()
    prompts  = loader.load_all()
    if countries != ["kenya", "rwanda", "nigeria"]:
        prompts = [p for p in prompts if p.country in countries]
    if condition:
        prompts = [p for p in prompts if p.condition == condition]

    console.print(f"\n[bold blue]ClinicalSafetyBench[/bold blue]")
    console.print(f"  Prompts : {len(prompts)}")
    console.print(f"  Models  : {', '.join(models)}")
    console.print(f"  Dry run : {dry_run}\n")

    if dry_run:
        for p in prompts[:3]:
            console.print(f"[dim]{p.id}[/dim]  {p.scenario[:120]}...")
        console.print(f"[yellow](dry-run) Would run {len(prompts)} prompts × {len(models)} models[/yellow]")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for model_id in models:
        console.print(f"\n[bold]▶ Evaluating: {model_id}[/bold]")
        try:
            adapter   = get_adapter(model_id)
            evaluator = Evaluator(adapter)
            scored    = evaluator.run(prompts)
        except EnvironmentError as exc:
            console.print(f"[red]Skipping {model_id}: {exc}[/red]")
            continue

        out_file = output_dir / f"{model_id.replace('/', '_')}.jsonl"
        with open(out_file, "w") as fh:
            for sr in scored:
                fh.write(json.dumps(sr.to_dict()) + "\n")

        passes = sum(1 for s in scored if s.overall_pass)
        console.print(f"  ✓ {passes}/{len(scored)} passed  →  {out_file}")

    console.print("\n[green]Evaluation complete.[/green]")


# ── report command ────────────────────────────────────────────────────────────

@app_report.command()
def report(
    results_dir: Path = typer.Argument(..., help="Directory containing .jsonl result files"),
    output: Path      = typer.Option(Path("results/report.html"), "--output", "-o"),
):
    """Generate an HTML report from saved result files."""
    from clinicalsafetybench.reporting.report_generator import ReportGenerator

    jsonl_files = list(results_dir.glob("*.jsonl"))
    if not jsonl_files:
        console.print(f"[red]No .jsonl files found in {results_dir}[/red]")
        raise typer.Exit(1)

    all_results: list = []
    for f in jsonl_files:
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    all_results.append(json.loads(line))

    gen = ReportGenerator()
    gen.generate(all_results, output)
    console.print(f"[green]Report saved to {output}[/green]")


# make both importable as callables
def main_eval():
    app_eval()

def main_report():
    app_report()
