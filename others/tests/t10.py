import customtkinter

class MyFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.label = customtkinter.CTkLabel(self, text="Hello!")
        self.label.place(x=10, y=30)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x200")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.my_frame = MyFrame(master=self, border_color="cyan", border_width=2, width=200, height=100)
        self.my_frame.place(x=100, y=40)

app = App()
app.mainloop()
