"""
Defines the Param pane which converts Parameterized classes into a
set of widgets.
"""
from __future__ import absolute_import

import os
import json
import types
import inspect
import itertools
from collections import OrderedDict, namedtuple

import param
from param.parameterized import classlist

from .pane import Pane, PaneBase
from .layout import WidgetBox, Row, Layout, Tabs
from .util import (
    default_label_formatter, is_parameterized, get_method_owner,
    full_groupby, push
)
from .widgets import (
    LiteralInput, Select, Checkbox, FloatSlider, IntSlider, RangeSlider,
    MultiSelect, StaticText, Button, Toggle, TextInput, DiscreteSlider,
    DatetimeInput
)


def ObjectSelector(pobj):
    """
    Determines param.ObjectSelector widget depending on whether all values
    are numeric.
    """
    options = list(pobj.objects.values()) if isinstance(pobj.objects, dict) else pobj.objects
    if options and all(param._is_number(o) for o in options):
        return DiscreteSlider
    else:
        return Select


class Param(PaneBase):
    """
    Param panes render a Parameterized class to a set of widgets which
    are linked to the parameter values on the class.
    """

    display_threshold = param.Number(default=0, precedence=-10, doc="""
        Parameters with precedence below this value are not displayed.""")

    default_precedence = param.Number(default=1e-8, precedence=-10, doc="""
        Precedence value to use for parameters with no declared
        precedence.  By default, zero predecence is available for
        forcing some parameters to the top of the list, and other
        values above the default_precedence values can be used to sort
        or group parameters arbitrarily.""")

    expand_by_default = param.Boolean(default=False, doc="""
        Whether parameterized subobjects are expanded or collapsed on
        instantiation.""")

    height = param.Integer(default=None, bounds=(0, None), doc="""
        Height of widgetbox the parameter widgets are displayed in.""")

    initializer = param.Callable(default=None, doc="""
        User-supplied function that will be called on initialization,
        usually to update the default Parameter values of the
        underlying parameterized object.""")

    label_formatter = param.Callable(default=default_label_formatter, allow_None=True,
        doc="Callable used to format the parameter names into widget labels.")

    parameters = param.List(default=None, doc="""
        If set this serves as a whitelist of parameters to display on the supplied
        Parameterized object.""")

    show_labels = param.Boolean(default=True, doc="""
        Whether to show labels for each .widget""")

    subobject_layout = param.Parameter(default=Row, doc="""
        Layout of subpanels.""")

    toggleable_subobjects = param.Boolean(default=True, doc="""
        Whether parameterized subobjects are expandable and
        collapseable. If False they may be either expanded or
        collapsed on instantation with the expand_by_default
        parameter.""")

    width = param.Integer(default=300, bounds=(0, None), doc="""
        Width of widgetbox the parameter widgets are displayed in.""")

    precedence = 0.1

    _mapping = {
        param.Action:         Button,
        param.Parameter:      LiteralInput,
        param.Dict:           LiteralInput,
        param.Selector:       Select,
        param.ObjectSelector: ObjectSelector,
        param.Boolean:        Checkbox,
        param.Number:         FloatSlider,
        param.Integer:        IntSlider,
        param.Range:          RangeSlider,
        param.String:         TextInput,
        param.ListSelector:   MultiSelect,
        param.Date:           DatetimeInput,
    }

    def __init__(self, object, **params):
        if isinstance(object, param.parameterized.Parameters):
            object = object.cls if object.self is None else object.self
        if 'name' not in params:
            params['name'] = object.name
        if 'parameters' not in params:
            params['parameters'] = [p for p in object.params() if p != 'name']
        super(Param, self).__init__(object, **params)

        # Construct widgets
        self._widgets = self._get_widgets()
        widgets = [widget for widgets in self._widgets.values() for widget in widgets]
        self._widget_box = WidgetBox(*widgets, height=self.height,
                                     width=self.width, name=self.name)

        # Construct Layout
        kwargs = {'name': self.name}
        if self.subobject_layout is Tabs:
            kwargs['width'] = self.width

        layout = self.subobject_layout
        if isinstance(layout, Layout):
            self._subobject_layout = layout
            self._layout = self._widget_box
        elif isinstance(layout, type) and issubclass(layout, Layout):
            self._layout = layout(self._widget_box, **kwargs)
            self._subobject_layout = self._layout
        else:
            raise ValueError('subobject_layout expected to be a panel.layout.Layout'
                             'type or instance, found %s type.' %
                             type(layout).__name__)

        if not (not self.toggleable_subobjects and not self.expand_by_default):
            self._link_subobjects()

    def _link_subobjects(self):
        for pname, widgets in self._widgets.items():
            if not any(is_parameterized(getattr(w, 'value', None)) or
                       any(is_parameterized(o) for o in getattr(w, 'options', []))
                       for w in widgets):
                continue
            selector, toggle = widgets if len(widgets) == 2 else (widgets[0], None)

            def toggle_pane(change, parameter=pname):
                "Adds or removes subpanel from layout"
                parameterized = getattr(self.object, parameter)
                existing = [p for p in self._subobject_layout.objects
                            if isinstance(p, Param)
                            and p.object is parameterized]
                if existing:
                    old_panel = existing[0]
                    if not change.new:
                        old_panel._cleanup(final=old_panel._temporary)
                        self._subobject_layout.pop(old_panel)
                elif change.new:
                    kwargs = {k: v for k, v in self.get_param_values()
                              if k not in ['name', 'object', 'parameters']}
                    pane = Param(parameterized, name=parameterized.name,
                                 _temporary=True, **kwargs)
                    self._subobject_layout.append(pane)

            def update_pane(change, parameter=pname):
                "Adds or removes subpanel from layout"
                layout = self._subobject_layout
                existing = [p for p in layout.objects if isinstance(p, Param)
                            and p.object is change.old]

                if toggle:
                    toggle.disabled = not is_parameterized(change.new)
                if not existing:
                    return
                elif is_parameterized(change.new):
                    parameterized = change.new
                    kwargs = {k: v for k, v in self.get_param_values()
                              if k not in ['name', 'object', 'parameters']}
                    pane = Param(parameterized, name=parameterized.name,
                                 _temporary=True, **kwargs)
                    layout[layout.objects.index(existing[0])] = pane
                else:
                    layout.pop(existing[0])

            watchers = [selector.param.watch(update_pane, 'value')]
            if toggle:
                watchers.append(toggle.param.watch(toggle_pane, 'active'))
            self._callbacks['instance'] += watchers

            if self.expand_by_default:
                if self.toggleable_subobjects:
                    toggle.active = True
                else:
                    toggle_pane(namedtuple('Change', 'new')(True))

    @classmethod
    def applies(cls, obj):
        return (is_parameterized(obj) or isinstance(obj, param.parameterized.Parameters))

    def widget_type(cls, pobj):
        ptype = type(pobj)
        for t in classlist(ptype)[::-1]:
            if t in cls._mapping:
                if isinstance(cls._mapping[t], types.FunctionType):
                    return cls._mapping[t](pobj)
                return cls._mapping[t]

    def widget(self, p_name):
        """Get widget for param_name"""
        p_obj = self.object.params(p_name)

        widget_class = self.widget_type(p_obj)
        value = getattr(self.object, p_name)

        kw = dict(value=value, disabled=p_obj.constant)

        if self.label_formatter is not None:
            kw['name'] = self.label_formatter(p_name)
        else:
            kw['name'] = p_name

        if hasattr(p_obj, 'get_range'):
            options = p_obj.get_range()
            if not options and value is not None:
                options = [value]
            kw['options'] = options

        if hasattr(p_obj, 'get_soft_bounds'):
            bounds = p_obj.get_soft_bounds()
            if bounds[0] is not None:
                kw['start'] = bounds[0]
            if bounds[1] is not None:
                kw['end'] = bounds[1]
            if ('start' not in kw or 'end' not in kw) and not issubclass(widget_class, LiteralInput):
                widget_class = LiteralInput

        kwargs = {k: v for k, v in kw.items() if k in widget_class.params()}
        widget = widget_class(**kwargs)
        watchers = self._callbacks['instance']
        if isinstance(p_obj, param.Action):
            widget.button_type = 'success'
            def action(change):
                value(self.object)
            watchers.append(widget.param.watch(action, 'clicks'))
        elif isinstance(widget, Toggle):
            pass
        else:
            widget.link(self.object, **{'value': p_name})
            def link(change, _updating=[]):
                key = (change.name, change.what)
                if key in _updating:
                    return

                _updating.append(key)
                updates = {}
                if change.what == 'constant':
                    updates['disabled'] = change.new
                elif change.what == 'precedence':
                    if change.new < 0 and widget in self._widget_box.objects:
                        self._widget_box.pop(widget)
                    elif change.new >= 0 and widget not in self._widget_box.objects:
                        precedence = lambda k: self.object.params(k).precedence
                        widgets = []
                        for k, ws in self._widgets.items():
                            if precedence(k) is None or precedence(k) >= self.display_threshold:
                                widgets += ws
                        self._widget_box.objects = widgets
                elif change.what == 'objects':
                    updates['options'] = p_obj.get_range()
                elif change.what == 'bounds':
                    start, end = p_obj.get_soft_bounds()
                    updates['start'] = start
                    updates['end'] = end
                else:
                    updates['value'] = change.new
                try:
                    widget.set_param(**updates)
                except Exception as e:
                    raise e
                finally:
                    _updating.pop(_updating.index(key))

            # Set up links to parameterized object
            watchers.append(self.object.param.watch(link, p_name, 'constant'))
            watchers.append(self.object.param.watch(link, p_name, 'precedence'))
            watchers.append(self.object.param.watch(link, p_name))
            if hasattr(p_obj, 'get_range'):
                watchers.append(self.object.param.watch(link, p_name, 'objects'))
            if hasattr(p_obj, 'get_soft_bounds'):
                watchers.append(self.object.param.watch(link, p_name, 'bounds'))

        options = kwargs.get('options', [])
        if isinstance(options, dict):
            options = options.values()
        if ((is_parameterized(value) or any(is_parameterized(o) for o in options))
            and self.toggleable_subobjects):
            toggle = Toggle(name='...', button_type='primary',
                            disabled=not is_parameterized(value))
            return [widget, toggle]
        else:
            return [widget]

    def _cleanup(self, model=None, final=False):
        self._layout._cleanup(model, final)
        super(Param, self)._cleanup(model, final)

    def _get_widgets(self):
        """Return name,widget boxes for all parameters (i.e., a property sheet)"""
        params = [(p, pobj) for p, pobj in self.object.params().items()
                  if p in self.parameters or p == 'name']
        key_fn = lambda x: x[1].precedence if x[1].precedence is not None else self.default_precedence
        sorted_precedence = sorted(params, key=key_fn)
        filtered = [(k,p) for (k,p) in sorted_precedence
                    if ((p.precedence is None) or (p.precedence >= self.display_threshold))]
        groups = itertools.groupby(filtered, key=key_fn)
        sorted_groups = [sorted(grp) for (k,grp) in groups]
        ordered_params = [el[0] for group in sorted_groups for el in group]

        # Format name specially
        ordered_params.pop(ordered_params.index('name'))
        if self.subobject_layout is Tabs:
            widgets = []
        else:
            widgets = [('name', [StaticText(value='<b>{0}</b>'.format(self.object.name))])]
        widgets += [(pname, self.widget(pname)) for pname in ordered_params]
        return OrderedDict(widgets)

    def _get_model(self, doc, root=None, parent=None, comm=None):
        return self._layout._get_model(doc, root, parent, comm)

    def _get_root(self, doc, comm=None):
        root = self._get_model(doc, comm=comm)
        self._preprocess(root)
        return root


