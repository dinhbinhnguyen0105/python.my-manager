import sys
import time
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QProgressBar,
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QMutex, Qt


# Bước 1: Tạo class Worker kế thừa từ QObject
# Class này chứa logic thực hiện công việc nặng
class Worker(QObject):
    # Định nghĩa các signal để giao tiếp với luồng chính
    # signal_progress sẽ phát ra một số nguyên (tiến độ)
    # signal_finished sẽ phát ra khi công việc hoàn thành
    signal_progress = pyqtSignal(int)
    signal_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._isRunning = True
        self._mutex = QMutex()  # Sử dụng mutex để đồng bộ hóa việc truy cập _isRunning

    def do_work(self):
        """
        Phương thức này chứa công việc cần thực hiện trong luồng phụ.
        """
        print("Worker: Bắt đầu công việc...")
        total_steps = 100
        for i in range(total_steps + 1):
            self._mutex.lock()  # Khóa mutex trước khi kiểm tra cờ
            if not self._isRunning:
                self._mutex.unlock()
                print("Worker: Công việc bị hủy.")
                break  # Thoát vòng lặp nếu cờ hủy được đặt
            self._mutex.unlock()  # Mở khóa mutex

            # Giả lập công việc tốn thời gian
            time.sleep(0.05)

            # Phát tín hiệu báo cáo tiến độ
            # signal_progress.emit(i) chỉ có thể được gọi từ luồng mà Worker đang sống (luồng phụ)
            self.signal_progress.emit(
                int((i / total_steps) * 100)
            )  # Phát tín hiệu phần trăm

        print("Worker: Công việc hoàn thành.")
        # Phát tín hiệu báo công việc đã xong
        self.signal_finished.emit()

    def stop(self):
        """
        Phương thức để yêu cầu dừng công việc.
        """
        print("Worker: Nhận yêu cầu dừng.")
        self._mutex.lock()
        self._isRunning = False
        self._mutex.unlock()


