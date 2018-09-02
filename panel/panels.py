"""
Panels allow wrapping external objects and rendering them as part of
a dashboard.
"""
from __future__ import absolute_import

import inspect
import base64
from io import BytesIO

import param

from bokeh.layouts import Column as _BkColumn
from bokeh.models import LayoutDOM, CustomJS, Div as _BkDiv

from .util import get_method_owner, push, Div
from .viewable import Reactive, Viewable


def Panel(obj, **kwargs):
    """
    Converts any object to a Panel if a matching Panel class exists.
    """
    if isinstance(obj, Viewable):
        return obj
    return PanelBase.get_panel_type(obj)(obj, **kwargs)



class PanelBase(Reactive):
    """
    PanelBase is the abstract baseclass for all atomic displayable units
    in the panel library. Panel defines an extensible interface for
    wrapping arbitrary objects and transforming them into bokeh models.
    allowing the panel to display itself in the notebook or be served
    using bokeh server.

    Panels are reactive in the sense that when the object they are
    wrapping is changed any dashboard containing the panel will update
    in response.

    To define a concrete Panel type subclass this class and implement
    the applies classmethod and the _get_model private method.
    """

    object = param.Parameter(default=None, doc="""
        The object being wrapped, which will be converted into a bokeh model.""")

    # When multiple Panels apply to an object the precedence is used
    precedence = 0

    # Declares whether Panel supports updates to the bokeh model
    _updates = False

    __abstract = True

    @classmethod
    def applies(cls, obj):
        """
        Given the object return a boolean indicating whether the Panel
        can render the object.
        """
        return None

    @classmethod
    def get_panel_type(cls, obj):
        if isinstance(obj, Viewable):
            return type(obj)
        descendents = [(p.precedence, p) for p in param.concrete_descendents(PanelBase).values()]
        panel_types = sorted(descendents, key=lambda x: x[0])
        for _, panel_type in panel_types:
            if not panel_type.applies(obj): continue
            return panel_type
        raise TypeError('%s type could not be rendered.' % type(obj).__name__)

    def __init__(self, object, **params):
        if not self.applies(object):
            name = type(self).__name__
            raise ValueError('%s object not understood by %s, '
                             'expected %s object.' %
                             (type(object).__name__, name, name[:-5]))

        # temporary flag denotes panels created for temporary, internal
        # use which should be garbage collected once they have been used
        self._temporary = params.pop('_temporary', False)

        super(PanelBase, self).__init__(object=object, **params)

    def _get_root(self, doc, comm=None):
        root = _BkColumn()
        model = self._get_model(doc, root, root, comm)
        root.children = [model]
        return root

    def _cleanup(self, model, final=False):
        super(PanelBase, self)._cleanup(model, final)
        if self._temporary or final:
            self.object = None

    def _update(self, model):
        """
        If _updates=True this method is used to update an existing bokeh
        model instead of replacing the model entirely. The supplied model
        should be updated with the current state.
        """
        raise NotImplementedError

    def _link_object(self, model, doc, root, parent, comm=None, panel=None):
        """
        Links the object parameter to the rendered bokeh model, triggering
        an update when the object changes.
        """
        def update_panel(change, history=[(panel, model)]):
            old_panel, old_model = history[0]

            # Panel supports model updates
            if self._updates:
                def update_models():
                    self._update(old_model)
                if comm:
                    update_models()
                    push(doc, comm)
                else:
                    doc.add_next_tick_callback(update_models)
                return

            # Otherwise replace the whole model
            new_model, new_panel = self._get_model(doc, root, parent, comm, rerender=True)
            if old_model is new_model:
                return
            elif old_panel is not None:
                old_panel._cleanup(old_model, final=True)

            def update_models():
                index = parent.children.index(old_model)
                parent.children[index] = new_model
                history[:] = [(new_panel, new_model)]
            if comm:
                update_models()
                push(doc, comm)
            else:
                doc.add_next_tick_callback(update_models)
        self.param.watch(update_panel, 'object')
        self._callbacks[model.ref['id']]['object'] = update_panel


