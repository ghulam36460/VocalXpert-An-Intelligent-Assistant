#!/usr/bin/env python3
"""
Face Registration Module - VocalXpert Security

Captures face images and trains a face recognition model for user authentication.
This script should be run when registering a new user for face unlock.

Features:
    - Face detection using Haar Cascade
    - Captures multiple face samples for training
    - Trains LBPH face recognition model
    - Saves trained model to userData/trainer.yml

Requirements:
    - OpenCV (opencv-python)
    - Webcam/camera access
    - userData directory (created automatically)

Usage:
    python modules/security.py
"""

import cv2
import numpy as np
import os
from os.path import isfile, join
import sys
from pathlib import Path


def assure_path_exists(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def collect_face_data():
    """Collect face samples from webcam for training."""
    print("🎥 Starting Face Registration for VocalXpert")
    print("=" * 50)

    # Initialize face detector
    face_classifier = cv2.CascadeClassifier(
        "Cascade/haarcascade_frontalface_default.xml")

    def face_detector(img, size=0.5):
        """Detect face in image and return cropped face region."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray,
                                                 scaleFactor=1.3,
                                                 minNeighbors=5,
                                                 minSize=(30, 30))

        if len(faces) == 0:
            return img, []

        # Get the largest face
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
        roi = img[y:y + h, x:x + w]
        roi = cv2.resize(roi, (200, 200))

        return img, roi

    # Create directories
    assure_path_exists("userData")
    assure_path_exists("userData/faceData")

    # Initialize camera
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("❌ Error: Cannot access webcam")
        return False

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    face_id = 0  # User ID (0 for first user)
    count = 0
    max_samples = 100

    print(f"📸 Collecting {max_samples} face samples...")
    print("Position your face in front of the camera.")
    print("Press 'q' or ESC to stop early.")
    print("Press 'c' to capture current frame.")
    print("-" * 40)

    face_samples = []

    while count < max_samples:
        ret, frame = cam.read()
        if not ret:
            print("❌ Error: Cannot read from camera")
            break

        image, face = face_detector(frame)

        if len(face) > 0:
            count += 1
            face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

            # Save face sample
            face_samples.append(face_gray)

            # Save individual face image for retraining capability
            face_filename = f"userData/faceData/face_{face_id}_{count:03d}.jpg"
            cv2.imwrite(face_filename, face_gray)
            print(f"Saved face sample: {face_filename}")

            # Display progress
            progress = int((count / max_samples) * 100)
            cv2.putText(
                image,
                f"Capturing... {count}/{max_samples} ({progress}%)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                image,
                "No face detected - position yourself",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        cv2.imshow("Face Registration - VocalXpert", image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            print("Registration cancelled by user.")
            break
        elif key == ord("c"):  # Manual capture
            if len(face) > 0:
                count += 1
                face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                face_samples.append(face_gray)

                # Save individual face image for retraining capability
                face_filename = f"userData/faceData/face_{face_id}_{count:03d}.jpg"
                cv2.imwrite(face_filename, face_gray)
                print(f"Manual capture saved: {face_filename}")

                print(f"Manual capture: {count}/{max_samples}")

    cam.release()
    cv2.destroyAllWindows()

    if len(face_samples) < 10:
        print(
            f"❌ Error: Only collected {len(face_samples)} samples. Need at least 10."
        )
        return False

    print(f"✅ Collected {len(face_samples)} face samples")

    # Train the model
    print("🤖 Training face recognition model...")
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        # Prepare training data
        faces = face_samples
        labels = [face_id] * len(faces)

        # Train the model
        recognizer.train(faces, np.array(labels))

        # Save the trained model
        model_path = "userData/trainer.yml"
        recognizer.save(model_path)

        print(f"✅ Model trained and saved to: {model_path}")
        print("🎉 Face registration completed successfully!")
        print("You can now use face unlock in VocalXpert.")

        return True

    except Exception as e:
        print(f"❌ Error training model: {e}")
        return False


def main():
    """Main function."""
    try:
        success = collect_face_data()
        if success:
            print("\n" + "=" * 50)
            print("🎊 REGISTRATION COMPLETE!")
            print("You can now close this window and use VocalXpert.")
            print("=" * 50)
            input("Press Enter to exit...")
        else:
            print("\n❌ Registration failed. Please try again.")
            input("Press Enter to exit...")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nRegistration cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
