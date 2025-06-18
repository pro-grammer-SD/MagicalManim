import customtkinter
from CTkColorPicker import *
from CTkTable import *
from CTkToolTip import *

def ask_color():
    pick_color = AskColor() # open the color picker
    color = pick_color.get() # get the color string
    button.configure(fg_color=color)
    
root = customtkinter.CTk()

value = [[1,2,3,4,5],
         [1,2,3,4,5],
         [1,2,3,4,5],
         [1,2,3,4,5],
         [1,2,3,4,5]]

table = CTkTable(master=root, row=5, column=5, values=value)
table.pack(expand=True, fill="both", padx=20, pady=20)

def show_value(value):
    tooltip_1.configure(message=int(value))
    
def show_text():
    print(tooltip_2.get())

root = customtkinter.CTk()

slider = customtkinter.CTkSlider(root, from_=0, to=100, command=show_value)
slider.pack(fill="both", padx=20, pady=20)

tooltip_1 = CTkToolTip(slider, message="50")

button = customtkinter.CTkButton(root, command=show_text)
button.pack(fill="both", padx=20, pady=20)

tooltip_2 = CTkToolTip(button, delay=0.5, message="This is a CTkButton!")

button = customtkinter.CTkButton(master=root, text="CHOOSE COLOR", text_color="black", command=ask_color)
button.pack(padx=30, pady=20)
root.mainloop()