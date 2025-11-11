# import pyscreenshot as ImageGrab
# import time
# import subprocess
# from pynput.keyboard import Key, Controller
# import psutil
# import pyautogui


# class SystemTasks:
#     def __init__(self):
#         self.keyboard = Controller()

#     def openApp(self, appName):
#         """
#         Tries to open an application from the System32 folder.
#         If that fails, it uses pyautogui to search for the app in the Start Menu.
#         """
#         appName = appName.lower()
        
#         # Replacements for common apps
#         app_replacements = {
#             'paint': 'mspaint',
#             'wordpad': 'write',
#             'word': 'winword',
#             'calculator': 'calc',
#             'notepad': 'notepad',
#             'cmd': 'cmd',
#             'edge': 'msedge',
#             'chrome': 'chrome',
#             'firefox': 'firefox',
#             'explorer': 'explorer',
#             'excel': 'excel',
#             'powerpoint': 'powerpnt',
#             'skype': 'Skype',
#             'teams': 'teams',
#             'discord': 'discord',
#             'spotify': 'spotify'
#         }
        
#         # Apply known replacements
#         for old, new in app_replacements.items():
#             appName = appName.replace(old, new)

#         # Try to open the app from System32
#         try:
#             subprocess.Popen(f'C:\\Windows\\System32\\{appName}.exe')
#             print(f"Opening {appName} from System32.")
#         except FileNotFoundError:
#             # If not found in System32, try using pyautogui to search the Start Menu
#             print(f"{appName} not found in System32, trying to search through Start Menu.")
#             self.searchAppInStartMenu(appName)

#     def searchAppInStartMenu(self, appName):
#         """
#         Uses PyAutoGUI to search for the app in the Start Menu and opens it.
#         """
#         try:
#             pyautogui.hotkey('winleft')  # Open Start Menu
#             time.sleep(1)
#             pyautogui.write(appName)  # Type the app name to search for it
#             time.sleep(1)
#             pyautogui.press('enter')  # Press Enter to open the app
#             print(f"App {appName} opened from Start Menu.")
#         except Exception as e:
#             print(f"Failed to open {appName} from Start Menu. Error: {e}")

#     def write(self, text):
#         text = text[5:]  # Remove any leading 'write' command
#         for char in text:
#             self.keyboard.type(char)
#             time.sleep(0.02)

#     def select(self):
#         self.keyboard.press(Key.ctrl)
#         self.keyboard.press('a')
#         self.keyboard.release('a')
#         self.keyboard.release(Key.ctrl)

#     def hitEnter(self):
#         self.keyboard.press(Key.enter)
#         self.keyboard.release(Key.enter)

#     def delete(self):
#         self.keyboard.press(Key.backspace)
#         self.keyboard.release(Key.backspace)

#     def save(self, text):
#         if "don't" in text:
#             self.keyboard.press(Key.right)
#         else: 
#             self.keyboard.press(Key.ctrl)
#             self.keyboard.press('s')
#             self.keyboard.release('s')
#             self.keyboard.release(Key.ctrl)
#         self.hitEnter()

# # class SystemTasks:
# # 	def __init__(self):
# # 		self.keyboard = Controller()

# # 	def openApp(self, appName):
# # 		appName = appName.replace('paint', 'mspaint')
# # 		appName = appName.replace('wordpad', 'write')
# # 		appName = appName.replace('word', 'write')
# # 		appName = appName.replace('calculator', 'calc')
# # 		try: subprocess.Popen('C:\\Windows\\System32\\'+appName[5:]+'.exe')
# # 		except: pass

# # 	def write(self, text):
# # 		text = text[5:]
# # 		for char in text:
# # 			self.keyboard.type(char)
# # 			time.sleep(0.02)

# # 	def select(self):
# # 		self.keyboard.press(Key.ctrl)
# # 		self.keyboard.press('a')
# # 		self.keyboard.release('a')
# # 		self.keyboard.release(Key.ctrl)

# # 	def hitEnter(self):
# # 		self.keyboard.press(Key.enter)
# # 		self.keyboard.release(Key.enter)

# # 	def delete(self):
# # 		self.keyboard.press(Key.backspace)
# # 		self.keyboard.release(Key.enter)

