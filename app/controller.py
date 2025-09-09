import os, time, shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThreadPool
from .model import AppModel
from .view import AppView
from .worker import Worker
from .constants import TEMPLATE_FILEPATH, ROOT_DIR

# Parser PARSE Form 적용
from Parser import coupang_parse_template


class AppController:
    def __init__(self, main_view:AppView, main_model:AppModel):
        self.model = main_model
        self.view = main_view

        self.view.push_button_open.clicked.connect(self.load_file)
        self.view.push_button_run.clicked.connect(self.run_command)
        self.view.download_label.mousePressEvent = self.on_download_label_click

        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(8)

        self.maximum_task_cnt = 0
        self.current_task_cnt = 0

    # Coupang Parse 적용
    @staticmethod
    def parsing_coupang():
        coupang_parse_template.report(ROOT_DIR)

    def on_download_label_click(self, event):
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Save File", "Collector_device_template.xlsx", "XLSX 파일 (*.xlsx)")
        if file_path:
            shutil.copy2(TEMPLATE_FILEPATH, file_path)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.view, "파일 열기", "", "XLSX 파일 (*.xlsx)", options=options)
        if not file_path: return
        invalid_index, data, result = self.model.excel_to_df(file_path)
        if not result["res"]:
            self.show_alert("Invalid file format!"); return

        data_list = data[["INDEX", "HOSTNAME", "IPADDR", "PLATFORM"]].values.tolist()
        self.view.table_widget.setRowCount(len(data_list))
        for row_idx, row_data in enumerate(data_list):
            self.fill_table_widget(row_data, row_idx)

        for idx in invalid_index:
            self.logging_text(f"Invalid row at index {idx + 1}")
        self.view.line_edit.setText(file_path)
        self.model.main_df = data

    def fill_table_widget(self, row, row_idx):
        for col_idx, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            font = QFont(); font.setPointSize(10); item.setFont(font)
            if col_idx == 0: item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.view.table_widget.setItem(row_idx, col_idx, item)

    def run_command(self):
        if len(self.model.main_df) == 0:
            self.show_alert("Not selected source.")
            return

        self.view.push_button_run.setEnabled(False)
        self.view.push_button_run.setText("Started...")
        self.view.progress_bar.setValue(0)
        self.maximum_task_cnt = len(self.model.main_df)
        self.current_task_cnt = 0

        self.init_logging()
        self.logging_text("Starting Log Collector")
        for row in self.model.main_df.itertuples(index=False, name=None):
            worker = Worker(row)
            worker.signals.log.connect(self.logging_text)
            worker.signals.logfile.connect(self.logging_file)
            worker.signals.finished.connect(self.task_finished)
            self.thread_pool.start(worker)
            time.sleep(0.1)

    def task_finished(self):
        self.current_task_cnt += 1
        pct = int((self.current_task_cnt / self.maximum_task_cnt) * 100)
        self.view.progress_bar.setValue(pct)
        if self.current_task_cnt == self.maximum_task_cnt:
            self.view.progress_bar.setValue(100)
            self.logging_text("Collecting finished!")
            time.sleep(10)

            self.parsing_coupang()
            self.logging_text("Generated Collector Log Summary!")

            self.view.push_button_run.setEnabled(True)
            self.view.push_button_run.setText("Run!")

    def logging_text(self, msg):
        self.view.text_browser.append(msg)
        now = time.localtime()
        cur_date = f"{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}"
        cur_time = f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"
        path = os.path.join(ROOT_DIR, f"Collector_raw_{cur_date}.log")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{cur_date} {cur_time} msg : {msg}\n")
        except Exception as e:
            print(e)

    @staticmethod
    def init_logging():
        now = time.localtime()
        cur_date = f"{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}"
        path = os.path.join(ROOT_DIR, f"Collector_Failed_{cur_date}.csv")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("DATE,INDEX,HOSTNAME,IPADDR,PORT,USERNAME,PASSWORD,ENABLE,PLATFORM,STATUS,REASON\n")
        except Exception as e:
            print(e)

    @staticmethod
    def logging_file(data):
        now = time.localtime()
        cur_date = f"{now.tm_year:04d}{now.tm_mon:02d}{now.tm_mday:02d}"
        cur_time = f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}"
        path = os.path.join(ROOT_DIR, f"Collector_Failed_{cur_date}.csv")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{cur_date}_{cur_time},{data}\n")
        except Exception as e:
            print(e)

    @staticmethod
    def show_alert(msg):
        try:
            box = QMessageBox()
            box.setWindowTitle("Error")
            box.setText(msg)
            box.setIcon(QMessageBox.Critical)
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
        except Exception as e:
            print(f"Failed to show alert: {e}")
