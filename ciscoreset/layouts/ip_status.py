import PySimpleGUI as sg


def create_ip_entry() -> list:
    return [
        [sg.Text("IP Address of device:")],
        [
            sg.In("", size=(18, 1), key="-IP-"),
            sg.Button("Connect", bind_return_key=True),
            sg.Button("Refresh"),
        ],
        [sg.Text("", key="-INFO-")],
        [sg.Text("", key="-STATUS-")],
        [sg.Text("", key="-DL_STATUS-", text_color="orange")],
    ]
