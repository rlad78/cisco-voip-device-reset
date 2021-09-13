from typing import Tuple
from ciscoreset import CUCM, get_credentials
from time import sleep
from tqdm import tqdm
import concurrent


def reset_lines_slowly(ucm: CUCM, lines: list[Tuple[str, str]], name="") -> None:
    try:
        for line in tqdm(lines, desc=name, leave=False):
            if line != lines[0]:
                sleep(30)
            devices: list[str] = ucm.get_dn_devices(line[0], line[1])
            for device in devices:
                ucm.do_device_reset(name=device)
    except Exception as e:
        tqdm.write(f"{name} FAILED: {e}")
        return name
    tqdm.write(f"{name} complete!")
    return name


if __name__ == "__main__":
    ucm = CUCM(*get_credentials())
    line_groups: dict = ucm.get_all_line_group_members()
    group_sample = [
        "Redfern COVID-19 Group 5XX",
        "Redfern COVID-19 Group 5XX - 6XX",
        "Redfern COVID-19 Group 6XX",
        "Redfern COVID-19 Group 7XX",
        "Redfern COVID-19 Group ALL",
        "IPTAY - Sales and Service LG",
        "Facilities-Dispatch-LG",
        "Redfern COVID-19 Group ALL",
        "Redfern Pharmacy Group",
        "Redfern-Apptmnt-LG",
        "Redfern-Health-Info-Mgmt-LG",
        "Sullivan-COVID-19-LG",
        "Undergrad-LG",
    ]

    for name in group_sample:
        line_groups.pop(name, None)

    # print(list(line_groups.keys()))
    # group_sample = [f"hunt-lab{i}" for i in range(1, 6, 1)]
    # line_groups: dict = {
    #     name: ucm.get_line_group_members(name) for name in group_sample
    # }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        lg_futures = [
            ex.submit(reset_lines_slowly, ucm, lg_members, lg_name)
            for lg_name, lg_members in line_groups.items()
        ]
        for future in tqdm(
            concurrent.futures.as_completed(lg_futures),
            total=len(line_groups),
            desc="TOTAL",
            position=0,
        ):
            pass
