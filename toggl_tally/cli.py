import ast
from pathlib import Path
from typing import List, Optional

import click
import yaml
from rich.console import Console
from rich.traceback import install

from toggl_tally import RichReport, TogglAPI, TogglFilter, TogglTally

CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"], auto_envvar_prefix="TOGGL_TALLY"
)


def _comma_separated_arg_split(ctx, param, value):
    """
    >>> _comma_separated_arg_split(None, None, 'foo,bar,baz')
    ['foo', 'bar', 'baz']
    >>> _comma_separated_arg_split(None, None, "['foo', 'bar']")
    ['foo', 'bar']
    >>> _comma_separated_arg_split(None, None, None)
    []
    >>> _comma_separated_arg_split(None, None, "foo bar")
    ['foo bar']
    >>> _comma_separated_arg_split(None, None, "['foo bar']")
    ['foo bar']
    """
    if value is None:
        return []
    # values read from yaml config will be a list cast to str
    error_msg = f"Expected comma-separated list but got {value}"
    try:
        options = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        # should be dealing with a comma-separated list of strs
        try:
            options = [option.strip() for option in value.split(",")]
        except AttributeError:
            raise ValueError(error_msg)
    except (TypeError, MemoryError, RecursionError):
        raise ValueError(error_msg)
    else:
        # did we literal eval to the expected type?
        if not isinstance(options, list):
            raise ValueError(error_msg)
    return options


@click.group(
    context_settings=CONTEXT_SETTINGS,
    help="A rich CLI to track hours worked against monthly targets with toggl",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to optional yaml config with CLI option values",
)
@click.pass_context
def toggl_tally(ctx: click.Context, config: Optional[Path]):
    # rich traceback handling
    install(max_frames=1)
    if config is not None:
        with config.open("r") as f:
            config_dict = yaml.safe_load(f)
        ctx.default_map = dict(hours=config_dict)


@toggl_tally.command(
    context_settings=CONTEXT_SETTINGS,
    help="Get remaining daily hours to hit monthly target",
)
@click.option(
    "--hours-per-month",
    type=int,
    required=True,
    help="Target working hours per month",
)
@click.option(
    "--invoice-day",
    type=int,
    required=True,
    help="Invoicing day of month",
)
@click.option(
    "--workspaces",
    "-w",
    callback=_comma_separated_arg_split,
    help="Comma-separated workspace(s) to filter time entries by (e.g. 'foo, bar')",
)
@click.option(
    "--clients",
    "-c",
    callback=_comma_separated_arg_split,
    help="Comma-separated client(s) to filter time entries by (e.g. 'foo, bar')",
)
@click.option(
    "--projects",
    "-p",
    callback=_comma_separated_arg_split,
    help="Comma-separated project(s) to filter time entries by (e.g. 'foo, bar')",
)
@click.option(
    "--skip-today",
    is_flag=True,
    show_default=True,
    default=False,
    help="Exclude today from remaining working days for the month",
)
@click.option(
    "--timezone",
    "-tz",
    help="Timezone for time entries",
)
@click.option(
    "--working-days",
    "-wd",
    callback=_comma_separated_arg_split,
    default=["MO", "TU", "WE", "TH", "FR"],
    help="Comma-separated days of week over which you work (e.g. 'MO, TU')",
)
@click.option(
    "--country",
    required=True,
    help="Your country code (used to determine holiday dates)",
)
@click.option(
    "--exclude-public-holidays",
    is_flag=True,
    show_default=True,
    default=True,
    help="Whether to assume public holidays are not working days",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show active filters and public holidays",
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
    timezone: Optional[str],
    working_days: List[str],
    country: str,
    exclude_public_holidays: bool,
    verbose: bool,
):
    console = Console()
    api = TogglAPI()
    tally = TogglTally(
        invoice_day_of_month=invoice_day,
        country=country,
        skip_today=skip_today,
        timezone=timezone,
        working_days=working_days,
        exclude_public_holidays=exclude_public_holidays,
    )
    with console.status("[bold dark_cyan]Getting clients, projects and workspaces"):
        filter = TogglFilter(
            api=api,
            projects=projects,
            clients=clients,
            workspaces=workspaces,
        )
    with console.status("[bold dark_cyan]Getting time entries"):
        unfiltered_time_entries = api.get_time_entries_between(
            start_date=tally.first_billable_date,
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
        seconds_outstanding=seconds_outstanding,
        remaining_working_days=tally.remaining_working_days,
        hours_per_month=hours_per_month,
        last_billable_date=tally.last_billable_date,
    )
    reporter.report_hours_worked(seconds_worked)
    reporter.month_progress_bar(
        seconds_worked=seconds_worked, target_seconds=target_seconds
    )
    if verbose:
        reporter.filters_table(
            workspaces=workspaces,
            clients=clients,
            projects=projects,
        )
        if tally.remaining_public_holidays:
            reporter.holidays_table(holidays=tally.remaining_public_holidays)
