from bokeh.core.properties import (
    Any, Bool, Dict, Either, Instance, List, Null, Nullable, String
)
from bokeh.models import ColumnDataSource, HTMLBox


class Perspective(HTMLBox):

    aggregates = Either(Dict(String, Any), Null())

    column_pivots = Either(List(String), Null())

    columns = Either(List(String), Null)

    computed_columns = Either(List(String), Null())

    editable = Nullable(Bool())

    filters = Either(List(Any), Null())

    plugin = String()

    plugin_config = Either(Dict(String, Any), Null)

    row_pivots = Either(List(String), Null())

    selectable = Nullable(Bool())

    sort = Either(List(List(String)), Null())

    source = Instance(ColumnDataSource)

    theme = String()

    # pylint: disable=line-too-long
    __javascript__ = [
        "https://unpkg.com/@finos/perspective@0.5.2/dist/umd/perspective.js",
        "https://unpkg.com/@finos/perspective-viewer@0.5.2/dist/umd/perspective-viewer.js",
        "https://unpkg.com/@finos/perspective-viewer-datagrid@0.5.2/dist/umd/perspective-viewer-datagrid.js",
        "https://unpkg.com/@finos/perspective-viewer-hypergrid@0.5.2/dist/umd/perspective-viewer-hypergrid.js",
        "https://unpkg.com/@finos/perspective-viewer-d3fc@0.5.2/dist/umd/perspective-viewer-d3fc.js",
    ]

    __js_skip__ = {
        "perspective": __javascript__[0:1],
        "perspective-viewer": __javascript__[1:2],
        "perspective-viewer-datagrid": __javascript__[2:3],
        "perspective-viewer-hypergrid": __javascript__[3:4],
        "perspective-viewer-d3fc": __javascript__[4:5],
    }

    __js_require__ = {
        "paths": {
            "perspective": "https://unpkg.com/@finos/perspective@0.5.2/dist/umd/perspective",
            "perspective-viewer": "https://unpkg.com/@finos/perspective-viewer@0.5.2/dist/umd/perspective-viewer",
            "perspective-viewer-datagrid": "https://unpkg.com/@finos/perspective-viewer-datagrid@0.5.2/dist/umd/perspective-viewer-datagrid",
            "perspective-viewer-hypergrid": "https://unpkg.com/@finos/perspective-viewer-hypergrid@0.5.2/dist/umd/perspective-viewer-hypergrid",
            "perspective-viewer-d3fc": "https://unpkg.com/@finos/perspective-viewer-d3fc@0.5.2/dist/umd/perspective-viewer-d3fc",
        },
        "exports": {
            "perspective": "Perspective",
            "perspective-viewer": "PerspectiveViewer",
            "perspective-viewer-datagrid": "PerspectiveViewerDatagrid",
            "perspective-viewer-hypergrid": "PerspectiveViewerHypergrid",
            "perspective-viewer-d3fc": "PerspectiveViewerD3fc",
        },
    }

    __css__ = ["https://unpkg.com/@finos/perspective-viewer@0.5.2/dist/umd/all-themes.css"]