class ParamMethod(PaneBase):
    """
    ParamMethod panes wrap methods on parameterized classes and
    rerenders the plot when any of the method's parameters change. By
    default ParamMethod will watch all parameters on the class owning
    the method or can be restricted to certain parameters by annotating
    the method using the param.depends decorator. The method may
    return any object which itself can be rendered as a Pane.
    """

    def __init__(self, object, **params):
        self._kwargs =  {p: params.pop(p) for p in list(params)
                         if p not in self.params()}
        super(ParamMethod, self).__init__(object, **params)
        self._pane = Pane(self.object(), name=self.name,
                          **dict(_temporary=True, **self._kwargs))

    @classmethod
    def applies(cls, obj):
        return inspect.ismethod(obj) and isinstance(get_method_owner(obj), param.Parameterized)

    def _get_model(self, doc, root=None, parent=None, comm=None):
        parameterized = get_method_owner(self.object)
        params = parameterized.param.params_depended_on(self.object.__name__)
        model = self._pane._get_model(doc, root, parent, comm)
        history = [model]
        deps = params

        def update_pane(*events):
            error = None
            old_model = history[0]
            old_ref = old_model.ref['id']

            # Update nested dependencies if parameterized object events
            if any(is_parameterized(event.new) for event in events):
                new_deps = parameterized.param.params_depended_on(self.object.__name__)
                for p in list(deps):
                    if p in new_deps: continue
                    watchers = self._callbacks.get(old_ref, [])
                    for w in list(watchers):
                        if (w.inst is p.inst and w.cls is p.cls and
                            p.name in w.parameter_names):
                            obj = p.cls if p.inst is None else p.inst
                            obj.param.unwatch(w)
                            watchers.pop(watchers.index(w))
                    deps.pop(deps.index(p))

                new_deps = [dep for dep in new_deps if dep not in deps]
                for _, params in full_groupby(new_deps, lambda x: (x.inst or x.cls, x.what)):
                    p = params[0]
                    pobj = p.cls if p.inst is None else p.inst
                    ps = [p.name for p in params]
                    watcher = pobj.param.watch(update_pane, ps, p.what)
                    self._callbacks[old_ref].append(watcher)
                    for p in params:
                        deps.append(p)

            # Try updating existing pane
            new_object = self.object()
            pane_type = self.get_pane_type(new_object)
            if type(self._pane) is pane_type:
                index = parent.children.index(old_model)
                if isinstance(new_object, PaneBase):
                    new_params = {k: v for k, v in new_object.get_param_values()
                                  if k != 'name'}
                    try:
                        self._pane.set_param(**new_params)
                    except Exception as e:
                        error = e
                    new_object._cleanup(None, new_object._temporary)
                else:
                    try:
                        self._pane.object = new_object
                    except Exception as e:
                        error = e

                # If model has changed update history and remap callbacks
                def update_state():
                    if old_model is parent.children[index]:
                        if error is not None:
                            raise error
                        return
                    new_model = parent.children[index]
                    history[0] = new_model
                    new_ref = new_model.ref['id']
                    old_callbacks = self._callbacks.pop(old_ref, [])
                    if old_callbacks:
                        self._callbacks[new_ref] = old_callbacks
                    if error is not None:
                        raise error

                if comm:
                    update_state()
                else:
                    doc.add_next_tick_callback(update_state)
                return

            # Replace pane entirely
            self._pane._cleanup(old_model, self._pane._temporary)
            self._pane = Pane(new_object, _temporary=True, **self._kwargs)
            new_model = self._pane._get_model(doc, root, parent, comm)
            new_ref = new_model.ref['id']
            def update_models():
                if old_model is new_model: return
                index = parent.children.index(old_model)
                parent.children[index] = new_model
                history[0] = new_model
                old_callbacks = self._callbacks.pop(old_ref, [])
                self._callbacks[new_ref] = old_callbacks

            if comm:
                update_models()
                push(doc, comm)
            else:
                doc.add_next_tick_callback(update_models)

        ref = model.ref['id']
        for _, params in full_groupby(params, lambda x: (x.inst or x.cls, x.what)):
            p = params[0]
            pobj = (p.inst or p.cls)
            ps = [p.name for p in params]
            watcher = pobj.param.watch(update_pane, ps, p.what)
            self._callbacks[ref].append(watcher)

        return model

    def _cleanup(self, model=None, final=False):
        self._pane._cleanup(model, final)
        super(ParamMethod, self)._cleanup(model, final)


