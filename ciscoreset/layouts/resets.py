import PySimpleGUI as sg


def create_reset_menu() -> list:
    return [
        [sg.Text("Reset Phone")],
        [
            sg.Button("Soft Reset", key="resetDevice"),
            sg.Button("Device Settings", key="resetSettings"),
        ],
        [
            sg.Button("Network", key="resetNetwork"),
            sg.Button("Service Mode", key="resetService"),
            sg.Button("Security", key="resetSecurity"),
        ],
    ]
