import tkinter as tk
from abc import abstractclassmethod


class AWSIAMConfigEditorGUI(tk.Toplevel):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        # initialize
        self.construct_config_aws()
        self.set_entries(config)
        self.toggle_entry_state()

    def construct_config_aws(self):
        setting_name_label = tk.Label(self, text="Setting Name:")
        setting_name_label.pack()
        self.setting_name_entry = tk.Entry(self)
        self.setting_name_entry.pack()

        self.use_profile_var = tk.IntVar(value=1)
        self.use_profile_check = tk.Checkbutton(
            self,
            text="Use AWS Profile",
            variable=self.use_profile_var,
            command=self.toggle_entry_state,
        )
        self.use_profile_check.pack()

        profile_label = tk.Label(self, text="AWS Profile:")
        profile_label.pack()
        self.profile_entry = tk.Entry(self)
        self.profile_entry.pack()

        access_key_label = tk.Label(self, text="AWS Access Key:")
        access_key_label.pack()
        self.access_key_entry = tk.Entry(self)
        self.access_key_entry.pack()

        secret_key_label = tk.Label(self, text="AWS Secret Key:")
        secret_key_label.pack()
        self.secret_key_entry = tk.Entry(self)
        self.secret_key_entry.pack()

        save_button = tk.Button(
            self,
            text="Save Config",
            command=self.click_save,
        )
        save_button.pack()

    def set_entries(self, config):
        if config:
            self.setting_name_entry.insert(0, config["name"])
            self.use_profile_var.set(config["use_profile"])
            self.access_key_entry.insert(0, config["aws_access_key"])
            self.secret_key_entry.insert(0, config["aws_secret_key"])
            self.profile_entry.insert(0, config["aws_profile"])

    def click_save(self):
        self.save_credentials()
        self.destroy()

    @abstractclassmethod
    def save_credentials(self):
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
