import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStackedWidget

from billeUI import welcomescreen, ICONSPATH

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(ICONSPATH, "wallet.png")))
    widget = QStackedWidget()
    main_window = welcomescreen.WelcomeScreen(widget=widget)
    widget.addWidget(main_window)
    widget.show()
    sys.exit(app.exec())
