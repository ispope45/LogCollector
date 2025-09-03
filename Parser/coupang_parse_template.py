import re

from .parser import Parser

FORM_NAME = "Collector_Summary"

def report(file_dir):
    ps = Parser()
    file_list = ps.gather_file(file_dir)

    columns = [
        "FILENAME",
        "INDEX",
        "PLATFORM",
        "PID",
        "SERIAL",
        "HOSTNAME",
        "CPU",
        "UPTIME",
        "VERSION",
        "NTP",
        "POWER",
        "FAN",
        "TEMP"
    ]

    ps.write_form("CREATE", columns, FORM_NAME)

    for file in file_list:
        try:
            with open(file, 'r', encoding="utf-8") as f:
                data = f.read()
                filename = file.split("\\")[-1]
                file_index = str(filename.split("_")[2])
                platform = "Unknown Platform"
                for key in ps.main_parser["PLATFORM"].keys():
                    if re.search(ps.main_parser["PLATFORM"][key], data):
                        platform = key
                        break

                datas = [
                    filename,
                    file_index,
                    platform,
                    ps.get_info(platform, "PID", data),
                    ps.get_info(platform, "SERIAL_NUMBER", data),
                    ps.get_info(platform, "HOSTNAME", data),
                    ps.get_cpu_info(platform, data),
                    ps.get_uptime_info(platform, data),
                    ps.get_info(platform, "VERSION", data),
                    ps.get_ntp_info(platform, data),
                    ps.get_power_info(platform, data),
                    ps.get_fan_info(platform, data),
                    ps.get_temp_info(platform, data)
                ]

                print(datas)

                ps.write_form("DATA", datas, FORM_NAME)

        except Exception as e:
            err = str(e).replace(",", "")
            ps.write_form(f"{err}", FORM_NAME)
            print(f"{file}:{err}")
