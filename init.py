import customtkinter
from gui.editor import EditorGui

class InitGui:
    def __init__(self):
        def new_project():
            EditorGui()
        
        self.app = customtkinter.CTk()
        self.app.iconbitmap("icon/ico/image.ico")
        self.app.title("Magical Manim")
        self.width, self.height = 400, 200
        self.app.geometry(f"{self.width}x{self.height}")
        self.app.resizable(False, False)
        
        np_button = customtkinter.CTkButton(self.app, text="New Project...", corner_radius=70, command=new_project)
        np_button.pack(padx=20, pady=20)
        
        self.app.mainloop()

InitGui()
