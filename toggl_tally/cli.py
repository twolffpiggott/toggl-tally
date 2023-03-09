from pathlib import Path
from typing import List

import click
import yaml
from rich.console import Console

from toggl_tally import RichReport, TogglAPI, TogglFilter, TogglTally


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
    seconds_worked = sum(entry["duration"] for entry in filtered_time_entries)
    target_seconds = hours_per_month * 60 * 60
    seconds_outstanding = max(target_seconds - seconds_worked, 0)
    reporter = RichReport(console)
    reporter.report_remaining_working_days(
        remaining_working_days=tally.remaining_working_days,
        next_invoice_date=tally.next_invoice_date,
    )
    reporter.report_hours_per_day(
        seconds_per_day=seconds_outstanding / tally.remaining_working_days,
        hours_per_month=hours_per_month,
        last_billable_date=tally.last_billable_date,
    )
    reporter.report_hours_worked(seconds_worked)
    reporter.month_progress_bar(
        seconds_worked=seconds_worked, target_seconds=target_seconds
    )
    reporter.filters_table(
        workspaces=workspaces,
        clients=clients,
        projects=projects,
    )
    if tally.remaining_public_holidays:
        reporter.holidays_table(holidays=tally.remaining_public_holidays)
