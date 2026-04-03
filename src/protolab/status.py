"""protolab status — rich dashboard."""

from __future__ import annotations

import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .analyze import analyze_corrections
from .check import evaluate_triggers
from .config import Config
from .store import load_corrections, load_rules


def render_status(config: Config, console: Console | None = None) -> None:
    """Load all data and render rich-formatted dashboard to terminal."""
    if console is None:
        console = Console()

    corrections = load_corrections(config)
    rules = load_rules(config)
    analysis = analyze_corrections(corrections, rules)
    triggers = evaluate_triggers(config, corrections, rules)

    # Protocol info
    protocol_file = config.root / config.protocol_path
    mod_time = ""
    if protocol_file.exists():
        mtime = os.path.getmtime(protocol_file)
        mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    console.print(Panel(
        f"[bold]Path:[/bold] {config.protocol_path}\n"
        f"[bold]Version:[/bold] {config.protocol_version}\n"
        f"[bold]Last modified:[/bold] {mod_time}",
        title="Protocol",
    ))

    # Corrections summary
    if corrections:
        dates = [c["date"] for c in corrections if isinstance(c.get("date"), datetime)]
        oldest = min(dates).strftime("%Y-%m-%d") if dates else "?"
        newest = max(dates).strftime("%Y-%m-%d") if dates else "?"
        console.print(f"\n[bold]Corrections:[/bold] {len(corrections)} (oldest: {oldest}, newest: {newest})")
    else:
        console.print("\n[bold]Corrections:[/bold] 0")

    # Step cluster table
    if analysis.clusters:
        table = Table(title="Corrections by Step")
        table.add_column("Step")
        table.add_column("Count", justify="right")
        table.add_column("Has Rules")
        table.add_column("Preventable", justify="right")
        for cluster in analysis.clusters:
            table.add_row(
                cluster.step,
                str(cluster.count),
                "yes" if cluster.rules else "no",
                str(cluster.preventable_count),
            )
        console.print(table)

    # Rules by confidence
    if rules:
        counts = {"provisional": 0, "strong_pattern": 0, "structural": 0}
        for r in rules:
            conf = r.get("confidence", "provisional")
            if conf in counts:
                counts[conf] += 1
        console.print(
            f"\n[bold]Rules:[/bold] {len(rules)} "
            f"(structural: {counts['structural']}, "
            f"strong_pattern: {counts['strong_pattern']}, "
            f"provisional: {counts['provisional']})"
        )

    # Triggers
    if triggers:
        trigger_table = Table(title="Triggers")
        trigger_table.add_column("Trigger")
        trigger_table.add_column("Status")
        trigger_table.add_column("Current", justify="right")
        trigger_table.add_column("Threshold", justify="right")
        for t in triggers:
            status_str = "[green]met[/green]" if t.met else "[dim]unmet[/dim]"
            trigger_table.add_row(
                t.name, status_str, str(t.current_value), str(t.threshold),
            )
        console.print(trigger_table)

    # Last resynthesis
    if config.last_resynthesis_date:
        console.print(
            f"\n[bold]Last resynthesis:[/bold] "
            f"{config.last_resynthesis_date.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        console.print("\n[bold]Last resynthesis:[/bold] never")
