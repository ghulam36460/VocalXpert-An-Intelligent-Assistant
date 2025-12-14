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

# Try to import conversation history module
try:
    from . import conversation_history
    HISTORY_AVAILABLE = True
except ImportError:
    try:
        import conversation_history
        HISTORY_AVAILABLE = True
    except ImportError:
        HISTORY_AVAILABLE = False

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

# Try to import advanced scraper module
try:
    from . import advanced_scraper
    SCRAPER_AVAILABLE = True
except ImportError:
    try:
        import advanced_scraper
        SCRAPER_AVAILABLE = True
    except ImportError:
        SCRAPER_AVAILABLE = False
        print("Advanced Scraper module not available - web scraping commands disabled")

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

# Get the directory where this module is located
import os
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
_json_path = os.path.join(_project_dir, 'assets', 'normal_chat.json')

try:
	data = json.load(open(_json_path, encoding='utf-8'))
except FileNotFoundError:
	# Fallback to relative path (when run from project directory)
	try:
		data = json.load(open('assets/normal_chat.json', encoding='utf-8'))
	except FileNotFoundError:
		print("Warning: normal_chat.json not found!")
		data = {}

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
    When internet is available: Try local knowledge first, then AI for enhanced responses/commands.
    When offline: Use only local knowledge and basic command fallbacks.
    
    Args:
        query: User's input text
        
    Returns:
        Response string or "None" if no response available
    """
    query_lower = query.lower().strip()
    
    # Handle history management commands
    if HISTORY_AVAILABLE:
        if query_lower in ['view history', 'show history', 'my history', 'conversation history']:
            return get_history_summary()
        elif query_lower.startswith('search history '):
            search_term = query[14:].strip()  # Remove "search history "
            return search_history(search_term)
        elif query_lower.startswith('delete history ') and 'item' in query_lower:
            try:
                # Extract ID from "delete history item 123"
                parts = query_lower.split()
                if len(parts) >= 4 and parts[3].isdigit():
                    item_id = int(parts[3])
                    return delete_history_item_command(item_id)
            except:
                pass
            return "Please specify a valid history item ID to delete. Example: 'delete history item 5'"
        elif query_lower in ['clear history', 'delete all history']:
            return clear_history_command()
        elif query_lower in ['history stats', 'history analytics', 'my stats']:
            return get_history_stats()
    
    # Handle advanced web scraping commands (support both "scrapper" and "scraper")
    if SCRAPER_AVAILABLE and (query_lower.startswith('web scrapper') or query_lower.startswith('web scraper')):
        return handle_web_scraping_command(query)
    
    # Handle scraping status/result queries
    if SCRAPER_AVAILABLE:
        if query_lower.startswith('scraping status ') or query_lower.startswith('scraper status '):
            task_id = query.split()[-1]
            return get_scraping_status_command(task_id)
        elif query_lower.startswith('scraping results ') or query_lower.startswith('scraper results '):
            task_id = query.split()[-1]
            return get_scraping_results_command(task_id)
        elif query_lower in ['active scrapers', 'scraping tasks', 'list scrapers']:
            return list_active_scrapers_command()
    
    # Check internet connectivity
    internet_available = AI_AVAILABLE and ai_chat.is_online()
    
    # Always try local knowledge first (works offline)
    local_response = get_offline_reply(query)
    
    # If internet is available, try AI for enhanced responses or commands
    ai_tried = False
    if internet_available:
        try:
            ai_response, is_ai = get_enhanced_ai_response(query)
            ai_tried = True
            if is_ai and ai_response:
                # AI provided a response - this could be a command or enhanced answer
                # Save local response to history if we have one
                if local_response and HISTORY_AVAILABLE:
                    conversation_history.add_to_history(query, local_response, 'offline')
                # Return AI response (history saving handled in ai_chat.py)
                return ai_response
        except Exception as e:
            print(f"AI response failed: {e}")
            ai_tried = True
    
    # No internet, AI failed, or AI not tried - use local response if available
    if local_response:
        # Save offline response to history
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, local_response, 'offline')
        return local_response
    
    # No local response found - try basic command fallbacks
    fallback_response = get_command_fallback(query)
    if fallback_response:
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, fallback_response, 'fallback')
        return fallback_response
    
    # No response found anywhere
    return "None"


def get_enhanced_ai_response(query):
    """
    Get AI response with command routing capabilities.
    AI should handle commands, web scraping, and complex queries that local knowledge can't.
    
    Args:
        query: User's input query
        
    Returns:
        tuple: (response_text, is_ai_response)
    """
    # Get AI response - AI should handle commands and complex queries
    ai_response, is_ai = ai_chat.get_ai_response(query)
    
    if is_ai and ai_response:
        # AI provided a response - return it directly
        # AI will generate [COMMAND:...] tags for actions like web scraping, app control, etc.
        return ai_response, True
    
    # AI not available or failed - check if we have local knowledge as fallback
    local_response = get_offline_reply(query)
    if local_response and local_response != "None":
        return local_response, False
    
    return None, False


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

def get_command_fallback(query):
    """
    Provide basic command fallbacks when AI is not available.
    This handles common commands that can work without AI.
    
    Args:
        query: User's input query
        
    Returns:
        Response string or None if no fallback available
    """
    query_lower = query.lower().strip()
    
    # Basic app opening commands
    if query_lower in ['open chrome', 'launch chrome', 'start chrome']:
        try:
            from modules import app_control
            result = app_control.openApp('chrome')
            return "Opening Chrome..." if result else "Could not open Chrome."
        except Exception as e:
            return "I can't open Chrome right now."
    
    elif query_lower in ['open notepad', 'launch notepad', 'start notepad']:
        try:
            from modules import app_control
            result = app_control.openApp('notepad')
            return "Opening Notepad..." if result else "Could not open Notepad."
        except Exception as e:
            return "I can't open Notepad right now."
    
    elif query_lower in ['open calculator', 'launch calculator', 'start calculator']:
        try:
            from modules import app_control
            result = app_control.openApp('calculator')
            return "Opening Calculator..." if result else "Could not open Calculator."
        except Exception as e:
            return "I can't open Calculator right now."
    
    # Basic system commands
    elif query_lower in ['volume up', 'increase volume']:
        try:
            from modules import app_control
            app_control.volumeUp()
            return "Volume increased."
        except Exception:
            return "I can't adjust volume right now."
    
    elif query_lower in ['volume down', 'decrease volume']:
        try:
            from modules import app_control
            app_control.volumeDown()
            return "Volume decreased."
        except Exception:
            return "I can't adjust volume right now."
    
    elif query_lower == 'volume mute':
        try:
            from modules import app_control
            app_control.volumeMute()
            return "Volume muted."
        except Exception:
            return "I can't adjust volume right now."
    
    # Time/date queries (already handled in chat function, but provide fallback)
    elif 'time' in query_lower:
        dt = DateTime()
        return f"Current time is: {dt.currentTime()}"
    
    elif 'date' in query_lower or 'today' in query_lower:
        dt = DateTime()
        return f"Today's date is: {dt.currentDate()}"
    
    # No fallback available
    return None


# History management functions
def get_history_summary():
    """Get a summary of recent conversation history."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."
    
    conversations = conversation_history.conversation_manager.get_recent_conversations(10)
    if not conversations:
        return "No conversation history found. Start chatting to build your history!"
    
    summary = f"Your Recent Conversations ({len(conversations)} shown):\n\n"
    
    for conv in conversations[-5:]:  # Show last 5
        timestamp = conv['timestamp'][:16]  # YYYY-MM-DD HH:MM
        summary += f"[{timestamp}] {conv['summary']}\n"
    
    summary += f"\nTIP: Say 'history stats' for analytics or 'search history [term]' to find specific conversations."
    return summary

