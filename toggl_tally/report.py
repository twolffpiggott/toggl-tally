from datetime import date, datetime
from typing import List, Tuple

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table

from toggl_tally.time_utils import format_seconds


class RichReport(object):
    def __init__(
        self,
        console: Console,
        date_format: str = "%a %d %b",
        int_style: str = "bold blue",
        date_style: str = "bold cyan",
        limit_int_style: str = "bold orange1",
        hours_style: str = "bold dark_cyan",
        error_style: str = "bold red",
        **kwargs,
    ):
        self.console = console
        self.date_format = date_format
        self.int_style = int_style
        self.date_style = date_style
        self.limit_int_style = limit_int_style
        self.hours_style = hours_style
        self.error_style = error_style

    def report_remaining_working_days(
        self, remaining_working_days: int, next_invoice_date: datetime
    ):
        self.console.print(
            f"{self.apply_style(remaining_working_days, 'int_style')}"
            " days to go before next invoice on"
            f" {self.apply_style(next_invoice_date.strftime(self.date_format), 'date_style')}."
        )

    def report_hours_per_day(
        self,
        seconds_outstanding: float,
        remaining_working_days: int,
        hours_per_month: float,
        last_billable_date: datetime,
    ):
        try:
            seconds_per_day = seconds_outstanding / remaining_working_days
        except ZeroDivisionError:
            self.console.print(
                f"You have {self.apply_style('no working days left', 'error_style')}."
            )
        else:
            self.console.print(
                f"Work {self.apply_style(format_seconds(seconds_per_day), 'hours_style')} per day"
                f" to hit your target of {self.apply_style(hours_per_month, 'limit_int_style')}"
                " hours on last billable workday"
                f" {self.apply_style(last_billable_date.strftime(self.date_format), 'date_style')}"
                "."
            )

    def report_hours_worked(self, seconds_worked: float):
        self.console.print(
            f"{self.apply_style(format_seconds(seconds_worked), 'hours_style')}"
            " hours worked since last invoice."
        )

    def month_progress_bar(self, seconds_worked: float, target_seconds: float):
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            progress.add_task(
                "[green]Progress for month",
                completed=seconds_worked,
                total=target_seconds,
            )

    def filters_table(
        self, workspaces: List[str], clients: List[str], projects: List[str]
    ):
        table = Table(title="Filters")
        table.add_column("Type", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        for workspace_name in workspaces:
            table.add_row("Workspace", workspace_name)
        for client_name in clients:
            table.add_row("Client", client_name)
        for project_name in projects:
            table.add_row("Project", project_name)
        self.console.print(table)

    def holidays_table(self, holidays: List[Tuple[str, date]]):
        table = Table(title="Public holidays")
        table.add_column("Name", justify="right", style="cyan", no_wrap=True)
        table.add_column("Date", style="magenta")
        for holiday in holidays:
            table.add_row(holiday[0], holiday[1].strftime("%a %d %b"))
        self.console.print(table)

    def apply_style(self, text, style: str):
        style_str = getattr(self, style)
        return f"[{style_str}]{text}[/{style_str}]"
