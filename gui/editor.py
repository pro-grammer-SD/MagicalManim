import ctypes
import subprocess
import sys
import threading
import json
from pathlib import Path
import customtkinter
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from manim import *
from CTkColorPicker import AskColor
from CTkListbox import *
from CTkMenuBar import *
from CTkToolTip import *
from ttkwidgets.autocomplete import AutocompleteEntry
import atexit

sys.path.append(str(Path(__file__).parent.parent))
from core.ls import get_exposed_classes, is_mobject_class, get_class_init_params, class_in_manim_animations

class Hierachy(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.label = customtkinter.CTkLabel(self, text="Heirarchy")
        self.label.place(x=230, y=10)
        self.listbox = CTkListbox(self, width=250, height=500)
        self.listbox.place(x=110, y=40)
        self.context_menu = tk.Menu(self.listbox, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.context_delete)
        self.context_menu.add_command(label="Duplicate", command=self.context_duplicate)
        self.selected_index = None

    def context_delete(self):
        if self.selected_index is not None:
            self.listbox.delete(self.selected_index)
            self.selected_index = None

    def context_duplicate(self):
        if self.selected_index is not None:
            item = self.listbox.get(self.selected_index)
            base_name = item.split(" (")[0]
            existing_items = [self.listbox.get(i) for i in range(self.listbox.size())]
            count = 1
            new_name = base_name
            while new_name in existing_items:
                count += 1
                new_name = f"{base_name} ({count})"
            self.listbox.insert("end", new_name)
            
class CodeFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.switch = customtkinter.CTkSwitch(self, text="Manual Config", command=self.toggle_edit)
        self.switch.pack(pady=10, anchor="w")
        self.textbox = customtkinter.CTkTextbox(self, width=500, height=300)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.default_code = (
            "from manim import *\n\n"
            "class Output(Scene):\n"
            "    def construct(self):\n"
            "        pass"
        )
        self.textbox.insert("1.0", self.default_code)
        self.textbox.configure(state="disabled")

    def toggle_edit(self):
        if self.switch.get():
            self.textbox.configure(state="normal")
        else:
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.default_code)
            self.textbox.configure(state="disabled")

