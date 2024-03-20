import tkinter as tk
from abc import abstractclassmethod
from tkinter import filedialog, messagebox, ttk


class ApplicationGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry("500x400")
        self.master.title("Watchdog for S3 Upload")
        self.master.resizable(width=False, height=False)

        # Shortcut
        self.bind_all("<Control-n>", self.menu_file_new)
        self.bind_all("<Control-o>", self.menu_file_open)
        self.bind_all("<Control-s>", self.menu_file_save)
        self.bind_all("<Control-Shift-Key-S>", self.menu_file_save_as)

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
        menu_file.add_command(
            label="New",
            command=self.menu_file_new,
            accelerator="Ctrl+N",
            state=tk.DISABLED,
        )
        menu_file.add_command(
            label="Open",
            command=self.menu_file_open,
            accelerator="Ctrl+O",
            state=tk.DISABLED,
        )
        menu_file.add_command(
            label="Save",
            command=self.menu_file_save,
            accelerator="Ctrl+S",
            state=tk.DISABLED,
        )
        menu_file.add_command(
            label="Save As...",
            command=self.menu_file_save_as,
            accelerator="Ctrl+Shift+S",
            state=tk.DISABLED,
        )
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.close_app)
        # Put menus in menubar
        menubar.add_cascade(label="File", menu=menu_file)
        self.master.config(menu=menubar)

    def _construct_bottom_status(self):
        frame_statusbar = tk.Frame(self.master, relief=tk.SUNKEN, bd=2)
        self.bottom_status_label = tk.Label(frame_statusbar, text="StatusLabel")
        self.bottom_status_label.pack(side=tk.LEFT)
        frame_statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _construct_right_frame(self):
        frame_right = tk.Frame(
            self.master, padx=5, pady=5, relief=tk.SUNKEN, bd=2, width=100
        )
        frame_right.propagate(False)
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
        frame_status = ttk.LabelFrame(frame_left, text="Status", width=280)
        self.status_label = ttk.Label(
            frame_status,
            text="Not Monitoring",
            font=("Helvetica", 16),
            foreground="red",
        )
        self.status_label.pack(padx=5, pady=5)
        frame_status.pack(padx=5, pady=5, anchor=tk.W)

        # Folder
        frame_folder = ttk.LabelFrame(
            frame_left, text="Folder for Monitoring", width=280
        )
        self.path_entry = tk.Entry(frame_folder, width=50)
        self.path_entry.pack(padx=5, anchor=tk.W)
        select_button = tk.Button(
            frame_folder,
            text="Select Folder",
            command=lambda: ApplicationGUI.select_folder(self.path_entry),
        )
        select_button.pack(padx=5, pady=5, anchor=tk.W)
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
        self.aws_iam_list = ["default"]
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

    def _click_add_credentials(self):
        self.click_add_credentials()

    def set_bottom_status_label(self, text, error=False):
        foreground = "red" if error else "black"
        self.bottom_status_label.config(text=text, foreground=foreground)

    def select_aws_iam_combobox(self, _):
        self.change_aws_iam_buttons_state()

    def change_aws_iam_buttons_state(self):
        if self.aws_iam_combobox.get() == "default":
            self.aws_iam_edit_button.config(state=tk.DISABLED)
            self.aws_iam_delete_button.config(state=tk.DISABLED)
        else:
            self.aws_iam_edit_button.config(state=tk.NORMAL)
            self.aws_iam_delete_button.config(state=tk.NORMAL)

    @abstractclassmethod
    def menu_file_new(self, *args):
        pass

    @abstractclassmethod
    def menu_file_open(self, *args):
        pass

    @abstractclassmethod
    def menu_file_save(self, *args):
        pass

    @abstractclassmethod
    def menu_file_save_as(self, *args):
        pass

    @abstractclassmethod
    def click_start_monitoring(self):
        pass

    @abstractclassmethod
    def click_stop_monitoring(self):
        pass

    @abstractclassmethod
    def click_edit_credentials(self):
        pass

    @abstractclassmethod
    def click_delete_credentials(self):
        pass

    @abstractclassmethod
    def click_add_credentials(self):
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
