import inspect
import re
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QPlainTextEdit, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSlider, QMessageBox, QColorDialog, QSpinBox, QMenu
)
from manim import *

sys.path.append(str(Path(__file__).parent.parent))
from core.elements import get_exposed_classes, get_class_init_params, class_in_manim_animations

from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class ProcThread(QThread):
    line = Signal(str)
    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
    def run(self):
        p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for ln in p.stdout:
            self.line.emit(ln.rstrip())
            
class AIThread(QThread):
    finished = Signal(str)
    log = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            self.log.emit(f"Generating AI code for: {self.prompt}")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are a code generation bot. Only output working Python Manim code, "
                        "no explanations or extra text. Generate complete, functional, properly formatted Python code."
                    )
                ),
                contents=self.prompt
            ).text
            code = re.sub(r'^```[\w]*\s*', '', response)
            code = re.sub(r'\s*```$', '', code).strip()
            self.finished.emit(code)
        except Exception as e:
            self.log.emit(f"AI generation failed: {e}")
            self.finished.emit("")
class PropertiesTable(QTableWidget):
    valueChanged = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Property", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self._widgets = {}
        self._meta = {}
        self._color_btn = None

    def clear_props(self):
        self.setRowCount(0)
        self._widgets.clear()
        self._meta.clear()
        self._color_btn = None

    def _add_row(self, key, widget):
        r = self.rowCount()
        self.insertRow(r)
        self.setItem(r, 0, QTableWidgetItem(key))
        self.setCellWidget(r, 1, widget)
        self._widgets[key] = widget
        
    def _focused_lineedit(self):
        w = QApplication.focusWidget()
        return w if isinstance(w, QLineEdit) else None

    def surround_with_dollars(self):
        e = self._focused_lineedit()
        if e:
            txt = e.text()
            if not (txt.startswith("$") and txt.endswith("$")):
                e.setText(f"${txt}$")
            self.emit_values()

    def surround_with_exclaim(self):
        e = self._focused_lineedit()
        if e:
            txt = e.text()
            if not (txt.startswith("!") and txt.endswith("!")):
                e.setText(f"!{txt}!")
            self.emit_values()
            
    def show_properties(self, cls, params=None):
        self.clear_props()
        if not cls:
            return
        if params is None:
            params = {}

        sig = inspect.signature(cls.__init__)
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            val = params.get(name, getattr(param, "default", ""))
            if val is inspect.Parameter.empty:
                val = ""
            if isinstance(val, (int, float)):
                wrap = QWidget()
                lay = QHBoxLayout(wrap)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.setSpacing(4)
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(-10000)
                slider.setMaximum(10000)
                slider.setValue(int(float(val) * 100))
                entry = QLineEdit(str(val))
                entry.setMaximumWidth(80)
                slider.valueChanged.connect(lambda v, e=entry: e.setText(str(round(v / 100, 2))))
                entry.editingFinished.connect(lambda s=entry, sl=slider: sl.setValue(int(float(s.text()) * 100)))
                lay.addWidget(slider)
                lay.addWidget(entry)
                self._add_row(name, wrap)
            elif isinstance(val, str):
                le = QLineEdit(val)
                le.setMinimumHeight(28)
                self._add_row(name, le)
            elif isinstance(val, QColor):
                self.add_color_picker(val.name())
            else:
                self._add_row(name, QLineEdit(repr(val)))

    def add_color_picker(self, existing_hex=None):
        btn = QPushButton(existing_hex or "Pick color")
        btn.setMinimumHeight(28)
        btn.setStyleSheet(f"background:{existing_hex or '#FFFFFF'};")
        def pick():
            col = QColorDialog.getColor()
            if col.isValid():
                btn.setText(col.name())
                btn.setStyleSheet(f"background:{col.name()};")
                self.emit_values()
        btn.clicked.connect(pick)
        self._add_row("color", btn)
        self._color_btn = btn

    def values(self):
        out = {}
        for key, w in self._widgets.items():
            if isinstance(w, QWidget) and isinstance(w.layout(), QHBoxLayout):
                e = w.layout().itemAt(1).widget()
                out[key] = e.text()
            elif isinstance(w, QLineEdit):
                out[key] = w.text()
            elif isinstance(w, QPushButton):
                t = w.text()
                if t.lower() != "pick color":
                    out[key] = t
        return out

    def emit_values(self):
        self.valueChanged.emit(self.values())

