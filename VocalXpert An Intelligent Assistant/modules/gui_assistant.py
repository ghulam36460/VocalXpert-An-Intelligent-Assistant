"""
GUI Assistant Module - Main Chat Interface

Provides the main Tkinter-based graphical interface for VocalXpert.
Handles voice recognition input, text-to-speech output, and all
user interactions including:
    - Voice and text command processing
    - Chat display with scrollable history
    - Theme switching (light/dark mode)
    - Integration with all feature modules

Dependencies:
    - pyttsx3: Text-to-speech engine
    - speech_recognition: Voice input processing
    - Custom modules: normal_chat, math_function, web_scrapping, etc.
"""

#########################
# GLOBAL VARIABLES USED #
#########################
ai_name = 'VocalXpert'.lower()
EXIT_COMMANDS = ['bye','exit','quit','shut down', 'shutdown','sleep', 'see you soon', 'turn off','bye bye']

rec_email, rec_phoneno = "", ""
WAEMEntry = None

avatarChoosen = 0
choosedAvtrImage = None

# Modern Color Palette
botChatTextBg = "#6366f1"  # Indigo
botChatText = "white"
userChatTextBg = "#10b981"  # Emerald

chatBgColor = '#0f172a'  # Slate 900
background = '#1e293b'  # Slate 800
textColor = '#f1f5f9'  # Slate 100
AITaskStatusLblBG = '#1e293b'
KCS_IMG = 1 #0 for light, 1 for dark

# Accent colors
ACCENT_PRIMARY = '#6366f1'  # Indigo
ACCENT_SECONDARY = '#10b981'  # Emerald
ACCENT_WARNING = '#f59e0b'  # Amber
BUTTON_HOVER = '#4f46e5'  # Darker indigo
voice_id = 0 #0 for female, 1 for male
ass_volume = 1 #max volume
ass_voiceRate = 200 #normal voice rate

# AI Status
AI_ONLINE = False

####################################### IMPORTING MODULES ###########################################
""" User Created Modules """
try:
	import normal_chat
	import math_function
	import app_control
	import web_scrapping
	# import game
	import app_timer
	import dictionary
	import todo_handler
	import file_handler
	from user_handler import UserData
	from face_unlocker import clickPhoto, viewPhoto
	from dotenv import load_dotenv

	load_dotenv()
except Exception as e:
	raise e

""" System Modules """
try:
	import os
	import speech_recognition as sr
	import pyttsx3
	from tkinter import *
	from tkinter import ttk
	from tkinter import messagebox
	from tkinter import colorchooser
	from PIL import Image, ImageTk
	from time import sleep
	from threading import Thread
except Exception as e:
	print(e)

########################################## LOGIN CHECK ##############################################
try:
	user = UserData()
	user.extractData()
	ownerName = user.getName().split()[0]
	ownerDesignation = "Sir"
	if user.getGender()=="Female": ownerDesignation = "Ma'am"
	ownerPhoto = user.getUserPhoto()
except Exception as e:
	print("You're not Registered Yet !\nRun SECURITY.py file to register your face.")
	raise SystemExit


########################################## BOOT UP WINDOW ###########################################
def ChangeSettings(write=False):
	import pickle
	global background, textColor, chatBgColor, voice_id, ass_volume, ass_voiceRate, AITaskStatusLblBG, KCS_IMG, botChatTextBg, botChatText, userChatTextBg
	setting = {'background': background,
				'textColor': textColor,
				'chatBgColor': chatBgColor,
				'AITaskStatusLblBG': AITaskStatusLblBG,
				'KCS_IMG': KCS_IMG,
				'botChatText': botChatText,
				'botChatTextBg': botChatTextBg,
				'userChatTextBg': userChatTextBg,
				'voice_id': voice_id,
				'ass_volume': ass_volume,
				'ass_voiceRate': ass_voiceRate
			}
	if write:
		with open('userData/settings.pck', 'wb') as file:
			pickle.dump(setting, file)
		return
	try:
		with open('userData/settings.pck', 'rb') as file:
			loadSettings = pickle.load(file)
			background = loadSettings['background']
			textColor = loadSettings['textColor']
			chatBgColor = loadSettings['chatBgColor']
			AITaskStatusLblBG = loadSettings['AITaskStatusLblBG']
			KCS_IMG = loadSettings['KCS_IMG']
			botChatText = loadSettings['botChatText']
			botChatTextBg = loadSettings['botChatTextBg']
			userChatTextBg = loadSettings['userChatTextBg']
			voice_id = loadSettings['voice_id']
			ass_volume = loadSettings['ass_volume']
			ass_voiceRate = loadSettings['ass_voiceRate']
	except Exception as e:
		pass

if os.path.exists('userData/settings.pck')==False:
	ChangeSettings(True)

