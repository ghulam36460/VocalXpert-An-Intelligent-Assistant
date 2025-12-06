"""
Security Module - Face Recognition Login System

Provides a multi-frame Tkinter GUI for user authentication using face recognition.
Includes registration flow (4 frames) and login functionality.

Frames:
    - root1: Main login screen with face detection
    - root2: User registration and face training
    - root3: Avatar selection for user profile
    - root4: Final registration confirmation
"""

from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
from os.path import isfile, join
from threading import Thread
from .user_handler import UserData
from . import face_unlocker as FU

# Modern Color Palette (matching gui_assistant.py)
background = '#1e293b'  # Slate 800
textColor = '#f1f5f9'  # Slate 100
ACCENT_PRIMARY = '#6366f1'  # Indigo
ACCENT_SUCCESS = '#10b981'  # Emerald
ACCENT_DANGER = '#ef4444'  # Red
TEXT_MUTED = '#94a3b8'  # Slate 400
SURFACE_DARK = '#0f172a'  # Slate 900

avatarChoosen = 0
choosedAvtrImage = None
user_name = ''
user_gender = ''

try:
	face_classifier = cv2.CascadeClassifier('Cascade/haarcascade_frontalface_default.xml')
except Exception as e:
	print('Cascade File is missing...')
	raise SystemExit

if os.path.exists('userData')==False:
	os.mkdir('userData')
if os.path.exists('userData/faceData')==False:
	os.mkdir('userData/faceData')


###### ROOT1 ########
def startLogin():		
	try:
		result = FU.startDetecting()
		if result:
			user = UserData()
			user.extractData()
			userName = user.getName().split()[0]
			welcLbl['text'] = f'Welcome back, {userName}! \n\nYour AI Assistant awaits.'
			loginStatus['text'] = '🔓 UNLOCKED'
			loginStatus['fg'] = ACCENT_SUCCESS
			faceStatus['text']='(✓ Face Recognized)'
			faceStatus['fg'] = ACCENT_SUCCESS
			os.system('python modules/gui_assistant.py')
		else:
			print('Error Occurred')

	except Exception as e:
		print(e)

####### ROOT2 ########
def trainFace():
	data_path = 'userData/faceData/'
	onlyfiles = [f for f in os.listdir(data_path) if isfile(join(data_path, f))]

	Training_data = []
	Labels = []

	for i, files in enumerate(onlyfiles):
		image_path = data_path + onlyfiles[i]
		images = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
		
		Training_data.append(np.asarray(images, dtype=np.uint8))
		Labels.append(i)


	Labels = np.asarray(Labels, dtype=np.int32)

	model = cv2.face.LBPHFaceRecognizer_create()
	model.train(np.asarray(Training_data), np.asarray(Labels))

	print('Model Trained Successfully !!!')
	model.save('userData/trainer.yml')
	print('Model Saved !!!')

def face_extractor(img):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	faces = face_classifier.detectMultiScale(gray, 1.3, 5)

	if len(faces) == 0:
		return None

	for (x, y, w, h) in faces:
		cropped_face = img[y:y+h, x:x+w]

	return cropped_face

cap = None
count = 0
def startCapturing():
	global count, cap
	ret, frame = cap.read()
	if face_extractor(frame) is not None:
		count += 1
		face = cv2.resize(face_extractor(frame), (200, 200))
		face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

		file_name_path = 'userData/faceData/img' + str(count) + '.png'
		cv2.imwrite(file_name_path, face)
		print(count)
		progress_bar['value'] = count

		cv2.putText(face, str(count), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0), 2)
	else:
		pass
	
	if count==200:
		progress_bar.destroy()
		lmain['image'] = defaultImg2
		statusLbl['text'] = '(Face added successfully)'
		cap.release()
		cv2.destroyAllWindows()
		Thread(target=trainFace).start()
		addBtn['text'] = '        Next        '
		addBtn['command'] = lambda:raise_frame(root3)
		return
	
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
	frame = cv2.flip(frame, 1)
	img = Image.fromarray(frame)
	imgtk = ImageTk.PhotoImage(image=img)
	lmain.imgtk = imgtk
	lmain.configure(image=imgtk)
	lmain.after(10, startCapturing)

