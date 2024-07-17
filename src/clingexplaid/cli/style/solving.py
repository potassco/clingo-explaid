MODE_SOLVING_STYLE = """
#content.mode-solving{
    Collapsible.model Collapsible{
        margin-right: 4;
        border-top: blank;
    }

    Collapsible.model Horizontal{
        height: auto;
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr auto auto;
        padding-top: 1;
        grid-gutter: 2;
    }

    Collapsible.model Horizontal Button{
        padding: 0;
        border: round $primary-lighten-1;
        background: transparent;
    }
}
"""