def changeTheme():
	global background, textColor, AITaskStatusLblBG, KCS_IMG, botChatText, botChatTextBg, userChatTextBg, chatBgColor
	if themeValue.get()==1:
		# Modern Dark Theme
		background, textColor, AITaskStatusLblBG, KCS_IMG = "#1e293b", "#f1f5f9", "#1e293b", 1
		cbl['image'] = cblDarkImg
		kbBtn['image'] = kbphDark
		settingBtn['image'] = sphDark
		AITaskStatusLbl['bg'] = AITaskStatusLblBG
		botChatText, botChatTextBg, userChatTextBg = "white", "#6366f1", "#10b981"
		chatBgColor = "#0f172a"
		colorbar['bg'] = chatBgColor
		bottomFrame1['bg'] = '#334155'
		VoiceModeFrame['bg'] = '#334155'
		TextModeFrame['bg'] = '#334155'
		cbl['bg'] = '#334155'
		settingBtn['bg'] = '#334155'
		kbBtn['bg'] = '#334155'
		micBtn['bg'] = '#334155'
		UserFieldLBL['bg'] = '#334155'
	else:
		# Modern Light Theme
		background, textColor, AITaskStatusLblBG, KCS_IMG = "#f8fafc", "#1e293b", "#10b981", 0
		cbl['image'] = cblLightImg
		kbBtn['image'] = kbphLight
		settingBtn['image'] = sphLight
		AITaskStatusLbl['bg'] = AITaskStatusLblBG
		botChatText, botChatTextBg, userChatTextBg = "#1e293b", "#e0e7ff", "#10b981"
		chatBgColor = "#f8fafc"
		colorbar['bg'] = '#e2e8f0'
		bottomFrame1['bg'] = '#e2e8f0'
		VoiceModeFrame['bg'] = '#e2e8f0'
		TextModeFrame['bg'] = '#e2e8f0'
		cbl['bg'] = '#e2e8f0'
		settingBtn['bg'] = '#e2e8f0'
		kbBtn['bg'] = '#e2e8f0'
		micBtn['bg'] = '#e2e8f0'
		UserFieldLBL['bg'] = '#e2e8f0'

	root['bg'], root2['bg'] = background, background
	settingsFrame['bg'] = background
	settingsLbl['fg'], userPhoto['fg'], userName['fg'], assLbl['fg'], voiceRateLbl['fg'], volumeLbl['fg'], themeLbl['fg'], chooseChatLbl['fg'] = textColor, textColor, textColor, textColor, textColor, textColor, textColor, textColor
	settingsLbl['bg'], userPhoto['bg'], userName['bg'], assLbl['bg'], voiceRateLbl['bg'], volumeLbl['bg'], themeLbl['bg'], chooseChatLbl['bg'] = background, background, background, background, background, background, background, background
	s.configure('Wild.TRadiobutton', background=background, foreground=textColor)
	volumeBar['bg'], volumeBar['fg'], volumeBar['highlightbackground'] = background, textColor, background
	chat_frame['bg'], chat_canvas['bg'], chat_container['bg'], root1['bg'] = chatBgColor, chatBgColor, chatBgColor, chatBgColor
	userPhoto['activebackground'] = background
	ChangeSettings(True)

def changeVoice(e):
	global voice_id
	voice_id=0
	if assVoiceOption.get()=='Male': voice_id=1
	engine.setProperty('voice', voices[voice_id].id)
	ChangeSettings(True)

def changeVolume(e):
	global ass_volume
	ass_volume = volumeBar.get() / 100
	engine.setProperty('volume', ass_volume)
	ChangeSettings(True)

def changeVoiceRate(e):
	global ass_voiceRate
	temp = voiceOption.get()
	if temp=='Very Low': ass_voiceRate = 100
	elif temp=='Low': ass_voiceRate = 150
	elif temp=='Fast': ass_voiceRate = 250
	elif temp=='Very Fast': ass_voiceRate = 300
	else: ass_voiceRate = 200
	print(ass_voiceRate)
	engine.setProperty('rate', ass_voiceRate)
	ChangeSettings(True)

ChangeSettings()

############################################ SET UP VOICE ###########################################
try:
	engine = pyttsx3.init()
	voices = engine.getProperty('voices')
	engine.setProperty('voice', voices[voice_id].id) #male
	engine.setProperty('volume', ass_volume)
except Exception as e:
	print(e)


####################################### SET UP TEXT TO SPEECH #######################################
def speak(text, display=False, icon=False):
	AITaskStatusLbl['text'] = 'Speaking...'
	if icon: Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor='w',pady=0)
	if display: attachTOframe(text, True)
	print('\n'+ai_name.upper()+': '+text)
	try:
		engine.say(text)
		engine.runAndWait()
	except:
		print("Try not to type more...")

####################################### SET UP SPEECH TO TEXT #######################################
def record(clearChat=True, iconDisplay=True):
	print('\nListening...')
	AITaskStatusLbl['text'] = 'Listening...'
	r = sr.Recognizer()
	r.dynamic_energy_threshold = False
	r.energy_threshold = 4000
	with sr.Microphone() as source:
		r.adjust_for_ambient_noise(source)
		audio = r.listen(source)
		said = ""
		try:
			AITaskStatusLbl['text'] = 'Processing...'
			said = r.recognize_google(audio)
			print(f"\nUser said: {said}")
			if clearChat:
				clearChatScreen()
			if iconDisplay: Label(chat_frame, image=userIcon, bg=chatBgColor).pack(anchor='e',pady=0)
			attachTOframe(said)
		except Exception as e:
			print(e)
			# speak("I didn't get it, Say that again please...")
			if "connection failed" in str(e):
				speak("Your System is Offline...", True, True)
			return 'None'
	return said.lower()

def voiceMedium():
	while True:
		query = record()
		if query == 'None': continue
		if isContain(query, EXIT_COMMANDS):
			speak("Shutting down the System. Good Bye "+ownerDesignation+"!", True, True)
			break
		else: main(query.lower())
	app_control.Win_Opt('close')

