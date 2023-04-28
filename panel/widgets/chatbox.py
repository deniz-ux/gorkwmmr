import random

from textwrap import wrap
from typing import (
    AnyStr,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
)

import param

from panel.pane.markup import Markdown
from panel.pane.image import Image
from panel.layout import Column, Row, HSpacer, ListPanel
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

    style = param.Dict(
        default={},
        doc="""Dictionary of CSS properties and values""",
    )

    show_name = param.Boolean(
        default=True,
        doc="""Whether to show the name of the user""",
    )

    _composite_type: ClassVar[Type[ListPanel]] = Column

    def __init__(
        self,
        value: AnyStr,
        text_color: AnyStr,
        background: AnyStr,
        icon: AnyStr = None,
        style: Dict[str, str] = None,
        **params,
    ):
        style = {
            "color": text_color,
            "background-color": background,
            "border-radius": "12px",
            "padding": "8px",
        }
        style.update(params.pop("style", {}))
        super().__init__(**params)

        # determine alignment
        message_layout = {
            p: getattr(self, p)
            for p in Layoutable.param
            if p not in ("name", "height", "margin") and getattr(self, p) is not None
        }
        # create the message icon
        icon_params = {
            "width": 36,
            "height": 36,
            "margin": (12, 2, 12, 2),
            "sizing_mode": "fixed",
        }
        if icon is None:
            # if no icon is provided,
            # use the first letter of the name
            # and a random colored background
            icon_style = {
                "background-color": background,
                "border-radius": "18px",
            }
            self._icon = Markdown(
                f"## <center>{self.name[0]}</center>",
                style=icon_style,
                **icon_params,
            )
        else:
            self._icon = Image(icon)

        # create the message bubble
        box_width = message_layout.get("width", 100)
        text_width = int(box_width / 2)  # make text start a new line
        wrapped_text = "\n".join(wrap(value, width=text_width))
        self._bubble = StaticText(
            value=wrapped_text,
            style=style,
            margin=13,
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

        container_params = {
            "align": horizontal_align,
            "sizing_mode": "stretch_width",
        }
        row = Row(*objects, **container_params)
        if self.show_name:
            name = StaticText(
                value=self.name,
                margin=margin,
                style={"color": "grey"},
                align=horizontal_align,
            )
            row = Column(name, row, **container_params)

        if horizontal_align == "start":
            row.append(HSpacer())
        else:
            row.insert(0, HSpacer())
        self._composite[:] = [row]


class ChatBox(CompositeWidget):
    user_messages = param.List(
        doc="""List of messages, mapping user to message""",
        item_type=Dict,
        default=[],
    )

    user_icons = param.Dict(
        doc="""Dictionary mapping name of users to their icons""",
        default={},
    )

    user_colors = param.Dict(
        doc="""Dictionary mapping name of users to their colors""",
        default={},
    )

    primary_user = param.String(
        doc="""
            Name of the primary user;
            the first key found in user_messages
            will be used if unspecified
        """,
        default=None,
    )

    _composite_type: ClassVar[Type[ListPanel]] = Column

    def __init__(self, user_messages: List[AnyStr] = None, **params):
        if user_messages:
            params["user_messages"] = user_messages
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
            layout,
            sizing_mode="stretch_both",
            width_policy="max",
            height_policy="max",
            height=None,
            margin=0,
        )
        self._chat_log = Column(**chat_layout)
        self._user_input = TextInput(
            name="Type your message",
            placeholder="Press Enter to send",
            sizing_mode="stretch_width",
            width_policy="max",
        )

        # this doesn't work:
        # self.param.watch(self._display_all_messages, "user_messages")
        self._user_input.param.watch(self._send_message, "value")
        self._composite[:] = [self._chat_log, self._user_input]

    def _get_name(self, dict_):
        """
        Get the name of the user who sent the message.
        """
        return list(dict_.keys())[0]

    def _generate_dark_color(self):
        """
        Generate a random dark color in hexadecimal format.
        """
        r, g, b = random.randint(0, 127), random.randint(0, 127), random.randint(0, 127)
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _create_message_row(self, user_message: Dict[str, str]):
        user = self._get_name(user_message)

        # try to get input color; if not generate one and save
        if user in self.user_colors:
            background = self.user_colors[user]
        else:
            background = self._generate_dark_color()
            self.user_colors[user] = background

        # try to get input icon
        user_icon = self.user_icons.get(user, None)

        # show name if the previous message wasn't from user
        if self._chat_log:
            last_user = self._chat_log[-1].name
            show_name = last_user != user
        else:
            show_name = True

        align = "start" if user != self.primary_user else "end"

        return MessageRow(
            name=user,
            value=user_message[user],
            text_color="white",
            background=background,
            icon=user_icon,
            show_name=show_name,
            align=align,
        )

    def _display_all_messages(self, event: Optional[param.parameterized.Event] = None):
        if self.primary_user is None and self.user_messages:
            self.primary_user = self._get_name(self.user_messages[0])

        message_rows = [
            self._create_message_row(user_message)
            for user_message in self.user_messages
        ]
        self._chat_log[:] = message_rows

    def _send_message(self, event: Optional[param.parameterized.Event] = None):
        if event.new == "":
            return

        user_message = {"You": event.new}
        self.user_messages.append(user_message)

        # this should be removed once display_all_messages callback works.
        message_row = self._create_message_row(user_message)
        self._chat_log.append(message_row)
        self._user_input.value = ""
