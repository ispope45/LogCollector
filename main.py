import sys
from PyQt5.QtWidgets import QApplication
from app import AppView, AppModel, AppController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = AppView()
    model = AppModel()
    controller = AppController(view, model)
    view.show()
    sys.exit(app.exec_())