def keyboardInput(e):
	user_input = UserField.get().lower()
	if user_input!="":
		clearChatScreen()
		if isContain(user_input, EXIT_COMMANDS):
			speak("Shutting down the System. Good Bye "+ownerDesignation+"!", True, True)
		else:
			Label(chat_frame, image=userIcon, bg=chatBgColor).pack(anchor='e',pady=0)
			attachTOframe(user_input.capitalize())
			Thread(target=main, args=(user_input,)).start()
		UserField.delete(0, END)

###################################### TASK/COMMAND HANDLER #########################################
def isContain(txt, lst):
	for word in lst:
		if word in txt:
			return True
	return False

def main(text):

		if "project" in text:
			if isContain(text, ['make', 'create']):
				speak("What do you want to give the project name ?", True, True)
				projectName = record(False, False)
				speak(file_handler.CreateHTMLProject(projectName.capitalize()), True)
				return

		if "create" in text and "file" in text:
			speak(file_handler.createFile(text), True, True)
			return

		if "translate" in text:
			speak("What do you want to translate?", True, True)
			sentence = record(False, False)
			speak("Which langauage to translate ?", True)
			langauage = record(False, False)
			result = normal_chat.lang_translate(sentence, langauage)
			if result=="None": speak("This langauage doesn't exists")
			else:
				speak(f"In {langauage.capitalize()} you would say:", True)
				if langauage=="hindi":
					attachTOframe(result.text, True)
					speak(result.pronunciation)
				else: speak(result.text, True)
			return

		if 'list' in text:
			if isContain(text, ['add', 'create', 'make']):
				speak("What do you want to add?", True, True)
				item = record(False, False)
				todo_handler.toDoList(item)
				speak("Alright, I added to your list", True)
				return
			if isContain(text, ['show', 'my list']):
				items = todo_handler.showtoDoList()
				if len(items)==1:
					speak(items[0], True, True)
					return
				attachTOframe('\n'.join(items), True)
				speak(items[0])
				return

		if isContain(text, ['battery', 'system info']):
			result = app_control.OSHandler(text)
			if len(result)==2:
				speak(result[0], True, True)
				attachTOframe(result[1], True)
			else:
				speak(result, True, True)
			return
			
		if isContain(text, ['meaning', 'dictionary', 'definition', 'define']):
			result = dictionary.translate(text)
			speak(result[0], True, True)
			if result[1]=='': return
			speak(result[1], True)
			return

		if 'selfie' in text or ('click' in text and 'photo' in text):
			speak("Sure "+ownerDesignation+"...", True, True)
			clickPhoto()
			speak('Do you want to view your clicked photo?', True)
			query = record(False)
			if isContain(query, ['yes', 'sure', 'yeah', 'show me']):
				Thread(target=viewPhoto).start()
				speak("Ok, here you go...", True, True)
			else:
				speak("No Problem "+ownerDesignation, True, True)
			return

		if 'volume' in text:
			app_control.volumeControl(text)
			Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor='w',pady=0)		
			attachTOframe('Volume Settings Changed', True)
			return
			
		if isContain(text, ['timer', 'countdown']):
			Thread(target=app_timer.startTimer, args=(text,)).start()
			speak('Ok, Timer Started!', True, True)
			return
	
		if 'whatsapp' in text:
			speak("Sure "+ownerDesignation+"...", True, True)
			speak('Whom do you want to send the message?', True)
			WAEMPOPUP("WhatsApp", "Phone Number")
			attachTOframe(rec_phoneno)
			speak('What is the message?', True)
			message = record(False, False)
			Thread(target=web_scrapping.sendWhatsapp, args=(rec_phoneno, message,)).start()
			speak("Message is on the way. Do not move away from the screen.")
			attachTOframe("Message Sent", True)
			return

		if 'email' in text:
			speak('Whom do you want to send the email?', True, True)
			WAEMPOPUP("Email", "E-mail Address")
			attachTOframe(rec_email)
			speak('What is the Subject?', True)
			subject = record(False, False)
			speak('What message you want to send ?', True)
			message = record(False, False)
			Thread(target=web_scrapping.email, args=(rec_email,message,subject,) ).start()
			speak('Email has been Sent', True)
			return

		if isContain(text, ['covid','virus']):
			result = web_scrapping.covid(text)
			if 'str' in str(type(result)):
				speak(result, True, True)
				return
			speak(result[0], True, True)
			result = '\n'.join(result[1])
			attachTOframe(result, True)
			return

		if isContain(text, ['youtube','video']):
			speak("Ok "+ownerDesignation+", here a video for you...", True, True)
			try:
				speak(web_scrapping.youtube(text), True)
			except Exception as e:
				print(e)
				speak("Desired Result Not Found", True)
			return

		if isContain(text, ['search', 'image']):
			if 'image' in text and 'show' in text:
				Thread(target=showImages, args=(text,)).start()
				speak('Here are the images...', True, True)
				return
			speak(web_scrapping.googleSearch(text), True, True)
			return
			
		if isContain(text, ['map', 'direction']):
			if "direction" in text:
				speak('What is your starting location?', True, True)
				startingPoint = record(False, False)
				speak("Ok "+ownerDesignation+", Where you want to go?", True)
				destinationPoint = record(False, False)
				speak("Ok "+ownerDesignation+", Getting Directions...", True)
				try:
					distance = web_scrapping.giveDirections(startingPoint, destinationPoint)
					speak('You have to cover a distance of '+ distance, True)
				except:
					speak("I think location is not proper, Try Again!")
			else:
				web_scrapping.maps(text)
				speak('Here you go...', True, True)
			return

		if isContain(text, ['factorial','log','value of','math',' + ',' - ',' x ','multiply','divided by','binary','hexadecimal','octal','shift','sin ','cos ','tan ']):
			try:
				speak(('Result is: ' + math_function.perform(text)), True, True)
			except Exception as e:
				return
			return

		if "joke" in text:
			speak('Here is a joke...', True, True)
			speak(web_scrapping.jokes(), True)
			return

		if isContain(text, ['news']):
			speak('Getting the latest news...', True, True)
			headlines,headlineLinks = web_scrapping.latestNews(2)
			for head in headlines: speak(head, True)
			speak('Do you want to read the full news?', True)
			text = record(False, False)
			if isContain(text, ["no","don't"]):
				speak("No Problem "+ownerDesignation, True)
			else:
				speak("Ok "+ownerDesignation+", Opening browser...", True)
				web_scrapping.openWebsite('https://indianexpress.com/latest-news/')
				speak("You can now read the full news from this website.")
			return

		if isContain(text, ['weather']):
			data = web_scrapping.weather()
			speak('', False, True)
			showSingleImage("weather", data[:-1])
			speak(data[-1])
			return

		if isContain(text, ['screenshot']):
			Thread(target=app_control.Win_Opt, args=('screenshot',)).start()
			speak("Screen Shot Taken", True, True)
			return

		if isContain(text, ['window','close that']):
			app_control.Win_Opt(text)
			return

		if isContain(text, ['tab']):
			app_control.Tab_Opt(text)
			return

		if isContain(text, ['setting']):
			raise_frame(root2)
			clearChatScreen()
			return

		if isContain(text, ['open','launch','type','save','delete','select','press enter','open site']):
			app_control.System_Opt(text)
			return

		if isContain(text, ['wiki', 'who is']):
			Thread(target=web_scrapping.downloadImage, args=(text, 1,)).start()
			speak('Searching...', True, True)
			result = web_scrapping.wikiResult(text)
			showSingleImage('wiki')
			speak(result, True)
			return
		
		# if isContain(text, ['game']):
		# 	speak("Which game do you want to play?", True, True)
		# 	attachTOframe(game.showGames(), True)
		# 	text = record(False)
		# 	if text=="None":
		# 		speak("Didn't understand what you say?", True, True)
		# 		return
		# 	if 'online' in text:
		# 		speak("Ok "+ownerDesignation+", Let's play some online games", True, True)
		# 		web_scrapping.openWebsite('https://www.agame.com/games/mini-games/')
		# 		return
		# 	if isContain(text, ["don't", "no", "cancel", "back", "never"]):
		# 		speak("No Problem "+ownerDesignation+", We'll play next time.", True, True)
		# 	else:
		# 		speak("Ok "+ownerDesignation+", Let's Play " + text, True, True)
		# 		os.system(f"python -c \"from modules import game; game.play('{text}')\"")
		# 	return

		# if isContain(text, ['coin','dice','die']):
		# 	if "toss" in text or "roll" in text or "flip" in text:
		# 		speak("Ok "+ownerDesignation, True, True)
		# 		result = game.play(text)
		# 		if "Head" in result: showSingleImage('head')
		# 		elif "Tail" in result: showSingleImage('tail')
		# 		else: showSingleImage(result[-1])
		# 		speak(result)
		# 		return
		
		if isContain(text, ['time','date']):
			speak(normal_chat.chat(text), True, True)
			return

		if 'my name' in text:
			speak('Your name is, ' + ownerName, True, True)
			return

		if isContain(text, ['voice']):
			global voice_id
			try:
				if 'female' in text: voice_id = 0
				elif 'male' in text: voice_id = 1
				else:
					if voice_id==0: voice_id=1
					else: voice_id=0
				engine.setProperty('voice', voices[voice_id].id)
				ChangeSettings(True)
				speak("Hello "+ownerDesignation+", I have changed my voice. How may I help you?", True, True)
				assVoiceOption.current(voice_id)
			except Exception as e:
				print(e)
			return

		if isContain(text, ['morning','evening','noon']) and 'good' in text:
			speak(normal_chat.chat("good"), True, True)
			return
		
		result = normal_chat.reply(text)
		if result != "None": speak(result, True, True)
		else:
			speak("I don't know anything about this. Do you want to search it on web?", True, True)
			response = record(False, True)
			if isContain(response, ["no","don't"]):
				speak("Ok "+ownerDesignation, True)
			else:
				speak("Here's what I found on the web... ", True, True)
				web_scrapping.googleSearch(text)
		

