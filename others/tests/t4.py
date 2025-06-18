import customtkinter
from tkinterdnd2 import TkinterDnD, DND_ALL

class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def get_path(event):
    dropped_file = event.data.replace("{","").replace("}", "")
    print(dropped_file)

root = CTk()
root.drop_target_register(DND_ALL)
root.dnd_bind("<<Drop>>", get_path)

root.mainloop()