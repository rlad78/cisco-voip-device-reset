from ciscoaxl import axl
from zeep.exceptions import Fault
import re
from typing import Any, Tuple


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

    def get_dn_devices(self, dn: str, partition="Phones-PT") -> list[str]:
        try:
            devices: list[str] = self.get_directory_number(
                pattern=dn, routePartitionName=partition
            )["return"]["line"]["associatedDevices"]
        except Fault:
            raise Exception(f"DN {dn} not found")
        if devices is None:
            return []
        else:
            return devices["device"]

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

    def get_phone_description(self, name: str) -> str:
        if (phone := check_output(self.get_phone(name=name))) is None:
            raise Exception(f"No phone found with name {name}")
        return phone["description"]

    def get_phone_main_line(self, name: str) -> str:
        if (phone := check_output(self.get_phone(name=name))) is None:
            raise Exception(f"No phone found with name {name}")
        if not phone["lines"]["line"]:
            return ""
        else:
            return phone["lines"]["line"][0]["dirn"]["pattern"]

    def get_phone_model(self, name: str) -> str:
        if not name.startswith("SEP"):
            raise Exception(f"Sorry, this method only works on desk phones ({name=})")
        if (phone := check_output(self.get_phone(name=name))) is None:
            raise Exception(f"No phone found with name {name}")
        model_name: str = phone["model"]
        return model_name.split(" ")[-1]

    def get_line_group_members(self, name: str) -> list[Tuple[str, str]]:
        line_group: dict = self.client.getLineGroup(name=name)["return"]["lineGroup"]

        if line_group["members"] is None:
            return []

        members: list[dict] = line_group["members"]["member"]

        return [
            (
                d["directoryNumber"]["pattern"],
                d["directoryNumber"]["routePartitionName"]["_value_1"],
            )
            for d in members
        ]

    def get_all_line_group_members(self) -> dict:
        line_groups: list[dict] = self.client.listLineGroup(
            searchCriteria={"name": "%"}, returnedTags={"name": ""}
        )["return"]["lineGroup"]

        return {
            lg["name"]: self.get_line_group_members(lg["name"]) for lg in line_groups
        }