##################################### DELETE USER ACCOUNT #########################################
def deleteUserData():
	result = messagebox.askquestion('Alert', 'Are you sure you want to delete your Face Data ?')
	if result=='no': return
	messagebox.showinfo('Clear Face Data', 'Your face has been cleared\nRegister your face again to use.')
	import shutil
	shutil.rmtree('userData')
	root.destroy()

						#####################
						####### GUI #########
						#####################

############ ATTACHING BOT/USER CHAT ON CHAT SCREEN ###########
def attachTOframe(text,bot=False):
	if bot:
		# Bot message with modern styling
		msg_frame = Frame(chat_frame, bg=chatBgColor)
		msg_frame.pack(anchor='w', pady=4, padx=5)
		botchat = Label(msg_frame, text=text, bg=botChatTextBg, fg=botChatText, justify=LEFT, 
						wraplength=260, font=('Segoe UI', 11), padx=12, pady=8)
		botchat.pack()
	else:
		# User message with modern styling  
		msg_frame = Frame(chat_frame, bg=chatBgColor)
		msg_frame.pack(anchor='e', pady=4, padx=5)
		userchat = Label(msg_frame, text=text, bg=userChatTextBg, fg='white', justify=RIGHT, 
						wraplength=260, font=('Segoe UI', 11), padx=12, pady=8)
		userchat.pack()

