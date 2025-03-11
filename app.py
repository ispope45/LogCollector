import sys
import re
import json
import os
import time
import shutil
import pandas as pd

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject, Qt

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, AuthenticationException, SSHException

if getattr(sys, 'frozen', False):
    FILE_DIR = sys._MEIPASS
else:
    # 개발 환경에서 파일 경로 찾기
    FILE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_FILEPATH = os.path.join(FILE_DIR, 'Data/Collector_device_template.xlsx')
ICON_FILEPATH = os.path.join(FILE_DIR, 'icon.ico')

CMD_JSON = json.load(open(os.path.join(FILE_DIR, 'Data/command.json')))
PARSE_JSON = json.load(open(os.path.join(FILE_DIR, 'Data/parser.json')))


INIT_CMD = CMD_JSON["INIT"]

VALID_PARSE = PARSE_JSON["VALID_PARSE"]
INIT_PARSE = PARSE_JSON["INIT_PARSE"]

DEVICE_FORM = {
    "HOSTNAME":     0,
    "IPADDR":       1,
    "PORT":         2,
    "USERNAME":     3,
    "PASSWORD":     4,
    "ENABLE":       5,
    "PLATFORM":     6
}


class AppModel:
    def __init__(self):
        self.main_df = pd.DataFrame()

    def excel_to_df(self, excel_src):
        print("start excel_to_df")
        try:
            df = pd.read_excel(excel_src, usecols=range(0, 7))
            print(f"read dataframe \n {df}")
            print(f"{df.columns}\n{DEVICE_FORM.keys()}")
            if len(df.columns) == len(DEVICE_FORM.keys()):
                df.columns = DEVICE_FORM.keys()
                invalid_index, data = self.valid_dataframe(df)
                result = {"res": True}
            else:
                invalid_index = []
                data = pd.DataFrame()
                result = {"res": False}
            return invalid_index, data, result
        except Exception as e:
            print(f"excel_to_df Error : {e}")

    def valid_dataframe(self, df):
        df['PLATFORM'] = df['PLATFORM'].str.upper()
        # df = df.drop_duplicates(subset="IPADDR")
        df.loc[:, 'is_valid'] = df.apply(self.validate_row, axis=1)
        invalid_index = df.query("is_valid == False").index.tolist()
        df_cleaned = df[df['is_valid']].drop(columns=['is_valid'])
        return invalid_index, df_cleaned

    def validate_row(self, row):
        return all([
            self.is_valid_hostname(row['HOSTNAME']),
            self.is_valid_ipaddr(row['IPADDR']),
            self.is_valid_port(row['PORT']),
            self.is_valid_username(row['USERNAME']),
            self.is_valid_password(row['PASSWORD']),
            self.is_valid_enable(row['ENABLE']),
            self.is_valid_platform(row['PLATFORM']),
        ])

    @staticmethod
    def is_valid_hostname(hostname):
        return bool(re.match(VALID_PARSE["HOSTNAME"], str(hostname)))

    @staticmethod
    def is_valid_ipaddr(ipaddr):
        return bool(re.match(VALID_PARSE["IPADDR"], str(ipaddr)))

    @staticmethod
    def is_valid_port(port):
        return port in range(1, 65534)

    @staticmethod
    def is_valid_username(username):
        return bool(re.match(VALID_PARSE["USERNAME"], str(username)))

    @staticmethod
    def is_valid_password(password):
        return bool(re.match(VALID_PARSE["PASSWORD"], str(password)))

    @staticmethod
    def is_valid_enable(enable):
        return bool(re.match(VALID_PARSE["ENABLE"], str(enable)))

    @staticmethod
    def is_valid_platform(platform):
        return bool(re.match(VALID_PARSE["PLATFORM"], str(platform)))


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
        hostname = self.data[DEVICE_FORM["HOSTNAME"]]
        ipaddr = self.data[DEVICE_FORM["IPADDR"]]
        port = self.data[DEVICE_FORM["PORT"]]
        username = self.data[DEVICE_FORM["USERNAME"]]
        password = self.data[DEVICE_FORM["PASSWORD"]]
        enable = self.data[DEVICE_FORM["ENABLE"]]
        platform = self.data[DEVICE_FORM["PLATFORM"]]

        commands = CMD_JSON[platform]

        if platform == "CISCO_XE":
            dev_type = "cisco_xe"
        elif platform == "CISCO_NXOS":
            dev_type = "cisco_xe"
        elif platform == "CISCO_WLC_AIR":
            dev_type = "cisco_wlc"
        elif platform == "CISCO_WLC_CAT":
            dev_type = "cisco_xe"
        elif platform == "CISCO_IOS":
            dev_type = "cisco_ios"
        else:
            dev_type = "cisco_ios"

        try:
            target_device = {
                'device_type': dev_type,
                'host': ipaddr,
                'username': username,
                'password': password,
                'secret': enable,
                'port': int(port),
            }

            try:
                ssh = ConnectHandler(**target_device)
                ssh.enable(enable_pattern="#")

            except AuthenticationException:
                self.signals.log.emit(f"Authentication Failed: {hostname} ({ipaddr}:{port})")
                self.signals.logfile.emit(
                    f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,Authentication Failed")
                return
            except NetmikoTimeoutException:
                self.signals.log.emit(f"SSH Timeout: {hostname} ({ipaddr}:{port})")
                self.signals.logfile.emit(
                    f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,SSH Timeout")
                return
            except SSHException:
                self.signals.log.emit(f"SSH Connection Refused: {hostname} ({ipaddr}:{port})")
                self.signals.logfile.emit(
                    f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,SSH Connection Refused")
                return
            except Exception as e:
                self.signals.log.emit(f"Unknown Error: {hostname} ({ipaddr}) - {e}")
                self.signals.logfile.emit(
                    f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,Unknown Error")
                return

            result = {}
            if platform == "CISCO_XE":
                init_cmd = INIT_CMD["CISCO_XE"]
                init_parse = INIT_PARSE["CISCO_XE"]
            elif platform == "CISCO_NXOS":
                init_cmd = INIT_CMD["CISCO_NXOS"]
                init_parse = INIT_PARSE["CISCO_NXOS"]
            elif platform == "CISCO_IOS":
                init_cmd = INIT_CMD["CISCO_IOS"]
                init_parse = INIT_PARSE["CISCO_IOS"]
            elif platform == "CISCO_WLC_AIR":
                init_cmd = INIT_CMD["CISCO_WLC_AIR"]
                init_parse = INIT_PARSE["CISCO_WLC_AIR"]
            elif platform == "CISCO_WLC_CAT":
                init_cmd = INIT_CMD["CISCO_WLC_CAT"]
                init_parse = INIT_PARSE["CISCO_WLC_CAT"]
            else:
                self.signals.log.emit(f"Unsupported Platform: {hostname} ({ipaddr}:{port})")
                self.signals.logfile.emit(
                    f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,Unsupported Platform")
                raise Exception("Unsupported Platform")

            init_data = ssh.send_command(init_cmd)
            result["HOSTNAME"] = hostname
            result["IPADDR"] = ipaddr
            result["PLATFORM"] = platform

            if bool(re.search(init_parse["VERSION"], init_data)):
                result["VERSION"] = re.search(init_parse["VERSION"], init_data).group(1)
            else:
                result["VERSION"] = ""

            if bool(re.search(init_parse["SERIAL_NUMBER"], init_data)):
                result["SERIAL_NUMBER"] = re.search(init_parse["SERIAL_NUMBER"], init_data).group(1)
            else:
                result["SERIAL_NUMBER"] = ""

            if bool(re.search(init_parse["PID"], init_data)):
                result["PID"] = re.search(init_parse["PID"], init_data).group(1)
            else:
                result["PID"] = ""

            for command in commands:
                tmp = ssh.send_command(command)
                if tmp:
                    result[command] = tmp

            if platform == "CISCO_IOS":
                ssh.send_command("write memory")
            elif platform == "CISCO_XE":
                ssh.send_command("write memory")
            elif platform == "CISCO_NXOS":
                ssh.send_command("copy running-config startup-config")
            elif platform == "CISCO_WLC_AIR":
                output = ssh.send_command_timing('save config')
                if "save" in output.lower():
                    ssh.send_command_timing("y")  # 'y' 입력
            elif platform == "CISCO_WLC_CAT":
                ssh.send_command("write memory")

            self.make_report(result)
            self.signals.log.emit(f"Success: {hostname} ({ipaddr}:{port})")
        except Exception as e:
            self.signals.log.emit(f"Failed: {hostname} ({ipaddr}:{port}) - {e}")
            self.signals.logfile.emit(
                f"{hostname},{ipaddr},{port},{username},{password},{enable},{platform},Failed,Unknown Error")
        finally:
            self.signals.finished.emit()

    @staticmethod
    def make_report(data):
        now = time.localtime()
        cur_date = "%04d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
        result_path = os.getcwd() + f"/Collector_{cur_date}_{data['HOSTNAME']}({data['IPADDR']}).txt"
        try:
            with open(result_path, "w") as outputFile:
                outputFile.write(f'HOSTNAME: {data.pop("HOSTNAME")}\n'
                                 f'IPADDR: {data.pop("IPADDR")}\n'
                                 f'PLATFORM: {data.pop("PLATFORM")}\n'
                                 f'VERSION: {data.pop("VERSION")}\n'
                                 f'SERIAL_NUMBER: {data.pop("SERIAL_NUMBER")}\n'
                                 f'PID: {data.pop("PID")}\n\n'
                                 )
                for command, contents in data.items():
                    outputFile.write(f'+ COMMAND: {command}\n\n'
                                     f'============ START_CONTENTS ============\n\n'
                                     f'{contents}\n'
                                     f'============ END_CONTENTS ==============\n\n\n\n')
        except Exception as e:
            print(e)


class AppView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Collector(v1.0)")
        self.setWindowIcon(QIcon(ICON_FILEPATH))
        self.setMinimumSize(685, 600)

        # 💡 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 📁 Source File (HBoxLayout)
        source_layout = QHBoxLayout()
        self.label_source_file = QLabel("📂 Source File")
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.push_button_open = QPushButton("Open")

        source_layout.addWidget(self.label_source_file)
        source_layout.addWidget(self.line_edit)
        source_layout.addWidget(self.push_button_open)

        # 🔍 Device Source Label
        self.label_device_source = QLabel("🖥️ Device Source")

        # 📊 장치 목록 테이블
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Idx", "Hostname", "IP Address", "Platform"])
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        header = self.table_widget.horizontalHeader()
        total_width = self.table_widget.viewport().width()

        self.table_widget.setColumnWidth(0, int(total_width * 0.1))  # Idx (10%)
        self.table_widget.setColumnWidth(1, int(total_width * 0.4))  # Hostname (30%)
        self.table_widget.setColumnWidth(2, int(total_width * 0.3))  # IP Address (30%)
        self.table_widget.setColumnWidth(3, int(total_width * 0.2))  # Platform (20%)

        # 사용자가 조절할 수 있도록 설정
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)

        # Index col not visible
        self.table_widget.verticalHeader().setVisible(False)

        # ⏳ 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # ▶ 실행 버튼
        self.push_button_run = QPushButton("Run!")
        self.push_button_run.setFixedHeight(35)

        # 📜 Log Label
        self.label_log = QLabel("📝 Log")

        # 📖 로그 출력창
        self.text_browser = QTextBrowser()

        # 📌 하이퍼링크처럼 동작하는 QLabel 추가
        self.download_label = QLabel('Download Device Source Template', self)
        # self.download_label.setOpenExternalLinks(True)  # 링크 클릭 시 외부 웹페이지 열기
        self.download_label.setAlignment(Qt.AlignLeft)
        self.download_label.setStyleSheet("color: blue; font-size: 9pt;")
        self.download_label.setCursor(Qt.PointingHandCursor)

        # 📌 레이아웃에 추가
        main_layout.addLayout(source_layout)
        main_layout.addWidget(self.download_label)  # 하이퍼링크 QLabel 추가
        main_layout.addWidget(self.label_device_source)
        main_layout.addWidget(self.table_widget, 2)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.push_button_run)
        main_layout.addWidget(self.label_log)
        main_layout.addWidget(self.text_browser, 1)

        self.setLayout(main_layout)
        self.apply_styles()  # 💅 스타일 적용

    def apply_styles(self):
        """QSS 스타일 적용 (밝은 테마)"""
        self.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    color: #333;
                    font-size: 12pt;
                }
                QLabel {
                    font-weight: bold;
                    font-size: 11pt;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    padding: 5px;
                    border-radius: 4px;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    padding: 6px;
                    border-radius: 5px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:pressed {
                    background-color: #004C8C;
                }
                QTableWidget {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    gridline-color: #ddd;
                }
                QHeaderView::section {
                    background-color: #e9ecef;
                    padding: 4px;
                    border: 1px solid #ccc;
                    font-size: 10pt;
                }
                QTextBrowser {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    padding: 5px;
                    border-radius: 4px;
                    font-size: 10pt;
                }
                QProgressBar {
                    border: 1px solid #ccc;
                    background-color: #e9ecef;
                    height: 12px;
                    border-radius: 6px;
                    text-align: center;
                    font-size: 10pt;
                }
                QProgressBar::chunk {
                    background-color: #0078D7;
                    border-radius: 6px;
                }
            """)


class AppController:
    def __init__(self,  main_view, main_model):
        self.model = main_model
        self.view = main_view

        self.view.push_button_open.clicked.connect(self.load_file)
        self.view.push_button_run.clicked.connect(self.run_command)

        self.view.download_label.mousePressEvent = self.on_download_label_click

        self.thread_pool = QThreadPool()

        self.maximum_task_cnt = 0
        self.current_task_cnt = 0

    def on_download_label_click(self, event):
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Save File", "Collector_device_template.xlsx", "XLSX 파일 (*.xlsx)")

        if file_path:
            shutil.copy2(TEMPLATE_FILEPATH, file_path)

    def load_file(self):
        print(f"start load_file")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view, "파일 열기", "", "XLSX 파일 (*.xlsx)", options=options)
        if file_path:
            print(f"read file_path: {file_path}")
            invalid_index, data, result = self.model.excel_to_df(file_path)
            if result["res"]:
                data_list = data[['HOSTNAME', 'IPADDR', 'PLATFORM']].values.tolist()

                # Device Source database view
                self.view.table_widget.setRowCount(len(data_list))
                for row_idx, row_data in enumerate(data_list):
                    self.fill_table_widget(row_data, row_idx)

                for index in invalid_index:
                    self.logging_text(f"Invalid row at index {index + 2}")
                self.view.line_edit.setText(file_path)
                self.model.main_df = data

            else:
                self.show_alert("Invalid file format!")

    def fill_table_widget(self, row, row_idx):
        item = QTableWidgetItem(str(row_idx + 1))
        font = QFont()
        font.setPointSize(10)  # 폰트 크기 10으로 설정
        item.setFont(font)
        item.setTextAlignment(Qt.AlignCenter)  # 🌟 가운데 정렬 적용
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 수정 불가
        self.view.table_widget.setItem(row_idx, 0, item)

        for col_idx, value in enumerate(row):
            item = QTableWidgetItem(value)
            font = QFont()
            font.setPointSize(10)  # 폰트 크기 10으로 설정
            item.setFont(font)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 수정 불가
            self.view.table_widget.setItem(row_idx, col_idx + 1, item)

    def run_command(self):
        if len(self.model.main_df) == 0:
            self.show_alert("Not selected source.")
            return

        self.view.push_button_run.setEnabled(False)
        self.view.progress_bar.setValue(0)
        self.maximum_task_cnt = len(self.model.main_df)
        self.current_task_cnt = 0

        # 작업 시작 전 디버깅 로그 추가
        print(f"Starting {self.maximum_task_cnt} tasks...")
        self.init_logging()

        for row in self.model.main_df.itertuples(index=False, name=None):
            worker = Worker(row)
            worker.signals.log.connect(self.logging_text)
            worker.signals.logfile.connect(self.logging_file)
            worker.signals.finished.connect(self.task_finished)

            self.thread_pool.start(worker)  # QThreadPool에서 실행

        # 작업 종료 후 디버깅 로그 추가
        print("All tasks started.")

    def task_finished(self):
        self.current_task_cnt += 1
        print(f"Task finished. {self.current_task_cnt}/{self.maximum_task_cnt} tasks completed.")
        int_value = int((self.current_task_cnt / self.maximum_task_cnt) * 100)
        self.view.progress_bar.setValue(int_value)
        if self.current_task_cnt == self.maximum_task_cnt:
            self.view.progress_bar.setValue(100)
            self.view.push_button_run.setEnabled(True)  # 작업 완료 후 버튼 활성화

    def logging_text(self, msg):
        self.view.text_browser.append(msg)

    @staticmethod
    def init_logging():
        now = time.localtime()
        cur_date = "%04d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
        result_path = os.getcwd() + f"/Collector_{cur_date}_logging.csv"
        try:
            with open(result_path, "w") as outputFile:
                outputFile.write("DATE,HOSTNAME,IPADDR,PORT,USERNAME,PASSWORD,ENABLE,PLATFORM,STATUS,REASON\n")
        except Exception as e:
            print(e)

    @staticmethod
    def logging_file(data):
        now = time.localtime()
        cur_date = "%04d%02d%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
        cur_time = "%02d:%02d:%02d" % (now.tm_hour, now.tm_min, now.tm_sec)
        result_path = os.getcwd() + f"/Collector_{cur_date}_logging.csv"
        try:
            with open(result_path, "a") as outputFile:
                outputFile.write(f"{cur_date}_{cur_time},{data}\n")
        except Exception as e:
            print(e)

    @staticmethod
    def show_alert(msg):
        try:
            box = QMessageBox()
            box.setWindowTitle("Error")
            box.setText(msg)
            box.setIcon(QMessageBox.Critical)
            box.setStandardButtons(QMessageBox.Ok)  # 확인 버튼 추가
            box.exec_()
        except Exception as e:
            print(f"Failed to show alert: {e}")


if __name__ == "__main__":
    main_app = QApplication(sys.argv)
    main_view = AppView()
    main_model = AppModel()

    control = AppController(main_view, main_model)
    main_view.show()
    sys.exit(main_app.exec_())
