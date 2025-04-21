import sys
from PyQt6.QtWidgets import QApplication

from .app import MainWindow
from src.database.user_database import initialize_user_db
from src.database.re_database import initialize_re_db

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not initialize_re_db():
        print("Failed initialize re db")
        exit()
    if not initialize_user_db():
        print("Failed initialize user db")
        exit()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