# # 	def save(self, text):
# # 		if "don't" in text:
# # 			self.keyboard.press(Key.right)
# # 		else: 
# # 			self.keyboard.press(Key.ctrl)
# # 			self.keyboard.press('s')
# # 			self.keyboard.release('s')
# # 			self.keyboard.release(Key.ctrl)
# # 		self.hitEnter()

# class TabOpt:
# 	def __init__(self):
# 		self.keyboard = Controller()

# 	def switchTab(self):
# 		self.keyboard.press(Key.ctrl)
# 		self.keyboard.press(Key.tab)
# 		self.keyboard.release(Key.tab)
# 		self.keyboard.release(Key.ctrl)

# 	def closeTab(self):
# 		self.keyboard.press(Key.ctrl)
# 		self.keyboard.press('w')
# 		self.keyboard.release('w')
# 		self.keyboard.release(Key.ctrl)

# 	def newTab(self):
# 		self.keyboard.press(Key.ctrl)
# 		self.keyboard.press('n')
# 		self.keyboard.release('n')
# 		self.keyboard.release(Key.ctrl)


# class WindowOpt:
# 	def __init__(self):
# 		self.keyboard = Controller()

# 	def openWindow(self):
# 		self.maximizeWindow()
	
# 	def closeWindow(self):
# 		self.keyboard.press(Key.alt_l)
# 		self.keyboard.press(Key.f4)
# 		self.keyboard.release(Key.f4)
# 		self.keyboard.release(Key.alt_l)
	
# 	def minimizeWindow(self):
# 		for i in range(2):
# 			self.keyboard.press(Key.cmd)
# 			self.keyboard.press(Key.down)
# 			self.keyboard.release(Key.down)
# 			self.keyboard.release(Key.cmd)
# 			time.sleep(0.05)
	
# 	def maximizeWindow(self):
# 		self.keyboard.press(Key.cmd)
# 		self.keyboard.press(Key.up)
# 		self.keyboard.release(Key.up)
# 		self.keyboard.release(Key.cmd)

# 	def moveWindow(self, operation):
# 		self.keyboard.press(Key.cmd)

# 		if "left" in operation:
# 			self.keyboard.press(Key.left)
# 			self.keyboard.release(Key.left)
# 		elif "right" in operation:
# 			self.keyboard.press(Key.right)
# 			self.keyboard.release(Key.right)
# 		elif "down" in operation:
# 			self.keyboard.press(Key.down)
# 			self.keyboard.release(Key.down)
# 		elif "up" in operation:
# 			self.keyboard.press(Key.up)
# 			self.keyboard.release(Key.up)
# 		self.keyboard.release(Key.cmd)

# 	def switchWindow(self):
# 		self.keyboard.press(Key.alt_l)
# 		self.keyboard.press(Key.tab)
# 		self.keyboard.release(Key.tab)
# 		self.keyboard.release(Key.alt_l)
		

# 	def takeScreenShot(self):
# 		from random import randint
# 		im = ImageGrab.grab()
# 		im.save(f'Files and Document/ss_{randint(1, 100)}.jpg')

# def isContain(text, lst):
# 	for word in lst:
# 		if word in text:
# 			return True
# 	return False

# def Win_Opt(operation):
# 	w = WindowOpt()
# 	if isContain(operation, ['open']):
# 		w.openWindow()
# 	elif isContain(operation, ['close']):
# 		w.closeWindow()
# 	elif isContain(operation, ['mini']):
# 		w.minimizeWindow()
# 	elif isContain(operation, ['maxi']):
# 		w.maximizeWindow()
# 	elif isContain(operation, ['move', 'slide']):
# 		w.moveWindow(operation)
# 	elif isContain(operation, ['switch','which']):
# 		w.switchWindow()
# 	elif isContain(operation, ['screenshot','capture','snapshot']):
# 		w.takeScreenShot()
# 	return

# def Tab_Opt(operation):
# 	t = TabOpt()
# 	if isContain(operation, ['new','open','another','create']):
# 		t.newTab()
# 	elif isContain(operation, ['switch','move','another','next','previous','which']):
# 		t.switchTab()
# 	elif isContain(operation, ['close','delete']):
# 		t.closeTab()
# 	else:
# 		return


