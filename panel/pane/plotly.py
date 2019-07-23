"""
Defines a PlotlyPane which renders a plotly plot using PlotlyPlot
bokeh model.
"""
from __future__ import absolute_import, division, unicode_literals

import sys

import numpy as np

from bokeh.models import ColumnDataSource
from pyviz_comms import JupyterComm
import param

from .base import PaneBase


class Plotly(PaneBase):
    """
    Plotly panes allow rendering plotly Figures and traces.

    For efficiency any array objects found inside a Figure are added
    to a ColumnDataSource which allows using binary transport to sync
    the figure on bokeh server and via Comms.
    """

    config = param.Dict(doc="""config data""")
    relayout_data = param.Dict(doc="""relayout callback data""")
    restyle_data = param.List(doc="""restyle callback data""")
    click_data = param.Dict(doc="""click callback data""")
    hover_data = param.Dict(doc="""hover callback data""")
    clickannotation_data = param.Dict(doc="""clickannotation callback data""")
    selected_data = param.Dict(doc="""selected callback data""")

    _updates = True

    priority = 0.8

    @classmethod
    def applies(cls, obj):
        return ((isinstance(obj, list) and obj and all(cls.applies(o) for o in obj)) or
                hasattr(obj, 'to_plotly_json') or (isinstance(obj, dict)
                                                   and 'data' in obj and 'layout' in obj))

    def __init__(self, object=None, **params):
        super(Plotly, self).__init__(object, **params)
        self._figure = None
        self._update_figure()

    def _to_figure(self, obj):
        import plotly.graph_objs as go
        if isinstance(obj, go.Figure):
            return obj
        elif isinstance(obj, dict):
            data, layout = obj['data'], obj['layout']
        elif isinstance(obj, tuple):
            data, layout = obj
        else:
            data, layout = obj, {}
        data = data if isinstance(data, list) else [data]
        return go.Figure(data=data, layout=layout)

    @staticmethod
    def _get_sources(json):
        sources = []
        traces = json.get('data', [])
        for trace in traces:
            data = {}
            Plotly._get_sources_for_trace(trace, data)
            sources.append(ColumnDataSource(data))
        return sources

    @staticmethod
    def _get_sources_for_trace(json, data, parent_path=''):
        for key, value in list(json.items()):
            full_path = key if not parent_path else (parent_path + '.' + key)
            if isinstance(value, np.ndarray):
                # Extract numpy array
                data[full_path] = [json.pop(key)]
            elif isinstance(value, dict):
                # Recurse into dictionaries:
                Plotly._get_sources_for_trace(value, data=data, parent_path=full_path)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # recurse into object arrays:
                for i, element in enumerate(value):
                    element_path = full_path + '.' + str(i)
                    Plotly._get_sources_for_trace(
                        element, data=data, parent_path=element_path
                    )

    @param.depends('object', watch=True)
    def _update_figure(self):
        import plotly.graph_objs as go

        if (self.object is None or
                type(self.object) is not go.Figure or
                self.object is self._figure):
            return

        # Monkey patch the message stubs used by FigureWidget.
        # We only patch `Figure` objects (not subclasses like FigureWidget) so
        # we don't interfere with subclasses that override these methods.
        fig = self.object
        fig._send_addTraces_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_moveTraces_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_deleteTraces_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_restyle_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_relayout_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_update_msg = lambda *_, **__: self.param.trigger('object')
        fig._send_animate_msg = lambda *_, **__: self.param.trigger('object')
        self._figure = fig

    def _update_data_sources(self, cds, trace):
        trace_arrays = {}
        Plotly._get_sources_for_trace(trace, trace_arrays)

        for key, new_col in trace_arrays.items():
            new = new_col[0]

            try:
                old = cds.data.get(key)[0]
                update_array = (
                    (type(old) != type(new)) or
                    (new.shape != old.shape) or
                    (new != old).any())
            except:
                update_array = True

            if update_array:
                cds.data[key] = [new]

    def _get_model(self, doc, root=None, parent=None, comm=None):
        """
        Should return the bokeh model to be rendered.
        """
        if 'panel.models.plotly' not in sys.modules:
            if isinstance(comm, JupyterComm):
                self.param.warning('PlotlyPlot was not imported on instantiation '
                                   'and may not render in a notebook. Restart '
                                   'the notebook kernel and ensure you load '
                                   'it as part of the extension using:'
                                   '\n\npn.extension(\'plotly\')\n')
            from ..models.plotly import PlotlyPlot
        else:
            PlotlyPlot = getattr(sys.modules['panel.models.plotly'], 'PlotlyPlot')

        if self.object is None:
            json, sources = {}, []
        else:
            fig = self._to_figure(self.object)
            json = fig.to_plotly_json()
            sources = Plotly._get_sources(json)
        model = PlotlyPlot(data=json.get('data', []),
                           layout=json.get('layout', {}),
                           config=self.config,
                           data_sources=sources)

        if root is None:
            root = model

        self._link_props(
            model, [
                'config', 'relayout_data', 'restyle_data', 'click_data',  'hover_data',
                'clickannotation_data', 'selected_data'
            ],
            doc,
            root,
            comm
        )

        if root is None:
            root = model
        self._models[root.ref['id']] = (model, parent)
        return model

    def _update(self, model):
        if self.object is None:
            model.update(data=[], layout={})
            return

        fig = self._to_figure(self.object)
        json = fig.to_plotly_json()

        traces = json['data']
        new_sources = []
        for i, trace in enumerate(traces):
            if i < len(model.data_sources):
                cds = model.data_sources[i]
            else:
                cds = ColumnDataSource()
                new_sources.append(cds)

            self._update_data_sources(cds, trace)

        try:
            update_layout = model.layout != json.get('layout')
        except:
            update_layout = True

        # Determine if model needs updates
        if (len(model.data) != len(traces)):
            update_data = True
        else:
            update_data = False
            for new, old in zip(traces, model.data):
                try:
                    update_data = (
                        {k: v for k, v in new.items() if k != 'uid'} !=
                        {k: v for k, v in old.items() if k != 'uid'})
                except:
                    update_data = True
                if update_data:
                    break

        if new_sources:
            model.data_sources += new_sources

        if update_data:
            model.data = json.get('data')

        if update_layout:
            model.layout = json.get('layout')
