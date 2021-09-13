from time import sleep
from ciscoreset import PhoneConnection, get_menu_position, get_list_position


with PhoneConnection("10.12.4.231", verbose=True) as myphone:
    myphone._to_home()
