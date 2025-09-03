# cording = utf-8
import pandas as pd
import glob
import re

from app.constants import MAIN_PARSER, ROOT_DIR


class Parser:
    def __init__(self):
        self.parse_df = pd.DataFrame()
        self.main_parser = MAIN_PARSER

    @staticmethod
    def find_section(data, start_key, end_key):
        if start_key == "":
            return data
        else:
            start_match = re.search(start_key, data)
            if start_match:
                start_idx = start_match.start()
            else:
                return data

        if end_key == "":
            end_idx = start_idx + 10000
        elif end_key == "UNLIMITED":
            return data[start_idx:]
        else:
            end_match = re.search(end_key, data[start_idx:])
            if end_match:
                end_idx = start_idx + end_match.start()
            else:
                end_idx = start_idx + 10000
        # print(f"{start_idx}-{end_idx}")
        return data[start_idx:end_idx]

    def find_single_value(self, platform, key, data):
        # 임시 code
        if MAIN_PARSER[key]:
            for i in range(1, 10):
                md_data = data

                if MAIN_PARSER[key][platform].get(f"SECTION{str(i)}"):
                    start_key = MAIN_PARSER[key][platform][f"SECTION{str(i)}"]["START"]
                    end_key = MAIN_PARSER[key][platform][f"SECTION{str(i)}"]["END"]

                    md_data = self.find_section(data, start_key, end_key)

                if not MAIN_PARSER[key][platform].get(f"PATTERN{str(i)}"):
                    continue

                match = re.search(MAIN_PARSER[key][platform][f"PATTERN{str(i)}"], md_data)
                if match:
                    return match

        return None

    def find_multi_value(self, platform, key, data):
        if MAIN_PARSER[key]:
            for i in range(1, 10):
                md_data = data

                if MAIN_PARSER[key][platform].get(f"SECTION{str(i)}"):
                    start_key = MAIN_PARSER[key][platform][f"SECTION{str(i)}"]["START"]
                    end_key = MAIN_PARSER[key][platform][f"SECTION{str(i)}"]["END"]

                    md_data = self.find_section(data, start_key, end_key)

                if not MAIN_PARSER[key][platform].get(f"PATTERN{str(i)}"):
                    continue
                matches = list(re.finditer(MAIN_PARSER[key][platform][f"PATTERN{str(i)}"], md_data))

                if matches:
                    return matches

        return []

    def get_info(self, platform, key, data):
        if self.find_single_value(platform, key, data):
            res = self.find_single_value(platform, key, data).group(1)
        else:
            res = None
        return res

    def get_cpu_info(self, platform, data):
        if self.find_single_value(platform, "CPU", data):
            value = self.find_single_value(platform, "CPU", data).group(1)
            res = str(int(float(value))) + " %"
        else:
            res = None
        return res

    def get_uptime_info(self, platform, data):
        if list(self.find_multi_value(platform, "UPTIME", data)):
            values = self.find_multi_value(platform, "UPTIME", data)
            uptime = 0
            for value in values:
                group_data = value.groupdict()

                if group_data.get("YEAR"):
                    uptime = uptime + (int(value.group("YEAR")) * 365 * 24)
                if group_data.get("WEEK"):
                    uptime = uptime + (int(value.group("WEEK")) * 7 * 24)
                if group_data.get("DAY"):
                    uptime = uptime + (int(value.group("DAY")) * 24)
                if group_data.get("HOUR"):
                    uptime = uptime + int(value.group("HOUR"))
            res = str(int(uptime / 24)) + " Days"
        else:
            res = None
        return res

    def get_power_info(self, platform, data):
        if self.find_multi_value(platform, "POWER", data):
            values = self.find_multi_value(platform, "POWER", data)
            # print(values)
            pwr_module_cnt = len(values)
            pwr_normal_cnt = 0

            normal_status = ["Ok", "ok", "OK", "Good", "up"]

            for value in values:
                group_data = value.groupdict()
                if group_data.get("PWR_STATUS") in normal_status:
                    pwr_normal_cnt = pwr_normal_cnt + 1

            res = f"({pwr_normal_cnt}/{pwr_module_cnt})"
        else:
            res = None
        return res

    def get_fan_info(self, platform, data):
        if self.find_multi_value(platform, "FAN", data):
            values = self.find_multi_value(platform, "FAN", data)
            # print(values)
            fan_module_cnt = len(values)
            fan_normal_cnt = 0

            normal_status = ["Ok", "ok", "OK", "Good", "up", "Powered-Up"]

            for value in values:
                group_data = value.groupdict()
                if group_data.get("FAN_STATUS") in normal_status:
                    fan_normal_cnt = fan_normal_cnt + 1

            res = f"({fan_normal_cnt}/{fan_module_cnt})"
        else:
            res = None
        return res

    def get_temp_info(self, platform, data):
        if self.find_multi_value(platform, "TEMP", data):
            values = self.find_multi_value(platform, "TEMP", data)
            # print(values)
            temp_sensor_cnt = len(values)
            temp_normal_cnt = 0

            if platform in ["DELL_OS"]:
                for value in values:
                    if int(value.group("TEMP_STATUS")) < 50:
                        temp_normal_cnt = temp_normal_cnt + 1
                return f"({temp_normal_cnt}/{temp_sensor_cnt})"

            if platform in ["CISCO_WLC_AIR"]:
                for value in values:
                    if int(value.group("TEMP_STATUS")) < 60:
                        temp_normal_cnt = temp_normal_cnt + 1
                return f"({temp_normal_cnt}/{temp_sensor_cnt})"

            normal_status = ["Normal", "GREEN", "OK", "Ok"]

            for value in values:
                group_data = value.groupdict()
                if group_data.get("TEMP_STATUS") in normal_status:
                    temp_normal_cnt = temp_normal_cnt + 1

            res = f"({temp_normal_cnt}/{temp_sensor_cnt})"
        else:
            res = None
        return res

    def get_ntp_info(self, platform, data):
        if self.find_multi_value(platform, "NTP", data):
            values = self.find_multi_value(platform, "NTP", data)
            ntp_status = None

            good_status = ["synchronized", "NTP", "In Sync"]

            for value in values:
                group_data = value.groupdict()
                if group_data.get("NTP_STATUS") in good_status:
                    ntp_status = "good"
                else:
                    ntp_status = "bad"

            res = ntp_status
        else:
            res = None
        return res

    @staticmethod
    def chk_ap(ap_count, ap_status, platform, hostname):
        if platform == "CISCO_WLC_CAT" or platform == "CISCO_WLC_AIR":
            # print(platform)
            if ap_count == "":
                print(f"{hostname} is ap_count null")
                return None

            if ap_status == []:
                print(f"{hostname} is ap_status null")

            summ_ap = list()
            summ_ap.append(hostname)
            summ_ap.append(platform)
            summ_ap.append(ap_count)

            down_ap = list()
            down_count = 0
            for ap in ap_status:
                if ap[2] == "Not Joined":
                    down_count = down_count + 1
                    down_ap.append([hostname, ap[0], ap[1], ap[2]])

            summ_ap.append(down_count)
            # print(summ_ap)
            with open(ROOT_DIR + r"\ap_summ.csv", "a") as f1:
                f1.write(f"{summ_ap[0]},{summ_ap[1]},{summ_ap[2]},{summ_ap[3]}\n")

            if down_count > 0:
                with open(ROOT_DIR + r"\ap_down.csv", "a") as f2:
                    for v in down_ap:
                        f2.write(f"{v[0]},{v[1]},{v[2]},{v[3]}\n")
        #     res = "Bad"
        # else:
        #     res = "Good"
        # return res

    @staticmethod
    def write_form(command, data, form_name):
        try:
            if command == "CREATE":
                open(ROOT_DIR + rf"\{form_name}.csv", "w")

            with open(ROOT_DIR + rf"\{form_name}.csv", "a") as outputFile:
                row = ",".join(data) + "\n"
                outputFile.write(row)

        except Exception as e:
            print(e)

    @staticmethod
    def gather_file(file_path):
        file_list = glob.glob(file_path + "\\*.txt")
        filtered_file_list = [item for item in file_list if "Collector_" in item]

        return filtered_file_list


