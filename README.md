

## Features / Tasks it can perform:  
1. Search anything from wikipedia, google maps, etc  
2. Play video from YouTube  
3. Email Sender  
4. WhatsApp Message Sender  
5. Weather  
6. Jokes  
7. News  
8.  High Security (Face Unlock)  
9.  Capture Photo  
10. Math Calculations  
11. Timer  
12. In-built search image display  
13. Smart Dictionary Search  
14. OS Info, Battery Info  
15. Window, Tab Operations  
16. Opening Websites  
17. File Operations (Creating Files)  
18. Web Automation (HTML Project)    
19. Translator  
20. ToDo List  
21. Screenshots  
22. Volume Control  

## Modules Requirements and Installation:  
```sh
pip install SpeechRecognition  
pip install pyttsx3  
pip install playsound  
pip install Pillow  
pip install pyscreenshot  
pip install pynput  
pip install psutil  
pip install opencv-contrib-python  
pip install opencv  
pip install wikipedia  
pip install webbrowser [Available with installer]  
pip install bs4  
pip install smtplib [Available with installer]  
pip install youtube-search-python  
pip install wmi  
pip install geopy  
pip install googletrans==3.1.0a0  
pip install python-dotenv  
```
## ***NOTE: This project is currently supported on Windows OS only***

## Environment
```sh
# create .env file and add these two properties
MAIL_USERNAME="myemail@gmail.com"
MAIL_PASSWORD="mypassword"
```

### To get started run main.py  
```sh
python main.py
```

## Curated Knowledge Datasets (Phase 1 Update)

Phase 1 replaced an oversized and malformed `assets/normal_chat.json` with a concise, policy‑aligned dataset focusing on:
- Military College of Signals (MCS)
- Signal Corps (Pakistan Army)
- Pakistan Army overview
- NUST, PMA
- Pakistan history, national days, heroes, awards
- Instructor info (DSA: Lt Col Imran Javed, EDC: Zeeshan Zahid, CP: Lt Col Raza, MVC: Ma'am Farhanda)

New files introduced:
- `assets/normal_chat_v2.json`: Active chat intent → list of response strings (55 clean intents). The old `normal_chat.json` was malformed (extra trailing JSON) and is deprecated.
- `assets/websites_v2.json`: Focused keyword → list of URLs emphasizing MCS, NUST, PMA, Pakistan Army, Signal Corps plus core study/platform sites.

Code changes:
- `modules/normal_chat.py` now loads `normal_chat_v2.json`.
- `modules/app_control.py` now loads `websites_v2.json` and its website opener handles both list and single string URL values safely.

If you need to restore legacy breadth temporarily, keep a backup copy of the old files outside the repo; they are intentionally removed to reduce redundancy and improve relevance.

### Extending Datasets
Add intents or URLs by editing the v2 JSON files. Maintain the structure:
```json
// normal_chat_v2.json
"intent phrase": ["Response A", "Response B"]
```
```json
// websites_v2.json
"keyword": ["https://example.com/", "https://alternate.example.com/"]
```
Keep keys unique and responses factual, concise, and aligned with the focus areas above.


## Math Calculations 
- What is the binary of 142?  
- 2 + 4 - 3 x 9  
- Right shift 4  
- What is the value of factorial 10?  
- What is the value of Sin 90?  
- 9 power 5  
- what is the log of 1000  
  

## Email Sender  
- Send an email -> Receiver Email -> Subject -> Message  

## WhatsApp Sender  
- Send a whatsapp message -> Receiver Phone No -> Message   

## Translator  
- Translate a sentence -> "Hello, how are you?" -> Hindi  

## Smart Dictionary  
- What is the definition of Machine Learning?  
- What is the meaning of Natural Language Processing?  

## Timer  
- Set a timer for 10 seconds  
- Set a timer for 2 minutes  
- Set a timer for 1 minute 10 seconds  

## ToDo List  
- Add an item to my list -> "This is my first Item in my list"  
- Show my list  

## OS Info  
- Give my System Information  
- What's my battery life  

## Selfie / Photo Clicker  
- Take a Selfie  
- Click a Photo  

## Volume Control  
- Increase the Volume  
- Decrease the Volume  
- Mute the Volume  
- Full Volume  

## YouTube  
- Play Captain America Trailer on YouTube  
- Google I/O on YouTube  

## Image Result  
- Show the images of Robot  
- Show the images of Samosa  

## Wikipedia Result  
- Who is Sundar Pichai?  
- Who is Satya Nadella?  
- Artifical Intelligence on Wikipedia  

## Google Search  
- Search for new technologies  
- Search for data structures and algorithms  

## Google Maps  
- India on Google Maps  
- Washington DC on Google Maps  

## Joke Teller  
- Tell me a joke  
- Tell me a funny joke  

## News  
- Give me some news  
- Get the latest news  

## Weather  
- What is the weather?  

## ScreenShot  
- Take a ScreenShot  

## Window Operations  
- Open Window  
- Close Window 
- Switch Window  
- Maximize/Minimize Window  

## Tab Operations  
- Create new tab  
- Switch Tab  
- Close tab  

## System Apps  
- Open Paint  
- Open Notepad  
- Open Calculator  

## Automatic Typer  
- Open Notepad -> Say type " I'm currently not typing the text which I'm saying right now "
- Select All  
- Delete/Backspace  
- Save that  
- Press enter  


## Time / Date  
- What is the time?  
- What is the date today?  

## Voice Changer  
- Change your voice  
- Change your voice to Male/Female voice  

## Website Opener  
- Open Facebook  
- Open NADRA  
- Open PIA  
  
## Smart Reply  
- How are you?  
- Who are you?  
- Tell me something  
- When is your birthday?  
- You're so funny  
- Thank You  
- I'm sorry  


## Common Installation Issues  
```
pyaudio not installing  
  1. Download the pyaudio wheel version from https://www.lfd.uci.edu/~gohlke/pythonlibs/ (eg, if you have python version 3.7, download the file containing cp37)
  2. Install it using (eg, pip install PyAudio‑0.2.11‑cp37‑cp37m‑win_amd64.whl)
```

(USE PYTHON <= 3.8 WHICH SUPPORTS ALL THE LIBRARIES)
