from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from .constants import APP_VERSION, ICON_FILEPATH, TEMPLATE_FILEPATH


class AppView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_VERSION)
        self.setWindowIcon(QIcon(ICON_FILEPATH))
        self.setMinimumSize(685, 600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(12)

        source_layout = QHBoxLayout()
        self.label_source_file = QLabel("📂 Source File")
        self.line_edit = QLineEdit(); self.line_edit.setReadOnly(True)
        self.push_button_open = QPushButton("Open")
        source_layout.addWidget(self.label_source_file)
        source_layout.addWidget(self.line_edit)
        source_layout.addWidget(self.push_button_open)

        self.label_device_source = QLabel("🖥️ Device Source")

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Index","Hostname","IP Address","Platform"])
        self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        header = self.table_widget.horizontalHeader()
        total_width = self.table_widget.viewport().width()
        self.table_widget.setColumnWidth(0, int(total_width*0.1))
        self.table_widget.setColumnWidth(1, int(total_width*0.4))
        self.table_widget.setColumnWidth(2, int(total_width*0.3))
        self.table_widget.setColumnWidth(3, int(total_width*0.2))
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        self.table_widget.verticalHeader().setVisible(False)

        self.progress_bar = QProgressBar(); self.progress_bar.setValue(0)
        self.push_button_run = QPushButton("Run!"); self.push_button_run.setFixedHeight(35)

        self.label_log = QLabel("📝 Log")
        self.text_browser = QTextBrowser()

        self.download_label = QLabel('Download Device Source Template', self)
        self.download_label.setAlignment(Qt.AlignLeft)
        self.download_label.setStyleSheet("color: blue; font-size: 9pt;")
        self.download_label.setCursor(Qt.PointingHandCursor)

        main_layout.addLayout(source_layout)
        main_layout.addWidget(self.download_label)
        main_layout.addWidget(self.label_device_source)
        main_layout.addWidget(self.table_widget, 2)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.push_button_run)
        main_layout.addWidget(self.label_log)
        main_layout.addWidget(self.text_browser, 1)
        self.setLayout(main_layout)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color:#f8f9fa; color:#333; font-size:12pt; }
            QLabel { font-weight:bold; font-size:11pt; }
            QLineEdit { background:#fff; border:1px solid #ccc; padding:5px; border-radius:4px; }
            QPushButton { background:#0078D7; color:#fff; padding:6px; border-radius:5px; font-weight:bold; border:none; }
            QPushButton:hover { background:#005A9E; }
            QPushButton:pressed { background:#004C8C; }
            QTableWidget { background:#fff; border:1px solid #ccc; gridline-color:#ddd; }
            QHeaderView::section { background:#e9ecef; padding:4px; border:1px solid #ccc; font-size:10pt; }
            QTextBrowser { background:#fff; border:1px solid #ccc; padding:5px; border-radius:4px; font-size:10pt; }
            QProgressBar { border:1px solid #ccc; background:#e9ecef; height:12px; border-radius:6px; text-align:center; font-size:10pt; }
            QProgressBar::chunk { background:#0078D7; border-radius:6px; }
        """)
