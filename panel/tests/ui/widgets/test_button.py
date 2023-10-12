import pytest

pytestmark = pytest.mark.ui

from bokeh.models import Tooltip

from panel.tests.util import serve_component, wait_until
from panel.widgets import (
    Button, CheckButtonGroup, RadioButtonGroup, TooltipIcon,
)

try:
    from playwright.sync_api import expect
except ImportError:
    pytestmark = pytest.mark.skip("playwright not available")


def test_button_click(page):
    button = Button(name='Click')

    events = []
    def cb(event):
        events.append(event)
    button.on_click(cb)

    serve_component(page, button)

    page.click('.bk-btn')

    wait_until(lambda: len(events) == 1, page)


@pytest.mark.parametrize(
    "tooltip",
    ["Test", Tooltip(content="Test", position="right"), TooltipIcon(value="Test")],
    ids=["str", "Tooltip", "TooltipIcon"],
)
@pytest.mark.parametrize(
    "button_fn,button_locator",
    [
        (lambda **kw: Button(**kw), ".bk-btn"),
        (lambda **kw: CheckButtonGroup(options=["A", "B"], **kw), ".bk-btn-group"),
        (lambda **kw: RadioButtonGroup(options=["A", "B"], **kw), ".bk-btn-group"),
    ],
    ids=["Button", "CheckButtonGroup", "RadioButtonGroup"],
)
def test_button_tooltip(page, button_fn, button_locator, tooltip):
    pn_button = button_fn(name="test", description="Test")

    serve_component(page, pn_button)

    button = page.locator(button_locator)
    expect(button).to_have_count(1)
    tooltip = page.locator(".bk-Tooltip")
    expect(tooltip).to_have_count(0)

    # Hovering over the button should show the tooltip
    page.hover(button_locator)
    tooltip = page.locator(".bk-Tooltip")
    expect(tooltip).to_have_count(1)
    assert tooltip.locator("div").first.text_content().strip() == "Test"

    # Removing hover should hide the tooltip
    page.hover("body")
    tooltip = page.locator(".bk-Tooltip")
    expect(tooltip).to_have_count(0)
