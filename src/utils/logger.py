import inspect, os


def log(message):
    caller_frame_record = inspect.stack()[1]
    frame = caller_frame_record[0]  # Lấy đối tượng frame
    info = inspect.getframeinfo(frame)

    filename = os.path.basename(info.filename)
    line_number = info.lineno

    print(f"[{filename}:{line_number}] {message}")
