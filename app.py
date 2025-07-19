import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStackedWidget, QMainWindow

from billeUI import welcomescreen, ICONSPATH


class BilleterApp(QMainWindow):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setWindowTitle("BilleterApp")
        self.setCentralWidget(stacked_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(ICONSPATH, "wallet2.png")))
    app.setApplicationName("BilleterApp")
    app.setApplicationDisplayName("BilleterApp")
    widget = QStackedWidget()
    main_window = welcomescreen.WelcomeScreen(widget=widget)
    widget.addWidget(main_window)

    window = BilleterApp(widget)
    window.show()
    sys.exit(app.exec())
