import tkinter as tk
from abc import abstractmethod
from tkinter import ttk


class AWSIAMConfigEditorGUI(tk.Toplevel):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        self.title("Save AWS Settings")
        self.geometry("300x300")
        # initialize
        self.construct_config_aws()
        self.set_entries(config)
        self.toggle_entry_state()

    def construct_config_aws(self):
        setting_name_label = ttk.LabelFrame(self, text="Setting Name")
        self.setting_name_entry = tk.Entry(setting_name_label)
        self.setting_name_entry.pack(padx=5, pady=5, fill=tk.X)
        setting_name_label.pack(padx=5, pady=5, fill=tk.X)

        self.use_profile_var = tk.IntVar(value=1)
        self.use_profile_check = tk.Checkbutton(
            self,
            text="Use AWS Profile",
            variable=self.use_profile_var,
            command=self.toggle_entry_state,
        )
        self.use_profile_check.pack(anchor=tk.W, pady=10)

        profile_label = ttk.LabelFrame(self, text="AWS Profile")
        self.profile_entry = tk.Entry(profile_label)
        self.profile_entry.pack(padx=5, pady=5, fill=tk.X)
        profile_label.pack(padx=5, pady=5, fill=tk.X)

        # Credentials
        credentials_label = ttk.LabelFrame(self, text="AWS Credentials")
        # Access Key
        access_key_frame = tk.Frame(credentials_label)
        access_key_label = tk.Label(access_key_frame, text="Access Key ID")
        access_key_label.pack(anchor=tk.W)
        self.access_key_entry = tk.Entry(access_key_frame)
        self.access_key_entry.pack(fill=tk.X)
        access_key_frame.pack(padx=5, pady=5, fill=tk.X)
        # Secret Key
        secret_key_frame = tk.Frame(credentials_label)
        secret_key_label = tk.Label(secret_key_frame, text="Secret Access Key")
        secret_key_label.pack(anchor=tk.W)
        self.secret_key_entry = tk.Entry(secret_key_frame)
        self.secret_key_entry.pack(fill=tk.X)
        secret_key_frame.pack(padx=5, pady=5, fill=tk.X)
        credentials_label.pack(padx=5, pady=5, fill=tk.X)

        frame_actions = tk.Frame(self, relief=tk.SUNKEN)
        save_button = tk.Button(
            frame_actions,
            text="Save",
            command=self.click_save,
        )
        save_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.RIGHT)
        cancel_button = tk.Button(
            frame_actions,
            text="Cancel",
            command=self.click_cancel,
        )
        cancel_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.RIGHT)
        frame_actions.pack(anchor=tk.W, side=tk.RIGHT)

    def set_entries(self, config):
        if config:
            self.setting_name_entry.insert(0, config["name"])
            self.use_profile_var.set(config["use_profile"])
            self.access_key_entry.insert(0, config["aws_access_key"])
            self.secret_key_entry.insert(0, config["aws_secret_key"])
            self.profile_entry.insert(0, config["aws_profile"])

    def click_save(self):
        if self.save():
            self.destroy()

    def click_cancel(self):
        self.destroy()

    @abstractmethod
    def save(self) -> bool:
        pass

    def toggle_entry_state(self):
        self.use_profile = bool(self.use_profile_var.get())
        if self.use_profile:
            self.access_key_entry.config(state="disabled")
            self.secret_key_entry.config(state="disabled")
            self.profile_entry.config(state="normal")
        else:
            self.access_key_entry.config(state="normal")
            self.secret_key_entry.config(state="normal")
            self.profile_entry.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = AWSIAMConfigEditorGUI(master=root)
    app.mainloop()
