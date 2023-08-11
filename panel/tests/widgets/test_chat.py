import asyncio
import datetime
import time

from unittest.mock import MagicMock

import pytest

from panel.layout import Row, Tabs
from panel.pane.image import Image
from panel.pane.markup import HTML, Markdown
from panel.widgets.button import Button
from panel.widgets.chat import (
    ChatEntry, ChatFeed, ChatInterface, ChatReactionIcons, _FileInputMessage,
)
from panel.widgets.input import FileInput, TextAreaInput, TextInput


class TestChatEntry:
    def test_layout(self):
        entry = ChatEntry(value="ABC")
        columns = entry._composite.objects
        assert len(columns) == 2

        avatar_pane = columns[0][0].object()
        assert isinstance(avatar_pane, HTML)
        assert avatar_pane.object == "U"

        user_pane = columns[1][0].object()
        assert isinstance(user_pane, HTML)
        assert user_pane.object == "User"

        center_row = columns[1][1]
        assert isinstance(center_row, Row)

        value_pane = center_row[0].object()
        assert isinstance(value_pane, Markdown)
        assert value_pane.object == "ABC"

        icons = center_row[1]
        assert isinstance(icons, ChatReactionIcons)

        timestamp_pane = columns[1][2].object()
        assert isinstance(timestamp_pane, HTML)

    def test_reactions_link(self):
        # on init
        entry = ChatEntry(reactions=["favorite"])
        assert entry.reaction_icons.value == ["favorite"]

        # on change in entry
        entry.reactions = []
        assert entry.reaction_icons.value == []

        # on change in reaction_icons
        entry.reactions = ["favorite"]
        assert entry.reaction_icons.value == ["favorite"]

    def test_reaction_icons_input_dict(self):
        entry = ChatEntry(reaction_icons={"favorite": "heart"})
        assert isinstance(entry.reaction_icons, ChatReactionIcons)
        assert entry.reaction_icons.options == {"favorite": "heart"}

    def test_update_avatar(self):
        entry = ChatEntry(avatar="A")
        columns = entry._composite.objects
        avatar_pane = columns[0][0].object()
        assert isinstance(avatar_pane, HTML)
        assert avatar_pane.object == "A"

        entry.avatar = "B"
        avatar_pane = columns[0][0].object()
        assert avatar_pane.object == "B"

        entry.avatar = "❤️"
        avatar_pane = columns[0][0].object()
        assert avatar_pane.object == "❤️"

        entry.avatar = "https://assets.holoviz.org/panel/samples/jpg_sample.jpg"
        avatar_pane = columns[0][0].object()
        assert isinstance(avatar_pane, Image)
        assert (
            avatar_pane.object
            == "https://assets.holoviz.org/panel/samples/jpg_sample.jpg"
        )

        entry.show_avatar = False
        avatar_pane = columns[0][0].object()
        assert not avatar_pane.visible

    def test_update_user(self):
        entry = ChatEntry(user="Andrew")
        columns = entry._composite.objects
        user_pane = columns[1][0].object()
        assert isinstance(user_pane, HTML)
        assert user_pane.object == "Andrew"

        entry.user = "August"
        user_pane = columns[1][0].object()
        assert user_pane.object == "August"

        entry.show_user = False
        user_pane = columns[1][0].object()
        assert not user_pane.visible

    def test_update_value(self):
        entry = ChatEntry(value="Test")
        columns = entry._composite.objects
        value_pane = columns[1][1][0].object()
        assert isinstance(value_pane, Markdown)
        assert value_pane.object == "Test"

        entry.value = TextInput(value="Also testing...")
        value_pane = columns[1][1][0].object()
        assert isinstance(value_pane, TextInput)
        assert value_pane.value == "Also testing..."

        entry.value = _FileInputMessage(
            contents=b"I am a file", file_name="test.txt", mime_type="text/plain"
        )
        value_pane = columns[1][1][0].object()
        assert isinstance(value_pane, Markdown)
        assert value_pane.object == "I am a file"

    def test_update_timestamp(self):
        entry = ChatEntry()
        columns = entry._composite.objects
        timestamp_pane = columns[1][2].object()
        assert isinstance(timestamp_pane, HTML)
        dt_str = datetime.datetime.utcnow().strftime("%H:%M")
        assert timestamp_pane.object == dt_str

        special_dt = datetime.datetime(2023, 6, 24, 15)
        entry.timestamp = special_dt
        timestamp_pane = columns[1][2].object()
        dt_str = special_dt.strftime("%H:%M")
        assert timestamp_pane.object == dt_str

        mm_dd_yyyy = "%b %d, %Y"
        entry.timestamp_format = mm_dd_yyyy
        timestamp_pane = columns[1][2].object()
        dt_str = special_dt.strftime(mm_dd_yyyy)
        assert timestamp_pane.object == dt_str

        entry.show_timestamp = False
        timestamp_pane = columns[1][2].object()
        assert not timestamp_pane.visible


