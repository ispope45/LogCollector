import os
import sys
import json

APP_VERSION = "LogCollector V2.0"

#
# def resource_path(*parts):
#     if getattr(sys, 'frozen', False):
#         base = sys._MEIPASS
#     else:
#         base = os.path.dirname(os.path.abspath(__file__))
#     return os.path.join(base, *parts)

#
# def resource_path(*parts):
#     base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
#     return os.path.join(base, *parts)


def resource_path(*parts):
    # 배포(exe): _MEIPASS 아래에 리소스가 풀림
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


ROOT_DIR = os.getcwd()  # project root 기준
TEMPLATE_FILEPATH = resource_path("Data", "Collector_device_template.xlsx")
ICON_FILEPATH = resource_path("icon.ico")

with open(resource_path("Data", "command.json"), encoding="utf-8") as f:
    CMD_JSON = json.load(f)
with open(resource_path("Data", "parser.json"), encoding="utf-8") as f:
    PARSE_JSON = json.load(f)


INIT_CMD = CMD_JSON["INIT"]
VALID_PARSE = PARSE_JSON["VALID_PARSE"]
INIT_PARSE = PARSE_JSON["INIT_PARSE"]
MAIN_PARSER = PARSE_JSON["PARSE_PATTERN"]


DEVICE_FORM = {
    "INDEX":0,"HOSTNAME":1,"IPADDR":2,"PORT":3,
    "USERNAME":4,"PASSWORD":5,"ENABLE":6,"PLATFORM":7
}

PLATFORM_TO_NETMIKO = {
    "CISCO_XE":"cisco_xe",
    "CISCO_NXOS":"cisco_nxos",
    "CISCO_WLC_AIR":"cisco_wlc",
    "CISCO_WLC_CAT":"cisco_xe",
    "CISCO_IOS":"cisco_ios",
}