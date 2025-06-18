import threading
from CTkListbox import *
import customtkinter

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("500x500")
        self.title("Smart Listbox Search")

        self.entry = customtkinter.CTkEntry(self, placeholder_text="Search here...")
        self.entry.pack(pady=10)
        self.entry.bind("<KeyRelease>", self.start_filter_thread)

        self.listbox = CTkListbox(self, height=400)
        self.listbox.pack(fill="both", expand=True)

        self.all_items = sorted({i for i in dir(__builtins__) if not i.startswith("_")})
        self.current_items = []
        self.last_query = ""
        self.update_listbox(self.all_items)

    def start_filter_thread(self, event=None):
        query = self.entry.get().lower()
        if query != self.last_query:
            self.last_query = query
            threading.Thread(target=self.filter_list, args=(query,), daemon=True).start()

    def filter_list(self, search):
        filtered = [i for i in self.all_items if search in i.lower()]
        if filtered != self.current_items:
            self.after(0, lambda: self.update_listbox(filtered))

    def update_listbox(self, items):
        old = self.current_items
        new = items
        if old == new:
            return

        len_old = len(old)
        len_new = len(new)

        min_len = min(len_old, len_new)
        for i in range(min_len):
            if old[i] != new[i]:
                self.listbox.delete(i, "end")
                for j in range(i, len_new):
                    self.listbox.insert("end", new[j])
                self.current_items = new
                return

        if len_old > len_new:
            self.listbox.delete(len_new, "end")
        elif len_new > len_old:
            for i in range(len_old, len_new):
                self.listbox.insert("end", new[i])

        self.current_items = new

app = App()
app.mainloop()
