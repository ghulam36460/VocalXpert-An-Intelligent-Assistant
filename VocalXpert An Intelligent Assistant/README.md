# VocalXpert - An Intelligent Voice Assistant

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A Windows desktop voice assistant application featuring face recognition login, natural language processing, and a wide range of interactive features.

## 🌟 Features

### Authentication
- **Face Recognition Login** - Secure authentication using OpenCV's LBPH face recognizer
- **User Registration** - Easy setup with face data training
- **Avatar Selection** - Personalized user profiles

### Voice Commands
- **Speech Recognition** - Google Speech Recognition API
- **Text-to-Speech** - pyttsx3 engine with configurable voice
- **Natural Language Processing** - Intent detection and response generation

### Core Functionality
| Feature | Description |
|---------|-------------|
| 🌤️ Weather | Current weather conditions and forecasts |
| 📰 News | Latest headlines from news sources |
| 🔍 Wikipedia | Quick information lookups |
| ➗ Calculator | Voice-controlled mathematical operations |
| 📺 YouTube | Search and play videos |
| 📧 Email | Send emails via voice commands |
| 💬 WhatsApp | Automated WhatsApp messaging |
| 🌐 Web Scraping | Advanced intelligent web data extraction |
| 📝 Todo List | Task management and reminders |
| ⏰ Timer/Alarm | Time-based alerts |
| 🎮 Games | Interactive games (Dice, Rock-Paper-Scissors) |

### User Interface
- Modern dark/light theme toggle
- Scrollable chat history
- Real-time voice status indicator
- Responsive design

## 📁 Project Structure

```
VocalXpert An Intelligent Assistant/
├── main.py                 # Application entry point
├── Launcher.bat            # Windows launcher script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
├── .gitignore              # Git ignore rules
│
├── modules/                # Feature modules
│   ├── security.py         # Face recognition login GUI
│   ├── gui_assistant.py    # Main chat interface
│   ├── face_unlocker.py    # Face detection/recognition
│   ├── web_scrapping.py    # Weather, news, Wikipedia
│   ├── math_function.py    # Calculator with safe_eval
│   ├── normal_chat.py      # Casual conversation
│   ├── app_control.py      # System app control
│   ├── app_timer.py        # Timer functionality
│   ├── todo_handler.py     # Task management
│   ├── user_handler.py     # User data management
│   ├── file_handler.py     # File operations
│   ├── game.py             # Interactive games
│   └── dictionary.py       # Word definitions
│
├── assets/                 # Static resources
│   ├── images/             # UI images and avatars
│   ├── audios/             # Sound files
│   ├── dict_data.json      # Dictionary data
│   ├── normal_chat.json    # Chat responses
│   └── websites.json       # Website shortcuts
│
├── Cascade/                # OpenCV face detection model
├── model/                  # Speech recognition model (Vosk)
├── userData/               # User-specific data
│   ├── settings.pck        # App settings
│   ├── userData.pck        # User profile
│   ├── trainer.yml         # Face recognition model
│   └── faceData/           # Training face images
│
├── Camera/                 # Captured photos
├── Downloads/              # Downloaded files
└── Files and Document/     # User documents
```

## 🚀 Installation

### Prerequisites
- Windows 10/11
- Python 3.8 or higher
- Webcam (for face recognition)
- Microphone (for voice commands)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/VocalXpert.git
   cd VocalXpert
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Add your API keys if using external services

5. **Run the application**
   ```bash
   python main.py
   ```
   Or use the launcher:
   ```bash
   Launcher.bat
   ```

## 📦 Dependencies

Main dependencies (see `requirements.txt` for complete list):

| Package | Purpose |
|---------|---------|
| opencv-python | Face detection & recognition |
| Pillow | Image processing |
| pyttsx3 | Text-to-speech |
| SpeechRecognition | Voice input |
| beautifulsoup4 | Web scraping |
| requests | HTTP requests |
| wikipedia | Wikipedia API |
| geopy | Geolocation |
| vosk | Offline speech recognition |
| pyautogui | GUI automation |

## 🎯 Usage

### First Run
1. Launch the application
2. Click "Register" to create a new account
3. Follow the face registration process (50 images captured)
4. Select an avatar
5. Complete setup

### Voice Commands Examples
- "What's the weather today?"
- "Search Wikipedia for Python programming"
- "Play music on YouTube"
- "Open calculator"
- "What is 25 plus 17?"
- "Send email to example@email.com"
- "Set a timer for 5 minutes"
- "Tell me a joke"
- "Play rock paper scissors"

### Keyboard Shortcuts
- `Enter` - Send text message
- `Ctrl+D` - Toggle dark/light theme

## 🌐 Advanced Web Scraping

VocalXpert includes a powerful intelligent web scraping system that can extract information from multiple sources simultaneously.

### Scraping Modes

| Mode | Command Format | Description |
|------|----------------|-------------|
| **Normal** | `web scrapper : [query]` | Quick surface-level scraping from 3 sources |
| **Deep** | `web scrapper -deep : [query]` | Thorough scraping from 10+ sources with cross-references |
| **Force** | `web scrapper -force : [query]` | Maximum depth scraping (same as deep mode) |

### Usage Examples

```bash
# Basic information gathering
"web scrapper : list of programming languages"
"web scrapper : types of fruits"
"web scrapper : history of artificial intelligence"

# Deep research
"web scrapper -deep : quantum computing explained"
"web scrapper -force : machine learning algorithms"
```

### Task Management

Monitor and retrieve scraping results:

```bash
# Check scraping progress
"scraping status [task_id]"

# Get completed results
"scraping results [task_id]"

# List active scraping tasks
"list scrapers"
```

### Features

- **Background Processing** - Scraping runs asynchronously without blocking the UI
- **Multi-Source Aggregation** - Combines data from Wikipedia, dictionaries, encyclopedias, and more
- **Intelligent Deduplication** - Removes duplicate information automatically
- **Result Persistence** - Large result sets saved to temporary JSON files
- **Progress Tracking** - Real-time status updates with completion percentages
- **Error Handling** - Graceful failure handling with detailed error reporting

### Supported Libraries

- **BeautifulSoup4** - HTML parsing and data extraction
- **Requests** - HTTP client for web requests
- **Selenium** - Browser automation for JavaScript-heavy sites
- **lxml** - Fast XML/HTML processing
- **fake-useragent** - User agent rotation to avoid detection
- **aiohttp** - Asynchronous HTTP requests (future enhancement)

## ⚙️ Configuration

### Settings (userData/settings.pck)
- Voice selection (male/female)
- Volume level
- Speech rate
- Theme preference

### Environment Variables (.env)
```
WEATHER_API_KEY=your_weather_api_key
NEWS_API_KEY=your_news_api_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_email_password
```

## 🔒 Security

- Face recognition provides biometric authentication
- API keys stored in `.env` (not in version control)
- Safe mathematical expression evaluation (no `eval()`)
- User data stored locally in encrypted format

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not detected | Check webcam connection and permissions |
| Voice not recognized | Ensure microphone is working and volume is adequate |
| Face login fails | Re-train face data with better lighting |
| Module import errors | Verify all dependencies are installed |

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

- VocalXpert Development Team

## 🙏 Acknowledgments

- OpenCV team for face recognition capabilities
- Google Speech Recognition API
- Vosk for offline speech recognition
- All open-source libraries used in this project

---

*Made with ❤️ in Python*
