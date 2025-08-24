# ✨ Magical Manim

Magical Manim is a modern, custom GUI wrapper around [Manim](https://www.manim.community/) — making it easier to design, preview, and manage animations without touching the CLI every single time. Think of it as **Manim, but supercharged with a sleek editor and interactive rendering.**

---

## 🚀 Features

* 🎨 **PySide6 GUI** — clean, modern, and easy to navigate.
* ⚡ **One-click preview** — run Manim scenes instantly, no terminal commands needed.
* 🌀 **Interactive mode injection (dev)** — auto-adds `self.interactive_embed()` without duplicates.
* 🖼️ **Custom icons** — pretty app icons for Windows and taskbar.
* 🛠️ **Syntax helpers** — shortcuts for writing Manim scripts with less pain.
* 🤖 **Gemini Assisted Code Gen**
- faster coding at your fingertips.

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/pro-grammer-SD/MagicalManim.git
cd MagicalManim

# Install dependencies
pip install -r requirements.txt

# Run it
cd gui
python editor.py
```

---

## 🖥️ Usage

1. Launch the app with:

   ```bash
   cd gui
   python editor.py
   ```
2. Click **New Project** to open the editor.
3. Write your Manim scene inside the editor window.
4. Hit **Preview** to see your animation instantly with OpenGL renderer.

---

# 🌟 Tutorial

### ⚙️ Syntax

Magical Manim adds a couple of lightweight macros to make your scripting life easier:

* **`$randomtext$`** → expands to `randomtext` *(auto-escapes the string)*
  Example:

  ```text
  $Circle(1)$  
  ```

  → becomes `Circle(1)`

* **`!ignore!`** → removes the parameter entirely
  Example:

  ```text
  Create(circle, lag_ratio=1.0, !ignore!)
  ```

  → becomes `Create(circle, lag_ratio=1.0)`

---

## 📂 Project Structure

```
MagicalManim/
├── init.py             # Launcher (InitGui)
├── gui/
│   ├── editor.py       # Main editor (EditorGui)
│   └── ...
├── icon/
│   ├── ico/            # ICO icons
│   └── png/            # PNG icons
└── requirements.txt
```

---

## ⚡ Roadmap

* [ ] Scene templates (e.g., Circle demo, Text demo).
* [ ] Multi-project manager.
* [ ] Hot-reload for scripts.
* [ ] Export to GIF/MP4 directly from GUI.

---

## 🤝 Contributing

Pull requests are welcome! If you’ve got feature ideas or bug fixes, open an issue first to discuss what you’d like to change.

---

## 📜 License

MIT License. Do whatever you want, just don’t forget to credit.
