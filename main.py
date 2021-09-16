#!.venv/bin/python3
from time import sleep
from ciscoreset import PhoneConnection, get_menu_position, get_list_position
import ciscoreset.gui_homepage as gui


with PhoneConnection("10.12.4.231", verbose=True) as myphone:
    myphone._screenshot(full_name="screenshot")

# gui.run()
