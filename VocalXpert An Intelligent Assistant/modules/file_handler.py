"""
File Handler Module - File and Project Creation

Handles creating various file types and web project scaffolding.
"""

import subprocess
import os
import sys
import webbrowser

# Get the project directory
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
path = os.path.join(_project_dir, 'Files and Document/')

# Create directory if it doesn't exist
if not os.path.exists(path):
    os.makedirs(path)

def isContain(text, list):
	for word in list:
		if word in text:
			return True
	return False

def createFile(text):
	"""Create a new file of specified type and open in editor."""
	# Default to VS Code or Notepad
	appLocation = None
	
	# Try to find VS Code
	possible_vscode_paths = [
		os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
		r"C:\Program Files\Microsoft VS Code\Code.exe",
		r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
	]
	
	for vscode_path in possible_vscode_paths:
		if os.path.exists(vscode_path):
			appLocation = vscode_path
			break
	
	# Fallback to notepad
	if not appLocation:
		appLocation = "notepad.exe"
	
	file_name = "sample_file.txt"  # Default
	
	if isContain(text, ["ppt", "power point", "powerpoint"]):
		file_name = "sample_file.pptx"
	elif isContain(text, ['excel', 'spreadsheet']):
		file_name = "sample_file.xlsx"
	elif isContain(text, ['word', 'document']):
		file_name = "sample_file.docx"
	elif isContain(text, ["text", "simple", "normal"]): 
		file_name = "sample_file.txt"
	elif "python" in text: 
		file_name = "sample_file.py"
	elif "css" in text:	
		file_name = "sample_file.css"
	elif "javascript" in text: 
		file_name = "sample_file.js"
	elif "html" in text: 
		file_name = "sample_file.html"
	elif "c plus plus" in text or "c++" in text: 
		file_name = "sample_file.cpp"
	elif "java" in text: 
		file_name = "sample_file.java"
	elif "json" in text: 
		file_name = "sample_file.json"
	
	try:
		file = open(path + file_name, 'w')
		file.close()
		subprocess.Popen([appLocation, path + file_name])
		return f"File '{file_name}' created successfully. Opening in editor..."
	except Exception as e:
		return f"Unable to create file: {str(e)}"

def CreateHTMLProject(project_name='Sample'):
	"""Create a basic HTML/CSS/JS web project structure."""
	
	if os.path.isdir(path + project_name):
		webbrowser.open(os.getcwd() + '/' + path + project_name + "/index.html")
		return 'Project already exists. Opening it now...'
	
	try:
		os.mkdir(path + project_name)
		os.mkdir(path + project_name + '/images')
		os.mkdir(path + project_name + '/videos')
		
		# Create index.html
		htmlContent = f'''<!DOCTYPE html>
<html>
<head>
    <title>{project_name}</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <h1>Welcome to {project_name}</h1>
    <p id="label"></p>
    <button id="btn" onclick="showText()">Click Me</button>
    <script src="script.js"></script>
</body>
</html>'''
		
		with open(path + project_name + '/index.html', 'w') as f:
			f.write(htmlContent)
		
		# Create style.css
		cssContent = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

h1 {
    margin-bottom: 20px;
}

#btn {
    padding: 15px 30px;
    border-radius: 8px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
}

#btn:hover {
    background-color: #45a049;
    transform: scale(1.05);
}

#label {
    font-size: 24px;
    margin-bottom: 20px;
}'''
		
		with open(path + project_name + '/style.css', 'w') as f:
			f.write(cssContent)
		
		# Create script.js
		jsContent = f'''function showText() {{
    document.getElementById("label").innerHTML = "Welcome to {project_name}!";
    document.getElementById("btn").style.backgroundColor = "#2196F3";
    document.getElementById("btn").textContent = "Clicked!";
}}'''
		
		with open(path + project_name + '/script.js', 'w') as f:
			f.write(jsContent)
		
		# Open in browser
		webbrowser.open(os.getcwd() + '/' + path + project_name + "/index.html")
		
		return f'Successfully created {project_name} project!'
		
	except Exception as e:
		return f"Error creating project: {str(e)}"