class TestChatFeed:
    @pytest.fixture
    def chat_feed(self):
        return ChatFeed()

    def test_hide_header(self, chat_feed):
        assert chat_feed.header is None

        chat_feed.header = "# Header"
        assert not chat_feed._composite.hide_header

        chat_feed.header = None
        assert chat_feed._composite.hide_header

        chat_feed.header = ""
        assert chat_feed._composite.hide_header

    def test_send(self, chat_feed):
        entry = chat_feed.send("Message")
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"

    def test_send_with_user_avatar(self, chat_feed):
        user = "Bob"
        avatar = "👨"
        entry = chat_feed.send("Message", user=user, avatar=avatar)
        assert entry.user == user
        assert entry.avatar == avatar

    def test_send_dict(self, chat_feed):
        entry = chat_feed.send({"value": "Message", "user": "Bob", "avatar": "👨"})
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"
        assert chat_feed.entries[0].user == "Bob"
        assert chat_feed.entries[0].avatar == "👨"

    def test_send_dict_minimum(self, chat_feed):
        entry = chat_feed.send({"value": "Message"})
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"

    def test_send_dict_without_value(self, chat_feed):
        with pytest.raises(ValueError, match="it must contain a 'value' key"):
            chat_feed.send({"user": "Bob", "avatar": "👨"})

    def test_send_dict_with_user_avatar_override(self, chat_feed):
        user = "August"
        avatar = "👩"
        entry = chat_feed.send(
            {"value": "Message", "user": "Bob", "avatar": "👨"},
            user=user,
            avatar=avatar,
        )
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"
        assert chat_feed.entries[0].user == user
        assert chat_feed.entries[0].avatar == avatar

    def test_send_entry(self, chat_feed):
        entry = ChatEntry(value="Message", user="Bob", avatar="👨")
        chat_feed.send(entry)
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"
        assert chat_feed.entries[0].user == "Bob"
        assert chat_feed.entries[0].avatar == "👨"

    def test_send_entry_with_user_avatar_override(self, chat_feed):
        user = "August"
        avatar = "👩"
        entry = ChatEntry(value="Message", user="Bob", avatar="👨")
        chat_feed.send(entry, user=user, avatar=avatar)
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Message"
        assert chat_feed.entries[0].user == user
        assert chat_feed.entries[0].avatar == avatar

    def test_send_with_respond(self, chat_feed):
        def callback(contents, user, instance):
            return f"Response to: {contents}"

        chat_feed.callback = callback
        chat_feed.send("Question", respond=True)
        time.sleep(0.5)

        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Response to: Question"

        chat_feed.respond()
        time.sleep(0.5)

        assert len(chat_feed.entries) == 3
        assert chat_feed.entries[2].value == "Response to: Response to: Question"

    def test_send_without_respond(self, chat_feed):
        def callback(contents, user, instance):
            return f"Response to: {contents}"

        chat_feed.callback = callback
        chat_feed.send("Question", respond=False)
        time.sleep(0.5)

        assert len(chat_feed.entries) == 1

        chat_feed.respond()
        time.sleep(0.5)

        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Response to: Question"

    def test_respond_without_callback(self, chat_feed):
        chat_feed.respond()  # Should not raise any errors

    def test_stream(self, chat_feed):
        entry = chat_feed.stream("Streaming message", user="Person", avatar="P")
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"
        assert chat_feed.entries[0].user == "Person"
        assert chat_feed.entries[0].avatar == "P"

        updated_entry = chat_feed.stream(
            " Appended message", user="New Person", entry=entry, avatar="N"
        )
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is updated_entry
        assert chat_feed.entries[0].value == "Streaming message Appended message"
        assert chat_feed.entries[0].user == "New Person"
        assert chat_feed.entries[0].avatar == "N"

        new_entry = chat_feed.stream("New message")
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1] is new_entry
        assert chat_feed.entries[1].value == "New message"

    def test_stream_with_user_avatar(self, chat_feed):
        user = "Bob"
        avatar = "👨"
        entry = chat_feed.stream(
            "Streaming with user and avatar", user=user, avatar=avatar
        )
        assert entry.user == user
        assert entry.avatar == avatar

    def test_stream_dict(self, chat_feed):
        entry = chat_feed.stream(
            {"value": "Streaming message", "user": "Person", "avatar": "P"}
        )
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"
        assert chat_feed.entries[0].user == "Person"
        assert chat_feed.entries[0].avatar == "P"

    def test_stream_dict_minimum(self, chat_feed):
        entry = chat_feed.stream({"value": "Streaming message"})
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"

    def test_stream_dict_without_value(self, chat_feed):
        with pytest.raises(ValueError, match="it must contain a 'value' key"):
            chat_feed.stream({"user": "Person", "avatar": "P"})

    def test_stream_dict_with_user_avatar_override(self, chat_feed):
        user = "Bob"
        avatar = "👨"
        entry = chat_feed.stream(
            {"value": "Streaming message", "user": "Person", "avatar": "P"},
            user=user,
            avatar=avatar,
        )
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"
        assert chat_feed.entries[0].user == user
        assert chat_feed.entries[0].avatar == avatar

    def test_stream_entry(self, chat_feed):
        entry = ChatEntry(value="Streaming message", user="Person", avatar="P")
        chat_feed.stream(entry)
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"
        assert chat_feed.entries[0].user == "Person"
        assert chat_feed.entries[0].avatar == "P"

    def test_stream_entry_with_user_avatar_override(self, chat_feed):
        user = "Bob"
        avatar = "👨"
        entry = ChatEntry(value="Streaming message", user="Person", avatar="P")
        chat_feed.stream(entry, user=user, avatar=avatar)
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        assert chat_feed.entries[0].value == "Streaming message"
        assert chat_feed.entries[0].user == user
        assert chat_feed.entries[0].avatar == avatar

    @pytest.mark.parametrize(
        "obj",
        [
            "Some Text",
            TextInput(value="Some Text"),
            HTML("Some Text"),
            Row(HTML("Some Text")),
        ],
    )
    def test_stream_to_nested_entry(self, chat_feed, obj):
        entry = chat_feed.send(
            Row(
                obj,
                Image("https://panel.holoviz.org/_static/logo_horizontal.png"),
            )
        )
        chat_feed.stream(" Added", entry=entry)
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0] is entry
        entry_obj = chat_feed.entries[0].value[0]
        if isinstance(entry_obj, Row):
            entry_obj = entry_obj[0]

        if hasattr(entry_obj, "object"):
            assert entry_obj.object == "Some Text Added"
        else:
            assert entry_obj.value == "Some Text Added"

    def test_undo(self, chat_feed):
        chat_feed.send("Message 1")
        chat_feed.send("Message 2")
        entry3 = chat_feed.send("Message 3")

        assert len(chat_feed.entries) == 3

        undone_entries = chat_feed.undo()
        assert len(chat_feed.entries) == 2
        assert undone_entries == [entry3]

        chat_feed.undo(2)
        assert len(chat_feed.entries) == 0

    def test_clear(self, chat_feed):
        chat_feed.send("Message 1")
        chat_feed.send("Message 2")

        assert len(chat_feed.entries) == 2

        cleared_entries = chat_feed.clear()
        assert len(chat_feed.entries) == 0
        assert cleared_entries[0].value == "Message 1"
        assert cleared_entries[1].value == "Message 2"

    def test_set_entries(self, chat_feed):
        chat_feed.send("Message 1")
        chat_feed.send("Message 2")

        assert len(chat_feed.entries) == 2

        chat_feed.entries = [ChatEntry(value="Message 3")]
        assert len(chat_feed.entries) == 1
        assert chat_feed.entries[0].value == "Message 3"