class JSONInit(param.Parameterized):
    """
    Callable that can be passed to Widgets.initializer to set Parameter
    values using JSON. There are three approaches that may be used:
    1. If the json_file argument is specified, this takes precedence.
    2. The JSON file path can be specified via an environment variable.
    3. The JSON can be read directly from an environment variable.
    Here is an easy example of setting such an environment variable on
    the commandline:
    PARAM_JSON_INIT='{"p1":5}' jupyter notebook
    This addresses any JSONInit instances that are inspecting the
    default environment variable called PARAM_JSON_INIT, instructing it to set
    the 'p1' parameter to 5.
    """

    varname = param.String(default='PARAM_JSON_INIT', doc="""
        The name of the environment variable containing the JSON
        specification.""")

    target = param.String(default=None, doc="""
        Optional key in the JSON specification dictionary containing the
        desired parameter values.""")

    json_file = param.String(default=None, doc="""
        Optional path to a JSON file containing the parameter settings.""")

    def __call__(self, parameterized):
        warnobj = param.main if isinstance(parameterized, type) else parameterized
        param_class = (parameterized if isinstance(parameterized, type)
                       else parameterized.__class__)

        target = self.target if self.target is not None else param_class.__name__

        env_var = os.environ.get(self.varname, None)
        if env_var is None and self.json_file is None: return

        if self.json_file or env_var.endswith('.json'):
            try:
                fname = self.json_file if self.json_file else env_var
                spec = json.load(open(os.path.abspath(fname), 'r'))
            except:
                warnobj.warning('Could not load JSON file %r' % spec)
        else:
            spec = json.loads(env_var)

        if not isinstance(spec, dict):
            warnobj.warning('JSON parameter specification must be a dictionary.')
            return

        if target in spec:
            params = spec[target]
        else:
            params = spec

        for name, value in params.items():
           try:
               parameterized.set_param(**{name:value})
           except ValueError as e:
               warnobj.warning(str(e))
