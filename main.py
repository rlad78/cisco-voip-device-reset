from time import sleep
from ciscoreset import PhoneConnection, get_menu_position, get_list_position


with PhoneConnection("10.12.4.119") as myphone:
    myphone.xml.send_key("Soft3")
    sleep(7)
    myphone._wait_until_reachable()
    # myphone._screenshot()
    print("DONE")