class TestChatFeedCallback:
    @pytest.fixture
    def chat_feed(self) -> ChatFeed:
        return ChatFeed()

    def test_user_avatar(self, chat_feed):
        def echo(contents, user, instance):
            return f"{user}: {contents}"

        chat_feed.callback = echo
        chat_feed.callback_user = "Bob"
        chat_feed.callback_avatar = "👨"
        chat_feed.send("Message", respond=True)
        assert len(chat_feed.entries) == 2
        time.sleep(0.5)
        assert chat_feed.entries[1].user == "Bob"
        assert chat_feed.entries[1].avatar == "👨"

    def test_return(self, chat_feed):
        def echo(contents, user, instance):
            return contents

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        time.sleep(0.5)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    def test_yield(self, chat_feed):
        def echo(contents, user, instance):
            yield contents

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        time.sleep(0.5)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    @pytest.mark.asyncio
    async def test_async_return(self, chat_feed):
        async def echo(contents, user, instance):
            return contents

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        await asyncio.sleep(0.25)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    @pytest.mark.asyncio
    async def test_async_yield(self, chat_feed):
        async def echo(contents, user, instance):
            yield contents

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        await asyncio.sleep(0.25)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    @pytest.mark.asyncio
    async def test_generator(self, chat_feed):
        async def echo(contents, user, instance):
            message = ""
            for char in contents:
                message += char
                yield message

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        await asyncio.sleep(0.25)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    @pytest.mark.asyncio
    async def test_async_generator(self, chat_feed):
        async def async_gen(contents):
            for char in contents:
                yield char

        async def echo(contents, user, instance):
            message = ""
            async for char in async_gen(contents):
                message += char
                yield message

        chat_feed.callback = echo
        chat_feed.send("Message", respond=True)
        await asyncio.sleep(0.25)
        assert len(chat_feed.entries) == 2
        assert chat_feed.entries[1].value == "Message"

    def test_placeholder_disabled(self, chat_feed):
        def echo(contents, user, instance):
            time.sleep(0.25)

        chat_log_mock = MagicMock()
        chat_log_mock.__getitem__.return_value = ChatEntry(value="Message")
        chat_feed.placeholder_threshold = 0
        chat_feed.callback = echo
        chat_feed._chat_log = chat_log_mock
        chat_feed.send("Message", respond=True)
        # only append sent message
        assert chat_log_mock.append.call_count == 1

    def test_placeholder_enabled(self, chat_feed):
        def echo(contents, user, instance):
            time.sleep(0.25)

        chat_log_mock = MagicMock()
        chat_log_mock.__getitem__.return_value = ChatEntry(value="Message")
        chat_feed.callback = echo
        chat_feed._chat_log = chat_log_mock
        chat_feed.send("Message", respond=True)
        # append sent message and placeholder
        assert chat_log_mock.append.call_count == 2