# def System_Opt(operation):
# 	s = SystemTasks()
# 	if 'delete' in operation:
# 		s.delete()
# 	elif 'save' in operation:
# 		s.save(operation)
# 	elif 'type' in operation:
# 		s.write(operation)
# 	elif 'select' in operation:
# 		s.select()
# 	elif 'enter' in operation:
# 		s.hitEnter()
# 	elif isContain(operation, ['notepad','paint','calc','word']):
# 		s.openApp(operation)
# 	elif isContain(operation, ['music','video']):
# 		s.playMusic(operation)
# 	else:
# 		open_website(operation)
# 		return


# ###############################
# ###########  VOLUME ###########
# ###############################

# keyboard = Controller()
# def mute():
# 	for i in range(50):
# 		keyboard.press(Key.media_volume_down)
# 		keyboard.release(Key.media_volume_down)

# def full():
# 	for i in range(50):
# 		keyboard.press(Key.media_volume_up)
# 		keyboard.release(Key.media_volume_up)


# def volumeControl(text):
# 	if 'full' in text or 'max' in text: full()
# 	elif 'mute' in text or 'min' in text: mute()
# 	elif 'incre' in text:
# 		for i in range(5):
# 			keyboard.press(Key.media_volume_up)
# 			keyboard.release(Key.media_volume_up)
# 	elif 'decre' in text:
# 		for i in range(5):
# 			keyboard.press(Key.media_volume_down)
# 			keyboard.release(Key.media_volume_down)

# def systemInfo():
# 	import wmi
# 	c = wmi.WMI()  
# 	my_system_1 = c.Win32_LogicalDisk()[0]
# 	my_system_2 = c.Win32_ComputerSystem()[0]
# 	info = ["Total Disk Space: " + str(round(int(my_system_1.Size)/(1024**3),2)) + " GB",
# 			"Free Disk Space: " + str(round(int(my_system_1.Freespace)/(1024**3),2)) + " GB",
# 			"Manufacturer: " + my_system_2.Manufacturer,
# 			"Model: " + my_system_2. Model,
# 			"Owner: " + my_system_2.PrimaryOwnerName,
# 			"Number of Processors: " + str(my_system_2.NumberOfProcessors),
# 			"System Type: " + my_system_2.SystemType]
# 	return info

# def batteryInfo():
# 	# usage = str(psutil.cpu_percent(interval=0.1))
# 	battery = psutil.sensors_battery()
# 	pr = str(battery.percent)
# 	if battery.power_plugged:
# 		return "Your System is currently on Charging Mode and it's " + pr + "% done."
# 	return "Your System is currently on " + pr + "% battery life."

# def OSHandler(query):
# 	if isContain(query, ['system', 'info']):
# 		return ['Here is your System Information...', '\n'.join(systemInfo())]
# 	elif isContain(query, ['cpu', 'battery']):
# 		return batteryInfo()


# from difflib import get_close_matches
# import json
# from random import choice
# import webbrowser

# data = json.load(open('assets/websites.json', encoding='utf-8'))

# def open_website(query):
# 	query = query.replace('open','')
# 	if query in data:
# 		response = data[query]
# 	else:
# 		query = get_close_matches(query, data.keys(), n=2, cutoff=0.5)
# 		if len(query)==0: return "None"
# 		response = choice(data[query[0]])
# 	webbrowser.open(response)
import pyscreenshot as ImageGrab
import time
import subprocess
from pynput.keyboard import Key, Controller
import psutil
import pyautogui
from difflib import get_close_matches
import json
from random import choice
import webbrowser
import wmi


# Class to handle system tasks such as opening apps, writing, etc.
class SystemTasks:
    def __init__(self):
        self.keyboard = Controller()

    def openApp(self, appName):
        """
        Searches for the application in the Start Menu and opens it.
        """
        appName = appName.lower()  # Convert app name to lowercase
        
        # Try searching for the app in the Start Menu
        self.searchAppInStartMenu(appName)

    def searchAppInStartMenu(self, appName):
        """
        Uses PyAutoGUI to search for the app in the Start Menu and open it.
        """
        try:
            pyautogui.hotkey('winleft')  # Open Start Menu
            time.sleep(1)
            pyautogui.write(appName)  # Type the app name to search for it
            time.sleep(1)
            pyautogui.press('enter')  # Press Enter to open the app
            print(f"App '{appName}' opened from Start Menu.")
        except Exception as e:
            print(f"Failed to open '{appName}' from Start Menu. Error: {e}")
    
    def write(self, text):
        text = text[5:]  # Remove any leading 'write' command
        for char in text:
            self.keyboard.type(char)
            time.sleep(0.02)

    def select(self):
        self.keyboard.press(Key.ctrl)
        self.keyboard.press('a')
        self.keyboard.release('a')
        self.keyboard.release(Key.ctrl)

    def hitEnter(self):
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)

    def delete(self):
        self.keyboard.press(Key.backspace)
        self.keyboard.release(Key.backspace)

    def save(self, text):
        if "don't" in text:
            self.keyboard.press(Key.right)
        else: 
            self.keyboard.press(Key.ctrl)
            self.keyboard.press('s')
            self.keyboard.release('s')
            self.keyboard.release(Key.ctrl)
        self.hitEnter()


