from __future__ import annotations

import random

from typing import (
    ClassVar, Dict, List, Optional, Tuple, Type,
)

import param

from panel.layout import Column, ListPanel, Row
from panel.layout.spacer import VSpacer
from panel.pane import Markdown
from panel.pane.image import Image
from panel.viewable import Layoutable
from panel.widgets.base import CompositeWidget
from panel.widgets.input import StaticText, TextInput


class MessageRow(CompositeWidget):
    value = param.String(
        default="",
        doc="""The message to display""",
    )

    text_color = param.String(
        default="white",
        doc="""Font color of the chat text""",
    )

    background_color = param.String(
        default="black",
        doc="""Background color of the chat bubble""",
    )

    icon = param.String(default=None, doc="""The icon to display""")

    styles = param.Dict(
        default={},
        doc="""
            Dictionary of CSS properties and values to apply
            message to the bubble.
            """,
    )

    show_name = param.Boolean(
        default=True,
        doc="""Whether to show the name of the user""",
    )

    _composite_type: ClassVar[Type[ListPanel]] = Column

    def __init__(
        self,
        value: str,
        text_color: str = "white",
        background: str = "black",
        icon: str = None,
        styles: Dict[str, str] = None,
        show_name: bool = True,
        **params,
    ):
        bubble_styles = {
            "color": text_color,
            "background-color": background,
            "border-radius": "12px",
            "padding": "8px",
        }
        bubble_styles.update(styles or {})
        super().__init__(**params)

        # determine alignment
        message_layout = {
            p: getattr(self, p)
            for p in Layoutable.param
            if p not in ("name", "height", "margin", "styles")
            and getattr(self, p) is not None
        }
        # create the message icon
        icon_params = dict(
            width=40,  # finetuned so it doesn't start a new line
            height=40,  # designed to not match width
            margin=(12, 2, 12, 2),
            sizing_mode="fixed",
            align="center",
        )
        if icon is None:
            # if no icon is provided,
            # use the first and last letter of the name
            # and a random colored background
            icon_label = f"{self.name[0]}-{self.name[-1]}".upper()
            self._icon = StaticText(
                value=icon_label,
                styles=bubble_styles,
                **icon_params,
            )
        else:
            self._icon = Image(icon, **icon_params)

        # create the message bubble
        self._bubble = Markdown(
            object=value,
            renderer="markdown",
            styles=bubble_styles,
            margin=10,
            **message_layout,
        )

        # layout objects
        horizontal_align = message_layout.get("align", "start")
        if isinstance(horizontal_align, tuple):
            horizontal_align = horizontal_align[0]
        if horizontal_align == "start":
            margin = (0, 0, -5, 60)
            objects = (self._icon, self._bubble)
        else:
            margin = (0, 60, -5, 0)
            objects = (self._bubble, self._icon)

        container_params = dict(
            align=horizontal_align,
        )
        row = Row(*objects, **container_params)
        if show_name:
            name = StaticText(
                value=self.name,
                margin=margin,
                styles={"color": "grey"},
                align=horizontal_align,
            )
            row = Column(name, row, **container_params)

        self._composite[:] = [row]


