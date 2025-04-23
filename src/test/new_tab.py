import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Thêm Tab Mới bằng Tab 'New action'")
        self.setGeometry(100, 100, 500, 300)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Add some initial tabs
        self.add_content_tab("Tab Gốc 1")
        self.add_content_tab("Tab Gốc 2")

        # Add the special "New action" tab
        self.add_new_action_tab()

        # Connect the tabBarClicked signal to a slot
        self.tab_widget.tabBarClicked.connect(self.on_tab_bar_clicked)

        self.tab_count = 2  # Start counting tabs from the initial ones

    def add_content_tab(self, title):
        """Adds a regular content tab."""
        new_tab = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"Nội dung của {title}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        new_tab.setLayout(layout)
        # Add the tab normally at the end (before the "New action" tab if it exists)
        index = self.tab_widget.addTab(new_tab, title)
        return index

    def add_new_action_tab(self):
        """Adds the special 'New action' tab."""
        new_action_widget = QWidget()  # This widget can be empty or contain some info
        # We add it at the end for now, and will insert new tabs before it
        self.tab_widget.addTab(new_action_widget, "New action")

    def on_tab_bar_clicked(self, index):
        """Handles the tab bar clicked signal."""
        # Get the title of the clicked tab
        clicked_tab_title = self.tab_widget.tabText(index)

        # Check if the clicked tab is the "New action" tab
        if clicked_tab_title == "New action":
            self.tab_count += 1
            new_tab_title = f"Tab Mới {self.tab_count}"
            # Insert the new tab just before the "New action" tab
            self.insert_content_tab_before_index(index, new_tab_title)
            # Optionally, switch to the newly added tab
            self.tab_widget.setCurrentIndex(index)  # The new tab is now at 'index'

    def insert_content_tab_before_index(self, target_index, title):
        """Inserts a content tab before a specific index."""
        new_tab = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"Nội dung của {title}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        new_tab.setLayout(layout)
        # Insert the new tab at the target_index
        self.tab_widget.insertTab(target_index, new_tab, title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
