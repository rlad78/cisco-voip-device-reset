from ciscoreset import PhoneConnection


with PhoneConnection("10.12.4.231", verbose=True) as myphone:
    myphone.send_reset("security")
