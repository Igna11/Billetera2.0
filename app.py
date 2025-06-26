import os
import sys

from PyQt5.QtWidgets import QApplication, QStackedWidget

from billeUI import welcomescreen

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QStackedWidget()
    main_window = welcomescreen.WelcomeScreen(widget=widget)
    widget.addWidget(main_window)
    widget.show()
    app.exec()
