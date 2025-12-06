"""
AI Chat Module - Groq AI Integration

Provides intelligent AI-powered responses using Groq's fast LLM API.
Falls back to local responses when internet is unavailable.

Features:
    - Fast responses using Groq's Llama model
    - Internet connectivity check
    - Automatic fallback to offline mode
    - Context-aware conversation

Dependencies:
    - requests: HTTP requests to Groq API
    - python-dotenv: Environment variable loading
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# System prompt for VocalXpert personality
SYSTEM_PROMPT = """You are VocalXpert, an intelligent AI desktop assistant created by Ghulam Murtaza, Capt. Asim Iqbal, Capt. Bilal Zaib, and Huzaifa Kahut as a semester project.

Your personality:
- Helpful, friendly, and professional
- Concise but informative (keep responses under 100 words unless detailed explanation needed)
- You can help with general questions, explanations, advice, and conversation
- You're running on a Windows desktop application

Important guidelines:
- Be conversational and natural
- If asked about capabilities you don't have (like opening apps, sending emails), mention that you can help with information but the user should use voice commands for actions
- Always be respectful and supportive
- For coding questions, provide clear explanations
- For factual questions, be accurate and helpful"""

# Conversation history for context
conversation_history = []
MAX_HISTORY = 10  # Keep last 10 exchanges for context


def check_internet():
    """Check if internet connection is available."""
    try:
        requests.get("https://api.groq.com", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False


def get_ai_response(user_message):
    """
    Get AI response from Groq API.
    
    Args:
        user_message: The user's input message
        
    Returns:
        tuple: (response_text, is_ai_response)
               is_ai_response is True if from Groq, False if fallback
    """
    global conversation_history
    
    # Check for API key
    if not GROQ_API_KEY:
        return None, False
    
    # Check internet connectivity
    if not check_internet():
        return None, False
    
    try:
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Keep history limited
        if len(conversation_history) > MAX_HISTORY * 2:
            conversation_history = conversation_history[-MAX_HISTORY * 2:]
        
        # Prepare messages with system prompt
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",  # Fast model for quick responses
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response, True
        else:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            # Remove the user message since we couldn't get a response
            conversation_history.pop()
            return None, False
            
    except requests.Timeout:
        print("Groq API request timed out")
        if conversation_history:
            conversation_history.pop()
        return None, False
    except Exception as e:
        print(f"AI Chat Error: {e}")
        if conversation_history:
            conversation_history.pop()
        return None, False


def clear_conversation():
    """Clear conversation history for a fresh start."""
    global conversation_history
    conversation_history = []


def is_online():
    """Check if AI service is available."""
    return check_internet() and GROQ_API_KEY is not None


# Test function
if __name__ == "__main__":
    print("Testing Groq AI Integration...")
    print(f"Internet available: {check_internet()}")
    print(f"API Key configured: {GROQ_API_KEY is not None}")
    
    if is_online():
        response, is_ai = get_ai_response("Hello! What can you do?")
        if is_ai:
            print(f"\nAI Response: {response}")
        else:
            print("Failed to get AI response")
    else:
        print("AI service not available - will use offline mode")
