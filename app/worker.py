import os
import time
import re
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject
from netmiko import ConnectHandler, ReadTimeout
from netmiko.exceptions import NetmikoTimeoutException, AuthenticationException, SSHException, ConnectionException

from .constants import CMD_JSON, INIT_CMD, INIT_PARSE, PLATFORM_TO_NETMIKO, DEVICE_FORM, ROOT_DIR


class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    logfile = pyqtSignal(str)
    finished = pyqtSignal()


class Worker(QRunnable):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.signals = WorkerSignals()
        self.parse_data = {}

    def run(self):
        index, hostname, ipaddr, port, username, password, enable, platform = (
            self.data[DEVICE_FORM[k]] for k in ["INDEX","HOSTNAME","IPADDR","PORT","USERNAME","PASSWORD","ENABLE","PLATFORM"]
        )

        commands = CMD_JSON.get(platform, [])
        dev_type = PLATFORM_TO_NETMIKO.get(platform, "cisco_ios")

        ssh = None
        try:
            target_device = {
                'device_type': dev_type, 'host': ipaddr, 'username': username,
                'password': password, 'secret': enable, 'port': int(port),
                'conn_timeout': 10, 'global_delay_factor': 2
            }

            for attempt in range(3):
                try:
                    ssh = ConnectHandler(**target_device, allow_auto_change=False)
                    try:
                        out = ssh.send_command_timing("\n", delay_factor=2)
                        if "ser:" in out:
                            out += ssh.send_command_timing(target_device['username'])
                        if "assword:" in out:
                            out += ssh.send_command_timing(target_device['password'])
                        try:
                            ssh.enable()
                        except Exception:
                            ssh.enable(enable_pattern=r"[>#]")
                    except Exception:
                        self.signals.log.emit(f"SSH Connection Failed: {hostname} ({ipaddr}:{port})")
                    break
                except NetmikoTimeoutException:
                    if attempt < 2:
                        time.sleep(5)
                        target_device['conn_timeout'] *= 2
                        continue
                    raise
                except AuthenticationException:
                    self._fail("Authentication Failed", index, hostname, ipaddr, port, username, password, enable, platform); return
                except SSHException:
                    self._fail("SSH Connection Refused", index, hostname, ipaddr, port, username, password, enable, platform); return
                except ConnectionException:
                    self._fail("Connection Failed", index, hostname, ipaddr, port, username, password, enable, platform); return
                except Exception as e:
                    self._fail(f"Unknown Error: {e}", index, hostname, ipaddr, port, username, password, enable, platform); return

            if platform not in INIT_CMD:
                self._fail("Unsupported Platform", index, hostname, ipaddr, port, username, password, enable, platform); return

            init_cmd = INIT_CMD[platform]
            init_parse = INIT_PARSE[platform]

            init_data = ""
            for cmd in init_cmd:
                init_data += self.execute_command(ssh, cmd)

            result = {
                "INDEX": index,
                "HOSTNAME": hostname,           # 원 코드 버그 수정: HOSTNAME 포함
                "IPADDR": ipaddr,
                "PLATFORM": platform
            }

            for key in ["VERSION", "SERIAL_NUMBER", "PID", "HOSTNAME"]:
                m = re.search(init_parse[key], init_data)
                result[key] = m.group(1) if m else ""

                if result[key] == "":
                    self.signals.log.emit(f"Initial data({key}) not found: {index}_{hostname} ({ipaddr}:{port})")
                    self.signals.logfile.emit(
                        f"{index},{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Initial data({key}) not found")
                    return

            for command in commands:
                tmp = self.execute_command(ssh, command)
                if tmp:
                    result[command] = tmp

            # save
            self._save_config(platform, ssh)
            self.make_report(result)

            self.signals.log.emit(f"Success: {index}_{hostname} ({ipaddr}:{port})")
            self.signals.logfile.emit(f"{index},{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Success")
        except Exception as e:
            self.signals.log.emit(f"Failed: {index}_{hostname} ({ipaddr}:{port}) - {e}")
            self.signals.logfile.emit(f"{index},{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,Connection Failed/Unknown Error")
        finally:
            try:
                if ssh: ssh.disconnect()
            except Exception: pass
            self.signals.finished.emit()

    def execute_command(self, ssh, command, retries=5, delay=2):
        if not command:
            return ""
        rd_timeout = 300 if command in ["show ap wlan summary", "show wireless client summary"] else 60
        for attempt in range(retries):
            try:
                return ssh.send_command(command, delay_factor=5, read_timeout=rd_timeout*(attempt+1))
            except ReadTimeout:
                self.signals.log.emit(f"Command Timeout Error: {ssh.host} '{command}' - Retrying in {delay} seconds..")
                time.sleep(delay)
            except Exception as e:
                self.signals.log.emit(f"Error executing Command: {ssh.host} '{command}': {e}")
                break
        return ""

    @staticmethod
    def _save_config(platform, ssh):
        if platform in ("CISCO_IOS", "CISCO_XE", "CISCO_WLC_CAT"):
            ssh.send_command_timing("write memory", delay_factor=3)
        elif platform == "CISCO_NXOS":
            ssh.send_command_timing("copy running-config startup-config", delay_factor=3)
        elif platform == "CISCO_WLC_AIR":
            out = ssh.send_command_timing("save config", delay_factor=3)
            if "save" in out.lower():
                ssh.send_command_timing("y")

    @staticmethod
    def make_report(data):
        now = time.localtime()
        cur_date = f"{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}"
        path = os.path.join(ROOT_DIR, f"Collector_{cur_date}_{data['INDEX']}_({data['HOSTNAME']})[{data['IPADDR']}].txt")
        try:
            head = (
                f"INDEX: {data['INDEX']}\n"
                f"HOSTNAME: {data['HOSTNAME']}\n"
                f"IPADDR: {data['IPADDR']}\n"
                f"PLATFORM: {data['PLATFORM']}\n"
                f"VERSION: {data.get('VERSION','')}\n"
                f"SERIAL_NUMBER: {data.get('SERIAL_NUMBER','')}\n"
                f"PID: {data.get('PID','')}\n\n"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(head)
                for command, contents in data.items():
                    if command in {"INDEX","HOSTNAME","IPADDR","PLATFORM","VERSION","SERIAL_NUMBER","PID"}:
                        continue
                    f.write(f"+ COMMAND: {command}\n\n"
                            "============ START_CONTENTS ============\n"
                            f"{contents}\n"
                            "============ END_CONTENTS ==============\n\n\n\n")
        except Exception as e:
            print(e)

    def _fail(self, reason, index, hostname, ipaddr, port, username, password, enable, platform):
        self.signals.log.emit(f"{reason}: {hostname} ({ipaddr}:{port})")
        self.signals.logfile.emit(f"{index},{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,{reason}")
