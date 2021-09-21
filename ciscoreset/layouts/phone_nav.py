import PySimpleGUI as sg


def create_navigation_menu() -> list:
    soft_keys = [
        [
            sg.Button(
                "        ",
                key=f"Soft{n}",
                tooltip=f"Softkey {n}",
                button_color=("white", "black"),
                pad=(10, 0),
                metadata="nav",
            )
            for n in range(1, 5, 1)
        ]
    ]

    directional_buttons = [
        [
            sg.Button(
                "↑",
                key="NavUp",
                tooltip="Up",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "←",
                key="NavLeft",
                tooltip="Left",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "o",
                key="NavSelect",
                tooltip="Select",
                button_color=("black", "silver"),
                metadata="nav",
            ),
            sg.Button(
                "→",
                key="NavRight",
                tooltip="Right",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "↓",
                key="NavDwn",
                tooltip="Down",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
    ]

    def dial_factory(num_string: str) -> list[sg.Button]:
        def digit(n) -> str:
            if n.isnumeric():
                return n
            elif n == "*":
                return "Star"
            elif n == "#":
                return "Pound"
            else:
                raise Exception(f"dial factory: digit issue with {n}")

        return [
            sg.Button(
                c,
                key=f"KeyPad{digit(c)}",
                tooltip=f"KeyPad{digit(c)}",
                button_color=("white", "black"),
                metadata="nav",
            )
            for c in num_string
        ]

    dial_pad = [dial_factory(chars) for chars in ["123", "456", "789", "*0#"]]

    left_pane = [
        [
            sg.Button(
                "Voicemail",
                key="Messages",
                tooltip="Voicemail",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "Settings",
                key="Applications",
                tooltip="Settings",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "Directory",
                key="Directories",
                tooltip="Directory",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                " +           ",
                key="VolUp",
                tooltip="Volume Up",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
            sg.Button(
                "           - ",
                key="VolDwn",
                tooltip="Volume Down",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
        ],
    ]

    right_pane = [
        [
            sg.Button(
                "Hold",
                key="Hold",
                tooltip="Hold",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
        [
            sg.Button(
                "Transfer",
                key="FixedFeature1",
                tooltip="Transfer",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Button(
                "Conference",
                key="FixedFeature2",
                tooltip="Conference",
                button_color=("white", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "Headset",
                key="Headset",
                tooltip="Headset",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
            sg.Button(
                "Speaker",
                key="Speaker",
                tooltip="Speaker",
                button_color=("white", "black"),
                pad=((0, 0), (20, 0)),
                metadata="nav",
            ),
        ],
        [
            sg.Button(
                "Mute",
                key="Mute",
                tooltip="Mute",
                button_color=("white", "black"),
                metadata="nav",
            )
        ],
    ]

    return [
        [
            sg.Column(
                soft_keys,
                element_justification="c",
                vertical_alignment="center",
                pad=((0, 0), (0, 10)),
            )
        ],
        [
            sg.Button(
                "⤺",
                key="NavBack",
                tooltip="Back",
                button_color=("white", "black"),
                metadata="nav",
            ),
            sg.Column(
                directional_buttons,
                pad=(20, 0),
                element_justification="c",
                vertical_alignment="center",
            ),
            sg.Button(
                "END",
                key="Release",
                tooltip="Hang Up",
                button_color=("red", "black"),
                metadata="nav",
            ),
        ],
        [
            sg.Column(
                left_pane,
                pad=(0, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
            sg.Column(
                dial_pad,
                pad=(15, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
            sg.Column(
                right_pane,
                pad=(0, 5),
                justification="center",
                element_justification="center",
                vertical_alignment="center",
            ),
        ],
    ]
