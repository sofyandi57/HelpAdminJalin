"""Launcher untuk versi .exe: menjalankan app.py Streamlit tanpa perlu terminal/Python."""

import os
import sys


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def ensure_streamlit_credentials():
    # Mencegah Streamlit menunggu input email di first-run (akan hang karena .exe
    # tidak punya konsol/stdin untuk dijawab).
    config_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
    os.makedirs(config_dir, exist_ok=True)
    cred_path = os.path.join(config_dir, "credentials.toml")
    if not os.path.exists(cred_path):
        with open(cred_path, "w", encoding="utf-8") as f:
            f.write('[general]\nemail = ""\n')


if __name__ == "__main__":
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    ensure_streamlit_credentials()

    from streamlit.web import cli as stcli

    app_path = resource_path("app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=false",
    ]
    sys.exit(stcli.main())
