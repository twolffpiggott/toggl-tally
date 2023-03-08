from datetime import datetime

from rich.console import Console


class RichReport(object):
    def __init__(
        self,
        date_format: str = "%a %d %b",
        int_style: str = "bold blue",
        date_style: str = "bold cyan",
        **kwargs,
    ):
        self.console = Console(**kwargs)
        self.date_format = date_format
        self.int_style = int_style
        self.date_style = date_style

    def report_remaining_working_days(
        self, remaining_working_days: int, next_invoice_date: datetime
    ):
        self.console.print(
            f"{self.apply_style(remaining_working_days, 'int_style')}"
            " days to go before next invoice on"
            f" {self.apply_style(next_invoice_date.strftime('%a %d %b'), 'date_style')}."
        )

    def apply_style(self, text, style: str):
        style_str = getattr(self, style)
        return f"[{style_str}]{text}[/{style_str}]"
