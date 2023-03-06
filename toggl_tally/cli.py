from pathlib import Path
from typing import List

import click
import yaml
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table

from toggl_tally import TogglAPI, TogglFilter, TogglTally


@click.group()
@click.option(
    "--config", default="config.yml", type=click.Path(exists=True, path_type=Path)
)
@click.pass_context
def toggl_tally(ctx: click.Context, config: Path):
    with config.open("r") as f:
        config_dict = yaml.safe_load(f)
    ctx.default_map = dict(hours=config_dict)


def _comma_separated_arg_split(ctx, param, value):
    if value is None:
        return []
    options = [option.strip() for option in value.split(",")]
    return options


@toggl_tally.command()
@click.option(
    "--hours-per-month",
    type=int,
    help="Target working hours per month",
)
@click.option(
    "--invoice-day",
    type=int,
    help="Invoicing day of month",
)
@click.option(
    "--workspaces",
    callback=_comma_separated_arg_split,
    help="Comma-separated list of workspaces",
)
@click.option(
    "--clients",
    callback=_comma_separated_arg_split,
    help="Comma-separated list of clients",
)
@click.option(
    "--projects",
    callback=_comma_separated_arg_split,
    help="Comma-separated list of projects",
)
@click.option(
    "--skip-today",
    is_flag=True,
    show_default=True,
    default=False,
    help="Exclude today from remaining working days for the month",
)
@click.pass_context
def hours(
    ctx: click.Context,
    hours_per_month: int,
    invoice_day: int,
    workspaces: List[str],
    clients: List[str],
    projects: List[str],
    skip_today: bool,
):
    console = Console()
    api = TogglAPI()
    tally = TogglTally(invoice_day_of_month=invoice_day, skip_today=skip_today)
    with console.status("[bold dark_cyan]Getting clients, projects and workspaces"):
        filter = TogglFilter(
            api=api,
            projects=projects,
            clients=clients,
            workspaces=workspaces,
        )
    with console.status("[bold dark_cyan]Getting time entries"):
        unfiltered_time_entries = api.get_time_entries_between(
            start_date=tally.last_invoice_date,
            end_date=tally.now,
        )
    filtered_time_entries = filter.filter_time_entries(response=unfiltered_time_entries)
    # exclude running entries
    seconds_worked = sum(
        entry["duration"] for entry in filtered_time_entries if entry["duration"] > 0
    )
    target_seconds = hours_per_month * 60 * 60
    seconds_outstanding = max(target_seconds - seconds_worked, 0)
    str_hours = format_seconds(seconds_outstanding / tally.remaining_working_days)
    console.print(
        f"[bold blue]{tally.remaining_working_days}[/bold blue]"
        " days remaining before next invoice on"
        f" [bold cyan]{tally.next_invoice_date.strftime('%d %b')}[/bold cyan]."
    )
    console.print(
        f"Work [bold dark_cyan]{str_hours}[/bold dark_cyan] per day to hit your target"
        f" of [bold orange1]{hours_per_month}[/bold orange1] hours"
        " by last billable workday"
        f" [bold cyan]{tally.last_billable_date.strftime('%d %b')}[/bold cyan]."
    )
    console.print(
        f"[bold dark_cyan]{format_seconds(seconds_worked)}[/bold dark_cyan]"
        " hours worked since last invoice."
    )
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        progress.add_task(
            "[green]Progress for month", completed=seconds_worked, total=target_seconds
        )
    table = Table(title="Filters")
    table.add_column("Type", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    for workspace_name in workspaces:
        table.add_row("Workspace", workspace_name)
    for client_name in clients:
        table.add_row("Client", client_name)
    for project_name in projects:
        table.add_row("Project", project_name)
    console.print(table)


def format_seconds(seconds: float) -> str:
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"