def Add_Face():

	global cap, user_name, user_gender
	user_name = nameField.get()
	user_gender = r.get()
	if user_name != '' and user_gender!=0:
		if agr.get()==1:
			cap = cv2.VideoCapture(0)
			startCapturing()
			progress_bar.place(x=20, y=273)
			statusLbl['text'] = ''
		else:
			statusLbl['text'] = '(Check the Condition)'
	else:
		statusLbl['text'] = '(Please fill the details)'


def SuccessfullyRegistered():
	if avatarChoosen != 0:
		gen = 'Male'
		if user_gender==2: gen = 'Female'
		u = UserData()
		u.updateData(user_name, gen, avatarChoosen)
		usernameLbl['text'] = user_name
		raise_frame(root4)

def selectAVATAR(avt=0):
	global avatarChoosen, choosedAvtrImage
	avatarChoosen = avt
	i=1
	for avtr in (avtb1,avtb2,avtb3,avtb4,avtb5,avtb6,avtb7,avtb8):
		if i==avt:
			avtr['state'] = 'disabled'
			userPIC['image'] = avtr['image']
		else: avtr['state'] = 'normal'
		i+=1


################################################# GUI ###############################


def raise_frame(frame):
	frame.tkraise()


root = Tk()
root.title('VocalXpert An Ai Assistant')
w_width, w_height = 350, 600
s_width, s_height = root.winfo_screenwidth(), root.winfo_screenheight()
x, y = (s_width/2)-(w_width/2), (s_height/2)-(w_height/2)
root.geometry('%dx%d+%d+%d' % (w_width,w_height,x,y-30)) #center location of the screen
root.configure(bg=background)
# root.attributes('-toolwindow', True)
root1 = Frame(root, bg=background)
root2 = Frame(root, bg=background)
root3 = Frame(root, bg=background)
root4 = Frame(root, bg=background)

for f in (root1, root2, root3, root4):
	f.grid(row=0, column=0, sticky='news')	
	
################################
########  MAIN SCREEN  #########
################################

image1 = Image.open('assets/images/home2.jpg')
image1 = image1.resize((300,250))
defaultImg1 = ImageTk.PhotoImage(image1)

dataFrame1 = Frame(root1, bd=10, bg=background)
dataFrame1.pack()
logo = Label(dataFrame1, width=300, height=250, image=defaultImg1, bg=background)
logo.pack(padx=10, pady=10)

#welcome label
welcLbl = Label(root1, text='Welcome to VocalXpert\nYour Intelligent AI Assistant', font=('Segoe UI', 16, 'bold'), fg=textColor, bg=background)
welcLbl.pack(padx=10, pady=20)

#add face
loginStatus = Label(root1, text='🔒 LOCKED', font=('Segoe UI', 16, 'bold'), bg=background, fg=ACCENT_DANGER)
loginStatus.pack(pady=(40,20))	

if os.path.exists('userData/trainer.yml')==False:
	loginStatus['text'] = '⚠ Face Not Registered'
	loginStatus['fg'] = ACCENT_DANGER
	addFace = Button(root1, text='  📷 Register Face  ', font=('Segoe UI', 12, 'bold'), bg=ACCENT_PRIMARY, fg='white', relief=FLAT, activebackground='#4f46e5', activeforeground='white', cursor='hand2', command=lambda:raise_frame(root2))
	addFace.pack(ipadx=15, ipady=5)
else:
	Thread(target=startLogin).start()
	
#status of add face
faceStatus = Label(root1, text='(Scanning for face...)', font=('Segoe UI', 10), fg=TEXT_MUTED, bg=background)
faceStatus.pack(pady=5)

