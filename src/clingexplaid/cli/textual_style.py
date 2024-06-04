"""
Module containing TCSS style strings for the textual TUI
"""

MAIN_CSS = """
Screen {
    layout: grid;
    grid-size: 2 2;
    grid-columns: 1fr 2fr;
    grid-rows: 1fr auto;
}
#debug{
    column-span: 2;
}

.box {
    height: 100%;
    border: round #455A64;
    padding: 1;
}

.box.tabs{
    padding: 0;
}

#top-cell {
    layout: grid;
    grid-size: 1;
    grid-rows: auto 1fr;
}

ControlPanel {
    layout: grid;
    grid-size: 2;
    grid-columns: auto 1fr;
    grid-gutter: 1;
}

ControlPanel Input{
    width: 100%;
}

ControlPanel Label {
    padding: 1 2;
    background: #263238;
    width: 100%;
}

ControlPanel Label.error{
    border: tall rgb(235,64,52);
    background: rgba(235,64,52,0.2);
    padding: 0 2;
    color: rgb(235,64,52);
}

ControlPanel .error{
    display: none;
}

ControlPanel.error .error{
    display: block
}

ControlPanel #solve-button{
    column-span: 2;
    width: 100%;
}

ControlPanel.error #solve-button{
    display: none;
}

ControlPanel #solve-button{
    display: block;
    width: 100%;
}

.selectors{
    background: #000;
}

SelectorWidget{
    layout: grid;
    grid-size: 2;
    grid-columns: auto 1fr;
}

LabelInputWidget{
    layout: grid;
    grid-size: 3;
    grid-columns: auto 1fr 1fr;
}

SelectorWidget{
    background: transparent;
}

SelectorWidget.active{
    background: $primary-darken-3;
}

SelectorWidget Label{
    padding: 1;
}

SelectorWidget Checkbox{
    background: transparent;
}

SelectorWidget Input{
    border: none;
    padding: 1 2;
}

SelectorWidget HorizontalScroll{
    height: auto;
    background: transparent;
}

SolverTreeView{
    content-align: center middle;
}

SolverTreeView Tree{
    display: block;
    padding: 1 2;
    background: #000;
}

SolverTreeView LoadingIndicator{
    height: auto;
    padding: 1;
    background: #000;
    display: none;
}

SolverTreeView.solving LoadingIndicator{
    display: block;
}
"""
