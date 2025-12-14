#!/usr/bin/env python
"""
VocalXpert - Modern AI Voice Assistant

Entry point for the PySide6-based modern UI.
Run this file to start the application.

Usage:
    python main_pyside.py
    python main_pyside.py --skip-login    # Skip face login (demo mode)
    python main_pyside.py --debug         # Enable debug logging

Requirements:
    - PySide6
    - speech_recognition
    - pyttsx3
    - opencv-python (for face recognition)
    - All other dependencies in requirements.txt
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(project_root) / '.env'
    load_dotenv(env_path)
    logger_temp = logging.getLogger('VocalXpert')
except ImportError:
    pass  # dotenv not required

# Parse arguments
parser = argparse.ArgumentParser(description='VocalXpert AI Voice Assistant')
parser.add_argument('--skip-login', action='store_true', help='Skip face recognition login')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args, unknown = parser.parse_known_args()

# Setup logging
log_level = logging.DEBUG if args.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vocalxpert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VocalXpert')


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing = []
    
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        missing.append("PySide6")
    
    try:
        import speech_recognition
    except ImportError:
        missing.append("SpeechRecognition")
    
    try:
        import pyttsx3
    except ImportError:
        missing.append("pyttsx3")
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nPlease install them with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_user_data():
    """Check if user is registered."""
    user_data_path = os.path.join(project_root, 'userData', 'userData.pck')
    trainer_path = os.path.join(project_root, 'userData', 'trainer.yml')
    
    return os.path.exists(user_data_path) and os.path.exists(trainer_path)


def main():
    """Launch VocalXpert with the modern PySide6 UI."""
    print("=" * 50)
    print("🎙️  VocalXpert - AI Voice Assistant")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    print("\n✓ All dependencies OK")
    
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("VocalXpert")
    app.setApplicationVersion("2.0.0")
    
    # Check if we should skip login
    if args.skip_login:
        print("\n⚠️  Skipping login (--skip-login flag)\n")
        
        # Launch main app directly
        from frontend.main_window import MainWindow, create_splash_screen
        
        splash = create_splash_screen(app)
        window = MainWindow()
        
        def show_main():
            splash.finish(window)
            window.show()
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, show_main)
        
    else:
        # Always show login screen first
        if not check_user_data():
            print("\n🔐 No user data found. Starting login screen for registration.\n")
        else:
            print("\n🔐 Starting login screen...\n")
        
        from frontend.login_window import LoginWindow
        from frontend.main_window import MainWindow
        
        login_window = LoginWindow()
        main_window = None
        
        def on_login_success(user_name):
            nonlocal main_window
            logger.info(f"Login successful: {user_name}")
            
            # Create and show main window
            main_window = MainWindow()
            main_window.show()
            
            # Show welcome message
            main_window.chat_panel.add_message(
                f"Welcome back, {user_name}! 👋 How can I help you today?",
                is_user=False
            )
        
        login_window.login_successful.connect(on_login_success)
        login_window.show()
    
    logger.info("VocalXpert started")
    
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
