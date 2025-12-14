"""
VocalXpert - An Intelligent Voice Assistant

A Windows desktop application providing voice-controlled assistance
with features including face recognition login, weather updates,
web searching, task management, and interactive games.

Author: VocalXpert Team

Usage:
    python main.py               # Start with login
    python main.py --skip-login  # Skip face login (demo mode)
"""

import sys
import os

# Get the directory containing main.py
project_dir = os.path.dirname(os.path.abspath(__file__))

# Run the PySide6 application
if __name__ == "__main__":
    # Forward to main_pyside.py
    import subprocess
    
    # Get Python executable
    python_exe = sys.executable
    main_pyside = os.path.join(project_dir, "main_pyside.py")
    
    # Forward command line arguments
    args = [python_exe, main_pyside] + sys.argv[1:]
    
    print("Starting VocalXpert Assistant...")
    subprocess.run(args)
