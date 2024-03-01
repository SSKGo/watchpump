import logging
import os
import tkinter as tk
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
from tkinter import messagebox

import boto3
import yaml
from botocore.exceptions import NoCredentialsError
from modules.gui.config_window import ConfigGUI
from modules.gui.top_window import ApplicationGUI
from modules.worker import ChangeCheckWorker, FileHandler, S3UploadWorker
from watchdog.observers import Observer

DIR_LOG = "./logs"


logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not os.path.exists(DIR_LOG):
    os.makedirs(DIR_LOG)

log_file_handler = TimedRotatingFileHandler(os.path.join(DIR_LOG, "log.log"))
log_file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log_file_handler.setLevel(logging.INFO)
log_file_handler.setFormatter(log_file_formatter)
logger.addHandler(log_file_handler)

log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)
log_stream_handler.setFormatter(log_file_formatter)
logger.addHandler(log_stream_handler)

# TODO:
# 1. Detect Move
# 3. Config: to open a file
# 4. Config: to save a file


class Application(ApplicationGUI):
    def __init__(self, master=None):
        super().__init__(master=master)
        # Observer
        self.observer = None
        # Queue
        self.change_check_store = {}
        self.s3_upload_queue = Queue()

        # Initialize entry
        self._initialize_gui()

        # Credentials file
        self.credeintials_path = ".aws_iam.yaml"
        if not os.path.exists(self.credeintials_path):
            self._initialize_credentials_file()

    def menu_file_new(self, *args):
        pass

    def menu_file_open(self, *args):
        self._load_config("")

    def menu_file_save(self, *args):
        self._dump_config("")

    def menu_file_save_as(self, *args):
        self._dump_config("")

    def start_monitoring(self):
        try:
            session = self._create_boto3_session()
            s3 = session.client("s3")
            s3 = boto3.client("s3")
        except NoCredentialsError as e:
            logger.exception(str(e))
            if messagebox.showerror(
                "AWS Credentials Error", "Error happen in AWS session set up step."
            ):
                return
        except Exception as e:
            logger.exception(str(e))
            if messagebox.showerror(
                "AWS Session Error", "Error happen in AWS session set up step."
            ):
                return
        try:
            event_handler = FileHandler(self.change_check_store)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.path_entry.get(), recursive=True)
            self.observer.start()
        except FileNotFoundError as e:
            logger.info(f"{str(e)}, path: {self.path_entry.get()}")
            if messagebox.showerror(
                "Folder not found", "The specified folder for monitoring was not found."
            ):
                return
        except Exception as e:
            logger.exception(str(e))
            self.bottom_status_label.config(
                text=str(e), font=("Helvetica", 16), foreground="red"
            )
        try:
            self.change_check_workder = ChangeCheckWorker(
                self.change_check_store, self.s3_upload_queue
            )
            self.change_check_workder.start()
            self.s3_upload_workder = S3UploadWorker(
                self.s3_upload_queue,
                s3,
                self.bucket_entry.get(),
                self.prefix_entry.get(),
                self.set_bottom_status_label,
            )
            self.s3_upload_workder.start()
        except Exception as e:
            logger.exception(str(e))
            self.bottom_status_label.config(
                text=str(e), font=("Helvetica", 16), foreground="red"
            )
        self.status_label.config(
            text="Monitoring...",
            font=("Helvetica", 16),
            foreground="blue",
        )
        self.bottom_status_label.config(text="Start Monitoring.")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.path_entry.config(state=tk.DISABLED)
        self.bucket_entry.config(state=tk.DISABLED)
        self.prefix_entry.config(state=tk.DISABLED)
        logger.info(
            f"Start monitoring. Path: {self.path_entry.get()}, Bucket: {self.bucket_entry.get()}, Prefix: {self.prefix_entry.get()}."  # noqa: E501
        )

    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.change_check_workder.stop()
            self.change_check_workder.join()
            self.s3_upload_workder.stop()
            self.s3_upload_workder.join()
            self.observer = None
            self.status_label.config(
                text="Not Monitoring", font=("Helvetica", 16), foreground="red"
            )
            self.bottom_status_label.config(text="Stop Monitoring.")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.path_entry.config(state=tk.NORMAL)
            self.bucket_entry.config(state=tk.NORMAL)
            self.prefix_entry.config(state=tk.NORMAL)
            logger.info("Stop monitoring")

    def edit_credentials(self):
        config_window = ConfigGUI(self.master)
        config_window.transient(self.master)
        config_window.grab_set()
        config_window.focus_set()
        self.wait_window(config_window)

    def add_credentials(self):
        config_window = ConfigGUI(self.master)
        config_window.transient(self.master)
        config_window.grab_set()
        config_window.focus_set()
        self.wait_window(config_window)

    def _initialize_credentials_file(self):
        with open(self.credeintials_path, "w") as f:
            yaml.dump({}, f)

    def _create_boto3_session(self):
        if self.session_combobox.get() == "default":
            session = boto3.Session()
        # elif config["use_profile"]:
        #     session = boto3.Session(profile_name=config["aws_profile"])
        # else:
        #     session = boto3.Session(
        #         aws_access_key_id=config["aws_access_key"],
        #         aws_secret_access_key=config["aws_secret_key"],
        #     )
        return session

    def _initialize_gui(self):
        self.path_entry.insert(0, os.path.abspath("."))
        self.bucket_entry.insert(0, "")
        self.prefix_entry.insert(0, "")
        self.session_combobox.set("default")
        self.bottom_status_label.config(text="Stop Monitoring.")

    def _load_config(self, path):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        self.path_entry.insert(0, config["path"])
        self.bucket_entry.insert(0, config["bucket"])
        self.prefix_entry.insert(0, config["prefix"])
        self.session_combobox.set(config["session"])

    def _dump_config(self, path):
        config = {
            "path": self.path_entry.get(),
            "bucket": self.bucket_entry.get(),
            "prefix": self.prefix_entry.get(),
            "session": self.session_combobox.get(),
        }
        with open(path, "w") as f:
            yaml.dump(config, f)

    # def save_config(
    #     self,
    #     session_name,
    #     new_session_settings,
    #     window,
    # ):
    #     with open(self.credeintials_path, "r") as f:
    #         credentials = yaml.safe_load(f)
    #     credentials[session_name] = new_session_settings
    #     with open(self.credeintials_path, "w") as f:
    #         yaml.dump(new_session_settings, f)
    #     window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