# Class to handle tab operations like switching tabs, closing tabs, etc.
class TabOpt:
    def __init__(self):
        self.keyboard = Controller()

    def switchTab(self):
        self.keyboard.press(Key.ctrl)
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        self.keyboard.release(Key.ctrl)

    def closeTab(self):
        self.keyboard.press(Key.ctrl)
        self.keyboard.press('w')
        self.keyboard.release('w')
        self.keyboard.release(Key.ctrl)

    def newTab(self):
        self.keyboard.press(Key.ctrl)
        self.keyboard.press('n')
        self.keyboard.release('n')
        self.keyboard.release(Key.ctrl)


# Class to handle window operations like minimizing, maximizing, closing, etc.
class WindowOpt:
    def __init__(self):
        self.keyboard = Controller()

    def openWindow(self):
        self.maximizeWindow()
    
    def closeWindow(self):
        self.keyboard.press(Key.alt_l)
        self.keyboard.press(Key.f4)
        self.keyboard.release(Key.f4)
        self.keyboard.release(Key.alt_l)
    
    def minimizeWindow(self):
        for i in range(2):
            self.keyboard.press(Key.cmd)
            self.keyboard.press(Key.down)
            self.keyboard.release(Key.down)
            self.keyboard.release(Key.cmd)
            time.sleep(0.05)
    
    def maximizeWindow(self):
        self.keyboard.press(Key.cmd)
        self.keyboard.press(Key.up)
        self.keyboard.release(Key.up)
        self.keyboard.release(Key.cmd)

    def moveWindow(self, operation):
        self.keyboard.press(Key.cmd)

        if "left" in operation:
            self.keyboard.press(Key.left)
            self.keyboard.release(Key.left)
        elif "right" in operation:
            self.keyboard.press(Key.right)
            self.keyboard.release(Key.right)
        elif "down" in operation:
            self.keyboard.press(Key.down)
            self.keyboard.release(Key.down)
        elif "up" in operation:
            self.keyboard.press(Key.up)
            self.keyboard.release(Key.up)
        self.keyboard.release(Key.cmd)

    def switchWindow(self):
        self.keyboard.press(Key.alt_l)
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)
        self.keyboard.release(Key.alt_l)
        
    def takeScreenShot(self):
        from random import randint
        im = ImageGrab.grab()
        im.save(f'Files and Document/ss_{randint(1, 100)}.jpg')


# Function to check if a text contains a list of keywords
def isContain(text, lst):
    for word in lst:
        if word in text:
            return True
    return False


# Function to handle window operations
def Win_Opt(operation):
    w = WindowOpt()
    if isContain(operation, ['open']):
        w.openWindow()
    elif isContain(operation, ['close']):
        w.closeWindow()
    elif isContain(operation, ['mini']):
        w.minimizeWindow()
    elif isContain(operation, ['maxi']):
        w.maximizeWindow()
    elif isContain(operation, ['move', 'slide']):
        w.moveWindow(operation)
    elif isContain(operation, ['switch','which']):
        w.switchWindow()
    elif isContain(operation, ['screenshot','capture','snapshot']):
        w.takeScreenShot()
    return


# Function to handle tab operations
def Tab_Opt(operation):
    t = TabOpt()
    if isContain(operation, ['new','open','another','create']):
        t.newTab()
    elif isContain(operation, ['switch','move','another','next','previous','which']):
        t.switchTab()
    elif isContain(operation, ['close','delete']):
        t.closeTab()
    else:
        return