def clearChatScreen():
	for wid in chat_frame.winfo_children():
		wid.destroy()

### SWITCHING BETWEEN FRAMES ###
def raise_frame(frame):
	frame.tkraise()
	clearChatScreen()

################# SHOWING DOWNLOADED IMAGES ###############
img0, img1, img2, img3, img4 = None, None, None, None, None
def showSingleImage(type, data=None):
	global img0, img1, img2, img3, img4
	try:
		img0 = ImageTk.PhotoImage(Image.open('Downloads/0.jpg').resize((90,110), Image.ANTIALIAS))
	except:
		pass
	img1 = ImageTk.PhotoImage(Image.open('assets/images/heads.jpg').resize((220,200), Image.ANTIALIAS))
	img2 = ImageTk.PhotoImage(Image.open('assets/images/tails.jpg').resize((220,200), Image.ANTIALIAS))
	img4 = ImageTk.PhotoImage(Image.open('assets/images/WeatherImage.png'))

	if type=="weather":
		weather = Frame(chat_frame)
		weather.pack(anchor='w')
		Label(weather, image=img4, bg=chatBgColor).pack()
		Label(weather, text=data[0], font=('Arial Bold', 45), fg='white', bg='#3F48CC').place(x=65,y=45)
		Label(weather, text=data[1], font=('Montserrat', 15), fg='white', bg='#3F48CC').place(x=78,y=110)
		Label(weather, text=data[2], font=('Montserrat', 10), fg='white', bg='#3F48CC').place(x=78,y=140)
		Label(weather, text=data[3], font=('Arial Bold', 12), fg='white', bg='#3F48CC').place(x=60,y=160)

	elif type=="wiki":
		Label(chat_frame, image=img0, bg='#EAEAEA').pack(anchor='w')
	elif type=="head":
		Label(chat_frame, image=img1, bg='#EAEAEA').pack(anchor='w')
	elif type=="tail":
		Label(chat_frame, image=img2, bg='#EAEAEA').pack(anchor='w')
	else:
		img3 = ImageTk.PhotoImage(Image.open('assets/images/dice/'+type+'.jpg').resize((200,200), Image.ANTIALIAS))
		Label(chat_frame, image=img3, bg='#EAEAEA').pack(anchor='w')
	
def showImages(query):
	global img0, img1, img2, img3
	web_scrapping.downloadImage(query)
	w, h = 150, 110
	#Showing Images
	imageContainer = Frame(chat_frame, bg='#EAEAEA')
	imageContainer.pack(anchor='w')
	#loading images
	img0 = ImageTk.PhotoImage(Image.open('Downloads/0.jpg').resize((w,h), Image.ANTIALIAS))
	img1 = ImageTk.PhotoImage(Image.open('Downloads/1.jpg').resize((w,h), Image.ANTIALIAS))
	img2 = ImageTk.PhotoImage(Image.open('Downloads/2.jpg').resize((w,h), Image.ANTIALIAS))
	img3 = ImageTk.PhotoImage(Image.open('Downloads/3.jpg').resize((w,h), Image.ANTIALIAS))
	#Displaying
	Label(imageContainer, image=img0, bg='#EAEAEA').grid(row=0, column=0)
	Label(imageContainer, image=img1, bg='#EAEAEA').grid(row=0, column=1)
	Label(imageContainer, image=img2, bg='#EAEAEA').grid(row=1, column=0)
	Label(imageContainer, image=img3, bg='#EAEAEA').grid(row=1, column=1)


############################# WAEM - WhatsApp Email ##################################
def sendWAEM():
	global rec_phoneno, rec_email
	data = WAEMEntry.get()
	rec_email, rec_phoneno = data, data
	WAEMEntry.delete(0, END)
	app_control.Win_Opt('close')
def send(e):
	sendWAEM()

def WAEMPOPUP(Service='None', rec='Reciever'):
	global WAEMEntry
	PopUProot = Tk()
	PopUProot.title(f'{Service} Service')
	PopUProot.configure(bg='white')

	if Service=="WhatsApp": PopUProot.iconbitmap("assets/images/whatsapp.ico")
	else: PopUProot.iconbitmap("assets/images/email.ico")
	w_width, w_height = 410, 200
	s_width, s_height = PopUProot.winfo_screenwidth(), PopUProot.winfo_screenheight()
	x, y = (s_width/2)-(w_width/2), (s_height/2)-(w_height/2)
	PopUProot.geometry('%dx%d+%d+%d' % (w_width,w_height,x,y-30)) #center location of the screen
	Label(PopUProot, text=f'Reciever {rec}', font=('Arial', 16), bg='white').pack(pady=(20, 10))
	WAEMEntry = Entry(PopUProot, bd=10, relief=FLAT, font=('Arial', 12), justify='center', bg='#DCDCDC', width=30)
	WAEMEntry.pack()
	WAEMEntry.focus()

	SendBtn = Button(PopUProot, text='Send', font=('Arial', 12), relief=FLAT, bg='#14A769', fg='white', command=sendWAEM)
	SendBtn.pack(pady=20, ipadx=10)
	PopUProot.bind('<Return>', send)
	PopUProot.mainloop()