class ChatBox(CompositeWidget):
    value = param.List(
        doc="""List of messages, mapping user to message,
        e.g. `[{'You': 'Welcome!'}]`""",
        item_type=Dict,
        default=[],
    )

    primary_user = param.String(
        doc="""
            Name of the primary input user;
            the first key found in value
            will be used if unspecified
        """,
        default=None,
    )

    allow_input = param.Boolean(
        doc="""
            Whether to allow the primary user to interactively
            enter messages.
        """,
        default=True,
    )

    user_icons = param.Dict(
        doc="""Dictionary mapping name of users to their icons,
        e.g. `[{'You': 'path/to/icon.png'}]`""",
        default={},
    )

    user_colors = param.Dict(
        doc="""Dictionary mapping name of users to their colors,
        e.g. `[{'You': 'red'}]`""",
        default={},
    )

    _composite_type: ClassVar[Type[ListPanel]] = Column

    def __init__(self, **params):
        # set up parameters
        if params.get("width") and params.get("height") and "sizing_mode" not in params:
            params["sizing_mode"] = None

        super().__init__(**params)

        # Set up layout
        layout = {
            p: getattr(self, p)
            for p in Layoutable.param
            if p not in ("name", "height", "margin") and getattr(self, p) is not None
        }
        chat_layout = dict(
            sizing_mode="stretch_both",
            height=None,
            margin=0,
            **layout,
        )
        self._chat_title = StaticText(
            value=f"{self.name}",
            styles={"font-size": "1.5em"},
            align="center",
        )
        self._chat_log = Column(scroll=True, **chat_layout)

        box_objects = [self._chat_title] if self.name else []
        box_objects.append(self._chat_log)
        if self.allow_input:
            self._input_message = TextInput(
                name="Type your message",
                placeholder="Press Enter to send",
                sizing_mode="stretch_width",
                margin=0,
            )
            self._input_message.param.watch(self._enter_message, "value")
            box_objects.extend([VSpacer(height_policy="min"), self._input_message])
        self._composite[:] = box_objects

        # add interactivity
        self.param.watch(self._refresh_log, "value")
        self.param.trigger("value")


    def _generate_dark_color(self, string: str) -> str:
        """
        Generate a random dark color in hexadecimal format.
        """
        seed = sum([ord(c) for c in string])
        random.seed(seed)

        r, g, b = random.randint(0, 127), random.randint(0, 127), random.randint(0, 127)
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        return color

    @staticmethod
    def _get_name(dict_: Dict[str, str]) -> str:
        """
        Get the name of the user who sent the message.
        """
        return next(iter(dict_))

    def _separate_user_message(self, user_message: Dict[str, str]) -> Tuple[str, str]:
        """
        Separate the user and message from a dictionary.
        """
        if len(user_message) != 1:
            raise ValueError(
                f"Expected a dictionary with one key-value pair, e.g. "
                f"{{'User': 'Message'}} , but got {user_message}"
            )

        user = self._get_name(user_message)
        message = user_message[user]
        return user, message

    def _instantiate_message_row(
        self, user: str, message: str, show_name: bool
    ) -> MessageRow:
        """
        Instantiate a MessageRow object.
        """
        if self.primary_user is None:
            if self.value:
                self.primary_user = self._get_name(self.value[0])
            else:
                self.primary_user = "You"

        # try to get input color; if not generate one and save
        if user in self.user_colors:
            background = self.user_colors[user]
        else:
            background = self._generate_dark_color(string=user)
            self.user_colors[user] = background

        # try to get input icon
        user_icon = self.user_icons.get(user, None)

        align = "start" if user != self.primary_user else "end"

        message_row = MessageRow(
            name=user,
            value=message,
            text_color="white",
            background=background,
            icon=user_icon,
            show_name=show_name,
            align=align,
        )
        return message_row

    def _refresh_log(self, event: Optional[param.parameterized.Event] = None) -> None:
        """
        Refresh the chat log for complete replacement of all messages.
        """
        user_messages = event.new

        message_rows = []
        previous_user = None
        for user_message in user_messages:
            user, message = self._separate_user_message(user_message)

            show_name = user != previous_user
            previous_user = user

            message_row = self._instantiate_message_row(user, message, show_name)
            message_rows.append(message_row)

        self._chat_log.objects = message_rows

    def _enter_message(self, event: Optional[param.parameterized.Event] = None) -> None:
        """
        Append the message from the text input when the user presses Enter.
        """
        if event.new == "":
            return

        user = self.primary_user or "You"
        message = event.new
        self.append({user: message})
        self._input_message.value = ""

    def append(self, user_message: Dict[str, str]) -> None:
        """
        Appends a message to the chat log.

        Arguments
        ---------
        user_message (dict): Dictionary mapping user to message.
        """
        if not isinstance(user_message, dict):
            raise ValueError(f"Expected a dictionary, but got {user_message}")

        # this doesn't trigger anything because it's the same object
        # just append so it stays in sync
        self.value.append(user_message)
        user, message = self._separate_user_message(user_message)

        previous_user = None
        if self._chat_log.objects:
            previous_user = self._chat_log.objects[-1].name
        show_name = user != previous_user

        message_row = self._instantiate_message_row(user, message, show_name)
        self._chat_log.append(message_row)

    def extend(self, user_messages: List[Dict[str, str]]) -> None:
        """
        Extends the chat log with new users' messages.

        Arguments
        ---------
        user_messages (list): List of user messages to add.
        """
        for user_message in user_messages:
            self.append(user_message)

    def clear(self) -> None:
        """
        Clears the chat log.
        """
        self.value = []

    def __len__(self) -> int:
        return len(self.value)
