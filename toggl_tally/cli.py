from pathlib import Path
from typing import List

import click
import yaml

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
    api = TogglAPI()
    tally = TogglTally(invoice_day_of_month=invoice_day, skip_today=skip_today)
    filter = TogglFilter(
        api=api,
        projects=projects,
        clients=clients,
        workspaces=workspaces,
    )
    unfiltered_time_entries = api.get_time_entries_between(
        start_date=tally.last_invoice_date,
        end_date=tally.now,
    )
    filtered_time_entries = filter.filter_time_entries(response=unfiltered_time_entries)
    seconds_worked = sum(entry["duration"] for entry in filtered_time_entries)
    target_seconds = hours_per_month * 60 * 60
    seconds_outstanding = max(target_seconds - seconds_worked, 0)
    str_hours = format_seconds(seconds_outstanding / tally.remaining_working_days)
    click.echo(
        f"{tally.remaining_working_days} days remaining before next invoice on"
        f" {tally.next_invoice_date.strftime('%d %b')}"
    )
    click.echo(
        f"Work {str_hours} per day to hit your target of {hours_per_month} hours"
        f" by last billable workday {tally.last_billable_date.strftime('%d %b')}"
    )
    workspaces_str = f"\nworkspaces: {', '.join(workspaces)}" if workspaces else ""
    clients_str = f"\nclients: {', '.join(clients)}" if clients else ""
    projects_str = f"\nprojects: {', '.join(projects)}" if projects else ""
    context_str = workspaces_str + clients_str + projects_str
    click.echo(
        f"{format_seconds(seconds_worked)} hours worked since last invoice "
        f"across:{context_str}"
    )


def format_seconds(seconds: float) -> str:
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"
