"""
Module containing TCSS style strings for the textual TUI
"""

MAIN_CSS = """
Screen{
    layout: grid;
    grid-size: 1 2;
    grid-rows: auto 1fr;
}
#header{
    layout: grid;
    grid-size: 2 1;
    grid-columns: 1fr 11;  /* uneven for center alignment */
    grid-gutter: 2;
    padding: 1 2;
    height: auto;
}
#sat-indicator{
    padding: 0 1;
    background: $success-darken-2;
    width: 100%;
    text-align: center;
    border: thick $success-darken-3;
}
#sat-indicator.sat{
    background: $success-darken-2;
    border: thick $success-darken-3;

}
#sat-indicator.unsat{
    background: $error;
    border: thick $error-darken-1;
}

#content{
    height: 100%;
    width: 100%;
    padding: 1 2;
    background: $background;
}
"""
