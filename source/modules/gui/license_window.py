import tkinter as tk


class LicenseGUI(tk.Toplevel):
    def __init__(self, master=None, description=""):
        super().__init__(master)
        self.description = description
        self.title("License Information")
        self.geometry("500x400")
        # initialize
        self.construct()

    def construct(self):
        text_box = tk.Text(master=self, height=25, wrap=tk.WORD)
        text_box.insert(tk.END, self.description)
        text_box.config(state=tk.DISABLED)
        text_box.pack()

        close_button = tk.Button(
            self,
            text="Close",
            command=self.click_close,
        )
        close_button.pack()

    def click_close(self):
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LicenseGUI(master=root, description="XXXXXXXXXXXX")
    app.mainloop()
