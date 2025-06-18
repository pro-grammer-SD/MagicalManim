import customtkinter

class MyFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            border_color="cyan",
            border_width=2,
            fg_color="transparent",  # or match app background
            corner_radius=10,
            **kwargs
        )
        self.label = customtkinter.CTkLabel(self, text="Hello, world!")
        self.label.grid(row=0, column=0, padx=20, pady=20)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x200")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.my_frame = MyFrame(master=self)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

app = App()
app.mainloop()
