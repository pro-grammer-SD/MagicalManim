import os
import urllib.request
from zipfile import ZipFile
import customtkinter
import requests
from tkhtmlview import HTMLLabel
import markdown
import threading
from CTkMessagebox import CTkMessagebox
import shutil
import tempfile
import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

class Update:
    def __init__(self):
        self.url = "https://example.com/update"  # dummy URL

        if not is_admin():
            warn = CTkMessagebox(
                title="Admin Privileges Required",
                message="Run this app as an administrator.\nRestart with admin rights and try again.",
                icon="warning",
                option_1="OK"
            )
            if warn.get():
                sys.exit()
        else:
            self.app = customtkinter.CTk()
            self.app.title("Updater | ROM")
            self.app.geometry("700x500")

            self.progress = customtkinter.CTkProgressBar(self.app, width=680)
            self.progress.place(x=10, y=460)
            self.progress.set(0)

            self.markdown_text = "# Changes"
            html_content = markdown.markdown(self.markdown_text)

            self.html_label = HTMLLabel(self.app, html=html_content)
            self.html_label.place(x=10, y=10, width=680, height=400)

            cfu = customtkinter.CTkButton(self.app, text="Check for updates", width=140, height=28, command=self.check_for_updates)
            cfu.place(x=280, y=420)

            self.app.mainloop()

    def check_for_updates(self):
        try:
            self.latest_version = requests.get(f"{self.url}/latest_version.conf").text.strip()
            version_file_path = os.path.join(os.getcwd(), "version.conf")
            with open(version_file_path, "r") as installed_version_file:
                installed_version = installed_version_file.read().strip()

            if self.latest_version != installed_version:
                self.update_alert()
            else:
                self.on_latest_alert()
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Failed to check updates:\n{e}", icon="error", option_1="OK")

    def load_changes(self):
        try:
            self.markdown_text = requests.get(f"{self.url}/changes.md").text
            html_content = markdown.markdown(self.markdown_text)
            self.html_label.set_html(html_content)
        except Exception as e:
            self.html_label.set_html(f"<h3>Failed to load changes: {e}</h3>")

    def update_alert(self):
        self.load_changes()
        msg = CTkMessagebox(
            title=f"Update found! (v{self.latest_version})",
            message="Download it now?",
            icon="question",
            option_1="Cancel",
            option_2="Proceed"
        )
        if msg.get() == "Proceed":
            thread = threading.Thread(target=self.update)
            thread.start()

    def on_latest_alert(self):
        CTkMessagebox(message=f"You are already on the latest version {self.latest_version}", icon="check", option_1="OK")

    def progress_callback(self, block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded / total_size, 1.0)
        self.progress.set(percent)
        self.app.update_idletasks()

    def download_and_extract(self, temp_dir):
        zip_path = os.path.join(temp_dir, "updates.zip")
        conf_path = os.path.join(temp_dir, "version.conf")

        urllib.request.urlretrieve(f"{self.url}/updates.zip", zip_path, self.progress_callback)
        urllib.request.urlretrieve(f"{self.url}/latest_version.conf", conf_path)

        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)

        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        return extract_path, conf_path

    def update(self):
        temp_dir = tempfile.mkdtemp(prefix="mgm", suffix="updatefiles")
        install_path = os.getcwd()

        try:
            extract_path, conf_path = self.download_and_extract(temp_dir)

            for item in os.listdir(extract_path):
                s = os.path.join(extract_path, item)
                d = os.path.join(install_path, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Update failed:\n{e}", icon="error", option_1="OK")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    Update()