class BokehPanel(PanelBase):
    """
    BokehPanel allows including any bokeh model in a plot directly.
    """

    @classmethod
    def applies(cls, obj):
        return isinstance(obj, LayoutDOM)

    def _get_model(self, doc, root, parent=None, comm=None, rerender=False):
        """
        Should return the bokeh model to be rendered.
        """
        model = self.object
        plot_id = root.ref['id']
        if plot_id:
            for js in model.select({'type': CustomJS}):
                js.code = js.code.replace(self.object.ref['id'], plot_id)

        if rerender:
            return model, None

        self._link_object(model, doc, root, parent, comm)
        return model


class HoloViewsPanel(PanelBase):
    """
    HoloViewsPanel renders any HoloViews object to a corresponding
    bokeh model while respecting the currently selected backend.
    """

    @classmethod
    def applies(cls, obj):
        return hasattr(obj, 'kdims') and hasattr(obj, 'vdims')

    def _patch_plot(self, plot, plot_id, comm):
        if not hasattr(plot, '_update_callbacks'):
            return

        for subplot in plot.traverse(lambda x: x):
            subplot.comm = comm
            for cb in getattr(subplot, 'callbacks', []):
                for c in cb.callbacks:
                    c.code = c.code.replace(plot.id, plot_id)

    def _cleanup(self, model):
        """
        Traverses HoloViews object to find and clean up any streams
        connected to existing plots.
        """
        from holoviews.core.spaces import DynamicMap, get_nested_streams
        dmaps = self.object.traverse(lambda x: x, [DynamicMap])
        for dmap in dmaps:
            for stream in get_nested_streams(dmap):
                for _, sub in stream._subscribers:
                    if inspect.ismethod(sub):
                        owner = get_method_owner(sub)
                        if owner.state is model:
                            owner.cleanup()
        super(HoloViewsPanel, self)._cleanup(model)

    def _get_model(self, doc, root, parent=None, comm=None, rerender=False):
        """
        Should return the bokeh model to be rendered.
        """
        from holoviews import Store
        renderer = Store.renderers[Store.current_backend]
        renderer = renderer.instance(mode='server' if comm is None else 'default')
        kwargs = {'doc': doc} if renderer.backend == 'bokeh' else {}
        plot = renderer.get_plot(self.object, **kwargs)
        self._patch_plot(plot, root.ref['id'], comm)
        child_panel = Panel(plot.state, _temporary=True)
        model = child_panel._get_model(doc, root, parent, comm)
        if rerender:
            return model, child_panel
        self._link_object(model, doc, root, parent, comm, child_panel)
        return model


class ParamMethodPanel(PanelBase):
    """
    ParamMethodPanel wraps methods annotated with the param.depends
    decorator and rerenders the plot when any of the methods parameters
    change. The method may return any object which itself can be rendered
    as a Panel.
    """

    @classmethod
    def applies(cls, obj):
        return inspect.ismethod(obj) and isinstance(get_method_owner(obj), param.Parameterized)

    def _get_model(self, doc, root=None, parent=None, comm=None):
        parameterized = get_method_owner(self.object)
        params = parameterized.param.params_depended_on(self.object.__name__)
        panel = Panel(self.object(), _temporary=True)
        model = panel._get_model(doc, root, parent, comm)
        history = [(panel, model)]
        for p in params:
            def update_panel(change, history=history):
                if change.what != 'value': return

                # Try updating existing panel
                old_panel, old_model = history[0]
                new_object = self.object()
                panel_type = self.get_panel_type(new_object)
                if type(old_panel) is panel_type and panel_type._updates:
                    if isinstance(new_object, PanelBase):
                        new_params = {k: v for k, v in new_object.get_param_values()
                                      if k != 'name'}
                        old_panel.set_param(**new_params)
                        new_object._cleanup(None, final=True)
                    else:
                        old_panel.object = new_object
                    return

                # Replace panel entirely
                old_panel._cleanup(old_model)
                new_panel = Panel(new_object, _temporary=True)
                new_model = new_panel._get_model(doc, root, parent, comm)
                def update_models():
                    if old_model is new_model: return
                    index = parent.children.index(old_model)
                    parent.children[index] = new_model
                    history[:] = [(new_panel, new_model)]
                if comm:
                    update_models()
                    push(doc, comm)
                else:
                    doc.add_next_tick_callback(update_models)

            parameterized.param.watch(update_panel, p.name, p.what)
        return model

    def _cleanup(self, model):
        """
        Clean up method which is called when a Viewable is destroyed.
        """
        model_id = model.ref['id']
        callbacks = self._callbacks[model_id]
        parameterized = get_method_owner(self.object)
        for p, cb in callbacks.items():
            parameterized.param.unwatch(cb, p)
        super(ParamMethodPanel, self)._cleanup(model)


