"""
VocalXpert Login Screen - PySide6 Implementation

Modern login screen with face recognition integration.
"""

import sys
import os
import logging
from pathlib import Path

# Try to import OpenCV for face detection
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QLineEdit,
    QStackedWidget,
    QProgressBar,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QRect
from PySide6.QtGui import QFont, QPixmap, QIcon, QMovie, QImage

from .themes import DARK_THEME, FONTS, SPACING, generate_stylesheet, get_theme
from .components import Card, IconButton

logger = logging.getLogger("VocalXpert.Login")


class FaceRecognitionWorker(QThread):
    """Background thread for face recognition."""

    status_changed = Signal(
        str, str)  # (message, status_type: info/success/error/warning)
    progress = Signal(int)
    finished = Signal(bool, str)  # (success, user_name)

    def __init__(self):
        super().__init__()
        self._is_running = True

    def run(self):
        """Run face recognition."""
        try:
            self.status_changed.emit("🔍 Initializing camera...", "info")
            self.progress.emit(10)

            # Add project root to path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))

            # Check if model exists
            model_path = project_root / "userData" / "trainer.yml"
            if not model_path.exists():
                self.status_changed.emit("❌ No face data found", "error")
                self.finished.emit(False, "")
                return

            self.status_changed.emit("📷 Looking for your face...", "info")
            self.progress.emit(30)

            # Import and run face detection
            from modules import face_unlocker as FU

            self.progress.emit(50)
            result = FU.startDetecting()

            self.progress.emit(90)

            if result:
                # Get user data
                from modules.user_handler import UserData

                user = UserData()
                user.extractData()
                user_name = (user.getName().split()[0]
                             if user.getName() != "None" else "User")

                self.status_changed.emit(f"✅ Welcome back, {user_name}!",
                                         "success")
                self.progress.emit(100)
                self.finished.emit(True, user_name)
            else:
                self.status_changed.emit("❌ Face not recognized", "error")
                self.progress.emit(0)
                self.finished.emit(False, "")

        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            self.status_changed.emit(f"⚠️ Error: {str(e)[:40]}", "error")
            self.progress.emit(0)
            self.finished.emit(False, "")

    def stop(self):
        self._is_running = False


