import datetime
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
    # if value is derived from yaml config
    if isinstance(value, list):
        return value
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
@click.pass_context
def hours(
    ctx: click.Context,
    hours_per_month: int,
    invoice_day: int,
    workspaces: List[str],
    clients: List[str],
    projects: List[str],
):
    api = TogglAPI()
    tally = TogglTally(invoice_day_of_month=invoice_day)
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
    str_hours = float_seconds_to_str(seconds_outstanding / tally.remaining_working_days)
    click.echo(
        f"{tally.remaining_working_days} days remaining before next invoice on"
        f" {tally.next_invoice_date.strftime('%d %b')}"
    )
    click.echo(
        f"Work {str_hours} per day to hit your target of {hours_per_month} hours"
        f" by last billable workday {tally.last_billable_date.strftime('%d %b')}"
    )


def float_seconds_to_str(seconds: float) -> str:
    return str(datetime.timedelta(seconds=seconds)).rsplit(".", 1)[0]
