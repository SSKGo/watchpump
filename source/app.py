import logging
import os
import tkinter as tk
from collections.abc import Callable
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
from tkinter import messagebox

import boto3
import yaml
from botocore.exceptions import NoCredentialsError
from modules.config import AWSIAMConfig, SessionConfig
from modules.gui.config_window import AWSIAMConfigEditorGUI
from modules.gui.license_window import LicenseGUI
from modules.gui.top_window import ApplicationGUI
from modules.worker import ChangeCheckWorker, FileHandler, S3UploadWorker
from oss_license_descriptions import oss_license_descriptions
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


class Application(ApplicationGUI):
    def __init__(self, master=None):
        super().__init__(master=master)
        # Observer
        self.observer = None
        # Queue
        self.change_check_store = {}
        self.s3_upload_queue = Queue()
        # Setting files
        self.aws_iam_config = AWSIAMConfig()
        self.session_config = SessionConfig()
        # Initialize entry
        self._initialize_gui()

    def menu_file_new(self, *args):
        pass

    def menu_file_open(self, *args):
        self._load_config("")

    def menu_file_save(self, *args):
        self._dump_config("")

    def menu_file_save_as(self, *args):
        self._dump_config("")

    def menu_help_oss_licenses(self):
        license_window = LicenseGUI(
            master=self.master, description=oss_license_descriptions
        )
        license_window.transient(self.master)
        license_window.grab_set()
        license_window.focus_set()
        self.wait_window(license_window)

    def click_start_monitoring(self):
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

    def click_stop_monitoring(self):
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

    def click_edit_credentials(self):
        original_name = self.aws_iam_combobox.get()
        original_id = self.aws_iam_config.name2id(original_name)
        config_window = AWSIAMConfigEditor(
            master=self.master,
            original_id=original_id,
            after_save=self._after_aws_iam_save,
        )
        config_window.transient(self.master)
        config_window.grab_set()
        config_window.focus_set()
        self.wait_window(config_window)

    def click_add_credentials(self):
        config_window = AWSIAMConfigEditor(
            master=self.master,
            original_id=None,
            after_save=self._after_aws_iam_save,
        )
        config_window.transient(self.master)
        config_window.grab_set()
        config_window.focus_set()
        self.wait_window(config_window)

    def click_delete_credentials(self):
        name = self.aws_iam_combobox.get()
        delete_id = self.aws_iam_config.name2id(name)
        self.aws_iam_config.delete_iam(delete_id)
        self._after_aws_iam_delete()

    def _create_boto3_session(self):
        if self.aws_iam_combobox.get() == "default":
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
        self._update_aws_iam_combobox_values()
        self.aws_iam_combobox.set("default")
        self.bottom_status_label.config(text="Stop Monitoring.")

    def _update_aws_iam_combobox_values(self):
        aws_iam_list = ["default"]
        for value in self.aws_iam_config.config.values():
            aws_iam_list.append(value["name"])
        self.aws_iam_combobox.config(values=aws_iam_list)

    def _load_config(self, path):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        self.path_entry.insert(0, config["path"])
        self.bucket_entry.insert(0, config["bucket"])
        self.prefix_entry.insert(0, config["prefix"])
        self.aws_iam_combobox.set(config["aws_iam"])

    def _dump_config(self, path):
        config = {
            "path": self.path_entry.get(),
            "bucket": self.bucket_entry.get(),
            "prefix": self.prefix_entry.get(),
            "aws_iam": self.aws_iam_combobox.get(),
        }
        with open(path, "w") as f:
            yaml.dump(config, f)

    def _after_aws_iam_save(self, new_id):
        name_saved = self.aws_iam_config.config[new_id]["name"]
        self.aws_iam_combobox.set(name_saved)
        self._update_aws_iam_combobox_values()
        self.change_aws_iam_buttons_state()

    def _after_aws_iam_delete(self):
        self.aws_iam_combobox.set("default")
        self._update_aws_iam_combobox_values()
        self.change_aws_iam_buttons_state()


class AWSIAMConfigEditor(AWSIAMConfigEditorGUI):
    def __init__(
        self, master=None, original_id=None, after_save: Callable[[str], None] = None
    ):
        # Setting files
        self.aws_iam_config = AWSIAMConfig()
        self.original_id = original_id if original_id else None
        if self.original_id:
            config = self.aws_iam_config.config[self.original_id]
        else:
            config = None
        super().__init__(master=master, config=config)
        self.after_save = after_save

    def save_credentials(self):
        new_aws_iam_settings = {
            "name": self.setting_name_entry.get(),
            "use_profile": self.use_profile,
            "aws_profile": self.profile_entry.get(),
            "aws_access_key": self.access_key_entry.get(),
            "aws_secret_key": self.secret_key_entry.get(),
        }
        new_id = self.aws_iam_config.update(
            new_aws_iam_settings, original_id=self.original_id
        )
        self.after_save(new_id)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
