"""
Module containing TCSS style strings for the textual TUI
"""

MAIN_CSS = """
Screen{
    layout: grid;
    grid-size: 1 3;
    grid-rows: auto 1fr 7;
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

Log{
    padding: 1 2;
    height: 100%;
}

Button.outlined{
    background: transparent;
    border: none;
    width: 100%;
    border: round $background-lighten-3;
    color: #fff;
    margin-bottom: 1;
    opacity: 0.8;
    transition: opacity 100ms;
}

Button.outlined:hover{
    opacity: 1;
}

Button.outlined Label{
    background: transparent;
}

Button.hidden{
    display: none;
}
"""
