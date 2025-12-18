"""
Face Unlocker Module - Face Detection and Recognition

Uses OpenCV's LBPH (Local Binary Patterns Histograms) face recognizer
for user authentication. Compares detected faces against stored
training data.

Features:
    - Face detection using Haar Cascade classifier
    - Face recognition with confidence scoring
    - Real-time webcam face tracking

Dependencies:
    - opencv-python: Face detection and recognition
    - Pre-trained model: userData/trainer.yml
"""

import cv2
import os
from os.path import isfile, join
import logging
import numpy as np
from PIL import Image
from datetime import datetime

try:
    import playsound
except ImportError:
    playsound = None

# Configurable thresholds (can be overridden via environment variables)
PER_FRAME_THRESHOLD = int(os.getenv("FACE_PER_FRAME_THRESHOLD", "85"))
AVG_CONFIDENCE_THRESHOLD = float(os.getenv("FACE_AVG_THRESHOLD", "86.0"))
REQUIRED_RECOGNITIONS = int(os.getenv("FACE_REQUIRED_RECOGNITIONS", "4"))

# Setup logging for security monitoring
logging.basicConfig(
    filename="face_recognition.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("FaceRecognition")

face_classifier = cv2.CascadeClassifier(
    "Cascade/haarcascade_frontalface_default.xml")


def face_detector(img, size=0.5):
    """Detect face in image and return the cropped face region."""
    if img is None:
        return None, []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(
        gray,
        scaleFactor=1.2,  # Faster detection
        minNeighbors=4,  # Slightly less strict
        minSize=(30, 30),  # Smaller minimum
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    if len(faces) == 0:
        return img, []

    # Get the largest face (closest to camera)
    largest_face = max(faces, key=lambda f: f[2] * f[3])
    x, y, w, h = largest_face

    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
    roi = img[y:y + h, x:x + w]
    roi = cv2.resize(roi, (200, 200))

    return img, roi


def startDetecting():
    """Start face detection and recognition process."""
    logger.info("Face recognition session started")

    # Check if trained model exists
    if not os.path.exists("userData/trainer.yml"):
        logger.error("No trained model found - face recognition aborted")
        print("No trained model found. Please register your face first.")
        return False

    try:
        model = cv2.face.LBPHFaceRecognizer_create()
        model.read("userData/trainer.yml")
    except Exception as e:
        print(f"Error loading face model: {e}")
        return False

    # Open camera directly (index 0 is usually the default webcam)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW is faster on Windows

    if not cap.isOpened():
        # Fallback without DirectShow
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Could not open camera")
        return False

    # Set smaller resolution for faster processing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for less lag

    flag = False
    max_attempts = 150  # ~5 seconds
    attempt = 0
    successful_recognitions = 0
    # Configurable required recognitions
    required_recognitions = REQUIRED_RECOGNITIONS
    recent_confidences = []  # Track recent confidence scores

    while attempt < max_attempts:
        ret, frame = cap.read()

        if not ret or frame is None:
            attempt += 1
            continue

        image, face = face_detector(frame)

        if image is None:
            attempt += 1
            continue

        try:
            if len(face) == 0:
                # No face detected
                cv2.putText(
                    image,
                    "Looking for face...",
                    (150, 450),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 165, 0),
                    2,
                )
                cv2.imshow("Face Recognition - VocalXpert", image)
            else:
                face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                result = model.predict(face_gray)

                # Calculate confidence (lower distance = better match)
                # LBPH returns (label, distance), lower distance is better
                distance = result[1]

                if distance < 500:
                    confidence = int((1 - (distance / 400)) * 100)
                    confidence = max(0, min(100, confidence))  # Clamp 0-100
                    display_string = f"Match: {confidence}%"
                else:
                    confidence = 0
                    display_string = "No Match"

                cv2.putText(
                    image,
                    display_string,
                    (100, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (250, 120, 255),
                    2,
                )

                if (confidence > PER_FRAME_THRESHOLD
                    ):  # Per-frame threshold (configurable)
                    successful_recognitions += 1
                    recent_confidences.append(confidence)

                    # Keep only last 5 confidence scores
                    if len(recent_confidences) > 5:
                        recent_confidences.pop(0)

                    cv2.putText(
                        image,
                        f"Unlocking... ({successful_recognitions}/{required_recognitions})",
                        (150, 450),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                    if successful_recognitions >= required_recognitions:
                        # Additional validation: require consistent high
                        # confidence
                        if len(recent_confidences) >= 3:
                            avg_confidence = (sum(recent_confidences[-3:]) / 3
                                              )  # Average of last 3
                            # Use configurable average threshold
                            if avg_confidence >= AVG_CONFIDENCE_THRESHOLD:
                                logger.info(
                                    f"Face recognition successful - Average confidence: {avg_confidence:.1f}%, Samples: {len(recent_confidences)}"
                                )
                                print(
                                    f"Face recognition successful - Average confidence: {avg_confidence:.1f}%"
                                )
                                cv2.putText(
                                    image,
                                    "UNLOCKED!",
                                    (250, 400),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1.2,
                                    (0, 255, 0),
                                    3,
                                )
                                cv2.imshow("Face Recognition - VocalXpert",
                                           image)
                                cv2.waitKey(500)  # Show success briefly
                                flag = True
                                break
                            else:
                                # Reset counter if average confidence is not
                                # high enough
                                successful_recognitions = max(
                                    0, successful_recognitions - 2)
                                # Remove last 2
                                recent_confidences = recent_confidences[:-2]
                                logger.warning(
                                    f"Face recognition failed - Low average confidence: {avg_confidence:.1f}%"
                                )
                                print(
                                    f"Face recognition failed - Low average confidence: {avg_confidence:.1f}%"
                                )
                                cv2.putText(
                                    image,
                                    "Verification failed - inconsistent",
                                    (100, 450),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7,
                                    (0, 165, 255),
                                    2,
                                )
                        else:
                            # Not enough samples yet
                            cv2.putText(
                                image,
                                "Gathering more samples...",
                                (150, 480),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 165, 0),
                                2,
                            )
                else:
                    successful_recognitions = max(0,
                                                  successful_recognitions - 1)
                    # Clear recent confidences if we get a low confidence
                    if confidence < 60:
                        recent_confidences.clear()

                    if confidence > 50:
                        cv2.putText(
                            image,
                            "Face detected but not recognized",
                            (120, 450),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 165, 255),
                            2,
                        )
                    else:
                        cv2.putText(
                            image,
                            "Face not recognized",
                            (180, 450),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

                cv2.imshow("Face Recognition - VocalXpert", image)

        except Exception as e:
            cv2.putText(
                image,
                "Scanning...",
                (250, 450),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )
            cv2.imshow("Face Recognition - VocalXpert", image)

        attempt += 1

        # Check for quit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            break

    cap.release()
    cv2.destroyAllWindows()

    result_text = "successful" if flag else "failed"
    logger.info(
        f"Face recognition session ended - Result: {result_text}, Attempts: {attempt}, Successful recognitions: {successful_recognitions}"
    )

    return flag


def retrain_model():
    """
    Retrain the face recognition model with current face data.
    This can help fix recognition issues if the model is corrupted or outdated.
    """
    logger.info("Starting face recognition model retraining")

    try:
        # Check if face data exists
        face_data_dir = "userData/faceData"
        if not os.path.exists(face_data_dir):
            logger.error("No face data directory found")
            return False

        # Get all face images
        face_files = [
            f for f in os.listdir(face_data_dir)
            if f.endswith(".jpg") or f.endswith(".png")
        ]
        if not face_files:
            logger.error("No face images found in faceData directory")
            return False

        logger.info(f"Found {len(face_files)} face images for retraining")

        # Prepare training data
        faces = []
        labels = []

        for face_file in face_files:
            try:
                # Load image
                image_path = os.path.join(face_data_dir, face_file)
                pil_image = Image.open(image_path).convert(
                    "L")  # Convert to grayscale
                image_array = np.array(pil_image, "uint8")

                # Detect faces in the image
                faces_detected = face_classifier.detectMultiScale(image_array)

                if len(faces_detected) > 0:
                    # Use the first (largest) face found
                    (x, y, w, h) = faces_detected[0]
                    face_roi = image_array[y:y + h, x:x + w]
                    face_roi = cv2.resize(face_roi, (200, 200))

                    faces.append(face_roi)
                    labels.append(0)  # All faces belong to user ID 0
                    logger.info(f"Processed face from {face_file}")
                else:
                    logger.warning(f"No face detected in {face_file}")

            except Exception as e:
                logger.error(f"Error processing {face_file}: {e}")
                continue

        if len(faces) < 5:
            logger.error(
                f"Insufficient training data: only {len(faces)} faces found. Need at least 5."
            )
            return False

        # Train the model
        logger.info(f"Training model with {len(faces)} face samples")
        model = cv2.face.LBPHFaceRecognizer_create()
        model.train(faces, np.array(labels))

        # Save the trained model
        model.save("userData/trainer.yml")
        logger.info("Face recognition model retrained and saved successfully")

        return True

    except Exception as e:
        logger.error(f"Error during model retraining: {e}")
        return False


def takePhoto():
    """Take a photo using the webcam and save it to Camera folder."""
    global imageName
    if not os.path.exists("Camera"):
        os.mkdir("Camera")

    from datetime import datetime

    cam = cv2.VideoCapture(0)
    _, frame = cam.read()

    if playsound:
        try:
            playsound.playsound("assets/audios/photoclick.mp3")
        except BaseException:
            pass

    imageName = "Camera/Camera_" + str(datetime.now())[:19].replace(
        ":", "_") + ".png"
    cv2.imwrite(imageName, frame)
    cam.release()
    cv2.destroyAllWindows()
    return imageName


def viewPhoto():
    """View the last taken photo."""
    if "imageName" in globals() and os.path.exists(imageName):
        img = Image.open(imageName)
        img.show()
    else:
        print("No photo to view. Take a photo first.")