class TestChatInterfaceWidgetsSizingMode:
    def test_none(self):
        chat_interface = ChatInterface()
        assert chat_interface.sizing_mode is None
        assert chat_interface._chat_log.sizing_mode is None
        assert chat_interface._input_layout.sizing_mode is None
        assert chat_interface._input_layout[0].sizing_mode is None

    def test_fixed(self):
        chat_interface = ChatInterface(sizing_mode="fixed")
        assert chat_interface.sizing_mode == "fixed"
        assert chat_interface._chat_log.sizing_mode == "fixed"
        assert chat_interface._input_layout.sizing_mode == "fixed"
        assert chat_interface._input_layout[0].sizing_mode == "fixed"

    def test_stretch_both(self):
        chat_interface = ChatInterface(sizing_mode="stretch_both")
        assert chat_interface.sizing_mode == "stretch_both"
        assert chat_interface._chat_log.sizing_mode == "stretch_both"
        assert chat_interface._input_layout.sizing_mode == "stretch_width"
        assert chat_interface._input_layout[0].sizing_mode == "stretch_width"

    def test_stretch_width(self):
        chat_interface = ChatInterface(sizing_mode="stretch_width")
        assert chat_interface.sizing_mode == "stretch_width"
        assert chat_interface._chat_log.sizing_mode == "stretch_width"
        assert chat_interface._input_layout.sizing_mode == "stretch_width"
        assert chat_interface._input_layout[0].sizing_mode == "stretch_width"

    def test_stretch_height(self):
        chat_interface = ChatInterface(sizing_mode="stretch_height")
        assert chat_interface.sizing_mode == "stretch_height"
        assert chat_interface._chat_log.sizing_mode == "stretch_height"
        assert chat_interface._input_layout.sizing_mode is None
        assert chat_interface._input_layout[0].sizing_mode is None

    def test_scale_both(self):
        chat_interface = ChatInterface(sizing_mode="scale_both")
        assert chat_interface.sizing_mode == "scale_both"
        assert chat_interface._chat_log.sizing_mode == "scale_both"
        assert chat_interface._input_layout.sizing_mode == "stretch_width"
        assert chat_interface._input_layout[0].sizing_mode == "stretch_width"

    def test_scale_width(self):
        chat_interface = ChatInterface(sizing_mode="scale_width")
        assert chat_interface.sizing_mode == "scale_width"
        assert chat_interface._chat_log.sizing_mode == "scale_width"
        assert chat_interface._input_layout.sizing_mode == "scale_width"
        assert chat_interface._input_layout[0].sizing_mode == "scale_width"

    def test_scale_height(self):
        chat_interface = ChatInterface(sizing_mode="scale_height")
        assert chat_interface.sizing_mode == "scale_height"
        assert chat_interface._chat_log.sizing_mode == "scale_height"
        assert chat_interface._input_layout.sizing_mode == "stretch_width"
        assert chat_interface._input_layout[0].sizing_mode == "stretch_width"


