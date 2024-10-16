from unittest.mock import patch

from panel import config
from panel.widgets import CodeEditor


def test_ace(document, comm):
    editor = CodeEditor(value="Hello, World", language="python")
    widget = editor.get_root(document, comm=comm)

    assert isinstance(widget, editor._widget_type)
    assert editor.value == "Hello, World"
    assert editor.language == "python"

    # Try changes
    editor._process_events({"value": "Hi there!"})
    assert editor.value == "Hi there!"


def test_ace_input(document, comm):
    editor = CodeEditor(value="", language="python")
    editor.value = "Hello World!"
    assert editor.value == "Hello World!"
    assert editor.value_input == "Hello World!"

    editor.value = ""
    assert editor.value == ""
    assert editor.value_input == ""

def test_code_editor_theme():
    assert CodeEditor(value="My theme is appropriate").theme == CodeEditor.param.theme.default

    with patch('panel.config._config.theme', new_callable=lambda: "default"):
        assert CodeEditor(value="My theme is appropriate").theme == CodeEditor.param.theme.default

    with patch('panel.config._config.theme', new_callable=lambda: "dark"):
        assert CodeEditor(value="My theme is appropriate").theme == CodeEditor.THEME_CONFIGURATION[config.theme]
