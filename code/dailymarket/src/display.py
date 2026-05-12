from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from datetime import datetime

class DisplayManager:
    def __init__(self):
        self.console = Console()

    def format_perf(self, val):
        if val is None:
            return "N/A"
        color = "green" if val > 0 else "red"
        return f"[{color}]{val:+.2f}%[/]"

    def create_table(self, title, data):
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="dim", width=12)
        table.add_column("Price", justify="right")
        table.add_column("24h", justify="right")
        table.add_column("48h", justify="right")
        table.add_column("7d", justify="right")

        for item in data:
            table.add_row(
                item["symbol"],
                f"${item['price']:.2f}",
                self.format_perf(item["24h"]),
                self.format_perf(item["48h"]),
                self.format_perf(item["7d"])
            )
        return table

    def render(self, watchlist_data, gainers_data, losers_data):
        self.console.clear()
        self.console.print(Panel(f"Dailymarket - [bold blue]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]", expand=False))
        
        if watchlist_data:
            self.console.print(self.create_table("Watchlist", watchlist_data))
        
        if gainers_data:
            self.console.print(self.create_table("Top Gainers", gainers_data))
            
        if losers_data:
            self.console.print(self.create_table("Top Losers", losers_data))
            
        self.console.print("\n[dim]Press Ctrl+C to exit. Updates based on config.json interval.[/]")