##################################
########  FACE ADD SCREEN  #######
##################################

image2 = Image.open('assets/images/defaultFace4.png')
image2 = image2.resize((300, 250))
defaultImg2 = ImageTk.PhotoImage(image2)

dataFrame2 = Frame(root2, bd=10, bg=background)
dataFrame2.pack(fill=X)
lmain = Label(dataFrame2, width=300, height=250, image=defaultImg2, bg=SURFACE_DARK)
lmain.pack(padx=10, pady=10)

#Details
detailFrame2 = Frame(root2, bd=10, bg=background)
detailFrame2.pack(fill=X)
userFrame2 = Frame(detailFrame2, bd=10, width=300, height=250, relief=FLAT, bg=background)
userFrame2.pack(padx=10, pady=10)

#progress
progress_bar = ttk.Progressbar(root2, orient=HORIZONTAL, length=303, mode='determinate')

#name
nameLbl = Label(userFrame2, text='👤 Name', font=('Segoe UI', 12, 'bold'), fg=textColor, bg=background)
nameLbl.place(x=10,y=10)
nameField = Entry(userFrame2, bd=0, font=('Segoe UI', 11), width=22, relief=FLAT, bg='#334155', fg=textColor, insertbackground=ACCENT_PRIMARY)
nameField.focus()
nameField.place(x=90,y=10)

genLbl = Label(userFrame2, text='♂️ Gender', font=('Segoe UI', 12, 'bold'), fg=textColor, bg=background)
genLbl.place(x=10,y=55)
r = IntVar()
s = ttk.Style()
s.configure('Modern.TRadiobutton', background=background, foreground=textColor, font=('Segoe UI', 11), focuscolor=s.configure(".")["background"])
genMale = ttk.Radiobutton(userFrame2, text='Male', value=1, variable=r, style='Modern.TRadiobutton', takefocus=False)
genMale.place(x=100,y=57)
genFemale = ttk.Radiobutton(userFrame2, text='Female', value=2, variable=r, style='Modern.TRadiobutton', takefocus=False)
genFemale.place(x=175,y=57)

#agreement
agr = IntVar()
sc = ttk.Style()
sc.configure('Modern.TCheckbutton', background=background, foreground=TEXT_MUTED, font=('Segoe UI', 10), focuscolor=sc.configure(".")["background"])
# agree = Checkbutton(userFrame2, text='I agree to use my face for Security purpose', fg=textColor, bg=background, activebackground=background, activeforeground=textColor)
agree = ttk.Checkbutton(userFrame2, text='I agree to use my Face for Security', style='Modern.TCheckbutton', takefocus=False, variable=agr)
agree.place(x=28, y=100)
#add face
addBtn = Button(userFrame2, text='  📷 Add Face  ', font=('Segoe UI', 12, 'bold'), bg=ACCENT_SUCCESS, fg='white', command=Add_Face, relief=FLAT, activebackground='#059669', activeforeground='white', cursor='hand2')
addBtn.place(x=90, y=145)

#status of add face
statusLbl = Label(userFrame2, text='', font=('Segoe UI', 10), fg=ACCENT_DANGER, bg=background)
statusLbl.place(x=80, y=190)

##########################
#### AVATAR SELECTION ####
##########################
	
Label(root3, text="👤 Choose Your Avatar", font=('Segoe UI', 18, 'bold'), bg=background, fg=textColor).pack(pady=15)

avatarContainer = Frame(root3, bg=background, width=300, height=500)
avatarContainer.pack(pady=10)
size = 100