class Properties(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.widgets = []
        self.current_props = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def clear(self):
        for w in self.widgets:
            w.destroy()
        self.widgets.clear()
        self.current_props.clear()

    def show_value_callback(self, value, val_var, tooltip_widget):
        val_var.set(str(round(value, 2)))
        tooltip_widget.configure(message=str(int(value)))

    def show_properties(self, class_obj):
        self.clear()
        row = 0
        title = customtkinter.CTkLabel(self, text=f"Name: {class_obj.__name__}", font=("Arial", 16, "bold"))
        title.grid(row=row, column=0, columnspan=2, padx=10, pady=20, sticky="w")
        self.widgets.append(title)
        row += 1
        doc_label = customtkinter.CTkLabel(self, text="Documentation:", anchor="w")
        doc_label.grid(row=row, column=0, sticky="w", padx=10, pady=(10, 0))
        self.widgets.append(doc_label)
        row += 1
        doc_text = customtkinter.CTkTextbox(self, height=150, width=500, wrap="word")
        doc_text.insert("0.0", class_obj.__doc__ or "No documentation available.")
        doc_text.configure(state="disabled")
        doc_text.grid(row=row, column=0, columnspan=2, padx=10, pady=5)
        self.widgets.append(doc_text)
        row += 1
        props = get_class_init_params(class_obj)
        for key, meta in props.items():
            default = meta.get("default", "")
            label = customtkinter.CTkLabel(self, text=f"{key}:")
            label.grid(row=row, column=0, padx=10, pady=5, sticky="e")
            self.widgets.append(label)
            default_str = str(default)
            contains_digit = any(char.isdigit() for char in default_str)
            if contains_digit:
                try:
                    value = float(default_str)
                except:
                    value = 0.0
                frame = customtkinter.CTkFrame(self)
                frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
                self.widgets.append(frame)
                val_var = customtkinter.StringVar(value=str(value))
                slider = customtkinter.CTkSlider(frame, from_=-100, to=100, width=150,
                                                 command=lambda v, var=val_var: self.show_value_callback(v, var, tooltip_1))
                slider.set(value)
                slider.pack(side="left", padx=(0, 10))
                tooltip_1 = CTkToolTip(slider, message=str(int(value)))
                entry = customtkinter.CTkEntry(frame, textvariable=val_var, width=60)
                entry.pack(side="left")
                def update_slider_from_entry(event=None):
                    val = val_var.get().strip()
                    try:
                        num = float(val)
                        slider.set(num)
                        tooltip_1.configure(message=str(round(num, 2)))
                    except ValueError:
                        pass
                entry.bind("<Return>", update_slider_from_entry)
                self.widgets.extend([slider, entry])
                self.current_props.append((label, val_var))
            else:
                entry = customtkinter.CTkEntry(self, width=200)
                entry.insert(0, default_str)
                entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")
                self.widgets.append(entry)
                self.current_props.append((label, entry))
            row += 1
        extra_label = customtkinter.CTkLabel(self, text="kwargs:")
        extra_label.grid(row=row, column=0, padx=10, pady=5, sticky="e")
        extra_entry = customtkinter.CTkEntry(self, placeholder_text="k=v,k2=v2")
        extra_entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        self.widgets.extend([extra_label, extra_entry])
        self.current_props.append((extra_label, extra_entry))
        row += 1
        if is_mobject_class(class_obj):
            color_var = customtkinter.StringVar()

            def ask_color():
                pick_color = AskColor()
                color = pick_color.get()
                color_var.set(color)
                color_button.configure(fg_color=color)

            color_button = customtkinter.CTkButton(self, text="Pick a color", command=ask_color)
            color_button.grid(row=row, column=0, columnspan=2, padx=10, pady=20)
            self.widgets.append(color_button)
            self.current_props.append((customtkinter.CTkLabel(self, text="color"), color_var))

class LogsFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.textbox = customtkinter.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("1.0", ">> Logs will appear here...\n")
        self.textbox.configure(state="disabled")

    def log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{message}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

class MiscFrame(customtkinter.CTkFrame):
    def __init__(self, master, add_sound_callback, preview_callback, render_callback, **kwargs):
        super().__init__(master, **kwargs)
        button_container = customtkinter.CTkFrame(self)
        button_container.pack(expand=True, pady=10)
        
        self.res_entry = customtkinter.CTkEntry(button_container, placeholder_text="Eg. 1080x1920", width=140)
        self.res_entry.pack(pady=(5, 10))
        
        self.add_sound_btn = customtkinter.CTkButton(button_container, text="Add Sound", command=add_sound_callback, width=140)
        self.add_sound_btn.pack(pady=5)

        self.preview_btn = customtkinter.CTkButton(button_container, text="Preview", command=preview_callback, width=140, corner_radius=32)
        self.preview_btn.pack(pady=5)

        self.render_btn = customtkinter.CTkButton(button_container, text="Render", command=render_callback, width=140, corner_radius=32)
        self.render_btn.pack(pady=5)
        
class EditorGui:
    def __init__(self):
        self.app = customtkinter.CTk()
        self.app.title("Editor | Magical Manim")
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("magicalmanim.editor")
        self.app.iconbitmap("icon/ico/image.ico")
        self.wm_ip = ImageTk.PhotoImage(Image.open("icon/png/image.png"))
        self.app.wm_iconphoto(False, self.wm_ip)
        self.app.geometry("1920x1080")
        self.props_file = Path("props.json")
        self.props_data = {}
        if self.props_file.exists():
            try:
                self.props_data = json.loads(self.props_file.read_text(encoding="utf-8"))
            except:
                self.props_data = {}
        self.sound_path = None

        add_menu = CTkTitleMenu(self.app)
        add_menu_button = add_menu.add_cascade("Add Elements", fg_color="transparent", hover=False, hover_color=None)
        add_menu_dropdown = CustomDropdownMenu(widget=add_menu_button)

        self.listbox = CTkListbox(add_menu_dropdown, height=600, width=600, command=self.add_element)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        add_menu.add_cascade("Save", fg_color="transparent", hover=False, hover_color=None, command=self.save_current_element)

        self.all_classes = get_exposed_classes()
        self.all_elements = sorted([cls.__name__ for cls in self.all_classes], key=str.lower)

        for item in self.all_elements:
            cls = next(c for c in self.all_classes if c.__name__ == item)
            name = item + " [Effect]" if class_in_manim_animations(item) and not is_mobject_class(cls) else item
            self.listbox.insert("end", name)

        self.search_entry = AutocompleteEntry(add_menu_dropdown, width=300, completevalues=self.all_elements)
        self.search_entry.place(x=200, y=0)
        self.search_entry.bind("<Return>", self.scroll_to_result)

        self.ha = Hierachy(master=self.app, width=500, height=600)
        self.ha.place(x=10, y=10)
        self.ha.listbox.bind("<<ListboxSelect>>", self.on_hierarchy_select)
        self.ha.listbox.bind("<Button-3>", self.show_hierarchy_context_menu)

        self.code = CodeFrame(master=self.app)
        self.code.place(x=10, y=620)

        self.props = Properties(master=self.app, width=600, height=900)
        self.props.place(x=1300, y=10)
        self.props.grid_propagate(False)

        self.logs_frame = LogsFrame(self.app, width=600, height=180)
        self.logs_frame.place(x=800, y=30)

        self.misc_frame = MiscFrame(
            master=self.app,
            add_sound_callback=self.add_sound,
            preview_callback=self.preview_scene,
            render_callback=self.render_scene,
            width=160,
            height=200
        )
        self.misc_frame.place(x=900, y=800)

        self.app.protocol("WM_DELETE_WINDOW", self.exit_handler)
        atexit.register(self.exit_handler)
        
        self.app.bind("<Control-e>", lambda e: self.add_element())
        self.app.bind("<Control-s>", lambda e: self.save_current_element())
        self.app.bind("<Shift-m>", self.fake_right_click)

        self.app.mainloop()

    def exit_handler(self):
        try:
            self.props_file.write_text(json.dumps(self.props_data), encoding="utf-8")
        except:
            pass
        self.app.destroy()
        sys.exit()

    def scroll_to_result(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            return
        for i, item in enumerate(self.all_elements):
            if query in item.lower():
                self.listbox.see(i)
                self.listbox.select(i)
                break

    def add_element(self, _=None):
        selection_raw = self.listbox.get()
        if not selection_raw:
            return
        selection = selection_raw.replace(" [Effect]", "")
        existing_items = [self.ha.listbox.get(i) for i in range(self.ha.listbox.size())]
        base_name = selection_raw
        count = 1
        new_name = base_name
        while new_name in existing_items:
            count += 1
            new_name = f"{base_name} ({count})"
        try:
            cls = next(c for c in get_exposed_classes() if c.__name__ == selection)
            self.props.show_properties(cls)
            self.ha.listbox.insert("end", new_name)
            if new_name not in self.props_data:
                self.props_data[new_name] = {}
        except:
            pass

    def on_hierarchy_select(self, event=None):
        selected = self.ha.listbox.get()
        if not selected:
            return
        cls_name = selected.replace(" [Effect]", "").split(" (")[0]
        try:
            cls = next(c for c in get_exposed_classes() if c.__name__ == cls_name)
            self.props.show_properties(cls)
        except:
            pass

    def show_hierarchy_context_menu(self, event):
        widget = event.widget
        y = event.y
        button_height = 30
        index = y // button_height
        if 0 <= index < len(self.ha.listbox.buttons):
            self.ha.listbox.focus_set()
            self.ha.listbox.select(index)
            self.ha.selected_index = index
            self.ha.context_menu.tk_popup(event.x_root, event.y_root)

    def save_current_element(self):
        props = {}
        for label, w in self.props.current_props:
            if hasattr(label, "cget"):
                try:
                    key = label.cget("text").rstrip(":")
                    val = w.get()
                    props[key] = val
                except:
                    continue
        selected = self.ha.listbox.get()
        if selected:
            parsed = {}
            for k, v in props.items():
                if k == "kwargs":
                    kvs = v.strip()
                    for kv in kvs.split(","):
                        if "=" in kv:
                            kk, vv = kv.split("=",1)
                            parsed[kk.strip()] = self.parse_value(vv.strip())
                else:
                    parsed[k] = self.parse_value(v)
            self.props_data[selected] = parsed
            try:
                self.props_file.write_text(json.dumps(self.props_data), encoding="utf-8")
            except:
                pass
            self.update_code()

    def parse_value(self, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("$") and v.endswith("$"):
                return {"__raw__": v[1:-1]}
            try:
                return json.loads(v)
            except:
                return v
        return v

    def update_code(self):
        lines = ["from manim import *", "", "class Output(Scene):", "    def construct(self):"]
        if self.sound_path:
            lines.append(f'        self.add_sound(r"{self.sound_path}")')
        effects = []
        for i in range(self.ha.listbox.size()):
            name = self.ha.listbox.get(i)
            cls_name = name.replace(" [Effect]", "").split(" (")[0]
            var_name = name.replace(" [Effect]", "").replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_").lower()
            params = self.props_data.get(name, {})
            def format_val(v):
                if isinstance(v, dict) and "__raw__" in v:
                    return v["__raw__"]
                if isinstance(v, str):
                    return repr(v)
                return repr(v)

            raw_params = self.props_data.get(name, {})
            params = {
                k: v for k, v in raw_params.items()
                if v not in [None, ""] and (not isinstance(v, str) or "!ignore!" not in v)
            }
            param_str = ", ".join(f"{k}={format_val(v)}" for k, v in params.items())
            if " [Effect]" in name:
                effects.append(f"        self.play({cls_name}({param_str}))")
            else:
                lines.append(f"        {var_name} = {cls_name}({param_str})")
        lines.extend(effects)
        code = "\n".join(lines)
        self.code.textbox.configure(state="normal")
        self.code.textbox.delete("1.0", "end")
        self.code.textbox.insert("1.0", code)
        self.code.textbox.configure(state="disabled")
        with open("script.py", "w", encoding="utf-8") as f:
            f.write(code)
            
    def fake_right_click(self, event=None):
        x, y = self.app.winfo_pointerxy()
        widget = self.app.winfo_containing(x, y)
        if widget and widget == self.ha.listbox:
            rel_y = y - widget.winfo_rooty()
            button_height = 30
            index = rel_y // button_height
            if 0 <= index < len(self.ha.listbox.buttons):
                self.ha.listbox.select(index)
                self.ha.selected_index = index
                self.ha.context_menu.tk_popup(x, y)

    def add_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")])
        if path:
            self.sound_path = path
            self.update_code()
    
    def preview_scene(self):
        lines = self.code.textbox.get("1.0", "end-1c").splitlines()
        out = []
        inside_construct = False
        added_embed = False

        for ln in lines:
            stripped = ln.strip()

            if "self.interactive_embed()" in stripped:
                continue

            if stripped.startswith("def construct"):
                inside_construct = True

            if inside_construct and not added_embed:
                if stripped == "" or (stripped.startswith("def") and not stripped.startswith("def construct")):
                    out.append("        self.interactive_embed()")
                    added_embed = True

            out.append(ln)

        if not added_embed:
            out.append("        self.interactive_embed()")

        script = "\n".join(out)
        with open("script.py", "w", encoding="utf-8") as f:
            f.write(script)

        def run():
            cmd = ["manim", "script.py", "Output", "--renderer=opengl", "--enable_gui", "-p"]
            self.logs_frame.log(">> " + " ".join(cmd))
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.logs_frame.log(line.strip())

        threading.Thread(target=run, daemon=True).start()

    def render_scene(self):
        res = self.misc_frame.res_entry.get().strip()
        try:
            w, h = map(int, res.lower().split("x"))
        except:
            w, h = 1920, 1080
        with open("script.py", "w", encoding="utf-8") as f:
            f.write(self.code.textbox.get("1.0", "end-1c"))

        def run():
            cmd = ["manim", "script.py", "Output", "-pqm", "--resolution", f"{w},{h}"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.logs_frame.log(line.strip())

        threading.Thread(target=run, daemon=True).start()

EditorGui()
