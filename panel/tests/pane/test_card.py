"""Tests of the Cards inspired by Bootstrap Cards.

- [Get Bootstrap Card](https://getbootstrap.com/docs/4.3/components/card/) and
- [Card Collapse Tricks](https://disjfa.github.io/bootstrap-tricks/card-collapse-tricks/)

Please note that

- the css and javascript of Bootstrap and does not play well with Panel/ Bokeh, so I've had to
create a custom version for Panel/ Bokeh.
"""
from typing import Callable

import hvplot.pandas  # pylint: disable=unused-import
import pandas as pd

import panel as pn
from panel.card import Card
from panel.layout import Column
from panel.pane import Markdown

TEXT = """\
Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid.
3 wolf moon officia aute, non cupidatat skateboard dolor brunch.
Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on
 it squid single-origin coffee nulla assumenda shoreditch et. Nihil anim keffiyeh helvetica, craft
 beer labore wes anderson cred nesciunt sapiente ea proident. Ad vegan excepteur butcher vice lomo.
 Leggings occaecat craft beer farm-to-table, raw denim aesthetic synth nesciunt you probably
 haven't heard of them accusamus labore sustainable VHS."""


class TestApp(Column):
    """Creates a Test App from the name and docstring of the test function"""

    __test__ = False  # We don't wan't pytest to collect this

    def __init__(self, test_func: Callable, *args, **kwargs):
        """## Creates a Test App from the name and docstring of the test function

        Displays
        - __name__
        - __doc__

        Has sizing_mode="stretch_width" unless otherwise specified

        Arguments:
            test_func {Callable} -- The function to create an app from.
        """
        text_str = test_func.__name__.replace("_", " ",).capitalize()
        text_str = "    # " + text_str

        if test_func.__doc__:
            if test_func.__doc__.startswith("    "):
                text_str += "\n\n" + test_func.__doc__
            else:
                text_str += "\n\n    " + test_func.__doc__

        text = Markdown(text_str)

        if "sizing_mode" not in kwargs and "width" not in kwargs and "height" not in kwargs:
            kwargs["sizing_mode"] = "stretch_width"

        super().__init__(text, *args, **kwargs)

def _get_chart_data() -> pd.DataFrame:
    """## Chart Data

    Returns:
        pd.DataFrame -- A DataFrame with dummy data and columns=["Day", "Orders"]
    """

    chart_data = {
        "Day": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",],
        "Orders": [15539, 21345, 18483, 24003, 23489, 24092, 12034,],
    }
    return pd.DataFrame(chart_data)


def _holoviews_chart():
    """## Dashboard Orders Chart generated by HoloViews"""
    data = _get_chart_data()
    line_plot = data.hvplot.line(
        x="Day", y="Orders", width=None, height=500, line_color="#007BFF", line_width=6,
    )
    scatter_plot = data.hvplot.scatter(x="Day", y="Orders", height=300,).opts(
        marker="o", size=10, color="#007BFF",
    )
    fig = line_plot * scatter_plot
    gridstyle = {
        "grid_line_color": "black",
        "grid_line_width": 0.1,
    }
    fig = fig.opts(
        responsive=True,
        toolbar=None,
        yticks=list(range(12000, 26000, 2000,)),
        ylim=(12000, 26000,),
        gridstyle=gridstyle,
        show_grid=True,
    )
    return fig

def test_card():
    """We test that we can create a card with

    - A header with lightgray background
    - A Body
    - A fixed width of 300px.

    """

    card = Card(header="Card - Header and Body", width=300, body=[TEXT])
    return TestApp(test_card, card, width=600, background="ghostwhite",)


def test_card_stretch_width():
    """We test that we can create a card with

    - A header with lightgray background
    - A Body
    - A sizing_mode of `stretch_width`
    """
    card = Card(header="Card - Fixed Width", body=[TEXT], sizing_mode="stretch_width",)
    return TestApp(test_card_stretch_width, card, width=600, background="ghostwhite",)



def test_card_with_plot():
    """We test that we can create a card with

    - A header with lightgray background
    - A Plot Body

    And the card it self is has a fixed width or 600px
    """
    card = Card(header="Card With Plot", body=[_holoviews_chart()], width=600,)
    return TestApp(test_card_with_plot, card,)


def test_card_with_multiple_panels():
    """We test that we can create a card with

    - A header with lightgray background
    - A Plot Body
    - A Text Body
    - A Plot Body
    - A Text Body

    Please note that due to some Bokeh formatting I've not been able to create
    a divider line that stretches to full width.
    """
    card = Card(
        header="Card With Plot",
        body=[_holoviews_chart(), "Awesome Panel! " * 50, _holoviews_chart(), "Awesome Panel! " * 50,],
        width=600,
    )
    return TestApp(test_card_with_multiple_panels, card,)


def test_card_collapsable():
    """We test that we can create a collapsable card with

    - A header with lightgray background
    - A Plot Body
    - A Text Body

    Please **note** that

    - the header text and collapse button text are not vertically aligned. I have yet to figure
    that out.
    - I have not been able to use the *chevron down* with a *rotation* transition like at
    [Card Collapse Tricks](https://disjfa.github.io/bootstrap-tricks/card-collapse-tricks/)
    - When you click the collabse button, the button is shown for a short while. I would like to
    remove that but I do not yet know how.
    - I would like to change the collapse button callback from a Python callback to JS callback.
    """
    card = Card(
        header="Card with Plot",
        body=[_holoviews_chart(), "Awesome Panel! " * 50,],
        collapsable=True,
        width=600,
    )
    return TestApp(test_card_collapsable, card,)


def test_card_with_code():
    """We test that we can create a card with code content"""
    code = """\
        ```python
        card = Card("Code", pnx.Code(code),)
        return TestApp(test_card_collapsable, card)
        ```"""
    card = Card(header="Code", body=[pn.pane.Markdown(code)])
    return TestApp(test_card_with_code, card, width=600)


def view() -> pn.Column:
    """Wraps all tests in a Column that can be included in the Gallery or served independently

    Returns:
        pn.Column -- A Column containing all the tests
    """
    return pn.Column(
        pn.pane.Markdown(__doc__),
        pn.layout.Divider(),
        test_card(),
        pn.layout.Divider(),
        test_card_stretch_width(),
        pn.layout.Divider(),
        test_card_with_plot(),
        pn.layout.Divider(),
        test_card_with_multiple_panels(),
        pn.layout.Divider(),
        test_card_collapsable(),
        pn.layout.Divider(),
        test_card_with_code(),
        sizing_mode="stretch_width",
    )


if __name__.startswith("bk"):
    # import ptvsd
    # ptvsd.enable_attach(address=('localhost', 5678))
    # print('Ready to attach the VS Code debugger')
    # ptvsd.wait_for_attach() # Only include this line if you always wan't to attach the debugger
    view().servable()