avtr1 = Image.open('assets/images/avatars/a1.png')
avtr1 = avtr1.resize((size, size))
avtr1 = ImageTk.PhotoImage(avtr1)
avtr2 = Image.open('assets/images/avatars/a2.png')
avtr2 = avtr2.resize((size, size))
avtr2 = ImageTk.PhotoImage(avtr2)
avtr3 = Image.open('assets/images/avatars/a3.png')
avtr3 = avtr3.resize((size, size))
avtr3 = ImageTk.PhotoImage(avtr3)
avtr4 = Image.open('assets/images/avatars/a4.png')
avtr4 = avtr4.resize((size, size))
avtr4 = ImageTk.PhotoImage(avtr4)
avtr5 = Image.open('assets/images/avatars/a5.png')
avtr5 = avtr5.resize((size, size))
avtr5 = ImageTk.PhotoImage(avtr5)
avtr6 = Image.open('assets/images/avatars/a6.png')
avtr6 = avtr6.resize((size, size))
avtr6 = ImageTk.PhotoImage(avtr6)
avtr7 = Image.open('assets/images/avatars/a7.png')
avtr7 = avtr7.resize((size, size))
avtr7 = ImageTk.PhotoImage(avtr7)
avtr8 = Image.open('assets/images/avatars/a8.png')
avtr8 = avtr8.resize((size, size))
avtr8 = ImageTk.PhotoImage(avtr8)

	
avtb1 = Button(avatarContainer, image=avtr1, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(1))
avtb1.grid(row=0, column=0, ipadx=25, ipady=10)

avtb2 = Button(avatarContainer, image=avtr2, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(2))
avtb2.grid(row=0, column=1, ipadx=25, ipady=10)

avtb3 = Button(avatarContainer, image=avtr3, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(3))
avtb3.grid(row=1, column=0, ipadx=25, ipady=10)

avtb4 = Button(avatarContainer, image=avtr4, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(4))
avtb4.grid(row=1, column=1, ipadx=25, ipady=10)

avtb5 = Button(avatarContainer, image=avtr5, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(5))
avtb5.grid(row=2, column=0, ipadx=25, ipady=10)

avtb6 = Button(avatarContainer, image=avtr6, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(6))
avtb6.grid(row=2, column=1, ipadx=25, ipady=10)

avtb7 = Button(avatarContainer, image=avtr7, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(7))
avtb7.grid(row=3, column=0, ipadx=25, ipady=10)

avtb8 = Button(avatarContainer, image=avtr8, bg=background, activebackground=background, relief=FLAT, bd=0, command=lambda:selectAVATAR(8))
avtb8.grid(row=3, column=1, ipadx=25, ipady=10)


Button(root3, text='  ✓ Submit  ', font=('Segoe UI', 14, 'bold'), bg=ACCENT_SUCCESS, fg='white', bd=0, relief=FLAT, activebackground='#059669', activeforeground='white', cursor='hand2', command=SuccessfullyRegistered).pack(pady=10)

#########################################
######## SUCCESSFULL REGISTRATION #######
#########################################

userPIC = Label(root4, bg=background, image=avtr1)
userPIC.pack(pady=(40, 10))
usernameLbl = Label(root4, text="User", font=('Segoe UI', 18, 'bold'), bg=background, fg=ACCENT_SUCCESS)
usernameLbl.pack(pady=(0, 50))

Label(root4, text="✅ Account Successfully Activated!", font=('Segoe UI', 16, 'bold'), bg=background, fg=textColor, wraplength=300).pack(pady=15)
Label(root4, text="Launch the app again to start your conversation with VocalXpert - your Personal AI Assistant", font=('Segoe UI', 11), bg=background, fg=TEXT_MUTED, wraplength=320).pack()

Button(root4, text='  🚀 Get Started  ', bg=ACCENT_PRIMARY, fg='white', font=('Segoe UI', 14, 'bold'), bd=0, relief=FLAT, activebackground='#4f46e5', activeforeground='white', cursor='hand2', command=lambda:quit()).pack(pady=40)

root.iconbitmap('assets/images/assistant2.ico')
raise_frame(root1)
root.mainloop()




#########################################
#########################################

# End of security.py