# Bước 2: Tạo cửa sổ chính kế thừa từ QMainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ví dụ sử dụng QThread trong PyQt6")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Nhấn nút để bắt đầu tác vụ.")
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )  # PyQt6 dùng Qt.AlignmentFlag
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.start_button = QPushButton("Bắt đầu tác vụ")
        # Kết nối nút bấm với slot start_task
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Dừng tác vụ")
        self.stop_button.setEnabled(False)  # Vô hiệu hóa nút dừng ban đầu
        self.stop_button.clicked.connect(self.stop_task)
        layout.addWidget(self.stop_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Khởi tạo self.thread và self.worker là None ban đầu
        self.thread = None
        self.worker = None

    def start_task(self):
        """
        Slot được gọi khi nút "Bắt đầu tác vụ" được nhấn.
        Khởi tạo và chạy luồng.
        """
        if self.thread is not None and self.thread.isRunning():
            print("Tác vụ đã đang chạy.")
            return  # Không chạy lại nếu đã có luồng đang chạy

        print("GUI: Chuẩn bị bắt đầu tác vụ...")
        self.label.setText("Đang chạy tác vụ...")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)  # Vô hiệu hóa nút start
        self.stop_button.setEnabled(True)  # Kích hoạt nút stop

        # Bước 3: Tạo QThread và Worker
        self.thread = QThread()
        self.worker = Worker()

        # Bước 4: Di chuyển worker sang luồng mới
        self.worker.moveToThread(self.thread)
        print(
            f"GUI: Worker đã được di chuyển sang thread: {self.thread.currentThreadId()}"
        )

        # Bước 5: Kết nối các tín hiệu và slot
        # Kết nối signal 'started' của thread với phương thức do_work của worker
        self.thread.started.connect(self.worker.do_work)

        # Kết nối signal 'signal_progress' của worker với slot cập nhật GUI
        # Việc kết nối từ luồng phụ về luồng chính được Qt/PyQt xử lý an toàn
        self.worker.signal_progress.connect(self.update_progress_label)
        self.worker.signal_progress.connect(self.progress_bar.setValue)

        # Kết nối signal 'signal_finished' của worker với slot xử lý khi xong
        self.worker.signal_finished.connect(self.task_finished)

        # Kết nối signal 'finished' của thread để dọn dẹp worker và thread
        self.thread.finished.connect(
            self.worker.deleteLater
        )  # Xóa worker khi thread kết thúc
        self.thread.finished.connect(self.thread.deleteLater)  # Xóa thread object

        # Bắt đầu luồng
        self.thread.start()
        print("GUI: Thread đã bắt đầu.")

    def stop_task(self):
        """
        Slot được gọi khi nút "Dừng tác vụ" được nhấn.
        Yêu cầu worker dừng công việc VÀ yêu cầu thread thoát.
        """
        if (
            self.worker is not None and self.thread is not None
        ):  # Thêm kiểm tra self.thread
            print("GUI: Yêu cầu worker dừng và thread thoát...")
            self.worker.stop()  # Yêu cầu logic công việc dừng (trong luồng phụ)
            self.thread.quit()  # Yêu cầu vòng lặp sự kiện của thread thoát (trong luồng phụ)

            # Optional: Có thể thêm thread.wait() ở đây để chờ luồng kết thúc TRƯỚC khi phương thức này trả về.
            # Tuy nhiên, việc này có thể làm chặn luồng GUI nếu worker không phản hồi nhanh.
            # Thông thường, việc kết nối thread.finished với deleteLater là đủ an toàn.
            # self.thread.wait(5000) # Chờ tối đa 5 giây (thay đổi tùy ý)
            # print("GUI: Đã chờ thread kết thúc (tùy chọn).")
        else:
            print("GUI: Không có tác vụ nào đang chạy để dừng.")

    # Các slot này chạy trong luồng GUI chính vì chúng được kết nối từ signal của worker (ở luồng phụ)
    def update_progress_label(self, progress):
        """
        Slot để cập nhật nhãn tiến độ. Chạy trên luồng GUI.
        """
        self.label.setText(f"Tiến độ: {progress}%")
        # self.progress_bar.setValue(progress) # Cũng có thể cập nhật progress bar ở đây

    def task_finished(self):
        """
        Slot được gọi khi tác vụ trong luồng phụ hoàn thành. Chạy trên luồng GUI.
        """
        print("GUI: Tác vụ đã hoàn thành hoặc bị dừng.")
        self.label.setText("Tác vụ hoàn thành!")
        self.progress_bar.setValue(100)  # Đảm bảo thanh tiến độ đầy khi xong
        self.start_button.setEnabled(True)  # Kích hoạt lại nút start
        self.stop_button.setEnabled(False)  # Vô hiệu hóa nút stop

        # Dọn dẹp tham chiếu để chuẩn bị cho lần chạy tiếp theo
        self.thread = None
        self.worker = None

    def closeEvent(self, event):
        """
        Xử lý sự kiện đóng cửa sổ. Đảm bảo luồng phụ được dừng trước khi thoát ứng dụng.
        """
        print("GUI: Đóng cửa sổ. Kiểm tra và dừng thread...")
        if self.thread is not None and self.thread.isRunning():
            print("GUI: Thread đang chạy, yêu cầu dừng...")
            self.stop_task()  # Yêu cầu worker dừng
            self.thread.quit()  # Yêu cầu luồng thoát vòng lặp sự kiện của nó
            self.thread.wait(5000)  # Chờ luồng kết thúc, tối đa 5 giây
            if self.thread.isRunning():
                print("GUI: Thread vẫn đang chạy sau khi chờ, buộc kết thúc.")
                self.thread.terminate()  # Buộc kết thúc luồng (nên tránh nếu có thể)
                self.thread.wait()  # Chờ terminate xong

        print("GUI: Thread đã dừng hoặc không chạy. Cho phép đóng cửa sổ.")
        super().closeEvent(event)


# Phần chạy ứng dụng
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
