"""
Defines the Location  widget which allows changing the href of the window.
"""
import param

from panel.models.location import Location as _BkLocation

from .base import Widget
import param

from typing import Optional, List, Dict, Optional

import param
from panel.widgets.base import Widget


class Location(Widget):
    href = param.String(
        readonly=True,
        doc="""The full url, e.g. \
            'https://panel.holoviz.org/user_guide/Interact.html:80?color=blue#interact'""",
    )
    hostname = param.String(
        readonly=True, doc="hostname in window.location e.g. 'panel.holoviz.org'"
    )
    # Todo: Find the corect regex for pathname
    pathname = param.String(
        regex=r"^$|[^\/].*[^\/]$",
        doc="pathname in window.location e.g. 'user_guide/Interact.html'",
    )
    protocol = param.String(readonly=True, doc="protocol in window.location e.g. 'https:'")
    port = param.String(readonly=True, doc="port in window.location e.g. '80'")
    search = param.String(regex=r"^$|\?", doc="search in window.location e.g. '?color=blue'")
    hash_ = param.String(regex=r"^$|#", doc="hash in window.location e.g. '#interact'")

    refresh = param.Boolean(
        default=False,
        doc="""Refresh the page when the location is updated. For multipage apps this should be \
        set to True, For single page apps this should be set to False""",
    )

    _widget_type = _BkLocation  # type: ignore

    # Mapping from parameter name to bokeh model property name
    _rename: Dict[str, Optional[str]] = {"name": None}

    def update_search(
        self, param_class: param.Parameterized, parameters: Optional[List[str]] = None
    ):
        """Updates the search string from the specified parameters

        Parameters
        ----------
        param_class : param.Parameterized
            The Parameterized Class containing the Parameters
        parameters : [type], optional
            The parameters to provide in the search string. If None is provided then all, by default None
        """
        raise NotImplementedError()

    def update_param_class(self, parameters=None):
        """Updates the Parameterized Class from the parameters

        Parameters
        ----------
        param_class : param.Parameterized
            The Parameterized Class containing the Parameters
        parameters : [type], optional
            [description], by default None
        """
        raise NotImplementedError()