def search_history(search_term):
    """Search conversation history for a specific term."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."
    
    if not search_term:
        return "Please specify what to search for. Example: 'search history weather'"
    
    results = conversation_history.conversation_manager.search_conversations(search_term, 5)
    if not results:
        return f"No conversations found containing '{search_term}'."
    
    response = f"Search results for '{search_term}' ({len(results)} found):\n\n"
    
    for conv in results:
        timestamp = conv['timestamp'][:16]
        response += f"[{timestamp}] {conv['summary']}\n"
        response += f"   You: {conv['user_query'][:50]}{'...' if len(conv['user_query']) > 50 else ''}\n"
        response += f"   AI: {conv['ai_response'][:50]}{'...' if len(conv['ai_response']) > 50 else ''}\n\n"
    
    return response

def delete_history_item_command(item_id):
    """Delete a specific history item by ID."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."
    
    if conversation_history.conversation_manager.delete_conversation(item_id):
        return f"Conversation item {item_id} has been deleted."
    else:
        return f"ERROR: Could not find conversation item {item_id}. Use 'view history' to see available items with their IDs."

def clear_history_command():
    """Clear all conversation history."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."
    
    conversation_history.conversation_manager.clear_all_history()
    return "All conversation history has been cleared. Your chat history is now empty."

def get_history_stats():
    """Get conversation history statistics and analytics."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."
    
    analytics = conversation_history.conversation_manager.get_conversation_analytics()
    personalization = conversation_history.conversation_manager.get_personalization_data()
    
    stats = "Your Conversation Analytics:\n\n"
    stats += f"Total conversations: {analytics['total_conversations']}\n"
    stats += f"Conversation types: {analytics['conversation_types']}\n"
    stats += f"Common topics: {', '.join(analytics['common_topics'][:3])}\n"
    stats += f"Activity level: {personalization['preferences']['activity_level']}\n"
    stats += f"Recent activity: {personalization['recent_activity']} conversations this week\n"
    
    return stats


