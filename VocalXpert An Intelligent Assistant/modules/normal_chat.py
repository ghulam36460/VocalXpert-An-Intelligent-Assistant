"""
Normal Chat Module - Conversation Handler

Handles casual conversation with AI-powered responses when online,
and falls back to local JSON-based responses when offline.

Features:
    - Groq AI integration for intelligent responses
    - Offline fallback using pattern matching
    - Time/date queries
    - Language translation
"""

from difflib import get_close_matches
import json
from random import choice
import datetime

# Try to import AI chat module
try:
    from . import ai_chat
    AI_AVAILABLE = True
except ImportError:
    try:
        import ai_chat
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
        print("AI Chat module not available - using offline mode only")

class DateTime:
	def currentTime(self):
		time = datetime.datetime.now()
		x = " A.M."
		if time.hour>12: x = " P.M."
		time = str(time)
		time = time[11:16] + x
		return time

	def currentDate(self):
		now = datetime.datetime.now()
		day = now.strftime('%A')
		date = str(now)[8:10]
		month = now.strftime('%B')
		year = str(now.year)
		result = f'{day}, {date} {month}, {year}'
		return result
	
def wishMe():
	now = datetime.datetime.now()
	hr = now.hour
	if hr<12:
		wish="Good Morning"
	elif hr>=12 and hr<16:
		wish="Good Afternoon"
	else:
		wish="Good Evening"
	return wish


def isContain(text, lst):
	for word in lst:
		if word in text:
			return True
	return False

def chat(text):
	dt = DateTime()
	result = ""
	if isContain(text, ['good']):
		result = wishMe()		
	elif isContain(text, ['time']):
		result = "Current Time is: " + dt.currentTime()
	elif isContain(text, ['date','today','day','month']):
		result = dt.currentDate()

	return result

data = json.load(open('assets/normal_chat.json', encoding='utf-8'))

def get_offline_reply(query):
    """Get response from local JSON data (offline fallback)."""
    if query in data:
        response = data[query]
    else:
        matches = get_close_matches(query, data.keys(), n=2, cutoff=0.6)
        if len(matches) == 0:
            return None
        return choice(data[matches[0]])
    return choice(response)


def reply(query):
    """
    Get a reply for the user's query.
    Uses AI when online, falls back to local responses when offline.
    
    Args:
        query: User's input text
        
    Returns:
        Response string or "None" if no response available
    """
    # Try AI response first if available and online
    if AI_AVAILABLE:
        try:
            if ai_chat.is_online():
                ai_response, is_ai = ai_chat.get_ai_response(query)
                if is_ai and ai_response:
                    return ai_response
        except Exception as e:
            print(f"AI response failed: {e}")
    
    # Fallback to offline responses
    offline_response = get_offline_reply(query)
    if offline_response:
        return offline_response
    
    return "None"


def reply_offline(query):
    """Force offline response (for testing or preference)."""
    offline_response = get_offline_reply(query)
    if offline_response:
        return offline_response
    return "None"


def is_ai_online():
    """Check if AI service is available."""
    if AI_AVAILABLE:
        return ai_chat.is_online()
    return False

def lang_translate(text,language):
	from googletrans import Translator, LANGUAGES
	if language in LANGUAGES.values():
		translator = Translator()
		result = translator.translate(text, src='en', dest=language)
		return result
	else:
		return "None"