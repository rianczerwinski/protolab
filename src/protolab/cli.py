"""Click CLI group and all commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .analyze import analyze_corrections
from .check import evaluate_triggers
from .config import load_config
from .correct import batch_correct, extract_rule, interactive_correct
from .import_cmd import import_eval_failures
from .init_cmd import scaffold_project
from .resynthesis import assemble_prompt, promote_resynthesis, run_resynthesis, stage_resynthesis
from .status import render_status
from .store import load_corrections, load_rules, save_corrections, save_rules

console = Console()


def _version_increment(version: str) -> str:
    """Auto-increment version: v1.0 -> v1.1, v2.3.1 -> v2.3.2."""
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except ValueError:
        return version


@click.group()
def main():
    """Protolab: error-driven compression for protocol documents."""


@main.command()
@click.option("--bare", is_flag=True, help="Non-interactive, all defaults")
def init(bare):
    """Initialize a protolab project in the current directory."""
    try:
        scaffold_project(bare=bare)
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.option("--batch", type=click.Path(exists=True), help="Import corrections from file")
def correct(batch):
    """Log a correction to the protocol."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    if batch:
        corrections = batch_correct(config, Path(batch))
        existing = load_corrections(config)
        existing.extend(corrections)
        save_corrections(config, existing)

        # Extract rules from corrections that have them
        existing_rules = load_rules(config)
        for corr in corrections:
            rule = extract_rule(corr, config)
            if rule is not None:
                existing_rules.append(rule)
        save_rules(config, existing_rules)

        console.print(f"Added {len(corrections)} correction(s).")
    else:
        correction = interactive_correct(config)
        existing = load_corrections(config)
        existing.append(correction)
        save_corrections(config, existing)

        rule = extract_rule(correction, config)
        if rule is not None:
            existing_rules = load_rules(config)
            existing_rules.append(rule)
            save_rules(config, existing_rules)
            console.print(Panel(
                f"[bold]Rule {rule['id']}:[/bold] {rule['rule']}",
                title="Rule Extracted",
            ))

        console.print(Panel(
            f"[bold]{correction['id']}[/bold] — {correction['step']}\n"
            f"Subject: {correction['subject']}\n"
            f"Protocol said: {correction['protocol_output']}\n"
            f"Correct: {correction['correct_output']}",
            title="Correction Logged",
        ))


@main.command("import")
@click.argument("path", type=click.Path(exists=True))
@click.option("--subject-field", default="subject")
@click.option("--output-field", default="output")
@click.option("--step-field", default="step")
def import_cmd(path, subject_field, output_field, step_field):
    """Import eval failures as correction stubs."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    stubs, skipped = import_eval_failures(
        config, Path(path), subject_field, output_field, step_field,
    )
    existing = load_corrections(config)
    existing.extend(stubs)
    save_corrections(config, existing)
    msg = f"Imported {len(stubs)} correction stub(s)."
    if skipped:
        msg += f" {skipped} row(s) skipped (missing fields)."
    msg += " Run `protolab correct` to fill in reasoning."
    console.print(msg)


@main.command()
def check():
    """Evaluate resynthesis triggers."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    corrections = load_corrections(config)
    rules = load_rules(config)
    results = evaluate_triggers(config, corrections, rules)

    table = Table(title="Resynthesis Triggers")
    table.add_column("Trigger")
    table.add_column("Status")
    table.add_column("Current", justify="right")
    table.add_column("Threshold", justify="right")

    any_met = False
    for r in results:
        status = "[green]MET[/green]" if r.met else "[dim]unmet[/dim]"
        if r.met:
            any_met = True
        table.add_row(r.name, status, str(r.current_value), str(r.threshold))

    console.print(table)

    if any_met:
        console.print("\n[bold]Resynthesis recommended.[/bold] Run `protolab resynthesis`")
        sys.exit(1)


@main.command()
def analyze():
    """Cluster analysis of accumulated corrections."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    corrections = load_corrections(config)
    rules = load_rules(config)
    result = analyze_corrections(corrections, rules)

    if not result.clusters:
        console.print("No corrections to analyze.")
        return

    table = Table(title="Correction Clusters")
    table.add_column("Step")
    table.add_column("Count", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Rules")
    table.add_column("Preventable", justify="right")

    for cluster in result.clusters:
        table.add_row(
            cluster.step,
            str(cluster.count),
            f"{cluster.percentage:.0f}%",
            str(len(cluster.rules)),
            str(cluster.preventable_count),
        )

    console.print(table)

    top = result.clusters[0]
    console.print(
        f"\n{top.count} corrections ({top.percentage:.0f}%) target step "
        f"'{top.step}'. {top.preventable_count} occurred after rules were "
        f"established for this step."
    )
    console.print(
        f"\nTotal: {result.total_corrections} corrections, "
        f"{result.unique_steps} steps, "
        f"concentration ratio: {result.concentration_ratio:.2f}"
    )


@main.command()
@click.option("--run", is_flag=True, help="Execute via LLM API")
def resynthesis(run):
    """Assemble resynthesis prompt, optionally execute via LLM."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    corrections = load_corrections(config)
    rules = load_rules(config)
    analysis = analyze_corrections(corrections, rules)
    protocol_content = (config.root / config.protocol_path).read_text()

    prompt = assemble_prompt(config, protocol_content, corrections, rules, analysis)

    # Write prompt to output path
    output_path = config.root / config.resynthesis_output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt)
    console.print(f"Resynthesis prompt written to {config.resynthesis_output_path}")

    if not run:
        console.print("Feed to your preferred LLM, or use `--run` to execute via API.")
        return

    # Execute via LLM
    console.print("Sending to LLM...")
    try:
        new_protocol = run_resynthesis(config, prompt)
    except (ImportError, RuntimeError) as e:
        raise click.ClickException(str(e))

    staged_path = stage_resynthesis(config, new_protocol)
    console.print(f"Staged at {staged_path.relative_to(config.root)}")

    # Show diff
    console.print("\n[bold]--- Current protocol[/bold]")
    console.print(protocol_content)
    console.print("\n[bold]+++ Staged protocol[/bold]")
    console.print(new_protocol)

    if not click.confirm("\nAccept this resynthesis?", default=False):
        console.print("Resynthesis rejected. Staged file preserved.")
        return

    # Promote
    default_version = _version_increment(config.protocol_version)
    new_version = click.prompt("New version", default=default_version)
    promote_resynthesis(config, staged_path, new_version)
    console.print(f"Protocol updated to {new_version}. Corrections archived.")


@main.command()
def status():
    """Dashboard showing protocol, corrections, rules, and trigger status."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    render_status(config, console)
