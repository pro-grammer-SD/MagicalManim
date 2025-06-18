# Import Packages
from tkinter import Frame, Label
import tkinter.font as tkFont
from customtkinter import CTk, CTkButton

# Colors
WHITE = "#FFFFFF"
DARK_BLUE = "#031249"
SECOND_DARK_BLUE = "#142455"

# Custom Title Bar
class TitleBar(Frame):
    def __init__(self, parent, title:str):
        self.root = parent
        self.root.overrideredirect(True) # For Remove Default Title Bar
        super().__init__(parent, bg=DARK_BLUE)
        myFont = tkFont.Font(size=20, weight="bold")
        self.nav_title = Label(self, text=title, foreground=WHITE, background=DARK_BLUE, font=myFont)
        
        self.nav_title.bind("<ButtonPress-1>", self.oldxyset_label)
        self.nav_title.bind("<B1-Motion>", self.move)
        
        self.nav_title.pack(side="left", padx=(10))
        
        CTkButton(self, text='✕', cursor="hand2", corner_radius=0, fg_color=DARK_BLUE,
                  hover_color=SECOND_DARK_BLUE, width=40, command=self.close_window).pack(side="right")
        self.bind("<ButtonPress-1>", self.oldxyset)
        self.bind("<B1-Motion>", self.move)

    def oldxyset(self, event):
        self.oldx = event.x 
        self.oldy = event.y

    def oldxyset_label(self, event):
        self.oldx = event.x + self.nav_title.winfo_x()
        self.oldy = event.y + self.nav_title.winfo_y()
        
    def move(self, event):
        self.y = event.y_root - self.oldy
        self.x = event.x_root - self.oldx
        self.root.geometry(f"+{self.x}+{self.y}")
    
    def close_window(self):
        self.root.destroy()
        
# Window Setup
window = CTk()
window.geometry("450x250")

# Set Title Bar
titlebar = TitleBar(window, title="Test Window")
titlebar.pack(fill="both")

# Run
window.mainloop()