class DivBasePanel(PanelBase):
    """
    Baseclass for Panels which render HTML inside a Bokeh Div.
    See the documentation for Bokeh Div for more detail about
    the supported options like style and sizing_mode.
    """

    # DivPanel supports updates to the model
    _updates = True

    __abstract = True

    height = param.Integer(default=None, bounds=(0, None))

    width = param.Integer(default=None, bounds=(0, None))

    sizing_mode = param.ObjectSelector(default=None, allow_None=True,
        objects=["fixed", "scale_width", "scale_height", "scale_both", "stretch_both"], 
        doc="How the item being displayed should size itself.")
                                       
    style = param.Dict(default=None, doc="""
        Dictionary of CSS property:value pairs to apply to this Div.""")

    def _get_properties(self):
        return {p : getattr(self,p) for p in ["width", "height", "sizing_mode", "style"]
                if getattr(self,p) is not None}

    def _get_model(self, doc, root=None, parent=None, comm=None, rerender=False):
        model = Div(**self._get_properties())
        if rerender:
            return model, None
        self._link_object(model, doc, root, parent, comm)
        return model

    def _update(self, model):
        div = model if isinstance(model, _BkDiv) else model.children[0].children[0]
        div.update(**self._get_properties())


class PNGPanel(DivBasePanel):
    """
    Encodes a PNG as base64 and wraps it in a Bokeh Div model.
    This base class supports anything with a _repr_png_ method, but
    subclasses can provide their own way of obtaining or generating a PNG.
    """

    @classmethod
    def applies(cls, obj):
        return hasattr(obj, '_repr_png_')

    def _png(self):
        return self.object._repr_png_()
    
    def _pngshape(self, data):
        """Calculate and return PNG width,height"""
        import struct
        w, h = struct.unpack('>LL', data[16:24])
        return int(w), int(h)
    
    def _get_properties(self):
        data = self._png()
        b64 = base64.b64encode(data).decode("utf-8")
        src = "data:image/png;base64,{b64}".format(b64=b64)
        html = "<img src='{src}'></img>".format(src=src)
        
        p = super(PNGPanel,self)._get_properties()
        width, height = self._pngshape(data)
        if self.width  is None: p["width"]  = width
        if self.height is None: p["height"] = height
        p["text"]=html
        return p


class MatplotlibPanel(PNGPanel):
    """
    A MatplotlibPanel renders a matplotlib figure to png and wraps
    the base64 encoded data in a bokeh Div model.
    """

    @classmethod
    def applies(cls, obj):
        return type(obj).__name__ == 'Figure' and hasattr(obj, '_cachedRenderer')

    def _png(self):
        b = BytesIO()
        self.object.canvas.print_figure(b)
        return b.getvalue()



class HTMLPanel(DivBasePanel):
    """
    HTMLPanel renders any object which has a _repr_html_ method and wraps
    the HTML in a bokeh Div model. The height and width can optionally
    be specified, to allow room for whatever is being wrapped.
    """

    precedence = 1

    @classmethod
    def applies(cls, obj):
        return hasattr(obj, '_repr_html_')

    def _get_properties(self):
        return dict(text=self.object._repr_html_(),
                    **super(HTMLPanel,self)._get_properties())


class RGGPlotPanel(PNGPanel):
    """
    An RGGPlotPanel renders an r2py-based ggplot2 figure to png
    and wraps the base64-encoded data in a bokeh Div model.
    """

    height = param.Integer(default=400)

    width = param.Integer(default=400)

    dpi = param.Integer(default=144, bounds=(1, None))

    @classmethod
    def applies(cls, obj):
        return type(obj).__name__ == 'GGPlot' and hasattr(obj, 'r_repr')

    def _png(self):
        from rpy2.robjects.lib import grdevices
        from rpy2 import robjects
        with grdevices.render_to_bytesio(grdevices.png,
                 type="cairo-png", width=self.width, height=self.height,
                 res=self.dpi, antialias="subpixel") as b:
            robjects.r("print")(self.object)
        return b.getvalue()
