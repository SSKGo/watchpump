import tkinter as tk
from abc import abstractmethod


class NameEditorGUI(tk.Toplevel):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        self.construct()
        self.set_entries(config)

    def construct(self):
        name_label = tk.Label(self, text="Name:")
        name_label.pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()
        cancel_button = tk.Button(
            self,
            text="Cancel",
            command=self.click_cancel,
        )
        cancel_button.pack()
        save_button = tk.Button(
            self,
            text="Save",
            command=self.click_save,
        )
        save_button.pack()

    def set_entries(self, config):
        if config:
            self.name_entry.insert(0, config["name"])

    def click_save(self):
        self.save()
        self.destroy()

    def click_cancel(self):
        self.destroy()

    @abstractmethod
    def save(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = NameEditorGUI(master=root)
    app.mainloop()
