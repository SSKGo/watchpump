import tkinter as tk
from abc import abstractmethod
from tkinter import ttk


class NameEditorGUI(tk.Toplevel):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        self.title("Save Settings")
        self.geometry("300x100")
        self.construct()
        self.set_entries(config)
        master.resizable(0, 0)

    def construct(self):
        frame_name = ttk.LabelFrame(self, text="Name")
        self.name_entry = tk.Entry(frame_name)
        self.name_entry.pack(padx=5, pady=5, fill=tk.X)
        frame_name.pack(padx=5, pady=5, fill=tk.X)

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
            self.name_entry.insert(0, config["name"])

    def click_save(self):
        if self.save():
            self.destroy()

    def click_cancel(self):
        self.destroy()

    @abstractmethod
    def save(self) -> bool:
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = NameEditorGUI(master=root)
    app.mainloop()
