import customtkinter

def button_event():
    print("button pressed")

root = customtkinter.CTk()
root.title("Grid Table Example")
root.geometry("600x400")

for row in range(5):
    for col in range(5):
        if row == 0 and col == 4:
            btn = customtkinter.CTkButton(master=root, text="CTkButton", width=140, height=28, command=button_event)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        else:
            label = customtkinter.CTkLabel(master=root, text=f"{row+1},{col+1}")
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

# Make grid cells expand with window resize
for i in range(5):
    root.grid_columnconfigure(i, weight=1)
    root.grid_rowconfigure(i, weight=1)

root.mainloop()
