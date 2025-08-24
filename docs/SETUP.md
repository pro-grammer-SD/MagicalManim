# ⚙️ Setup Guide

## 1. 📦 Install dependencies

Run the installer script from the project root:

```bash
./install.bat
```

⚠️ Important:
Make sure you use the **same version of Python and pip** for both the app and all dependencies.
If your system defaults to a different version, modify the command in `install.bat` (e.g., `python3.13 -m pip install -r requirements.txt`) so it matches the version you’ll run the app with.

*Recommend to use with 🐍 Python 3.13.x*

---

## 2. 🔑 Configure API Key

Create a `.env` file in the **project root** with the following content:

```env
GEMINI_API_KEY=your_api_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

---

## 3. 🚀 Run the app

Navigate to the GUI folder and start the editor:

```bash
cd gui
python editor.py
```

---

🎉 Done! You should now have the editor running.
