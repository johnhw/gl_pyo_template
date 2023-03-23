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

    def watch(self, name, value):
        self.watches[name] = value

    def clear_watch(self, keys):
        for k in keys:
            if k in self.watches:
                del self.watches[k]
        
    def update_watches(self):
        self.watch_table = Table(expand=True)
        self.watch_table.add_column("Variable", style="yellow", width=10)
        self.watch_table.add_column("Value", style="white", justify="right", width=20)        
        
        for k in sorted(self.watches.keys()):
            self.watch_table.add_row(k, str(self.watches[k]))
        self.layout["box1"].update(self.watch_table)

    def __init__(self):
        self.watches = {}
        self.flags = {}
        self.log = []
        self.max_log = 100
        self.start_time = datetime.now()
        self.stats = {"FPS":0.0,  "ZMQ": None}
        layout = self.make_layout()
        header = self.get_header()
        layout["header"].update(Panel(header, box.ROUNDED, height=4, title="Version"))
        
        
        status = Panel("")
        layout["footer"].update(status)        
        self.layout = layout
        self._gen = self._run()

    def print(self, text, end="\n"):
        self.log.append(str(text)+end)

    def set_flag(self, flag):
        self.flags[flag] = True

    def clear_flag(self, flag):
        self.flags[flag] = False
        
    def update_output(self):  
        
        if len(self.log)>1:
            self.log = self.log[-self.max_log:]

        self.layout["body"].update(Panel(Text.assemble(*self.log, overflow="ellipsis")))

    def format_flag(self, flag, set):
        if set is None:
            return f"[yellow]? {flag}[/yellow]"
        elif set:
            return f"[green]* {flag}[/green]"
        else:
            return f"[red]x {flag}[/red]"

    def unset_flag(self, flag):
        self.flags[flag] = None

    def update_flags(self):
        flags = "\n".join([self.format_flag(k, v) for k, v in self.flags.items()])        
        self.layout["box2"].update(Panel(flags))

    def update(self):
        next(self._gen)

    
    

    def _run(self):
        i = 0
        with Live(self.layout, refresh_per_second=10, screen=True):                             
            while True:
                self.update_watch({"spaceman":i})
                i += 1
                self.layout["footer"].update(Panel(self.format_basic_stats()))
                self.update_watches()
                self.update_output()
                self.update_flags()
                
                yield
            
import random
if __name__=="__main__":
    m = Monitor()
    for i in range(100):
        time.sleep(0.1)
        v = random.randint(0,100)
        if v<10:
            m.unset_flag("network")
        elif v<50:
            m.clear_flag("network")
        elif v>90:
            m.set_flag("network")

        m.print(v)
        m.update()
