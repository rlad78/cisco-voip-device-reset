from ciscoaxl import axl
from zeep.exceptions import Fault
import re
from typing import Any


def check_output(query) -> Any:
    if not issubclass(type(query), Fault):
        return query
    else:
        return None


class CUCM(axl):
    def __init__(self, username, password):
        cucm_address = "ucm-01.clemson.edu"
        cucm_version = "11.5"
        super().__init__(username, password, cucm_address, cucm_version)

    def get_user_devices(self, userid: str) -> list:
        dev_list = self.get_user(userid).associatedDevices.device
        if dev_list is Fault:
            raise Exception(f"Could not get user devices from user {userid}")
        return dev_list

    def get_user_ipcc(self, userid: str) -> str:
        result = check_output(self.get_user(userid))
        if result is not None:
            return result.ipccExtension._value_1
        else:
            return ""

    def update_user_devices(self, userid: str, devices: list) -> None:
        result = self.update_user(
            userid=userid,
            associatedDevices={"device": devices},
        )
        if result is Fault:
            raise Exception(
                f"Could not update user devices from user {userid}:\n{devices}"
            )

    def get_dn_partition(self, dn: str) -> str:
        for partition in ["Phones-PT", "ALLiphones", "Staging-PT"]:
            result = self.get_directory_number(pattern=dn, routePartitionName=partition)
            if not issubclass(type(result), Fault):
                return partition
        return ""

    def does_dn_exist(self, dn: str) -> bool:
        if not self.get_dn_partition(dn):
            return False
        else:
            return True

    def does_phone_exist(self, mac: str) -> bool:
        # mac = mac.replace(':', '').upper().strip()
        # check MAC is legit
        if not re.match(r"^[0-9A-F]{12}$", mac):
            raise Exception(f"Invalid MAC format: {mac}")
        elif check_output(self.get_phone(name="SEP" + mac)) is None:
            return False
        else:
            return True

    def get_phone_model(self, name: str) -> str:
        if not name.startswith("SEP"):
            raise Exception(f"Sorry, this method only works on desk phones ({name=})")
        if (phone := check_output(self.get_phone(name=name))) is None:
            raise Exception(f"No phone found with name {name}")
        model_name: str = phone["model"]
        return model_name.split(" ")[-1]


# class CUCMConnection(CUCM):
#     def __init__(self):
#         super().__init__(*get_passwords())
