import glob
import os
import re
import sys
from datetime import date
import time


BASE_PATH = "C:\\Users\\Jungly\\Desktop\\20250413\\log\\"
RESULT_PATH = BASE_PATH + "result\\"
cisco_prompt_regex = r'((?:CAMP_|FC_|PICO_|SPA3_|Gwangju\-|coupang_)[a-zA-Z0-9\-_.]+)#'
cisco_show_cmd_regex = r'((?:CAMP_|FC_|PICO_|SPA3_|Gwangju\-|coupang_)[a-zA-Z0-9\-_.]+)#\s*sh'

wlc_prompt_regex = r'\(((?:CAMP_|FC_|PICO_|SPA3_|coupang_)[a-zA-Z0-9\-_.]+)\) >'
wlc_show_cmd_regex = r'\(((?:CAMP_|FC_|PICO_|SPA3_|coupang_)[a-zA-Z0-9\-_.]+)\) >\s*sh'


def parse_data_cisco(data):
    match = False
    hostname = None
    contents = None

    if bool(re.search(cisco_prompt_regex, data)):
        hostname = re.search(cisco_prompt_regex, data).group(1)
        if bool(re.search(cisco_show_cmd_regex, data)):
            a_start_idx = re.search(cisco_show_cmd_regex, data).start()
            b_start_idx = re.search(cisco_show_cmd_regex, data).end()
            if bool(re.search(cisco_prompt_regex, data[b_start_idx:])):
                end_idx = re.search(cisco_prompt_regex, data[b_start_idx:]).start() + b_start_idx
                contents = data[a_start_idx:end_idx]
                data = data[end_idx:]
                match = True
            else:
                contents = data[a_start_idx:]
                data = data[b_start_idx:]
                match = False

    return match, hostname, contents, data


def parse_data_wlc(data):
    match = False
    hostname = None
    contents = None

    if bool(re.search(wlc_prompt_regex, data)):
        hostname = re.search(wlc_prompt_regex, data).group(1)
        if bool(re.search(wlc_show_cmd_regex, data)):
            a_start_idx = re.search(wlc_show_cmd_regex, data).start()
            b_start_idx = re.search(wlc_show_cmd_regex, data).end()
            if bool(re.search(wlc_prompt_regex, data[b_start_idx:])):
                end_idx = re.search(wlc_prompt_regex, data[b_start_idx:]).start() + b_start_idx
                contents = data[a_start_idx:end_idx]
                data = data[end_idx:]
                match = True
            else:
                contents = data[a_start_idx:]
                data = data[b_start_idx:]
                match = True

    return match, hostname, contents, data


if __name__ == "__main__":
    target_files = glob.glob(BASE_PATH + "*")
    print(target_files)
    file_list = []

    for file in target_files:
        if f'.log' not in file:
            target_files.remove(file)
            continue
        file_list.append(file)

    for target in file_list:
        # with open("C:\\Users\\Biber\\Desktop\\Log\\3.log", 'r', encoding="utf-8") as f:
        print(target)
        with open(target, 'r', encoding="utf-8") as f:
            match = True
            data = f.read()
            data1 = data
            data2 = data
            print("start cisco")
            while match:
                match, hostname, contents, data1 = parse_data_cisco(data1)
                if match:
                    result_path = RESULT_PATH + f"{hostname}.txt"
                    try:
                        with open(result_path, "a") as outputFile:
                            outputFile.write(contents)
                    except Exception as e:
                        print(e)
                    try:
                        with open(RESULT_PATH + "logging.log", "a") as outputFile:
                            outputFile.write(hostname + "\n")
                    except Exception as e:
                        print(e)
                else:
                    break

            print("start wlc")
            match = True
            while match:
                match, hostname, contents, data2 = parse_data_wlc(data2)
                if match:
                    result_path = RESULT_PATH + f"{hostname}.txt"
                    try:
                        with open(result_path, "a") as outputFile:
                            outputFile.write(contents)
                    except Exception as e:
                        print(e)
                    try:
                        with open(RESULT_PATH + "logging.log", "a") as outputFile:
                            outputFile.write(hostname + "\n")
                    except Exception as e:
                        print(e)

                else:
                    break