class TestChatInterface:
    @pytest.fixture
    def chat_interface(self):
        return ChatInterface()

    def test_init(self, chat_interface):
        assert len(chat_interface._button_data) == 4
        assert len(chat_interface._widgets) == 1
        assert isinstance(chat_interface._input_layout, Row)
        assert isinstance(chat_interface._widgets["TextInput"], TextInput)

        # Buttons added to input layout
        inputs = chat_interface._input_layout
        for index, button_data in enumerate(chat_interface._button_data.values()):
            widget = inputs[index+1]
            assert isinstance(widget, Button)
            assert widget.name == button_data.name.title()

    def test_init_custom_widgets(self):
        widgets = [TextInput(name="Text"), FileInput()]
        chat_interface = ChatInterface(widgets=widgets)
        assert len(chat_interface._widgets) == 2
        assert isinstance(chat_interface._input_layout, Tabs)
        assert isinstance(chat_interface._widgets["Text"], TextInput)
        assert isinstance(chat_interface._widgets["FileInput"], FileInput)

    def test_active_widget(self, chat_interface):
        active_widget = chat_interface.active_widget
        assert isinstance(active_widget, TextInput)

    def test_active_tab(self):
        widget = TextInput(name="input")
        chat_interface = ChatInterface(widgets=[widget])
        assert chat_interface.active_tab == -1

    def test_active_tab_multiple_widgets(self, chat_interface):
        widget1 = TextInput(name="input1")
        widget2 = TextInput(name="input2")
        chat_interface.widgets = [widget1, widget2]
        assert chat_interface.active_tab == 0

        chat_interface.active_tab = 1
        assert chat_interface.active_tab == 1
        assert isinstance(chat_interface.active_widget, TextInput)

    def test_click_send(self, chat_interface):
        chat_interface.widgets = [TextAreaInput()]
        chat_interface.active_widget.value = "Message"
        chat_interface._click_send(None)
        assert len(chat_interface.entries) == 1
        assert chat_interface.entries[0].value == "Message"

    def test_click_undo(self, chat_interface):
        chat_interface.user = "User"
        chat_interface.send("Message 1")
        chat_interface.send("Message 2")
        chat_interface.send("Message 3", user="Assistant")
        expected = chat_interface.entries[-2:].copy()
        chat_interface._click_undo(None)
        assert len(chat_interface.entries) == 1
        assert chat_interface.entries[0].value == "Message 1"
        assert chat_interface._button_data["undo"].objects == expected

        # revert
        chat_interface._click_undo(None)
        assert len(chat_interface.entries) == 3
        assert chat_interface.entries[0].value == "Message 1"
        assert chat_interface.entries[1].value == "Message 2"
        assert chat_interface.entries[2].value == "Message 3"

    def test_click_clear(self, chat_interface):
        chat_interface.send("Message 1")
        chat_interface.send("Message 2")
        chat_interface.send("Message 3")
        expected = chat_interface.entries.copy()
        chat_interface._click_clear(None)
        assert len(chat_interface.entries) == 0
        assert chat_interface._button_data["clear"].objects == expected

    def test_click_rerun(self, chat_interface):
        self.count = 0
        def callback(contents, user, instance):
            self.count += 1
            return self.count
        chat_interface.callback = callback
        chat_interface.send("Message 1")
        assert chat_interface.entries[1].value == 1
        chat_interface._click_rerun(None)
        assert chat_interface.entries[1].value == 2

    def test_click_rerun_null(self, chat_interface):
        chat_interface._click_rerun(None)
        assert len(chat_interface.entries) == 0