class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor | Magical Manim")
        self.resize(1500, 950)
        self.props_path = Path("props.json")
        self.props_data = {}
        if self.props_path.exists():
            try:
                self.props_data = json.loads(self.props_path.read_text(encoding="utf-8"))
            except:
                self.props_data = {}
        self.sound_path = None
        self.ai_generated_code = ""
        self.all_classes = get_exposed_classes()
        self.all_names = sorted([c.__name__ for c in self.all_classes], key=str.lower)
        self.class_map = {c.__name__: c for c in self.all_classes}
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(120)
        self.scene_elements = []
        self.props = PropertiesTable()
        self.setup_actions()
        self.setup_central()
        self.setup_docks()
        self.refresh_elements_list()
        self.update_code()

    def setup_actions(self):
        bar = self.menuBar()
        filem = bar.addMenu("File")
        act_save_script = QAction("Save Script", self)
        act_save_script.setShortcut("Ctrl+Shift+S")
        act_save_script.triggered.connect(self.save_script)
        filem.addAction(act_save_script)
        act_save_props = QAction("Save Element Props", self)
        act_save_props.setShortcut("Ctrl+S")
        act_save_props.triggered.connect(self.save_current_element)
        filem.addAction(act_save_props)
        act_export = QAction("Export Props As JSON", self)
        act_export.triggered.connect(self.export_props)
        filem.addAction(act_export)
        act_import = QAction("Import Props JSON", self)
        act_import.triggered.connect(self.import_props)
        filem.addAction(act_import)
        editm = bar.addMenu("Edit")
        act_add_elem = QAction("Add Selected Element", self)
        act_add_elem.setShortcut("Ctrl+E")
        act_add_elem.triggered.connect(self.add_element_from_pool)
        editm.addAction(act_add_elem)
        act_dup = QAction("Duplicate Selected", self)
        act_dup.setShortcut("Ctrl+D")
        act_dup.triggered.connect(self.duplicate_selected)
        editm.addAction(act_dup)
        act_del = QAction("Delete Selected", self)
        act_del.setShortcut("Del")
        act_del.triggered.connect(self.delete_selected)
        editm.addAction(act_del)
        act_wrap_dollar = QAction("Surround with $$", self)
        act_wrap_dollar.setShortcut("Ctrl+L")
        act_wrap_dollar.triggered.connect(self.props.surround_with_dollars)
        editm.addAction(act_wrap_dollar)
        act_wrap_exclaim = QAction("Surround with !!", self)
        act_wrap_exclaim.setShortcut("Ctrl+I")
        act_wrap_exclaim.triggered.connect(self.props.surround_with_exclaim)
        editm.addAction(act_wrap_exclaim)
        runm = bar.addMenu("Run")
        act_preview = QAction("Preview", self)
        act_preview.triggered.connect(self.preview_scene)
        runm.addAction(act_preview)
        act_render = QAction("Render", self)
        act_render.triggered.connect(self.render_scene)
        runm.addAction(act_render)
        aim = bar.addMenu("AI")
        act_generate = QAction("Generate With AI", self)
        act_generate.setShortcut("Ctrl+G")
        act_generate.triggered.connect(self.generate_with_ai)
        aim.addAction(act_generate)
        helpm = bar.addMenu("Help")
        about = QAction("About", self)
        about.triggered.connect(lambda: QMessageBox.information(self, "About", "Magical Manim with AI"))
        helpm.addAction(about)

    def setup_central(self):
        central = QWidget()
        lay = QVBoxLayout(central)
        code_bar = QHBoxLayout()
        self.res_w = QSpinBox()
        self.res_h = QSpinBox()
        self.res_w.setRange(256, 7680)
        self.res_h.setRange(256, 4320)
        self.res_w.setValue(1920)
        self.res_h.setValue(1080)
        code_bar.addWidget(QLabel("W"))
        code_bar.addWidget(self.res_w)
        code_bar.addWidget(QLabel("H"))
        code_bar.addWidget(self.res_h)
        code_bar.addStretch(1)
        lay.addLayout(code_bar)
        self.code = QPlainTextEdit()
        self.code.setReadOnly(True)
        lay.addWidget(self.code, 1)
        self.setCentralWidget(central)

    def _lock_dock(self, dock):
        dock.setFeatures(QDockWidget.DockWidgetMovable)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setTitleBarWidget(QWidget())

    def setup_docks(self):
        self.elements_dock = QDockWidget("Elements", self)
        elw = QWidget()
        v = QVBoxLayout(elw)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search elements")
        self.search.textChanged.connect(self._schedule_search)
        v.addWidget(self.search)
        self.elements_list = QListWidget()
        self.elements_list.itemDoubleClicked.connect(self.add_element_from_pool)
        v.addWidget(self.elements_list, 1)
        self.elements_dock.setWidget(elw)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.elements_dock)
        self._lock_dock(self.elements_dock)

        self.elements_tree_dock = QDockWidget("Elements Tree", self)
        self.elements = QTreeWidget()
        self.elements.setHeaderHidden(True)
        self.elements.itemSelectionChanged.connect(self.on_elements_select)
        self.elements.setContextMenuPolicy(Qt.CustomContextMenu)
        self.elements.customContextMenuRequested.connect(self.show_elements_menu)
        self.elements_tree_dock.setWidget(self.elements)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.elements_tree_dock)
        self._lock_dock(self.elements_tree_dock)
        self.tabifyDockWidget(self.elements_dock, self.elements_tree_dock)
        self.elements_dock.raise_()

        self.props_dock = QDockWidget("Properties", self)
        self.props.valueChanged.connect(self.on_props_changed)
        self.props_dock.setWidget(self.props)
        self.addDockWidget(Qt.RightDockWidgetArea, self.props_dock)
        self._lock_dock(self.props_dock)

        self.logs_dock = QDockWidget("Logs", self)
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs_dock.setWidget(self.logs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logs_dock)
        self._lock_dock(self.logs_dock)

        self.misc_dock = QDockWidget("Actions", self)
        mw = QWidget()
        mv = QVBoxLayout(mw)
        self.btn_add_sound = QPushButton("Add Sound")
        self.btn_add_sound.clicked.connect(self.add_sound)
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.clicked.connect(self.preview_scene)
        self.btn_render = QPushButton("Render")
        self.btn_render.clicked.connect(self.render_scene)
        self.btn_add_elem = QPushButton("Add Selected Element")
        self.btn_add_elem.clicked.connect(self.add_element_from_pool)
        self.btn_dup = QPushButton("Duplicate Selected")
        self.btn_dup.clicked.connect(self.duplicate_selected)
        self.btn_del = QPushButton("Delete Selected")
        self.btn_del.clicked.connect(self.delete_selected)
        for btn in [self.btn_add_sound, self.btn_add_elem, self.btn_dup, self.btn_del, self.btn_preview, self.btn_render]:
            mv.addWidget(btn)
        mv.addStretch(1)
        self.misc_dock.setWidget(mw)
        self.addDockWidget(Qt.RightDockWidgetArea, self.misc_dock)
        self._lock_dock(self.misc_dock)

        self.ai_dock = QDockWidget("Generate with AI", self)
        aiw = QWidget()
        aiv = QVBoxLayout(aiw)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Describe Python Manim code to generate")
        self.ai_btn = QPushButton("Generate")
        self.ai_btn.clicked.connect(self.generate_with_ai)
        self.ai_output = QPlainTextEdit()
        self.ai_output.setReadOnly(True)
        aiv.addWidget(self.ai_input)
        aiv.addWidget(self.ai_btn)
        aiv.addWidget(self.ai_output, 1)
        self.ai_dock.setWidget(aiw)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_dock)
        self._lock_dock(self.ai_dock)
        
    def on_props_changed(self, vals):
        item = self.elements.currentItem()
        if not item:
            return
        cls = item.data(0, Qt.UserRole).get("cls")
        props = item.data(0, Qt.UserRole).get("props", {})
        
        for k, v in vals.items():
            try:
                if isinstance(v, str):
                    if re.match(r"^-?\d+(\.\d+)?$", v):
                        props[k] = float(v) if "." in v else int(v)
                    elif re.match(r"^[A-Z_]+$", v):  
                        props[k] = v
                    else:
                        props[k] = v
                else:
                    props[k] = v
            except:
                props[k] = v

        item.setData(0, Qt.UserRole, {"cls": cls, "props": props})
        self.update_code()

    def _schedule_search(self):
        self.search_timer.stop()
        self.search_timer.timeout.connect(self._apply_search)
        self.search_timer.start()

    def _apply_search(self):
        txt = self.search.text().lower()
        self.elements_list.clear()
        for name in self.all_names:
            if txt in name.lower():
                QListWidgetItem(name, self.elements_list)

    def refresh_elements_list(self):
        self.elements_list.clear()
        for name in self.all_names:
            QListWidgetItem(name, self.elements_list)
            
    def rebuild_elements_tree_from_code(self, code_text):
        self.elements.clear()
        self.props_data.clear()
        import ast

        try:
            if "class " in code_text and "Scene" in code_text:
                tree = ast.parse(code_text)
            else:
                code_wrapped = "class DummyScene(Scene):\n"
                for line in code_text.splitlines():
                    code_wrapped += "    " + line + "\n"
                tree = ast.parse(code_wrapped)
        except Exception as e:
            self.logs.appendPlainText(f"Failed to parse code: {e}")
            return

        def extract_calls(node):
            elements = []
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    elements.append((node.targets[0].id, node.value))
            elif isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call):
                    call = node.value
                    if hasattr(call.func, "id") or hasattr(call.func, "attr"):
                        elements.append((None, call))
            for child in ast.iter_child_nodes(node):
                elements.extend(extract_calls(child))
            return elements

        scene_body = []
        
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                for base in n.bases:
                    if getattr(base, "id", None) == "Scene":
                        scene_body = n.body
                        break

        calls = []
        for node in scene_body:
            calls.extend(extract_calls(node))

        for idx, (var_name, call) in enumerate(calls):
            cls_node = call.func
            cls_name = cls_node.id if isinstance(cls_node, ast.Name) else getattr(cls_node, "attr", "Unknown")
            params = {}
            for i, arg in enumerate(call.args):
                try:
                    params[f"arg{i}"] = ast.literal_eval(arg)
                except:
                    params[f"arg{i}"] = None
            for kw in call.keywords:
                try:
                    params[kw.arg] = ast.literal_eval(kw.value)
                except:
                    params[kw.arg] = None
            display_name = f"{var_name or f'{cls_name}_{idx}'} ({cls_name})"
            item = QTreeWidgetItem([display_name])
            self.elements.addTopLevelItem(item)
            self.props_data[display_name] = params
            cls = self.class_map.get(cls_name)
            item.setData(0, Qt.UserRole, {"cls": cls, "props": params})
            
    def add_element_from_pool(self):
        it = self.elements_list.currentItem()
        if not it:
            return
        cls_name = it.text().replace(" [Effect]", "")
        names = self.current_elements_names()
        base_var = re.sub(r"[^0-9a-zA-Z_]+", "_", cls_name).lower()
        new_var = base_var
        count = 1
        while any(new_var in n for n in names):
            count += 1
            new_var = f"{base_var}{count}"
        display_name = f"{new_var} ({cls_name})"
        
        node = QTreeWidgetItem([display_name])
        self.elements.addTopLevelItem(node)
        if display_name not in self.props_data:
            self.props_data[display_name] = {}
        
        cls = self.class_map.get(cls_name)
        node.setData(0, Qt.UserRole, {"cls": cls, "props": {}})
        if cls:
            self.show_properties_for(cls)
        self.update_code()
        
    def current_elements_names(self):
        names = []
        root = self.elements.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            names.append(item.text(0))
        return names
    
    def on_elements_select(self):
        item = self.elements.currentItem()
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        cls = data.get("cls")
        
        self.props.show_properties(cls)
        if "color" in get_class_init_params(cls):
            self.props.add_color_picker()
            
        self.props.valueChanged.disconnect()
        self.props.valueChanged.connect(lambda v, it=item: self._update_element_props(it, v))

    def _update_element_props(self, item, vals):
        cls = item.data(0, Qt.UserRole).get("cls")
        item.setData(0, Qt.UserRole, {"cls": cls, "props": vals})
        self.update_code()
        
    def show_properties_for(self, cls):
        if not cls:
            return
        self.props.show_properties(cls)
        if "color" in get_class_init_params(cls):
            self.props.add_color_picker()
            
    def duplicate_selected(self):
        item = self.elements.currentItem()
        if not item:
            return
        name = item.text(0)
        cls = item.data(0, Qt.UserRole).get("cls")
        props = dict(item.data(0, Qt.UserRole).get("props", {}))

        # ensure unique name
        base_name = name.split(" (")[0]
        cls_name = name.split(" (")[1][:-1] if "(" in name else name
        count = 1
        new_name = f"{base_name}_copy"
        while new_name in self.current_elements_names():
            count += 1
            new_name = f"{base_name}_copy{count}"
        display_name = f"{new_name} ({cls_name})"

        # create tree item
        clone = QTreeWidgetItem([display_name])
        clone.setData(0, Qt.UserRole, {"cls": cls, "props": props})
        self.elements.addTopLevelItem(clone)

        # store props
        self.props_data[display_name] = props

        # refresh code
        self.update_code()

    def delete_selected(self):
        item = self.elements.currentItem()
        if item:
            index = self.elements.indexOfTopLevelItem(item)
            self.elements.takeTopLevelItem(index)
            self.update_code()

    def preview_scene(self):
        self.sync_current_props()
        self.update_code()
        code_path = Path("temp_scene.py")
        code_path.write_text(self.code.toPlainText(), encoding="utf-8")
        cmd = [sys.executable, "-m", "manim", str(code_path), "-pql", "-p"]
        self.logs.appendPlainText("Previewing scene...")
        self._run_cmd(cmd)

    def render_scene(self):
        self.sync_current_props()
        self.update_code()
        code_path = Path("temp_scene.py")
        code_path.write_text(self.code.toPlainText(), encoding="utf-8")
        w, h = self.res_w.value(), self.res_h.value()
        cmd = [sys.executable, "-m", "manim", str(code_path), "-ql", f"--media_dir=media", f"--fps=60", f"--resolution={w},{h}", "-p"]
        self.logs.appendPlainText("Rendering scene...")
        self._run_cmd(cmd)

    def _run_cmd(self, cmd):
        self.proc = ProcThread(cmd)
        self.proc.line.connect(lambda ln: self.logs.appendPlainText(ln))
        self.proc.start()
        
    def save_script(self):
        code_text = self.code.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "Save Script", "script.py", "Python Files (*.py)")
        if path:
            Path(path).write_text(code_text, encoding="utf-8")
            self.logs.appendPlainText(f"Saved script to {path}")
            
    def save_current_element(self):
        item = self.elements.currentItem()
        if not item:
            return

        # Update props_data with the current element's properties
        self.props_data[item.text(0)] = item.data(0, Qt.UserRole).get("props", {})

        # Save props.json
        self.props_path.write_text(json.dumps(self.props_data, indent=4), encoding="utf-8")
        self.logs.appendPlainText(f"Saved properties of {item.text(0)}")

        # Refresh code and write to script.py
        self.update_code()
        Path("script.py").write_text(self.code.toPlainText(), encoding="utf-8")
        self.logs.appendPlainText("Synced props into script.py")

    def export_props(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Props JSON", "", "JSON Files (*.json)")
        if not path:
            return
        all_props = {}
        for i in range(self.elements.topLevelItemCount()):
            itm = self.elements.topLevelItem(i)
            all_props[itm.text(0)] = itm.data(0, Qt.UserRole).get("props", {})
        Path(path).write_text(json.dumps(all_props, indent=4), encoding="utf-8")
        self.logs.appendPlainText(f"Exported props to {path}")
        
    def import_props(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Props JSON", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            for name, props in data.items():
                cls = self.class_map.get(name)
                if not cls:
                    continue
                item = QTreeWidgetItem([name])
                item.setData(0, Qt.UserRole, {"cls": cls, "props": props})
                self.elements.addTopLevelItem(item)
            self.logs.appendPlainText(f"Imported props from {path}")
        except Exception as e:
            self.logs.appendPlainText(f"Failed import: {e}")

    def show_elements_menu(self, pos):
        item = self.elements.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        act_dup = QAction("Duplicate", self)
        act_dup.triggered.connect(self.duplicate_selected)
        act_del = QAction("Delete", self)
        act_del.triggered.connect(self.delete_selected)
        menu.addAction(act_dup)
        menu.addAction(act_del)
        menu.exec(self.elements.viewport().mapToGlobal(pos))

    def add_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.mp3 *.wav)")
        if not path:
            return
        self.sound_path = path
        self.logs.appendPlainText(f"Added sound: {path}")

    def update_code(self):
        def format_param(k, v):
            if isinstance(v, str):
                if v.startswith("!") and v.endswith("!"):
                    return None
                elif v.startswith("$") and v.endswith("$"):
                    inner = v[1:-1]
                    return f"{k}={inner}"
                else:
                    return f"{k}={repr(v)}"
            else:
                return f"{k}={v}"

        self.sync_current_props()
        if self.ai_generated_code:
            code = self.ai_generated_code
            lines = code.splitlines()
            insert_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith("def construct"):
                    insert_idx = i + 1
                    break
            if insert_idx:
                if self.sound_path and "self.add_sound" not in "\n".join(lines):
                    lines.insert(insert_idx, f'        self.add_sound(r"{self.sound_path}")')

                for i in range(self.elements.topLevelItemCount()):
                    item = self.elements.topLevelItem(i)
                    name = item.text(0)
                    cls_name = name.split(" (")[1][:-1] if "(" in name else name
                    raw_params = self.props_data.get(name, {})

                    param_parts = []
                    for k, v in raw_params.items():
                        part = format_param(k, v)
                        if part:
                            param_parts.append(part)
                    param_str = ", ".join(param_parts)

                    cls = self.class_map.get(cls_name)
                    if not cls:
                        continue

                    if class_in_manim_animations(cls):
                        new_line = f"        self.play({cls_name}({param_str}))"
                    else:
                        var_name = re.sub(r"[^0-9a-zA-Z_]+", "_", name.split(" (")[0]).lower()
                        new_line = f"        {var_name} = {cls_name}({param_str})"

                    lines.insert(insert_idx, new_line)

            code = "\n".join(lines)
        else:
            lines = ["from manim import *", "", "class Output(Scene):", "    def construct(self):"]
            if self.sound_path:
                lines.append(f'        self.add_sound(r"{self.sound_path}")')

            for i in range(self.elements.topLevelItemCount()):
                item = self.elements.topLevelItem(i)
                name = item.text(0)
                cls_name = name.split(" (")[1][:-1] if "(" in name else name
                raw_params = self.props_data.get(name, {})

                param_parts = []
                for k, v in raw_params.items():
                    part = format_param(k, v)
                    if part:
                        param_parts.append(part)
                param_str = ", ".join(param_parts)

                cls = self.class_map.get(cls_name)
                if not cls:
                    continue

                if class_in_manim_animations(cls):
                    lines.append(f"        self.play({cls_name}({param_str}))")
                else:
                    var_name = re.sub(r"[^0-9a-zA-Z_]+", "_", name.split(" (")[0]).lower()
                    lines.append(f"        {var_name} = {cls_name}({param_str})")

            code = "\n".join(lines)

        self.code.blockSignals(True)
        self.code.setPlainText(code)
        self.code.blockSignals(False)
        Path("script.py").write_text(code, encoding="utf-8")
        
    def sync_current_props(self):
        item = self.elements.currentItem()
        if item:
            self.props_data[item.text(0)] = self.props.values()
        
    def generate_with_ai(self):
        prompt = self.ai_input.text().strip()
        if not prompt:
            return
        if not client:
            self.logs.appendPlainText("No Gemini API key provided")
            return

        self.ai_btn.setEnabled(False)
        self.logs.appendPlainText(f"Starting AI generation for: {prompt}")

        def on_finished(code_text):
            self.ai_btn.setEnabled(True)
            if code_text:
                self.ai_generated_code = code_text  # store full AI code for retention
                self.ai_output.setPlainText(code_text)
                self.code.setPlainText(code_text)
                self.rebuild_elements_tree_from_code(code_text)
                self.update_code()  # merge current props and sound
            else:
                self.logs.appendPlainText("AI generation returned empty code")

        self.ai_thread = AIThread(prompt)
        self.ai_thread.finished.connect(on_finished)
        self.ai_thread.log.connect(lambda ln: self.logs.appendPlainText(ln))
        self.ai_thread.start()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(Path("styles.qss").read_text())
    font_id = QFontDatabase.addApplicationFont("fonts/Inter_18pt-Regular.ttf")
    family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(family, 10))
    w = EditorWindow()
    w.show()
    sys.exit(app.exec())
    