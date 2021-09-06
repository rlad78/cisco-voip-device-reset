from ciscoreset import PhoneConnection


with PhoneConnection("10.12.4.231") as myphone:
    myphone._screenshot()
