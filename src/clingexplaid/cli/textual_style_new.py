"""
Module containing TCSS style strings for the textual TUI
"""

MAIN_CSS = """
$bg: #0A0E0F;
$bg-1: #141D1F;
$sec: #37474F;
$pr: #6666FF;

$green: #558B2F;
$green-d: #33691E;

Screen{
    layout: grid;
    grid-size: 1 2;
    grid-rows: 1fr 7;
    background: $bg;
}
#content{
    layout: grid;
    grid-size: 2 2;
    grid-columns: 2fr 1fr;
    grid-rows: auto 1fr;
    grid-gutter: 1 2;
    padding: 1 2;
    height: 100%;
}

Button{
    border: none;
    padding: 0 2;
    border: tall;
}

Header{
    layout: grid;
    grid-size: 4 1;
    grid-columns: auto 1fr auto auto;
    grid-gutter: 2;
}

Header #sat-indicator{
    padding: 0 2;
    background: $green;
    border: thick $green-d;
}

Header Button{
    border: tall $pr;
    background: transparent;
}

SolverActions{
    layout: grid;
    grid-size: 3 1;
    grid-columns: 1fr 1fr 1fr;
    grid-gutter: 2;
}

SolverActions Button{
    width: 100%;
    background: $sec;
    border: $sec;
}

Actions{
    height: 100%;
    background: $bg-1;
}

Log{
    background: black;
}
"""
