from __future__ import absolute_import

import pytest

import param
from bokeh.models import (Div, Row as BkRow, WidgetBox as BkWidgetBox,
                          GlyphRenderer, Circle, Line)
from bokeh.plotting import Figure
from panel.panes import (Pane, PaneBase, BokehPane, HoloViewsPane,
                         MatplotlibPane, ParamMethodPane)

try:
    import holoviews as hv
except:
    hv = None
hv_available = pytest.mark.skipif(hv is None, reason="requires holoviews")

try:
    import matplotlib as mpl
    mpl.use('Agg')
except:
    mpl = None
mpl_available = pytest.mark.skipif(mpl is None, reason="requires matplotlib")

from .fixtures import mpl_figure


def test_get_bokeh_pane_type():
    div = Div()
    assert PaneBase.get_pane_type(div) is BokehPane


def test_bokeh_pane(document, comm):
    div = Div()
    pane = Pane(div)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    assert div.ref['id'] in pane._callbacks
    model = row.children[0]
    assert model is div

    # Replace Pane.object
    div2 = Div()
    pane.object = div2
    model = row.children[0]
    assert model is div2
    assert div2.ref['id'] in pane._callbacks
    assert div.ref['id'] not in pane._callbacks

    # Cleanup
    pane._cleanup(div2)
    assert pane._callbacks == {}


@hv_available
def test_get_holoviews_pane_type():
    curve = hv.Curve([1, 2, 3])
    assert PaneBase.get_pane_type(curve) is HoloViewsPane


@pytest.mark.usefixtures("hv_mpl")
@mpl_available
@hv_available
def test_holoviews_pane_mpl_renderer(document, comm):
    curve = hv.Curve([1, 2, 3])
    pane = Pane(curve)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    assert len(pane._callbacks) == 1
    model = row.children[0]
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div = model.children[0].children[0]
    assert isinstance(div, Div)
    assert '<img' in div.text

    # Replace Pane.object
    scatter = hv.Scatter([1, 2, 3])
    pane.object = scatter
    model = row.children[0]
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div2 = model.children[0].children[0]
    assert isinstance(div2, Div)
    assert div2.text != div.text

    # Cleanup
    pane._cleanup(model)
    assert pane._callbacks == {}


@pytest.mark.usefixtures("hv_bokeh")
@hv_available
def test_holoviews_pane_bokeh_renderer(document, comm):
    curve = hv.Curve([1, 2, 3])
    pane = Pane(curve)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    assert len(pane._callbacks) == 1
    model = row.children[0]
    assert isinstance(model, Figure)
    renderers = [r for r in model.renderers if isinstance(r, GlyphRenderer)]
    assert len(renderers) == 1
    assert isinstance(renderers[0].glyph, Line)

    # Replace Pane.object
    scatter = hv.Scatter([1, 2, 3])
    pane.object = scatter
    model = row.children[0]
    assert isinstance(model, Figure)
    renderers = [r for r in model.renderers if isinstance(r, GlyphRenderer)]
    assert len(renderers) == 1
    assert isinstance(renderers[0].glyph, Circle)
    assert len(pane._callbacks) == 1

    # Cleanup
    pane._cleanup(model)
    assert pane._callbacks == {}


@mpl_available
def test_get_matplotlib_pane_type():
    assert PaneBase.get_pane_type(mpl_figure()) is MatplotlibPane


@mpl_available
def test_matplotlib_pane(document, comm):
    pane = Pane(mpl_figure())

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    assert len(pane._callbacks) == 1
    model = row.children[0]
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div = model.children[0].children[0]
    assert isinstance(div, Div)
    assert '<img' in div.text
    text = div.text

    # Replace Pane.object
    pane.object = mpl_figure()
    model = row.children[0]
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div2 = model.children[0].children[0]
    assert div is div2
    assert div.text != text

    # Cleanup
    pane._cleanup(model)
    assert pane._callbacks == {}


class View(param.Parameterized):

    a = param.Integer(default=0)

    @param.depends('a')
    def view(self):
        return Div(text='%d' % self.a)

    @param.depends('a')
    def mpl_view(self):
        return mpl_figure()

    @param.depends('a')
    def mixed_view(self):
        return self.view() if (self.a % 2) else self.mpl_view()


def test_get_param_method_pane_type():
    assert PaneBase.get_pane_type(View().view) is ParamMethodPane


def test_param_method_pane(document, comm):
    test = View()
    pane = Pane(test.view)
    inner_pane = pane._pane
    assert isinstance(inner_pane, BokehPane)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    div = row.children[0]
    assert div.ref['id'] in inner_pane._callbacks
    assert isinstance(div, Div)
    assert div.text == '0'

    # Update pane
    test.a = 5
    div = row.children[0]
    assert inner_pane is pane._pane
    assert div.text == '5'
    assert len(inner_pane._callbacks) == 1
    assert div.ref['id'] in inner_pane._callbacks

    # Cleanup pane
    pane._cleanup(div)
    assert inner_pane._callbacks == {}


@mpl_available
def test_param_method_pane_mpl(document, comm):
    test = View()
    pane = Pane(test.mpl_view)
    inner_pane = pane._pane
    assert isinstance(inner_pane, MatplotlibPane)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    model = row.children[0]
    assert model.ref['id'] in inner_pane._callbacks
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div = model.children[0].children[0]
    assert isinstance(div, Div)
    text = div.text

    # Update pane
    test.a = 5
    model = row.children[0]
    assert inner_pane is pane._pane
    assert div is row.children[0].children[0].children[0]
    assert div.text != text
    assert len(inner_pane._callbacks) == 1
    assert model.ref['id'] in inner_pane._callbacks

    # Cleanup pane
    pane._cleanup(model)
    assert inner_pane._callbacks == {}


@mpl_available
def test_param_method_pane_changing_type(document, comm):
    test = View()
    pane = Pane(test.mixed_view)
    inner_pane = pane._pane
    assert isinstance(inner_pane, MatplotlibPane)

    # Create pane
    row = pane._get_root(document, comm=comm)
    assert isinstance(row, BkRow)
    assert len(row.children) == 1
    model = row.children[0]
    assert model.ref['id'] in inner_pane._callbacks
    assert isinstance(model, BkRow)
    assert isinstance(model.children[0], BkWidgetBox)
    div = model.children[0].children[0]
    assert isinstance(div, Div)
    text = div.text

    # Update pane
    test.a = 5
    model = row.children[0]
    new_pane = pane._pane
    assert pane._callbacks == {}
    assert isinstance(new_pane, BokehPane)
    div = row.children[0]
    assert isinstance(div, Div)
    assert div.text != text
    assert len(new_pane._callbacks) == 1
    assert model.ref['id'] in new_pane._callbacks

    # Cleanup pane
    new_pane._cleanup(model)
    assert new_pane._callbacks == {}
