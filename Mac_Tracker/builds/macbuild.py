import os
import subprocess

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(BASE_DIR, "tracker_gui_tk.py")
PEOPLE_CSV = os.path.join(BASE_DIR, "people.csv")

# Format for PyInstaller: "source:destination"
MAC_DATA = f"{PEOPLE_CSV}:."

# Build .app
def build_macos_app():
    print("Building macOS .app (onedir mode)...")
    cmd = [
        "pyinstaller",
        "--windowed",        # no console
        SCRIPT
    ]
    subprocess.run(cmd)
    print("\n✅ macOS .app build finished! Check the dist/ folder.")

if __name__ == "__main__":
    build_macos_app()