"""
Defines Button and button-like widgets which allow triggering events
or merely toggling between on-off states.
"""
from __future__ import absolute_import, division, unicode_literals

import param

from bokeh.models import Button as _BkButton, Toggle as _BkToggle

from .base import Widget


class _ButtonBase(Widget):

    button_type = param.ObjectSelector(default='default', objects=[
        'default', 'primary', 'success', 'warning', 'danger'])

    _rename = {'name': 'label'}


class Button(_ButtonBase):

    clicks = param.Integer(default=0)

    _widget_type = _BkButton

    def on_click(self, callback):
        self.param.watch(callback, 'clicks')


class Toggle(_ButtonBase):

    value = param.Boolean(default=False, doc="""
        Whether the button is currently toggled.""")

    _rename = {'value': 'active'}

    _widget_type = _BkToggle
