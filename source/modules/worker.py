import datetime
import logging
import os
import time
from abc import abstractclassmethod
from queue import Queue
from threading import Thread
from typing import Callable

import boto3
from botocore.exceptions import ParamValidationError
from watchdog.events import FileSystemEventHandler

log_handler_file_handler = logging.getLogger("app").getChild("file_handler")
log_handler_change_check = logging.getLogger("app").getChild("change_check")
log_handler_s3_upload = logging.getLogger("app").getChild("s3_upload")


class FileHandler(FileSystemEventHandler):
    def __init__(self, out_store):
        self.out_store = out_store

    def on_modified(self, event):
        path = event.src_path
        self.task(path, event)

    def on_created(self, event):
        path = event.src_path
        self.task(path, event)

    def on_moved(self, event):
        path = event.dest_path
        self.task(path, event)

    def task(self, path, event):
        if not event.is_directory and not os.path.basename(path).startswith("."):
            item = {
                "size": os.path.getsize(path),
                "time": datetime.datetime.now().timestamp(),
            }
            self.out_store[path] = item
            log_handler_file_handler.debug(
                f"'{path}' was modified. Size: {os.path.getsize(path)}, Time: {datetime.datetime.now().timestamp()}."  # noqa: E501
            )


class BaseWorker(Thread):
    def __init__(self, in_queue: Queue):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.monitoring = False

    def run(self):
        self.monitoring = True
        while self.monitoring:
            if self.in_queue.empty():
                time.sleep(1)
            else:
                item = self.in_queue.get()
                self.func(item)
        else:
            print("stop")

    def stop(self):
        self.monitoring = False

    @abstractclassmethod
    def func(self):
        pass


class ChangeCheckWorker(Thread):
    def __init__(self, in_store, out_queue):
        super().__init__(daemon=True)
        self.in_store = in_store
        self.out_queue = out_queue
        self.monitoring = False

    def run(self):
        self.monitoring = True
        while self.monitoring:
            path_list = [path for path in self.in_store.keys()]
            for path in path_list:
                item = self.in_store[path]
                current_time = datetime.datetime.now().timestamp()
                if current_time - item["time"] > 3:
                    try:
                        if os.path.getsize(path) == item["size"]:
                            self.out_queue.put(path)
                            del self.in_store[path]
                    except FileNotFoundError as e:
                        log_handler_change_check.error(f"{str(e)}, path: {path}")
                        del self.in_store[path]
            time.sleep(1)
        else:
            log_handler_change_check.info("ChangeCheckWorker stop.")

    def stop(self):
        self.monitoring = False

    def func(self, item):
        path = item["path"]
        if not os.path.exists(path):
            print("Error Log")
        else:
            self._change_check(item)


class S3UploadWorker(Thread):
    def __init__(
        self,
        in_queue: Queue,
        s3,
        bucket_name: str,
        prefix: str,
        status_stream: Callable[[str], None],
    ):
        super().__init__(daemon=True)
        self.s3 = s3
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.in_queue = in_queue
        self.monitoring = False
        self.status_stream = status_stream

    def run(self):
        self.monitoring = True
        while self.monitoring:
            if self.in_queue.empty():
                time.sleep(1)
            else:
                item = self.in_queue.get()
                self.func(item)
        else:
            log_handler_s3_upload.info("ChangeCheckWorker stop.")

    def stop(self):
        self.monitoring = False

    def func(self, path: str):
        log_handler_s3_upload.info(
            f"Start uploading {path} to {self.bucket_name} bucket."
        )
        self.status_stream(f"Uploading {path} to {self.bucket_name} bucket....")
        try:
            self.s3.upload_file(
                path,
                self.bucket_name,
                os.path.join(self.prefix, os.path.basename(path)),
            )
            log_handler_s3_upload.info(
                f"Finish uploading {path} to {self.bucket_name} bucket."
            )
            self.status_stream(f"Finish uploading {path} to {self.bucket_name} bucket.")
        except boto3.exceptions.S3UploadFailedError as e:
            log_handler_s3_upload.error(
                f"Failed to upload {path} to {self.bucket_name} bucket."
            )
            self.status_stream(
                f"Failed to upload {path} to {self.bucket_name} bucket.", error=True
            )
            log_handler_change_check.error(str(e))
        except ParamValidationError as e:
            log_handler_s3_upload.error(
                f"Failed to upload {path} to {self.bucket_name} bucket."
            )
            self.status_stream(
                f"Failed to upload {path} to {self.bucket_name} bucket.", error=True
            )
            log_handler_change_check.error(str(e))
