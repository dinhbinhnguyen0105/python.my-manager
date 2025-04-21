# src/utils/file_handler.py
import os
import sys
import shutil
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)


def get_images_in_directory(image_dir):
    if not os.path.exists(image_dir):
        return []
    images = []
    for file in os.listdir(image_dir):
        if file.endswith((".png", ".jpg", ".jpeg")):
            images.append(os.path.join(image_dir, file))
    return images


def delete_dir(dir_path):
    dir_path = os.path.abspath(dir_path)
    if not os.path.exists(dir_path):
        logger.warning(f"directory '{dir_path}' does not exist.".lower())
        return True
    try:
        shutil.rmtree(dir_path)
        logger.info(f"successfully deleted directory: '{dir_path}'".lower())
        return True
    except OSError as e:
        logger.error(f"error deleting directory '{dir_path}': {e}".lower())
        return False


def copy_files(sources, destination, id):
    os.makedirs(destination, exist_ok=True)
    destination_img_num = len(get_images_in_directory(destination))

    for index, file in enumerate(sources):
        _, extension = os.path.splitext(file)
        file_name = f"{id}_{index + destination_img_num}{extension}"
        destination_path = os.path.join(destination, file_name)
        try:
            shutil.copy2(file, destination_path)
        except FileNotFoundError:
            print(f"Error: File not found: {file}")
            return False
        except Exception as e:
            print(f"Error copying {file}: {e}")
            return False
    return True
