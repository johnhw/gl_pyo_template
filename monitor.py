import time
import version 
from datetime import datetime

from rich.live import Live
from rich.table import Table
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

# running print log
# watch variables (table)
# FPS, network, elapsed in footer

def format_time_since_now(dt):
    if dt is None:
        return "---"
    td = datetime.now() - dt
    seconds = td.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:03.0f}:{minutes:02.0f}:{seconds:02.0f}"

class Monitor:
        
    def make_layout(self):        
        layout = Layout(name="root")

        layout.split(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="side"),
            Layout(name="body", ratio=2, minimum_size=60),
        )
        layout["side"].split(Layout(name="box1"), Layout(name="box2"))
        return layout

    def get_header(self):
        git_info = version.get_git_info()
        return f"[bold]{version.demo_name}[/bold] {version.version} {version.author} \nGit: [red]{git_info['branch']}[/red] [yellow]{git_info['author']}[/yellow] [blue]{git_info['sha'][:8]}...[/blue] [white]{git_info['date']}[/white]"

    def set_fps(self, fps):
        self.stats["FPS"] = fps

    def format_basic_stats(self):
        return f"FPS:{self.stats['FPS']:5.0f} Elapsed {format_time_since_now(self.start_time)} ZMQ:{format_time_since_now(self.stats['ZMQ'])}"

    def update_watch(self, watches):
        self.watches.update(watches)

    def clear_watch(self, keys):
        for k in keys:
            if k in self.watches:
                del self.watches[k]
        
    def __init__(self):
        self.watches = {}
        self.watch_table = Table(expand=True)
        self.watch_table.add_column("Variable", style="yellow", width=10)
        self.watch_table.add_column("Value", style="white")        
        
        self.start_time = datetime.now()
        self.stats = {"FPS":0.0,  "ZMQ": None}
        layout = self.make_layout()
        header = self.get_header()
        layout["header"].update(Panel(header, box.ROUNDED, height=4, title="Version"))
        log = Panel("")
        layout["footer"].update(log)        
        layout["box1"].update(self.watch_table)
        with Live(layout, refresh_per_second=10, screen=True):    
            while True:
                time.sleep(0.1)
                #log.print("hello")
                layout["footer"].update(Panel(self.format_basic_stats()))
                


if __name__=="__main__":
    m = Monitor()