# Advanced Web Scraping Functions
def handle_web_scraping_command(query):
    """Handle web scraping commands."""
    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available. Please check your installation."
    
    try:
        result = advanced_scraper.start_web_scraping(query)
        
        # Save to history
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, result, 'web_scraping')
        
        return result
    except Exception as e:
        error_msg = f"ERROR: Web scraping failed: {str(e)}"
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, error_msg, 'web_scraping_error')
        return error_msg

def get_scraping_status_command(task_id):
    """Get status of a scraping task."""
    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available."
    
    try:
        status = advanced_scraper.get_scraping_status(task_id)
        if status:
            progress = status.get('progress', 0)
            status_text = status.get('status', 'unknown')
            
            response = f"Scraping Task {task_id[:8]}...\n"
            response += f"Status: {status_text}\n"
            response += f"Progress: {progress}%\n"
            
            if status_text == 'completed':
                response += f"Results: {status.get('results_count', 0)} items found\n"
                response += f"Sources: {status.get('sources_count', 0)} websites\n"
                response += f"Time: {status.get('metadata', {}).get('scraping_time', 'N/A'):.1f}s\n"
                response += f"\nTIP: Say 'scraping results {task_id}' to view the results."
            elif status_text == 'error':
                response += f"ERROR: Errors: {status.get('errors_count', 0)}\n"
            
            return response
        else:
            return f"ERROR: No scraping task found with ID: {task_id}"
    except Exception as e:
        return f"ERROR: Failed to get scraping status: {str(e)}"

def get_scraping_results_command(task_id):
    """Get results of a completed scraping task."""
    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available."
    
    try:
        results = advanced_scraper.get_scraping_results(task_id)
        if results:
            status = results.get('status', 'unknown')
            if status != 'completed':
                return f"WARNING: Task {task_id[:8]} is not completed yet. Status: {status}. Try again later."
            
            result_count = results.get('results_count', 0)
            response = f"Scraping Results for Task {task_id[:8]}\n"
            response += f"Query: {results.get('query', 'N/A')}\n"
            response += f"Mode: {results.get('mode', 'normal')}\n"
            response += f"Found: {result_count} results\n\n"
            
            # Show preview of results
            preview_results = results.get('results', [])[:5]  # Show first 5
            
            if preview_results:
                for i, result in enumerate(preview_results, 1):
                    title = result.get('title', 'No title')[:50]
                    content = result.get('content', '')[:150]
                    source = result.get('source', 'Unknown')
                    
                    response += f"{i}. {title}\n"
                    response += f"   {content}...\n"
                    response += f"   Source: {source}\n\n"
                
                if result_count > 5:
                    response += f"FILE: ... and {result_count - 5} more results.\n"
                    
                    # Check if saved to file
                    if 'saved_to_file' in results.get('metadata', {}):
                        file_path = results['metadata']['saved_to_file']
                        response += f"SAVED: Full results saved to: {file_path}\n"
            else:
                response += "ERROR: No results found for this query.\n"
            
            return response
        else:
            return f"ERROR: No completed scraping task found with ID: {task_id}"
    except Exception as e:
        return f"ERROR: Failed to get scraping results: {str(e)}"

def list_active_scrapers_command():
    """List all active scraping tasks."""
    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available."
    
    try:
        tasks = advanced_scraper.list_scraping_tasks()
        if not tasks:
            return "No active scraping tasks. Start one with 'web scrapper : your query'"
        
        response = f"Active Scraping Tasks ({len(tasks)}):\n\n"
        
        for task in tasks:
            task_id = task['id'][:8]
            query = task.get('query', 'N/A')[:30]
            mode = task.get('mode', 'normal')
            status = task.get('status', 'unknown')
            progress = task.get('progress', 0)
            
            response += f"ID {task_id} | Query: {query}... | Mode: {mode} | Status: {status} ({progress}%)\n"
        
        response += f"\nTIP: Use 'scraping status [ID]' to check progress or 'scraping results [ID]' for completed tasks."
        return response
    except Exception as e:
        return f"ERROR: Failed to list scraping tasks: {str(e)}"