######################## CHANGING CHAT BACKGROUND COLOR #########################
def getChatColor():
	global chatBgColor
	myColor = colorchooser.askcolor()
	if myColor[1] is None: return
	chatBgColor = myColor[1]
	colorbar['bg'] = chatBgColor
	chat_frame['bg'] = chatBgColor
	chat_canvas['bg'] = chatBgColor
	chat_container['bg'] = chatBgColor
	root1['bg'] = chatBgColor
	ChangeSettings(True)

chatMode = 1
def changeChatMode():
	global chatMode
	if chatMode==1:
		# appControl.volumeControl('mute')
		VoiceModeFrame.pack_forget()
		TextModeFrame.pack(fill=BOTH)
		UserField.focus()
		chatMode=0
	else:
		# appControl.volumeControl('full')
		TextModeFrame.pack_forget()
		VoiceModeFrame.pack(fill=BOTH)
		root.focus()
		chatMode=1

############################################## GUI #############################################

def onhover(e):
	userPhoto['image'] = chngPh
def onleave(e):
	userPhoto['image'] = userProfileImg

def UpdateIMAGE():
	global ownerPhoto, userProfileImg, userIcon

	os.system('python modules/avatar_selection.py')
	u = UserData()
	u.extractData()
	ownerPhoto = u.getUserPhoto()
	userProfileImg = ImageTk.PhotoImage(Image.open("assets/images/avatars/a"+str(ownerPhoto)+".png").resize((120, 120)))

	userPhoto['image'] = userProfileImg
	userIcon = PhotoImage(file="assets/images/avatars/ChatIcons/a"+str(ownerPhoto)+".png")

def SelectAvatar():	
	Thread(target=UpdateIMAGE).start()


#####################################  MAIN GUI ####################################################

#### SPLASH/LOADING SCREEN ####
def progressbar():
	s = ttk.Style()
	s.theme_use('clam')
	s.configure("modern.Horizontal.TProgressbar", foreground='#6366f1', background='#6366f1', troughcolor='#1e293b', bordercolor='#1e293b', lightcolor='#6366f1', darkcolor='#4f46e5')
	progress_bar = ttk.Progressbar(splash_root, style="modern.Horizontal.TProgressbar", orient="horizontal", mode="determinate", length=303)
	progress_bar.pack(pady=10)
	splash_root.update()
	progress_bar['value'] = 0
	splash_root.update()
 
	while progress_bar['value'] < 100:
		progress_bar['value'] += 5
		# splash_percentage_label['text'] = str(progress_bar['value']) + ' %'
		splash_root.update()
		sleep(0.1)

def destroySplash():
	splash_root.destroy()

