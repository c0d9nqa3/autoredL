#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path


def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("AutoRedL Setup")
    
    # Create directories
    for d in ["models", "output", "logs"]:
        Path(d).mkdir(exist_ok=True)
    
    # Install system deps on ARM
    if os.uname().machine.startswith(('arm', 'aarch64')):
        print("Installing system dependencies...")
        deps = "python3-dev python3-pip python3-venv libopencv-dev python3-opencv"
        run_cmd(f"sudo apt update && sudo apt install -y {deps}")
    
    # Setup venv and install packages
    if run_cmd("python3 -m venv venv"):
        pip = "./venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
        run_cmd(f"{pip} install --upgrade pip")
        run_cmd(f"{pip} install -r requirements.txt")
    
    # Download model
    model_path = "models/yolov5s.onnx"
    if not Path(model_path).exists():
        try:
            import urllib.request
            url = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.onnx"
            urllib.request.urlretrieve(url, model_path)
            print("Model downloaded")
        except Exception:
            print("Model download failed - will use HOG fallback")
    
    # Create startup script
    script = "#!/bin/bash\ncd \"$(dirname \"$0\")\"\nsource venv/bin/activate\npython main.py\n"
    with open("start.sh", "w") as f:
        f.write(script)
    if os.name != 'nt':
        os.chmod("start.sh", 0o755)
    
    print("Setup complete. Run: ./start.sh")


if __name__ == "__main__":
    main()

