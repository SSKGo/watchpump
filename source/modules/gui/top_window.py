import os
import tkinter as tk
from abc import abstractmethod
from tkinter import filedialog, messagebox, ttk


class ApplicationGUI(ttk.Frame):
    session_new = "New*"
    aws_iam_default = "default"

    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry("500x400")
        self.master.title("Watchdog for S3 Upload")
        self.master.resizable(width=False, height=False)

        self.session_edit_mode = False

        # Shortcut
        self.bind_all("<Control-n>", self.menu_file_new)
        self.bind_all("<Control-o>", self.menu_file_open)
        # self.bind_all("<Control-s>", self.click_menu_file_save)
        self.bind_all("<Control-Shift-Key-S>", self.click_menu_file_save_as)

        # Menubar
        self._construct_menubar()

        # Bottom statusbar
        self._construct_bottom_status()

        # Right column
        self._construct_right_frame()

        # Left Column
        self._construct_left_frame()

    def _construct_menubar(self):
        menubar = tk.Menu(self)
        # File menu
        menu_file = tk.Menu(menubar, tearoff=False)
        # menu_file.add_command(
        #     label="New",
        #     command=self.menu_file_new,
        #     accelerator="Ctrl+N",
        #     state=tk.DISABLED,
        # )
        # menu_file.add_command(
        #     label="Open",
        #     command=self.menu_file_open,
        #     accelerator="Ctrl+O",
        #     state=tk.DISABLED,
        # )
        # menu_file.add_command(
        #     label="Save",
        #     command=self.click_menu_file_save,
        #     accelerator="Ctrl+S",
        #     state=tk.NORMAL,
        # )
        menu_file.add_command(
            label="Save As...",
            command=self.click_menu_file_save_as,
            accelerator="Ctrl+Shift+S",
            state=tk.NORMAL,
        )
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.close_app)
        # Help menu
        menu_help = tk.Menu(menubar, tearoff=False)
        menu_help.add_command(
            label="License Information",
            command=self.menu_help_oss_licenses,
        )
        # Put menus in menubar
        menubar.add_cascade(label="File", menu=menu_file)
        menubar.add_cascade(label="Help", menu=menu_help)
        self.master.config(menu=menubar)

    def _construct_bottom_status(self):
        frame_statusbar = tk.Frame(self.master, relief=tk.SUNKEN, bd=2)
        self.bottom_status_label = tk.Label(frame_statusbar, text="StatusLabel")
        self.bottom_status_label.pack(side=tk.LEFT)
        frame_statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _construct_right_frame(self):
        frame_right = tk.Frame(
            self.master, padx=5, pady=5, relief=tk.SUNKEN, bd=2, width=120
        )
        frame_right.propagate(False)
        frame_status = ttk.LabelFrame(frame_right, text="Status", width=280)
        self.status_label = ttk.Label(
            frame_status,
            text="Not Monitoring",
            foreground="red",
        )
        self.status_label.pack(padx=5, pady=5)
        frame_status.pack(padx=5, pady=5, anchor=tk.W)

        self.start_button = ttk.Button(
            frame_right,
            text="Start Monitoring",
            command=self.click_start_monitoring,
        )
        self.start_button.pack(fill=tk.X, pady=5)
        self.stop_button = ttk.Button(
            frame_right,
            text="Stop Monitoring",
            command=self._click_stop_monitoring,
            state=tk.DISABLED,
        )
        self.stop_button.pack(fill=tk.X, pady=5)
        frame_right.pack(side=tk.RIGHT, fill=tk.Y)

    def _construct_left_frame(self):
        frame_left = tk.Frame(self.master, relief=tk.SUNKEN, bd=2)

        # Session Settings
        frame_session = ttk.LabelFrame(frame_left, text="Session Settings", width=280)
        self.session_list = [ApplicationGUI.session_new]
        # Combobox
        self.session_combobox = ttk.Combobox(
            frame_session,
            values=self.session_list,
            state="readonly",
            exportselection=0,
        )
        self.session_combobox.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.session_combobox.set(self.session_list[0])
        # Buttons
        self.session_edit_button = ttk.Button(
            frame_session,
            text="Edit",
            command=self.click_edit_session,
            state=tk.DISABLED,
        )
        self.session_combobox.bind("<<ComboboxSelected>>", self.select_session_combobox)
        self.session_edit_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.session_delete_button = ttk.Button(
            frame_session,
            text="Delete",
            command=self._click_delete_session,
            state=tk.DISABLED,
        )
        self.session_delete_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        # For Edit mode
        self.session_save_button = ttk.Button(
            frame_session,
            text="Save",
            command=self._click_save_session,
            state=tk.NORMAL,
        )
        self.session_cancel_button = ttk.Button(
            frame_session,
            text="Cancel",
            command=self._click_cancel_session,
            state=tk.NORMAL,
        )
        frame_session.pack(padx=5, pady=5, fill=tk.X)

        # Folder
        frame_folder = ttk.LabelFrame(
            frame_left, text="Folder for Monitoring", width=280
        )
        self.path_entry = tk.Entry(frame_folder, width=50)
        self.path_entry.pack(padx=5, anchor=tk.W)
        self.select_button = tk.Button(
            frame_folder,
            text="Select Folder",
            command=lambda: ApplicationGUI.select_folder(self.path_entry),
        )
        self.select_button.pack(padx=5, pady=5, anchor=tk.W)
        frame_folder.pack(padx=5, pady=5, fill=tk.X)

        # S3 Bucket Name
        frame_s3bucket = ttk.LabelFrame(frame_left, text="S3 Bucket Name", width=280)
        self.bucket_entry = tk.Entry(frame_s3bucket)
        self.bucket_entry.pack(padx=5, pady=5, anchor=tk.W)
        frame_s3bucket.pack(padx=5, pady=5, fill=tk.X)

        # S3 Key Prefix
        frame_s3prefix = ttk.LabelFrame(frame_left, text="S3 Key Prefix", width=280)
        self.prefix_entry = tk.Entry(frame_s3prefix)
        self.prefix_entry.pack(padx=5, pady=5, anchor=tk.W)
        frame_s3prefix.pack(padx=5, pady=5, fill=tk.X)

        # AWS IAM Settings
        frame_aws_iam = ttk.LabelFrame(frame_left, text="AWS IAM Settings", width=280)
        self.aws_iam_list = [ApplicationGUI.aws_iam_default]
        # Combobox
        self.aws_iam_combobox = ttk.Combobox(
            frame_aws_iam, values=self.aws_iam_list, state="readonly", exportselection=0
        )
        self.aws_iam_combobox.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.aws_iam_combobox.set(self.aws_iam_list[0])
        self.aws_iam_edit_button = ttk.Button(
            frame_aws_iam,
            text="Edit",
            command=self.click_edit_credentials,
            state=tk.DISABLED,
        )
        self.aws_iam_combobox.bind("<<ComboboxSelected>>", self.select_aws_iam_combobox)
        # Buttons
        self.aws_iam_edit_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.aws_iam_delete_button = ttk.Button(
            frame_aws_iam,
            text="Delete",
            command=self._click_delete_credentials,
            state=tk.DISABLED,
        )
        self.aws_iam_delete_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.aws_iam_add_button = ttk.Button(
            frame_aws_iam,
            text="Add",
            command=self._click_add_credentials,
            state=tk.NORMAL,
        )
        self.aws_iam_add_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        frame_aws_iam.pack(padx=5, pady=5, fill=tk.X)

        frame_left.pack(expand=True, fill=tk.BOTH)

    def close_app(self):
        if messagebox.askokcancel(
            "Close", "Are you sure you want to close the application?"
        ):
            self.master.destroy()

    def _click_stop_monitoring(self):
        if messagebox.askokcancel(
            "Stop Monitoring", "Are you sure you want to stop monitoring?"
        ):
            self.click_stop_monitoring()

    def _click_delete_credentials(self):
        if messagebox.askokcancel(
            "Delete", f"Are you sure you want to delete {self.aws_iam_combobox.get()}?"
        ):
            self.click_delete_credentials()

    def _click_delete_session(self):
        if messagebox.askokcancel(
            "Delete", f"Are you sure you want to delete {self.session_combobox.get()}?"
        ):
            self.click_delete_session()

    def _click_save_session(self):
        ok_save = False
        if self.session_combobox.get() == ApplicationGUI.session_new:
            ok_save = True
        else:
            if messagebox.askokcancel(
                "Save",
                f"Are you sure you want to overwrite {self.session_combobox.get()}?",
            ):
                ok_save = True
        if ok_save:
            self.click_save_session()

    def _click_cancel_session(self):
        self.select_session_combobox(None)
        self.disable_session_edit()
        self.session_combobox.config(state="readonly")

    def _click_add_credentials(self):
        self.click_add_credentials()

    def set_bottom_status_label(self, text, error=False):
        foreground = "red" if error else "black"
        self.bottom_status_label.config(text=text, foreground=foreground)

    def select_aws_iam_combobox(self, _):
        self.change_aws_iam_buttons_state()

    def select_session_combobox(self, _):
        session = self.session_combobox.get()
        if session == ApplicationGUI.session_new:
            self.initialize_session_input()
        else:
            self.load_session_config()
        self.change_session_buttons_state()

    def change_aws_iam_buttons_state(self):
        if self.aws_iam_combobox.get() == ApplicationGUI.aws_iam_default:
            self.aws_iam_edit_button.config(state=tk.DISABLED)
            self.aws_iam_delete_button.config(state=tk.DISABLED)
        else:
            self.aws_iam_edit_button.config(state=tk.NORMAL)
            self.aws_iam_delete_button.config(state=tk.NORMAL)

    def change_session_buttons_state(self):
        if self.session_combobox.get() == ApplicationGUI.session_new:
            self.session_edit_button.config(state=tk.DISABLED)
            self.session_delete_button.config(state=tk.DISABLED)
            self.enable_session_edit()
        else:
            self.session_edit_button.config(state=tk.NORMAL)
            self.session_delete_button.config(state=tk.NORMAL)
            self.disable_session_edit()

    def initialize_session_input(self):
        self.update_session_input(
            os.path.abspath("."), "", "", ApplicationGUI.aws_iam_default
        )

    def update_session_input(
        self, path: str, s3_bucket: str, s3_prefix: str, aws_iam: str
    ):
        self.path_entry.config(state=tk.NORMAL)
        self.bucket_entry.config(state=tk.NORMAL)
        self.prefix_entry.config(state=tk.NORMAL)
        self.path_entry.delete(first=0, last=tk.END)
        self.bucket_entry.delete(first=0, last=tk.END)
        self.prefix_entry.delete(first=0, last=tk.END)
        self.path_entry.insert(0, path)
        self.bucket_entry.insert(0, s3_bucket)
        self.prefix_entry.insert(0, s3_prefix)
        self.aws_iam_combobox.set(aws_iam)

    def disable_session_edit(self):
        self.session_save_button.pack_forget()
        self.session_cancel_button.pack_forget()
        self.session_edit_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.session_delete_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.path_entry.config(state="readonly")
        self.select_button.config(state=tk.DISABLED)
        self.bucket_entry.config(state="readonly")
        self.prefix_entry.config(state="readonly")
        self.aws_iam_combobox.config(state=tk.DISABLED)
        self.aws_iam_edit_button.config(state=tk.DISABLED)
        self.aws_iam_delete_button.config(state=tk.DISABLED)
        self.aws_iam_add_button.config(state=tk.DISABLED)

    def enable_session_edit(self):
        self.session_edit_button.pack_forget()
        self.session_delete_button.pack_forget()
        self.session_save_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        if self.session_combobox.get() != ApplicationGUI.session_new:
            self.session_cancel_button.pack(padx=5, pady=5, anchor=tk.W, side=tk.LEFT)
        self.path_entry.config(state=tk.NORMAL)
        self.select_button.config(state=tk.NORMAL)
        self.bucket_entry.config(state=tk.NORMAL)
        self.prefix_entry.config(state=tk.NORMAL)
        self.aws_iam_combobox.config(state="readonly")
        self.aws_iam_edit_button.config(state=tk.NORMAL)
        self.aws_iam_delete_button.config(state=tk.NORMAL)
        self.aws_iam_add_button.config(state=tk.NORMAL)
        self.change_aws_iam_buttons_state()

    @abstractmethod
    def load_session_config(self):
        pass

    @abstractmethod
    def menu_file_new(self, *args):
        pass

    @abstractmethod
    def menu_file_open(self, *args):
        pass

    @abstractmethod
    def click_menu_file_save(self, *args):
        pass

    @abstractmethod
    def click_menu_file_save_as(self, *args):
        pass

    @abstractmethod
    def menu_help_oss_licenses(self, *args):
        pass

    @abstractmethod
    def click_start_monitoring(self):
        pass

    @abstractmethod
    def click_stop_monitoring(self):
        pass

    @abstractmethod
    def click_edit_credentials(self):
        pass

    @abstractmethod
    def click_delete_credentials(self):
        pass

    @abstractmethod
    def click_add_credentials(self):
        pass

    @abstractmethod
    def click_edit_session(self):
        pass

    @abstractmethod
    def click_delete_session(self):
        pass

    @abstractmethod
    def click_add_session(self):
        pass

    @abstractmethod
    def click_save_session(self):
        pass

    @staticmethod
    def select_folder(entry):
        folder_selected = filedialog.askdirectory(
            title="Select folder", initialdir="./"
        )
        if folder_selected:
            entry.delete(0, tk.END)
            entry.insert(0, folder_selected)


if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationGUI(master=root)
    app.mainloop()
