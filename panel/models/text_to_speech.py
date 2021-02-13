"""The TextToSpeek Bokeh Model wraps the HTML5 SpeechSynthesis API

See https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice
"""
from bokeh.core.properties import (
    Any,
    Bool,
    Dict,
    Int,
    List,
    String,
)
from bokeh.models.widgets import Widget


class TextToSpeech(Widget):
    """The TextToSpeek Bokeh Model wraps the HTML5 SpeechSynthesis API

    See https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis
    """

    paused = Bool()
    pending = Bool()
    speaking = Bool()

    voices = List(Dict(String, Any))

    cancels = Int()
    pauses = Int()
    resumes = Int()
    speaks = Dict(String, Any)
