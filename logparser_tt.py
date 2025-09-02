import glob
import os
import re
import sys
from datetime import date
import time


BASE_PATH = "C:\\Users\\Biber\\Desktop\\Log\\20250812\\20250812\\Raw\\"
RESULT_PATH = BASE_PATH + "result\\"
cisco_prompt_regex = r'((?:CAMP_|FC_|PICO_|SPA3_|Gwangju\-|coupang_)[a-zA-Z0-9\-_.]+#)'
cisco_show_cmd_regex = r'((?:CAMP_|FC_|PICO_|SPA3_|Gwangju\-|coupang_)[a-zA-Z0-9\-_.]+#)\s*sh'

wlc_prompt_regex = r'(\((?:CAMP_|FC_|PICO_|SPA3_|coupang_)[a-zA-Z0-9\-_\.]+\)\s[>#])'
wlc_show_cmd_regex = r'(\((?:CAMP_|FC_|PICO_|SPA3_|coupang_)[a-zA-Z0-9\-_\.]+\)\s[>#])\s*sh'


def parse_data_cisco(data):
    match = False
    hostname = None
    contents = None

    if bool(re.search(cisco_show_cmd_regex, data)):
        prompt = re.search(cisco_show_cmd_regex, data).group(1)
        hostname = prompt.split("#")[0]
        a_start_idx = re.search(cisco_show_cmd_regex, data).start()
        b_start_idx = re.search(cisco_show_cmd_regex, data).end()

        if bool(re.search(cisco_prompt_regex, data[b_start_idx:])):
            prompt_start_idx = re.search(cisco_prompt_regex, data[b_start_idx:]).start() + b_start_idx
            # prompt_end_idx = re.search(cisco_prompt_regex, data[b_start_idx:]).end() + b_start_idx

            if re.search(cisco_prompt_regex, data[b_start_idx:]).group(1) == prompt:
                contents = data[a_start_idx:prompt_start_idx]
                data = data[prompt_start_idx:]
                match = True
            else:
                data = data[prompt_start_idx:]
                match = True

        else:
            data = data[b_start_idx:]
            match = True

    return match, hostname, contents, data


def parse_data_wlc(data):
    match = False
    hostname = None
    contents = None

    if bool(re.search(wlc_show_cmd_regex, data)):
        prompt = re.search(wlc_show_cmd_regex, data).group(1)
        print(prompt)
        hostname = prompt.split("#")[0].split(">")[0].replace(" ","")
        a_start_idx = re.search(wlc_show_cmd_regex, data).start()
        b_start_idx = re.search(wlc_show_cmd_regex, data).end()

        if bool(re.search(wlc_prompt_regex, data[b_start_idx:])):
            prompt_start_idx = re.search(wlc_prompt_regex, data[b_start_idx:]).start() + b_start_idx
            # prompt_end_idx = re.search(wlc_prompt_regex, data[b_start_idx:]).end() + b_start_idx
            if re.search(wlc_prompt_regex, data[b_start_idx:]).group(1) == prompt:
                contents = data[a_start_idx:prompt_start_idx]
                data = data[prompt_start_idx:]
                match = True
            else:
                data = data[prompt_start_idx:]
                match = True
        else:
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

    # file_list = ["C:\\Users\\Biber\\Desktop\\Coupang_Maintain\\20250516\\Log\\2025-05-15_10-51-05_gateway.txt"]
    for target in file_list:
        # with open("C:\\Users\\Biber\\Desktop\\Log\\3.log", 'r', encoding="utf-8") as f:
        print(target)
        with open(target, 'r', encoding="utf-8", errors='ignore') as f:
            match = True
            data = f.read()
            data1 = data
            data2 = data
            print(f"start cisco {target}")
            while match:
                match, hostname, contents, data1 = parse_data_cisco(data1)
                if match:
                    result_path = RESULT_PATH + f"{hostname}.txt"
                    try:
                        if contents is not None:
                            with open(result_path, "a") as outputFile:
                                outputFile.write(contents + "\n")
                    except Exception as e:
                        print(e)
                else:
                    break

            print(f"start wlc {target}")
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
                else:
                    break



