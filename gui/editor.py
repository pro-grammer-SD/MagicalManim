import sys
import os
import json
import re
import ast
import subprocess
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QPlainTextEdit, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QMessageBox, QColorDialog, QCheckBox,
    QMenu, QSpinBox
)
from manim import *
import qt_themes

sys.path.append(str(Path(__file__).parent.parent))
from core.elements import get_exposed_classes, is_mobject_class, get_class_init_params, class_in_manim_animations

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
    def show_properties(self, cls_obj):
        self.clear_props()
        props = get_class_init_params(cls_obj)
        for key, meta in props.items():
            d = meta.get("default", "")
            self._meta[key] = meta
            s = str(d)
            has_digit = any(ch.isdigit() for ch in s)
            if has_digit:
                try:
                    val = float(s)
                except:
                    val = 0.0
                wrap = QWidget()
                lay = QHBoxLayout(wrap)
                lay.setContentsMargins(0, 0, 0, 0)
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(-10000)
                slider.setMaximum(10000)
                slider.setValue(int(val * 100))
                entry = QLineEdit(str(val))
                def on_slide(v, e=entry):
                    vv = round(v/100.0, 2)
                    e.setText(str(vv))
                    self.emit_values()
                def on_entry():
                    try:
                        vv = float(entry.text().strip())
                    except:
                        vv = 0.0
                    slider.setValue(int(vv*100))
                    self.emit_values()
                slider.valueChanged.connect(on_slide)
                entry.editingFinished.connect(on_entry)
                lay.addWidget(slider)
                lay.addWidget(entry)
                self._add_row(key, wrap)
            else:
                entry = QLineEdit()
                entry.setText(s)
                entry.editingFinished.connect(self.emit_values)
                self._add_row(key, entry)
        extra = QLineEdit()
        extra.setPlaceholderText("k=v,k2=v2")
        extra.editingFinished.connect(self.emit_values)
        self._add_row("kwargs", extra)
    def add_color_picker(self, existing_hex=None):
        btn = QPushButton(existing_hex or "Pick color")
        def pick():
            col = QColorDialog.getColor()
            if col.isValid():
                btn.setText(col.name())
                btn.setStyleSheet(f"background:{col.name()}")
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
        self.all_classes = get_exposed_classes()
        self.all_names = sorted([c.__name__ for c in self.all_classes], key=str.lower)
        self.class_map = {c.__name__: c for c in self.all_classes}
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(120)
        self.setup_actions()
        self.setup_central()
        self.setup_docks()
        self.refresh_elements_list()
        self.update_code()
    def setup_actions(self):
        bar = self.menuBar()
        filem = bar.addMenu("File")
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
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        bar = QWidget()
        dock.setTitleBarWidget(bar)
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
        self.props = PropertiesTable()
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
        mv.addWidget(self.btn_add_sound)
        mv.addWidget(self.btn_add_elem)
        mv.addWidget(self.btn_dup)
        mv.addWidget(self.btn_del)
        mv.addWidget(self.btn_preview)
        mv.addWidget(self.btn_render)
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
    def refresh_elements_list(self):
        self.elements_list.clear()
        for n in self.all_names:
            c = self.class_map.get(n)
            label = n + " [Effect]" if class_in_manim_animations(n) and not is_mobject_class(c) else n
            self.elements_list.addItem(label)
    def _schedule_search(self):
        self.search_timer.stop()
        self.search_timer.timeout.connect(self.apply_search)
        self.search_timer.start()
    def apply_search(self):
        q = self.search.text().strip().lower()
        for i in range(self.elements_list.count()):
            it = self.elements_list.item(i)
            text = it.text().lower()
            it.setHidden(False if q == "" else (q not in text))
    def current_elements_names(self):
        out = []
        for i in range(self.elements.topLevelItemCount()):
            out.append(self.elements.topLevelItem(i).text(0))
        return out
    def add_element_from_pool(self):
        it = self.elements_list.currentItem()
        if not it:
            return
        label = it.text()
        base = label
        names = self.current_elements_names()
        new_name = base
        num = 1
        while new_name in names:
            num += 1
            new_name = f"{base} ({num})"
        node = QTreeWidgetItem([new_name])
        self.elements.addTopLevelItem(node)
        if new_name not in self.props_data:
            self.props_data[new_name] = {}
        cls_name = label.replace(" [Effect]", "")
        cls = self.class_map.get(cls_name)
        if cls:
            self.show_properties_for(cls)
        self.update_code()
    def on_elements_select(self):
        it = self.elements.currentItem()
        if not it:
            return
        title = it.text(0)
        cls_name = title.replace(" [Effect]", "").split(" (")[0]
        cls = self.class_map.get(cls_name)
        if cls:
            self.show_properties_for(cls, existing=self.props_data.get(title, {}))
    def show_elements_menu(self, pos):
        it = self.elements.itemAt(pos)
        if not it:
            return
        menu = QMenu(self)
        act_del = QAction("Delete", self)
        act_dup = QAction("Duplicate", self)
        act_del.triggered.connect(self.delete_selected)
        act_dup.triggered.connect(self.duplicate_selected)
        menu.addAction(act_dup)
        menu.addAction(act_del)
        menu.exec_(self.elements.mapToGlobal(pos))
    def delete_selected(self):
        it = self.elements.currentItem()
        if not it:
            return
        name = it.text(0)
        idx = self.elements.indexOfTopLevelItem(it)
        if idx >= 0:
            self.elements.takeTopLevelItem(idx)
        if name in self.props_data:
            del self.props_data[name]
        self.update_code()
    def duplicate_selected(self):
        it = self.elements.currentItem()
        if not it:
            return
        base = it.text(0)
        names = self.current_elements_names()
        new_name = base
        count = 1
        while new_name in names:
            count += 1
            new_name = f"{base} ({count})"
        node = QTreeWidgetItem([new_name])
        self.elements.addTopLevelItem(node)
        self.props_data[new_name] = dict(self.props_data.get(base, {}))
        self.update_code()
    def show_properties_for(self, cls, existing=None):
        self.props.show_properties(cls)
        if is_mobject_class(cls):
            self.props.add_color_picker(existing.get("color") if existing else None)
        if existing:
            for key, w in self.props._widgets.items():
                if key in existing:
                    v = existing[key]
                    if isinstance(w, QWidget) and isinstance(w.layout(), QHBoxLayout):
                        e = w.layout().itemAt(1).widget()
                        try:
                            e.setText(str(v))
                            sl = w.layout().itemAt(0).widget()
                            try:
                                sl.setValue(int(float(v)*100))
                            except:
                                pass
                        except:
                            pass
                    elif isinstance(w, QLineEdit):
                        w.setText(str(v))
                    elif isinstance(w, QPushButton):
                        w.setText(str(v))
                        w.setStyleSheet(f"background:{v}")
    def on_props_changed(self, vals):
        it = self.elements.currentItem()
        if not it:
            return
        name = it.text(0)
        parsed = {}
        for k, v in vals.items():
            if k == "kwargs":
                kvs = (v or "").strip()
                for kv in kvs.split(","):
                    if "=" in kv:
                        kk, vv = kv.split("=", 1)
                        parsed[kk.strip()] = self.parse_value(vv.strip())
            else:
                parsed[k] = self.parse_value(v)
        self.props_data[name] = parsed
        try:
            self.props_path.write_text(json.dumps(self.props_data), encoding="utf-8")
        except:
            pass
        self.update_code()
    def save_current_element(self):
        it = self.elements.currentItem()
        if not it:
            return
        name = it.text(0)
        vals = self.props.values()
        parsed = {}
        for k, v in vals.items():
            if k == "kwargs":
                kvs = (v or "").strip()
                for kv in kvs.split(","):
                    if "=" in kv:
                        kk, vv = kv.split("=", 1)
                        parsed[kk.strip()] = self.parse_value(vv.strip())
            else:
                parsed[k] = self.parse_value(v)
        self.props_data[name] = parsed
        try:
            self.props_path.write_text(json.dumps(self.props_data), encoding="utf-8")
            QMessageBox.information(self, "Saved", "Element properties saved")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
        self.update_code()
    def export_props(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export Props", "props_export.json", "JSON (*.json)")
        if not fn:
            return
        try:
            Path(fn).write_text(json.dumps(self.props_data, indent=2), encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
    def import_props(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Import Props", "", "JSON (*.json)")
        if not fn:
            return
        try:
            data = json.loads(Path(fn).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.props_data.update(data)
                self.update_code()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))
    def parse_value(self, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("$") and s.endswith("$"):
                return {"__raw__": s[1:-1]}
            try:
                return json.loads(s)
            except:
                return s
        return v
    def update_code(self):
        lines = ["from manim import *", "", "class Output(Scene):", "    def construct(self):"]
        if self.sound_path:
            lines.append(f'        self.add_sound(r"{self.sound_path}")')
        effects = []
        for i in range(self.elements.topLevelItemCount()):
            name = self.elements.topLevelItem(i).text(0)
            cls_name = name.replace(" [Effect]", "").split(" (")[0]
            var_name = re.sub(r"[^0-9a-zA-Z_]+", "_", cls_name).lower()
            raw_params = self.props_data.get(name, {})
            def fmt(v):
                if isinstance(v, dict) and "__raw__" in v:
                    return v["__raw__"]
                if isinstance(v, str):
                    return repr(v)
                return repr(v)
            params = {k: v for k, v in raw_params.items() if v not in [None, ""] and (not isinstance(v, str) or "!ignore!" not in v)}
            param_str = ", ".join(f"{k}={fmt(v)}" for k, v in params.items())
            if " [Effect]" in name:
                effects.append(f"        self.play({cls_name}({param_str}))")
            else:
                lines.append(f"        {var_name} = {cls_name}({param_str})")
        lines.extend(effects)
        code = "\n".join(lines)
        self.code.blockSignals(True)
        self.code.setPlainText(code)
        self.code.blockSignals(False)
        Path("script.py").write_text(code, encoding="utf-8")
    def add_sound(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Select Audio", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if fn:
            self.sound_path = fn
            self.update_code()
    def preview_scene(self):
        lines = self.code.toPlainText().splitlines()
        out = []
        inside_construct = False
        added = False
        for ln in lines:
            s = ln.strip()
            if "self.interactive_embed()" in s:
                continue
            if s.startswith("def construct"):
                inside_construct = True
            if inside_construct and not added:
                if s == "" or (s.startswith("def") and not s.startswith("def construct")):
                    out.append("        self.interactive_embed()")
                    added = True
            out.append(ln)
        if not added:
            out.append("        self.interactive_embed()")
        Path("script.py").write_text("\n".join(out), encoding="utf-8")
        cmd = ["manim", "script.py", "Output", "--renderer=opengl", "--enable_gui", "-p"]
        self.log(">> " + " ".join(cmd))
        t = ProcThread(cmd)
        t.line.connect(self.log)
        t.start()
    def render_scene(self):
        w = self.res_w.value()
        h = self.res_h.value()
        Path("script.py").write_text(self.code.toPlainText(), encoding="utf-8")
        cmd = ["manim", "script.py", "Output", "-pqm", "--resolution", f"{w},{h}"]
        self.log(">> " + " ".join(cmd))
        t = ProcThread(cmd)
        t.line.connect(self.log)
        t.start()
    def log(self, msg):
        self.logs.appendPlainText(msg)
    def generate_with_ai(self):
        prompt = self.ai_input.text().strip()
        if not prompt:
            return
        if not client:
            QMessageBox.critical(self, "AI Error", "Missing GEMINI_API_KEY")
            return
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="Please only output valid Python code for Manim scenes without any prose, explanations, or markdown."),
                contents=prompt
            )
            code = response.text or ""
            code = self._extract_code_block(code)
            self.ai_output.setPlainText(code)
            if code.strip():
                self.apply_generated_code(code)
        except Exception as e:
            QMessageBox.critical(self, "AI Error", str(e))
    def _extract_code_block(self, text):
        if not text:
            return ""
        if text.strip().startswith("```"):
            m = re.search(r"```(?:python)?\n(.*?)```", text, re.S|re.I)
            if m:
                return m.group(1)
        return text
    def apply_generated_code(self, code):
        self.code.setPlainText(code)
        try:
            parsed = ast.parse(code)
        except Exception:
            return
        targets = []
        class_names = set(self.class_map.keys())
        for node in ast.walk(parsed):
            if isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name and name in class_names:
                    kwargs = {}
                    for kw in node.keywords:
                        kwargs[kw.arg] = self._eval_ast_value(kw.value)
                    targets.append((name, kwargs))
        for cls_name, kwargs in targets:
            label = cls_name
            if class_in_manim_animations(cls_name) and not is_mobject_class(self.class_map[cls_name]):
                label = cls_name + " [Effect]"
            base = label
            names = self.current_elements_names()
            new_name = base
            c = 1
            while new_name in names:
                c += 1
                new_name = f"{base} ({c})"
            node = QTreeWidgetItem([new_name])
            self.elements.addTopLevelItem(node)
            normalized = {}
            for k, v in kwargs.items():
                normalized[k] = v
            self.props_data[new_name] = normalized
        if targets:
            first_cls = targets[0][0]
            self.show_properties_for(self.class_map[first_cls], existing=self.props_data.get(self.elements.topLevelItem(0).text(0), {}))
        self.update_code()
    def _eval_ast_value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.NameConstant):
            return node.value
        if isinstance(node, ast.List):
            return [self._eval_ast_value(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_ast_value(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return {self._eval_ast_value(k): self._eval_ast_value(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            v = node.operand.value
            if isinstance(v, (int, float)):
                return -v
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return f"$${node.value.id}.{node.attr}$$"
        if isinstance(node, ast.Name):
            return f"$${node.id}$$"
        return f"$${ast.unparse(node) if hasattr(ast, 'unparse') else ''}$$"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qt_themes.set_theme("blender")
    w = EditorWindow()
    w.show()
    sys.exit(app.exec())