# Function to handle system operations like saving, typing, deleting
def System_Opt(operation):
    s = SystemTasks()
    if 'delete' in operation:
        s.delete()
    elif 'save' in operation:
        s.save(operation)
    elif 'type' in operation:
        s.write(operation)
    elif 'select' in operation:
        s.select()
    elif 'enter' in operation:
        s.hitEnter()
    elif 'launch' in operation:
        app_name = operation.replace('launch', '').strip()
        s.openApp(app_name)
    elif isContain(operation, ['music', 'video']):
        s.playMusic(operation)
    elif 'open' in operation:  # Check if it's a website opening request
        open_website(operation)
    else:
        # If no app or website is detected, perform general operations
        open_website(operation)
        return


# Function to handle volume controls like mute, max volume, etc.
keyboard = Controller()
def mute():
    for i in range(50):
        keyboard.press(Key.media_volume_down)
        keyboard.release(Key.media_volume_down)

def full():
    for i in range(50):
        keyboard.press(Key.media_volume_up)
        keyboard.release(Key.media_volume_up)


def volumeControl(text):
    if 'full' in text or 'max' in text: full()
    elif 'mute' in text or 'min' in text: mute()
    elif 'incre' in text:
        for i in range(5):
            keyboard.press(Key.media_volume_up)
            keyboard.release(Key.media_volume_up)
    elif 'decre' in text:
        for i in range(5):
            keyboard.press(Key.media_volume_down)
            keyboard.release(Key.media_volume_down)

import wmi

def systemInfo():
    try:
        # Initialize the WMI client
        c = wmi.WMI()

        # Fetch system information
        logical_disk = c.Win32_LogicalDisk()[0]
        computer_system = c.Win32_ComputerSystem()[0]

        # Prepare system information
        info = [
            "Total Disk Space: " + str(round(int(logical_disk.Size) / (1024**3), 2)) + " GB",
            "Free Disk Space: " + str(round(int(logical_disk.Freespace) / (1024**3), 2)) + " GB",
            "Manufacturer: " + computer_system.Manufacturer,
            "Model: " + computer_system.Model,
            "Memory: " + str(round(int(computer_system.TotalPhysicalMemory) / (1024**3), 2)) + " GB",
            "OS: " + computer_system.Caption
        ]

        # Print system information
        for line in info:
            print(line)

    except Exception as e:
        print("An error occurred while fetching system information:", e)

# Test the function
systemInfo()

# # Function to get system information
# def systemInfo():
#     c = wmi.WMI()  
#     my_system_1 = c.Win32_LogicalDisk()[0]
#     my_system_2 = c.Win32_ComputerSystem()[0]
#     info = ["Total Disk Space: " + str(round(int(my_system_1.Size)/(1024**3),2)) + " GB",
#             "Free Disk Space: " + str(round(int(my_system_1.Freespace)/(1024**3),2)) + " GB",
#             "Manufacturer: " + my_system_2.Manufacturer,
#             "Model: " + my_system_2.Model,
#             "Memory: " + str(round(int(my_system_2.TotalPhysicalMemory)/(1024**3),2)) + " GB",
#             "OS: " + my_system_2.Caption]

#     for line in info:
#         print(line)


# Function to open a website based on user query
# def open_website(query):
#     websites_file = 'assets/websites.json'
#     try:
#         with open(websites_file, 'r') as file:
#             websites = json.load(file)
#         website_name = query.replace("open website", "").strip()
#         matching_website = get_close_matches(website_name, websites.keys(), n=1, cutoff=0.6)
#         if matching_website:
#             print(f"Opening {matching_website[0]}...")
#             webbrowser.open(websites[matching_website[0]])
#         else:
#             print(f"Website {website_name} not found.")
#     except FileNotFoundError:
#         print(f"Error: {websites_file} not found.")

data = json.load(open('assets/websites_v2.json', encoding='utf-8'))

def open_website(query):
    query = query.replace('open','').strip()
    # Exact match first
    if query in data:
        value = data[query]
        response = choice(value) if isinstance(value, list) else value
    else:
        # Fuzzy match fallback
        matches = get_close_matches(query, data.keys(), n=2, cutoff=0.5)
        if len(matches) == 0:
            return "None"
        value = data[matches[0]]
        response = choice(value) if isinstance(value, list) else value
    webbrowser.open(response)