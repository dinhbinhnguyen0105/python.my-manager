from datetime import datetime
import pytz
from random import randint
import platform
import subprocess
import os
from src import constants


def replace_keywords(data, template):
    if data.get("option") in ["cho thuê", "sang nhượng"]:
        data["unit"] = "triệu/tháng"
    else:
        data["unit"] = "tỷ"

    template = template.replace("<option>", data.get("option"))
    template = template.replace("<category>", data.get("category"))
    template = template.replace("<province>", data.get("province").title())
    template = template.replace("<district>", data.get("district").title())
    template = template.replace("<ward>", data.get("ward").title())
    template = template.replace("<legal>", data.get("legal"))
    template = template.replace("<furniture>", data.get("furniture"))
    template = template.replace("<building_line>", data.get("building_line"))
    template = template.replace("<price>", str(data.get("price")))
    template = template.replace("<PID>", data.get("pid"))
    template = template.replace("<street>", data.get("street").title())
    template = template.replace("<structure>", str(data.get("structure")) + " tầng")
    template = template.replace("<function>", data.get("function"))
    template = template.replace("<description>", data.get("description"))
    template = template.replace("<unit>", data.get("unit"))
    template = template.replace("<area>", str(data.get("area")) + "m2")

    icon = constants.ICONS[randint(0, len(constants.ICONS) - 1)]
    while template != template.replace("<icon>", icon, 1):
        icon = constants.ICONS[randint(0, len(constants.ICONS) - 1)]
        template = template.replace("<icon>", icon, 1)

    return template


def init_footer(pid, updated_at):
    now_utc = datetime.utcnow()
    tz_hochiminh = pytz.timezone("Asia/Ho_Chi_Minh")
    now_hochiminh = now_utc.replace(tzinfo=pytz.utc).astimezone(tz_hochiminh)
    format_string = "%Y-%m-%d %H:%M:%S"

    return f"""
[
    pid <{pid}>
    updated_at <{updated_at}>
    published_at <{now_hochiminh.strftime(format_string)}>
]
"""


def open_file_explorer(path=None):
    system = platform.system()
    if system == "Windows":
        if path:
            try:
                os.startfile(path)  # Simpler way to open on Windows
            except OSError:
                print(f"Could not open path: {path}")
        else:
            subprocess.Popen("explorer")
    elif system == "Darwin":  # Darwin is the system name for macOS
        if path:
            subprocess.Popen(["open", os.path.dirname(path)])
        else:
            subprocess.Popen(["open", "."])  # Open current directory
    else:
        print(f"Operating system '{system}' is not supported.")
