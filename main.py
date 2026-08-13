import sys
from PySide6.QtWidgets import QApplication
from ui.window import RedLineMainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = RedLineMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()