class FaceRegistrationDialog(QDialog):
    """Dialog for registering new users with face recognition."""

    registration_complete = Signal(bool)  # Emits success status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New User - VocalXpert")
        self.setModal(True)
        self.resize(800, 600)

        # Camera variables
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_camera)

        # Face detection variables
        self.face_classifier = None
        self.face_samples = []
        self.max_samples = 50
        self.user_name = ""

        self._setup_ui()
        self._load_face_detector()

    def _setup_ui(self):
        """Setup the registration dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])

        # Title
        title = QLabel("Face Registration")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_2xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # User name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Your Name:")
        name_label.setFont(
            QFont(FONTS["family"], FONTS["size_md"], FONTS["weight_medium"]))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Camera preview area
        self.camera_label = QLabel("Camera Preview")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.camera_label)

        # Status and progress
        self.status_label = QLabel("Click 'Start Registration' to begin")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont(FONTS["family"], FONTS["size_md"]))
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Registration")
        self.start_btn.clicked.connect(self._start_registration)
        self.start_btn.setFont(
            QFont(FONTS["family"], FONTS["size_md"], FONTS["weight_medium"]))

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFont(
            QFont(FONTS["family"], FONTS["size_md"], FONTS["weight_medium"]))

        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)

    def _load_face_detector(self):
        """Load the face detection classifier."""
        if not CV2_AVAILABLE:
            self.status_label.setText("❌ OpenCV not available")
            self.start_btn.setEnabled(False)
            return

        cascade_path = (Path(__file__).parent.parent / "Cascade" /
                        "haarcascade_frontalface_default.xml")
        if cascade_path.exists():
            self.face_classifier = cv2.CascadeClassifier(str(cascade_path))
        else:
            self.status_label.setText("❌ Face detection model not found")
            self.start_btn.setEnabled(False)

    def _start_registration(self):
        """Start the face registration process."""
        self.user_name = self.name_input.text().strip()
        if not self.user_name:
            self.status_label.setText("❌ Please enter your name")
            return

    def _start_registration(self):
        """Start the face registration process."""
        if not CV2_AVAILABLE:
            self.status_label.setText("❌ OpenCV not available")
            return

        self.user_name = self.name_input.text().strip()
        if not self.user_name:
            self.status_label.setText("❌ Please enter your name")
            return

        # Initialize camera
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Cannot access camera")

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            self.face_samples = []
            self.progress_bar.setValue(0)
            self.status_label.setText(
                "📸 Position your face in the camera and hold still...")
            self.start_btn.setText("Stop & Train")
            self.start_btn.clicked.disconnect()
            self.start_btn.clicked.connect(self._stop_and_train)

            self.timer.start(30)  # 30ms = ~33 FPS

        except Exception as e:
            self.status_label.setText(f"❌ Camera error: {str(e)}")

    def _update_camera(self):
        """Update camera preview and capture faces."""
        if self.camera is None:
            return

        try:
            ret, frame = self.camera.read()
            if not ret:
                return

            # Detect faces
            if self.face_classifier is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_classifier.detectMultiScale(gray,
                                                              scaleFactor=1.3,
                                                              minNeighbors=5,
                                                              minSize=(30, 30))

                # Draw rectangles around faces
                for x, y, w, h in faces:
                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Capture face sample if we haven't reached the limit
                    if len(self.face_samples) < self.max_samples:
                        face_roi = gray[y:y + h, x:x + w]
                        face_roi = cv2.resize(face_roi, (200, 200))
                        self.face_samples.append(face_roi)

                        # Update progress
                        progress = int(
                            (len(self.face_samples) / self.max_samples) * 100)
                        self.progress_bar.setValue(progress)

                        if len(self.face_samples) >= self.max_samples:
                            self.status_label.setText(
                                "✅ Enough samples collected! Click 'Stop & Train'"
                            )
                            break

            # Convert to Qt format and display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                              QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)

            # Scale to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.camera_label.size(),
                                          Qt.KeepAspectRatio,
                                          Qt.SmoothTransformation)
            self.camera_label.setPixmap(scaled_pixmap)

            # Update status
            samples_text = f"Captured: {len(self.face_samples)}/{self.max_samples}"
            if len(self.face_samples) < self.max_samples:
                self.status_label.setText(
                    f"📸 {samples_text} - Keep your face in frame")
            else:
                self.status_label.setText(
                    f"✅ {samples_text} - Ready to train!")

        except Exception as e:
            logger.error(f"Camera update error: {e}")

    def _stop_and_train(self):
        """Stop capturing and train the model."""
        self.timer.stop()

        if self.camera:
            self.camera.release()
            self.camera = None

        if len(self.face_samples) < 10:
            self.status_label.setText(
                f"❌ Not enough samples ({len(self.face_samples)}). Need at least 10."
            )
            return

        self.status_label.setText("🤖 Training face recognition model...")
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Train in background thread
        self.training_thread = FaceTrainingWorker(self.face_samples,
                                                  self.user_name)
        self.training_thread.finished.connect(self._on_training_complete)
        self.training_thread.start()

    def _on_training_complete(self, success, message):
        """Handle training completion."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        if success:
            self.status_label.setText(
                "✅ Registration complete! You can now use face unlock.")
            self.start_btn.setText("Done")
            self.start_btn.clicked.disconnect()
            self.start_btn.clicked.connect(self.accept)
        else:
            self.status_label.setText(f"❌ Training failed: {message}")
            self.start_btn.setText("Try Again")
            self.start_btn.clicked.disconnect()
            self.start_btn.clicked.connect(self._start_registration)

    def closeEvent(self, event):
        """Clean up on close."""
        self.timer.stop()
        if self.camera:
            self.camera.release()
        event.accept()


class FaceTrainingWorker(QThread):
    """Background worker for training face recognition model."""

    finished = Signal(bool, str)  # (success, message)

    def __init__(self, face_samples, user_name):
        super().__init__()
        self.face_samples = face_samples
        self.user_name = user_name

    def run(self):
        """Train the face recognition model."""
        if not CV2_AVAILABLE:
            self.finished.emit(False, "OpenCV not available")
            return

        try:
            import numpy as np

            # Create userData directory
            user_data_dir = Path(__file__).parent.parent / "userData"
            user_data_dir.mkdir(exist_ok=True)

            # Train the model
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            labels = [0] * len(self.face_samples)  # User ID 0 for first user

            recognizer.train(self.face_samples, np.array(labels))

            # Save the model
            model_path = user_data_dir / "trainer.yml"
            recognizer.save(str(model_path))

            # Save user name
            user_data_path = user_data_dir / "userData.pck"
            import pickle

            with open(user_data_path, "wb") as f:
                pickle.dump({"name": self.user_name}, f)

            self.finished.emit(True, "Model trained successfully")

        except Exception as e:
            logger.error(f"Training error: {e}")
            self.finished.emit(False, str(e))


