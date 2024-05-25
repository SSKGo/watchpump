import logging
import os
import tkinter as tk
from collections.abc import Callable
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
from tkinter import messagebox

import boto3
from botocore.exceptions import NoCredentialsError
from modules.config import AWSIAMConfig, SessionConfig
from modules.gui.config_window import AWSIAMConfigEditorGUI
from modules.gui.license_window import LicenseGUI
from modules.gui.name_window import NameEditorGUI
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
        pass

    def click_menu_file_save(self, *args):
        self.save_session()

    def click_menu_file_save_as(self, *args):
        session_name = self.session_combobox.get()
        if session_name == Application.session_new:
            session_name = ""
        new_session_data = {
            "name": session_name,
            "path": self.path_entry.get(),
            "bucket": self.bucket_entry.get(),
            "prefix": self.prefix_entry.get(),
            "aws_iam": self.aws_iam_combobox.get(),
        }
        window = NameEditor(
            master=self.master,
            new_session_data=new_session_data,
            after_save=self._after_session_save,
            taboo_names=[Application.session_new],
            existing_names=self.session_config.list_names(),
        )
        window.transient(self.master)
        window.grab_set()
        window.focus_set()
        self.wait_window(window)

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
            taboo_names=[Application.aws_iam_default],
            existing_names=self.aws_iam_config.list_names(),
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
            taboo_names=[Application.aws_iam_default],
            existing_names=self.aws_iam_config.list_names(),
        )
        config_window.transient(self.master)
        config_window.grab_set()
        config_window.focus_set()
        self.wait_window(config_window)

    def click_delete_credentials(self):
        name = self.aws_iam_combobox.get()
        delete_id = self.aws_iam_config.name2id(name)
        self.aws_iam_config.delete(delete_id)
        self._after_aws_iam_delete()

    def click_edit_session(self):
        self.enable_session_edit()
        self.session_combobox.config(state=tk.DISABLED)

    def click_delete_session(self):
        name = self.session_combobox.get()
        delete_id = self.session_config.name2id(name)
        self.session_config.delete(delete_id)
        self._after_session_delete()

    def click_save_session(self):
        self.save_session()

    def _create_boto3_session(self):
        if self.aws_iam_combobox.get() == Application.aws_iam_default:
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
        self._update_aws_iam_combobox_values()
        self._update_session_combobox_values()
        self.initialize_session_input()
        self.bottom_status_label.config(text="Stop Monitoring.")
        self.change_session_buttons_state()

    def _update_session_combobox_values(self):
        combobox_value_list = [Application.session_new]
        for value in self.session_config.config.values():
            combobox_value_list.append(value["name"])
        self.session_combobox.config(values=combobox_value_list)

    def _update_aws_iam_combobox_values(self):
        aws_iam_list = [Application.aws_iam_default]
        for value in self.aws_iam_config.config.values():
            aws_iam_list.append(value["name"])
        self.aws_iam_combobox.config(values=aws_iam_list)

    def load_session_config(self):
        session_name = self.session_combobox.get()
        session_id = SessionConfig.name2id(session_name)
        config = self.session_config.config[session_id]
        self.update_session_input(
            config["path"], config["bucket"], config["prefix"], config["aws_iam"]
        )

    def save_session(self):
        session_name = self.session_combobox.get()
        if session_name == Application.session_new:
            self.click_menu_file_save_as()
        else:
            session_id = SessionConfig.name2id(session_name)
            data = {
                "name": session_name,
                "path": self.path_entry.get(),
                "bucket": self.bucket_entry.get(),
                "prefix": self.prefix_entry.get(),
                "aws_iam": self.aws_iam_combobox.get(),
            }
            self.session_config.update(data, original_id=session_id)
            self._after_session_save(session_id)

    def _after_aws_iam_save(self, new_id):
        name_saved = self.aws_iam_config.config[new_id]["name"]
        self.aws_iam_combobox.set(name_saved)
        self._update_aws_iam_combobox_values()
        self.change_aws_iam_buttons_state()

    def _after_aws_iam_delete(self):
        self.aws_iam_combobox.set(Application.aws_iam_default)
        self._update_aws_iam_combobox_values()
        self.change_aws_iam_buttons_state()

    def _after_session_save(self, new_id):
        config = self.session_config.config[new_id]
        self.session_combobox.set(config["name"])
        self.update_session_input(
            config["path"], config["bucket"], config["prefix"], config["aws_iam"]
        )
        self._update_session_combobox_values()
        self.change_session_buttons_state()
        self.session_combobox.config(state="readonly")

    def _after_session_delete(self):
        self.session_combobox.set(Application.session_new)
        self._initialize_gui()


class AWSIAMConfigEditor(AWSIAMConfigEditorGUI):
    def __init__(
        self,
        master=None,
        original_id=None,
        after_save: Callable[[str], None] = None,
        taboo_names=[],
        existing_names=[],
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
        self.taboo_names = taboo_names
        self.existing_names = existing_names

    def save(self) -> bool:
        name = self.setting_name_entry.get()
        if name in self.existing_names:
            messagebox.showerror("Name Error", "The input name already exists.")
            return False
        elif name in self.taboo_names:
            messagebox.showerror(
                "Name Error", f"'{name}' is not acceptable name, give another name."
            )
            return False
        else:
            new_aws_iam_settings = {
                "name": name,
                "use_profile": self.use_profile,
                "aws_profile": self.profile_entry.get(),
                "aws_access_key": self.access_key_entry.get(),
                "aws_secret_key": self.secret_key_entry.get(),
            }
            new_id = self.aws_iam_config.update(
                new_aws_iam_settings, original_id=self.original_id
            )
            self.after_save(new_id)
            return True


class NameEditor(NameEditorGUI):
    def __init__(
        self,
        master=None,
        new_session_data=None,
        after_save: Callable[[str], None] = None,
        taboo_names=[],
        existing_names=[],
    ):
        # Setting files
        self.session_config = SessionConfig()
        self.new_session_data = new_session_data
        super().__init__(master=master, config=new_session_data)
        self.after_save = after_save
        self.taboo_names = taboo_names
        self.existing_names = existing_names

    def save(self) -> bool:
        name = self.name_entry.get()
        if name in self.existing_names:
            messagebox.showerror("Name Error", "The input name already exists.")
            return False
        elif name in self.taboo_names:
            messagebox.showerror(
                "Name Error", f"'{name}' is not acceptable name, give another name."
            )
            return False
        else:
            self.new_session_data["name"] = name
            new_id = self.session_config.update(self.new_session_data)
            self.after_save(new_id)
            return True


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
