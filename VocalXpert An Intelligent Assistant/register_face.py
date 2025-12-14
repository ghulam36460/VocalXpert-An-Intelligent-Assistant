#!/usr/bin/env python3
"""
Face Registration Helper Script
Helps users register their face for VocalXpert face unlock.
"""

import os
import sys
import subprocess

def main():
    print("Face Registration Helper - VocalXpert")
    print("=" * 40)
    print()
    print("This will help you register your face for secure login.")
    print()
    print("Instructions:")
    print("1. Make sure your webcam is working")
    print("2. Position yourself in front of the camera")
    print("3. Look directly at the camera with good lighting")
    print("4. The system will automatically capture face samples")
    print("5. Press 'q' or ESC to stop early if needed")
    print("6. Press 'c' to manually capture if auto-detection misses")
    print()
    input("Press Enter to start face registration...")

    try:
        # Run the security.py script
        result = subprocess.run([sys.executable, 'modules/security.py'],
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=False)

        if result.returncode == 0:
            print("\n✅ Face registration completed successfully!")
            print("You can now use face unlock in VocalXpert.")
        else:
            print("\n❌ Face registration failed.")
            print("Please try again with better lighting and positioning.")

    except Exception as e:
        print(f"\n❌ Error running face registration: {e}")
        print("Make sure all required packages are installed.")

if __name__ == "__main__":
    main()