class LoginWindow(QMainWindow):
    """Modern login window with face recognition."""

    login_successful = Signal(str)  # Emits user name

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._apply_theme()

        # Check if user data exists and update UI accordingly
        self._check_user_data()

        self._worker = None

    def _setup_window(self):
        """Configure window."""
        self.setWindowTitle("VocalXpert - Login")
        self.setFixedSize(450, 600)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 450) // 2
        y = (screen.height() - 600) // 2
        self.move(x, y)

        # Try to set icon
        icon_path = (Path(__file__).parent.parent / "assets" / "images" /
                     "assistant2.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_ui(self):
        """Build the login UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(SPACING["xl"], SPACING["3xl"], SPACING["xl"],
                                  SPACING["xl"])
        layout.setSpacing(SPACING["lg"])

        # Logo
        logo = QLabel("🎙️")
        logo.setFont(QFont(FONTS["family"], 64))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Title
        title = QLabel("VocalXpert")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_3xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("AI Voice Assistant")
        subtitle.setProperty("class", "muted")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(SPACING["2xl"])

        # Face recognition card
        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING["xl"], SPACING["xl"],
                                       SPACING["xl"], SPACING["xl"])
        card_layout.setSpacing(SPACING["md"])

        # Face icon
        face_icon = QLabel("👤")
        face_icon.setFont(QFont(FONTS["family"], 48))
        face_icon.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(face_icon)

        # Status label
        self.status_label = QLabel(
            "Click below to login with face recognition")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        card_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

        layout.addWidget(card)

        layout.addSpacing(SPACING["lg"])

        # Login button
        self.login_btn = QPushButton("🔓  Login with Face ID")
        self.login_btn.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        self.login_btn.setMinimumHeight(56)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._start_face_login)
        layout.addWidget(self.login_btn)

        # Skip button (only show in development/debug mode)
        import os

        if os.environ.get("VOCALXPERT_DEBUG", "").lower() == "true":
            self.skip_btn = QPushButton("Skip Login (Demo Mode)")
            self.skip_btn.setProperty("class", "ghost")
            self.skip_btn.setCursor(Qt.PointingHandCursor)
            self.skip_btn.clicked.connect(
                lambda: self._on_login_success("Guest"))
            layout.addWidget(self.skip_btn)

        layout.addStretch()

        # Register link
        register_layout = QHBoxLayout()
        register_label = QLabel("New user?")
        register_label.setProperty("class", "muted")

        self.register_btn = QPushButton("Register Face")
        self.register_btn.setProperty("class", "ghost")
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.clicked.connect(self._open_registration)

        register_layout.addStretch()
        register_layout.addWidget(register_label)
        register_layout.addWidget(self.register_btn)
        register_layout.addStretch()

        layout.addLayout(register_layout)

        # Version
        version = QLabel("v2.0.0")
        version.setProperty("class", "muted")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

    def _apply_theme(self):
        """Apply theme."""
        theme = get_theme("dark")
        self.setStyleSheet(generate_stylesheet(theme))

    def _check_user_data(self):
        """Check if user data exists and update UI accordingly."""
        model_path = Path(__file__).parent.parent / "userData" / "trainer.yml"
        user_data_path = Path(
            __file__).parent.parent / "userData" / "userData.pck"

        if not model_path.exists() or not user_data_path.exists():
            self.status_label.setText(
                "Welcome! No user registered yet. Please register your face first."
            )
            self.status_label.setStyleSheet(f"color: {get_theme().warning};")
        else:
            self.status_label.setText(
                "Click below to login with face recognition")
            self.status_label.setStyleSheet("")  # Reset to default

    def _start_face_login(self):
        """Start face recognition login."""
        self.login_btn.setEnabled(False)
        self.login_btn.setText("🔄  Scanning...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        self._worker = FaceRecognitionWorker()
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.progress.connect(self.progress_bar.setValue)
        self._worker.finished.connect(self._on_login_finished)
        self._worker.start()

    def _on_status_changed(self, message: str, status_type: str):
        """Update status display."""
        self.status_label.setText(message)

        theme = get_theme()
        colors = {
            "info": theme.info,
            "success": theme.success,
            "error": theme.error,
            "warning": theme.warning,
        }
        color = colors.get(status_type, theme.text_primary)
        self.status_label.setStyleSheet(f"color: {color};")

    def _on_login_finished(self, success: bool, user_name: str):
        """Handle login result."""
        if success:
            self._on_login_success(user_name)
        else:
            self.login_btn.setEnabled(True)
            self.progress_bar.hide()

            # Check if it's because no face data exists
            model_path = Path(
                __file__).parent.parent / "userData" / "trainer.yml"
            if not model_path.exists():
                self.login_btn.setText("🔓  Login with Face ID")
                self.status_label.setText(
                    "No face data found. Please register first using 'Register Face' below."
                )
                self.status_label.setStyleSheet(
                    f"color: {get_theme().warning};")
            else:
                self.login_btn.setText("🔓  Try Again")
                self.status_label.setText(
                    "Face not recognized. Please try again or register if you're a new user."
                )

    def _on_login_success(self, user_name: str):
        """Handle successful login."""
        logger.info(f"Login successful for user: {user_name}")
        self.login_successful.emit(user_name)

        # Small delay to show success message
        QTimer.singleShot(500, self.close)

    def _open_registration(self):
        """Open the face registration dialog."""
        dialog = FaceRegistrationDialog(self)
        dialog.registration_complete.connect(self._on_registration_complete)
        dialog.exec()

    def _on_registration_complete(self, success):
        """Handle registration completion."""
        if success:
            # Refresh the login screen or show success message
            self.status_label.setText(
                "✅ Registration successful! You can now log in with face recognition."
            )
            self._reset_ui()

    def closeEvent(self, event):
        """Clean up on close."""
        if self._worker:
            self._worker.stop()
        event.accept()
