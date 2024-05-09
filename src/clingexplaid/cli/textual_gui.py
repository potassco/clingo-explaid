from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Collapsible, Footer, Input, Label, Select, Tabs


class ClingexplaidTextualApp(App):
    """A textual app for a terminal GUI to use the clingexplaid functionality"""

    BINDINGS = [("ctrl+x", "exit", "Exit")]
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr
    }

    .box {
        height: 100%;
        border: round #455A64;
        padding: 1;
    }

    #top-cell {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr;
    }

    #main-config {
        layout: grid;
        grid-size: 2;
        grid-columns: auto 1fr;
        grid-gutter: 1;
    }

    #main-config Label {
        padding: 1 2;
        background: #263238;
        width: 100%;
    }

    #files {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr auto;
    }

    #files Button{
        width: 100%;
    }

    #files VerticalScroll{
        background: #000;
    }

    #files VerticalScroll Checkbox{
        width: 100%;
    }

    .no-padding-top{
        padding-top: 0;
    }
    """

    def __init__(self):
        super(ClingexplaidTextualApp, self).__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Vertical(
                Label("Mode"),
                Select(((line, line) for line in ["SOLVE", "MUS"]), allow_blank=False),
                Label("Models"),
                Input(placeholder="Number of Models (Default: 1)", type="number"),
                id="main-config",
                classes="box",
            ),
            Vertical(
                VerticalScroll(
                    Checkbox("encoding.lp"),
                    Checkbox("instance_1.lp"),
                    Checkbox("instance_2.lp"),
                    Checkbox("instance_3.lp"),
                    Checkbox("instance_4.lp"),
                ),
                Button("Add a new file"),
                classes="box",
                id="files",
            ),
            id="top-cell",
        )
        yield VerticalScroll(
            Tabs("Tab 1", "Tab 2", "Tab 3"),
            Collapsible(title="Model 1", collapsed=True),
            Collapsible(title="Model 2", collapsed=True),
            Collapsible(title="Model 3", collapsed=True),
            classes="box no-padding-top",
        )
        yield Footer()

    def action_exit(self):
        self.exit()
