"""
Module containing TCSS style strings for the textual TUI
"""

MAIN_CSS = """
$bg: #0A0E0F;
$bg-1: #141D1F;
$sec: #37474F;
$sec-l: #546E7A;
$pr: #6666FF;
$pr-d: #40409E;

$green: #558B2F;
$green-d: #33691E;
$red: #C62828;

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
    padding: 0 4;
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
    padding: 1 2;
    layout: grid;
    grid-size: 1 3;
    grid-rows: 1fr auto auto;
    grid-gutter: 1 2;
}

Actions SelectCurrent{
    margin-bottom: 1;
    border: tall $sec-l;
    background: $sec;
    color: #FFF;
}

Actions Filters{
    layout: grid;
    grid-size: 1;
    margin-bottom: 1;
}

Actions Filters Checkbox{
    width: 100%;
    background: transparent;
}

Actions #inputs{
    layout: grid;
    grid-size: 1;
    grid-gutter: 1;
}

Actions #inputs TextArea{
    height: 8;
    border: solid #FFF;
    padding: 1 2;
}

Actions Button{
    width: 100%;
}

Actions Button#apply{
    background: $pr-d;
    border: tall $pr;
    color: #FFF;
}

Actions Button#clear-history{
    background: transparent;
    border: tall $red;
    color: #FFF;
}

Log{
    background: black;
}
"""
