"""
Vanilla template
"""
import pathlib

import param

from ...config import config as pn_config
from ...theme import Design
from ...theme.native import Native
from ..vanilla import VanillaTemplate

REVEAL_THEMES = ['black', 'white', 'league', 'beige', 'night', 'solarized', 'simple']

REVEAL_CSS = f"{pn_config.npm_cdn}/reveal.js@4.5.0/dist/reveal.min.css"
REVEAL_THEME_CSS = {
    f'reveal-{theme}': f'{pn_config.npm_cdn}/reveal.js@4.5.0/dist/theme/{theme}.css'
    for theme in REVEAL_THEMES
}

class SlidesTemplate(VanillaTemplate):
    """
    SlidesTemplate is built on top of Vanilla web components.
    """

    design = param.ClassSelector(class_=Design, default=Native, constant=True,
                                 is_instance=False, instantiate=False, doc="""
        A Design applies a specific design system to a template.""")

    reveal_config = param.Dict(default={'embedded': True}, doc="""
        Configuration parameters for reveal.js""")

    reveal_theme = param.Selector(default=None, objects=REVEAL_THEMES)

    _css = [VanillaTemplate._css, pathlib.Path(__file__).parent / 'slides.css']

    _template = pathlib.Path(__file__).parent / 'slides.html'

    _resources = {
        'js': {
            'reveal': f"{pn_config.npm_cdn}/reveal.js@4.5.0/dist/reveal.min.js"
        },
        'css': dict(REVEAL_THEME_CSS, reveal=REVEAL_CSS)
    }

    def __init__(self, **params):
        super().__init__(**params)
        if 'reveal_theme' not in params:
            self.reveal_theme = 'black' if self._design.theme._name == 'dark' else 'white'
        self._update_render_vars()

    @param.depends('reveal_config', 'reveal_theme', watch=True)
    def _update_render_vars(self):
        self._resources['css'] = {
            'reveal': REVEAL_CSS, 'reveal-theme': REVEAL_THEME_CSS[f'reveal-{self.reveal_theme}']
        }
        self._render_variables['reveal_config'] = self.reveal_config
