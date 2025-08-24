# Magical Manim – Keybinds & Shortcuts

This doc lists all the current keyboard shortcuts and quick actions in the editor.

---

## 🎬 File

* **Ctrl+Shift+S** → Save Script (`script.py`)
* **Ctrl+S** → Save current element props into `props.json`
* *(no shortcut)* → Export Props as JSON
* *(no shortcut)* → Import Props from JSON

---

## ✏️ Edit

* **Ctrl+E** → Add Selected Element (⚠️ currently collides if reused elsewhere)
* **Ctrl+D** → Duplicate Selected Element
* **Del** → Delete Selected Element
* **Ctrl+L** → Surround focused property value with `$$...$$`
* **Ctrl+I** → Surround focused property value with `!!...!!`

---

## 🚀 Run

* *(no shortcut)* → Preview Scene
* *(no shortcut)* → Render Scene

---

## 🤖 AI

* **Ctrl+G** → Generate With AI

---

## ℹ️ Help

* *(no shortcut)* → About dialog

---

## 🖱️ Dock Buttons (no shortcuts)

* Add Sound
* Add Selected Element
* Duplicate Selected
* Delete Selected
* Preview
* Render

---

## ⚠️ Notes

* **Ctrl+E conflict** → You’ve got multiple actions using this shortcut, which causes Qt’s *ambiguous shortcut overload* spam. Only one QAction should own it.
* **Surround Macros** → `Ctrl+L` wraps with `$$`; `Ctrl+I` wraps with `!!`. `$...$` is treated as numeric expression in code gen, `!...!` is ignored (skipped from code).