if __name__ == '__main__':
	splash_root = Tk()
	splash_root.configure(bg='#0f172a')
	splash_root.overrideredirect(True)
	
	# App title with modern styling
	Label(splash_root, text="VocalXpert", font=('Segoe UI', 28, 'bold'), bg='#0f172a', fg='#6366f1').pack(pady=(30, 5))
	Label(splash_root, text="AI Assistant", font=('Segoe UI', 14), bg='#0f172a', fg='#94a3b8').pack(pady=(0, 10))
	splash_label = Label(splash_root, text="Loading...", font=('Segoe UI', 11), bg='#0f172a', fg='#64748b')
	splash_label.pack(pady=(10, 15))
	# splash_percentage_label = Label(splash_root, text="0 %", font=('montserrat',15),bg='#3895d3',fg='white')
	# splash_percentage_label.pack(pady=(0,10))

	w_width, w_height = 400, 200
	s_width, s_height = splash_root.winfo_screenwidth(), splash_root.winfo_screenheight()
	x, y = (s_width/2)-(w_width/2), (s_height/2)-(w_height/2)
	splash_root.geometry('%dx%d+%d+%d' % (w_width,w_height,x,y-30))

	progressbar()
	splash_root.after(1000, destroySplash)
	splash_root.mainloop()	

	root = Tk()
	root.title('VocalXpert An Ai Assistant')
	w_width, w_height = 400, 650
	s_width, s_height = root.winfo_screenwidth(), root.winfo_screenheight()
	x, y = (s_width/2)-(w_width/2), (s_height/2)-(w_height/2)
	root.geometry('%dx%d+%d+%d' % (w_width,w_height,x,y-30)) #center location of the screen
	root.configure(bg=background)
	# root.resizable(width=False, height=False)
	root.pack_propagate(0)

	root1 = Frame(root, bg=chatBgColor)
	root2 = Frame(root, bg=background)
	root3 = Frame(root, bg=background)

	for f in (root1, root2, root3):
		f.grid(row=0, column=0, sticky='news')	
	
	################################
	########  CHAT SCREEN  #########
	################################

	# Scrollable Chat Container
	chat_container = Frame(root1, width=380, height=551, bg=chatBgColor)
	chat_container.pack(padx=10)
	chat_container.pack_propagate(0)
	
	# Canvas for scrolling
	chat_canvas = Canvas(chat_container, bg=chatBgColor, highlightthickness=0, width=360, height=551)
	chat_scrollbar = Scrollbar(chat_container, orient="vertical", command=chat_canvas.yview)
	
	# Chat Frame inside Canvas
	chat_frame = Frame(chat_canvas, bg=chatBgColor, width=360)
	
	# Create window in canvas
	chat_canvas_window = chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw")
	
	# Configure scrolling
	chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
	
	def on_chat_frame_configure(event):
		chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
		# Auto-scroll to bottom when new content added
		chat_canvas.yview_moveto(1.0)
	
	def on_canvas_configure(event):
		chat_canvas.itemconfig(chat_canvas_window, width=event.width)
	
	chat_frame.bind("<Configure>", on_chat_frame_configure)
	chat_canvas.bind("<Configure>", on_canvas_configure)
	
	# Mouse wheel scrolling
	def on_mousewheel(event):
		chat_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
	
	chat_canvas.bind_all("<MouseWheel>", on_mousewheel)
	
	# Pack scrollbar and canvas
	chat_scrollbar.pack(side=RIGHT, fill=Y)
	chat_canvas.pack(side=LEFT, fill=BOTH, expand=True)

	# Modern bottom control bar
	bottomFrame1 = Frame(root1, bg='#334155', height=100)
	bottomFrame1.pack(fill=X, side=BOTTOM)
	VoiceModeFrame = Frame(bottomFrame1, bg='#334155')
	VoiceModeFrame.pack(fill=BOTH)
	TextModeFrame = Frame(bottomFrame1, bg='#334155')
	TextModeFrame.pack(fill=BOTH)

	# VoiceModeFrame.pack_forget()
	TextModeFrame.pack_forget()

	cblLightImg = PhotoImage(file='assets/images/centralButton.png')
	cblDarkImg = PhotoImage(file='assets/images/centralButton1.png')
	if KCS_IMG==1: cblimage=cblDarkImg
	else: cblimage=cblLightImg
	cbl = Label(VoiceModeFrame, fg='white', image=cblimage, bg='#334155')
	cbl.pack(pady=17)
	AITaskStatusLbl = Label(VoiceModeFrame, text='    Offline', fg='#f1f5f9', bg=AITaskStatusLblBG, font=('Segoe UI', 14))
	AITaskStatusLbl.place(x=140,y=32)
	
	#Settings Button
	sphLight = PhotoImage(file = "assets/images/setting.png")
	sphLight = sphLight.subsample(2,2)
	sphDark = PhotoImage(file = "assets/images/setting1.png")
	sphDark = sphDark.subsample(2,2)
	if KCS_IMG==1: sphimage=sphDark
	else: sphimage=sphLight
	settingBtn = Button(VoiceModeFrame,image=sphimage,height=30,width=30, bg='#334155',borderwidth=0,activebackground="#475569",command=lambda: raise_frame(root2))
	settingBtn.place(relx=1.0, y=30,x=-20, anchor="ne")	
	
	#Keyboard Button
	kbphLight = PhotoImage(file = "assets/images/keyboard.png")
	kbphLight = kbphLight.subsample(2,2)
	kbphDark = PhotoImage(file = "assets/images/keyboard1.png")
	kbphDark = kbphDark.subsample(2,2)
	if KCS_IMG==1: kbphimage=kbphDark
	else: kbphimage=kbphLight
	kbBtn = Button(VoiceModeFrame,image=kbphimage,height=30,width=30, bg='#334155',borderwidth=0,activebackground="#475569", command=changeChatMode)
	kbBtn.place(x=25, y=30)

	#Mic
	micImg = PhotoImage(file = "assets/images/mic.png")
	micImg = micImg.subsample(2,2)
	micBtn = Button(TextModeFrame,image=micImg,height=30,width=30, bg='#334155',borderwidth=0,activebackground="#475569", command=changeChatMode)
	micBtn.place(relx=1.0, y=30,x=-20, anchor="ne")	
	
	#Text Field
	TextFieldImg = PhotoImage(file='assets/images/textField.png')
	UserFieldLBL = Label(TextModeFrame, fg='white', image=TextFieldImg, bg='#334155')
	UserFieldLBL.pack(pady=17, side=LEFT, padx=10)
	UserField = Entry(TextModeFrame, fg='#f1f5f9', bg='#1e293b', font=('Segoe UI', 14), bd=8, width=22, relief=FLAT, insertbackground='#6366f1')
	UserField.place(x=20, y=30)
	UserField.insert(0, "Ask me anything...")
	UserField.bind('<Return>', keyboardInput)
	
	#User and Bot Icon
	userIcon = PhotoImage(file="assets/images/avatars/ChatIcons/a"+str(ownerPhoto)+".png")
	botIcon = PhotoImage(file="assets/images/assistant2.png")
	botIcon = botIcon.subsample(2,2)
	

	###########################
	########  SETTINGS  #######
	###########################

	# Settings header with modern styling
	settingsLbl = Label(root2, text='⚙ Settings', font=('Segoe UI', 18, 'bold'), bg=background, fg=textColor)
	settingsLbl.pack(pady=15)
	separator = ttk.Separator(root2, orient='horizontal')
	separator.pack(fill=X, padx=20)
	#User Photo
	userProfileImg = Image.open("assets/images/avatars/a"+str(ownerPhoto)+".png")
	userProfileImg = ImageTk.PhotoImage(userProfileImg.resize((120, 120)))
	userPhoto = Button(root2, image=userProfileImg, bg=background, bd=0, relief=FLAT, activebackground=background, command=SelectAvatar)
	userPhoto.pack(pady=(20, 5))

	#Change Photo
	chngPh = ImageTk.PhotoImage(Image.open("assets/images/avatars/changephoto2.png").resize((120, 120)))
	
	userPhoto.bind('<Enter>', onhover)
	userPhoto.bind('<Leave>', onleave)

	#Username
	userName = Label(root2, text=ownerName, font=('Arial Bold', 15), fg=textColor, bg=background)
	userName.pack()

	#Settings Frame
	settingsFrame = Frame(root2, width=300, height=300, bg=background)
	settingsFrame.pack(pady=20)

	assLbl = Label(settingsFrame, text='🔊 Assistant Voice', font=('Segoe UI', 12), fg=textColor, bg=background)
	assLbl.place(x=0, y=20)
	n = StringVar()
	assVoiceOption = ttk.Combobox(settingsFrame, values=('Female', 'Male'), font=('Segoe UI', 11), width=13, textvariable=n)
	assVoiceOption.current(voice_id)
	assVoiceOption.place(x=150, y=20)
	assVoiceOption.bind('<<ComboboxSelected>>', changeVoice)

	voiceRateLbl = Label(settingsFrame, text='⚡ Voice Rate', font=('Segoe UI', 12), fg=textColor, bg=background)
	voiceRateLbl.place(x=0, y=60)
	n2 = StringVar()
	voiceOption = ttk.Combobox(settingsFrame, font=('Segoe UI', 11), width=13, textvariable=n2)
	voiceOption['values'] = ('Very Low', 'Low', 'Normal', 'Fast', 'Very Fast')
	voiceOption.current(ass_voiceRate//50-2) #100 150 200 250 300
	voiceOption.place(x=150, y=60)
	voiceOption.bind('<<ComboboxSelected>>', changeVoiceRate)
	
	volumeLbl = Label(settingsFrame, text='🔉 Volume', font=('Segoe UI', 12), fg=textColor, bg=background)
	volumeLbl.place(x=0, y=105)
	volumeBar = Scale(settingsFrame, bg=background, fg=textColor, sliderlength=30, length=135, width=16, highlightbackground=background, troughcolor='#334155', activebackground='#6366f1', orient='horizontal', from_=0, to=100, command=changeVolume)
	volumeBar.set(int(ass_volume*100))
	volumeBar.place(x=150, y=85)



	themeLbl = Label(settingsFrame, text='🎨 Theme', font=('Segoe UI', 12), fg=textColor, bg=background)
	themeLbl.place(x=0,y=143)
	themeValue = IntVar()
	s = ttk.Style()
	s.configure('Wild.TRadiobutton', font=('Segoe UI', 10), background=background, foreground=textColor, focuscolor=s.configure(".")["background"])
	darkBtn = ttk.Radiobutton(settingsFrame, text='Dark', value=1, variable=themeValue, style='Wild.TRadiobutton', command=changeTheme, takefocus=False)
	darkBtn.place(x=150,y=145)
	lightBtn = ttk.Radiobutton(settingsFrame, text='Light', value=2, variable=themeValue, style='Wild.TRadiobutton', command=changeTheme, takefocus=False)
	lightBtn.place(x=230,y=145)
	themeValue.set(1)
	if KCS_IMG==0: themeValue.set(2)


	chooseChatLbl = Label(settingsFrame, text='💬 Chat Background', font=('Segoe UI', 12), fg=textColor, bg=background)
	chooseChatLbl.place(x=0,y=180)
	cimg = PhotoImage(file = "assets/images/colorchooser.png")
	cimg = cimg.subsample(3,3)
	colorbar = Label(settingsFrame, bd=3, width=18, height=1, bg=chatBgColor)
	colorbar.place(x=150, y=180)
	if KCS_IMG==0: colorbar['bg'] = '#E8EBEF'
	Button(settingsFrame, image=cimg, relief=FLAT, command=getChatColor).place(x=261, y=180)

	backBtn = Button(settingsFrame, text='  ← Back  ', bd=0, font=('Segoe UI', 11, 'bold'), fg='white', bg='#6366f1', relief=FLAT, activebackground='#4f46e5', activeforeground='white', cursor='hand2', command=lambda:raise_frame(root1))
	clearFaceBtn = Button(settingsFrame, text='  🗑 Clear Facial Data  ', bd=0, font=('Segoe UI', 11, 'bold'), fg='white', bg='#ef4444', relief=FLAT, activebackground='#dc2626', activeforeground='white', cursor='hand2', command=deleteUserData)
	backBtn.place(x=5, y=250)
	clearFaceBtn.place(x=100, y=250)

	# Function to check and update AI status
	def check_ai_status():
		global AI_ONLINE
		try:
			AI_ONLINE = normal_chat.is_ai_online()
			if AI_ONLINE:
				AITaskStatusLbl['text'] = '  🤖 AI Online'
				AITaskStatusLbl['fg'] = '#10b981'  # Green
			else:
				AITaskStatusLbl['text'] = '  📴 Offline Mode'
				AITaskStatusLbl['fg'] = '#f59e0b'  # Amber
		except:
			AITaskStatusLbl['text'] = '  📴 Offline Mode'
			AITaskStatusLbl['fg'] = '#f59e0b'
		# Re-check every 30 seconds
		root.after(30000, check_ai_status)

	try:
		# pass
		Thread(target=voiceMedium).start()
	except:
		pass
	try:
		# pass
		Thread(target=web_scrapping.dataUpdate).start()
	except Exception as e:
		print('System is Offline...')
	
	# Initial AI status check
	root.after(2000, check_ai_status)
	
	root.iconbitmap('assets/images/assistant2.ico')
	raise_frame(root1)
	root.mainloop()