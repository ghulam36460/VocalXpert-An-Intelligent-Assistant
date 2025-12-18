"""
Normal Chat Module - Conversation Handler

Handles casual conversation with intelligent offline-first approach:
1. OFFLINE MODE: Uses normal_chat.json, dict_data.json, conversation_history.json,
   and cached scraping results from temp_scraping_results/
2. ONLINE MODE: First searches ALL offline sources, then falls back to
   AI (Groq API), web scraping, and other online resources

Features:
    - Unified offline knowledge search across all local sources
    - Groq AI integration for intelligent responses
    - Offline fallback using pattern matching
    - Cached scraping results search
    - Conversation history for personalized responses
    - Time/date queries
    - Language translation
"""

from difflib import get_close_matches
import json
from random import choice
import datetime
import os
import glob
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger("VocalXpert.NormalChat")

# Get module and project directories
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
_scraped_data_dir = os.path.join(_project_dir, "temp_scraping_results",
                                 "scraped_data")

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
        print(
            "Advanced Scraper module not available - web scraping commands disabled"
        )

# Try to import dictionary module
try:
    from . import dictionary as dict_module

    DICTIONARY_AVAILABLE = True
except ImportError:
    try:
        import dictionary as dict_module

        DICTIONARY_AVAILABLE = True
    except ImportError:
        DICTIONARY_AVAILABLE = False


class DateTime:

    def currentTime(self):
        time = datetime.datetime.now()
        x = " A.M."
        if time.hour > 12:
            x = " P.M."
        time = str(time)
        time = time[11:16] + x
        return time

    def currentDate(self):
        now = datetime.datetime.now()
        day = now.strftime("%A")
        date = str(now)[8:10]
        month = now.strftime("%B")
        year = str(now.year)
        result = f"{day}, {date} {month}, {year}"
        return result


def wishMe():
    now = datetime.datetime.now()
    hr = now.hour
    if hr < 12:
        wish = "Good Morning"
    elif hr >= 12 and hr < 16:
        wish = "Good Afternoon"
    else:
        wish = "Good Evening"
    return wish


def isContain(text, lst):
    words = text.lower().split()  # Split into words and normalize to lowercase
    for word in lst:
        if word in words:
            return True
    return False


def chat(text):
    dt = DateTime()
    result = ""
    if isContain(text, ["good"]):
        result = wishMe()
    elif isContain(text, ["time"]):
        result = "Current Time is: " + dt.currentTime()
    elif isContain(text, ["date", "time", "day", "month"]):
        result = dt.currentDate()

    return result


# Note: _module_dir and _project_dir already defined at top of file
_json_path = os.path.join(_project_dir, "assets", "normal_chat.json")

try:
    _raw_data = json.load(open(_json_path, encoding="utf-8"))
    # Normalize all keys to lowercase for case-insensitive matching
    data = {k.lower(): v for k, v in _raw_data.items()}
except FileNotFoundError:
    # Fallback to relative path (when run from project directory)
    try:
        _raw_data = json.load(
            open(
                "assets/normal_chat.json",
                encoding="utf-8"))
        data = {k.lower(): v for k, v in _raw_data.items()}
    except FileNotFoundError:
        print("Warning: normal_chat.json not found!")
        data = {}


class OfflineKnowledgeBase:
    """
    Unified search system across all offline sources:
    - normal_chat.json (conversation patterns)
    - dict_data.json (dictionary definitions)
    - conversation_history.json (past conversations)
    - temp_scraping_results/scraped_data/*.json (cached scraping results)
    """

    def __init__(self):
        # Normalize all keys to lowercase for case-insensitive matching
        self.normal_chat_data = {k.lower(): v for k, v in data.items()}
        self.dict_data = self._load_dict_data()
        self.scraped_cache = {}
        self._load_scraped_cache()

    def _load_dict_data(self):
        """Load dictionary data from dict_data.json."""
        try:
            dict_path = os.path.join(_project_dir, "assets", "dict_data.json")
            with open(dict_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load dict_data.json: {e}")
            return {}

    def _load_scraped_cache(self):
        """Load all cached scraping results."""
        try:
            if os.path.exists(_scraped_data_dir):
                for json_file in glob.glob(
                        os.path.join(_scraped_data_dir, "*.json")):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            query = data.get("query", "").lower()
                            if query:
                                self.scraped_cache[query] = data
                    except Exception:
                        continue
        except Exception as e:
            print(f"Warning: Could not load scraped cache: {e}")

    def search_normal_chat(
            self,
            query: str,
            exact_only: bool = False) -> tuple:
        """
        Search normal_chat.json for matching response.

        Args:
            query: The search query
            exact_only: If True, only return exact matches

        Returns:
            tuple: (response, is_exact_match) or (None, False)
        """
        query_lower = query.lower().strip()

        # Direct/Exact match
        if query_lower in self.normal_chat_data:
            response = self.normal_chat_data[query_lower]
            return (choice(response)
                    if isinstance(response, list) else response, True)

        # Fuzzy match (only if exact_only is False)
        if not exact_only:
            matches = get_close_matches(query_lower,
                                        self.normal_chat_data.keys(),
                                        n=1,
                                        cutoff=0.6)
            if matches:
                response = self.normal_chat_data[matches[0]]
                return (
                    choice(response)
                    if isinstance(response, list) else response,
                    False,
                )

        return None, False

    def search_dictionary(self, query: str, exact_only: bool = False) -> tuple:
        """
        Search dict_data.json for definitions.

        IMPORTANT: Only returns dictionary results when:
        1. User explicitly asks for a definition (e.g., "meaning of X", "define X")
        2. Query is a SINGLE word that exists in dictionary

        Args:
            query: The search query
            exact_only: If True, only return exact matches

        Returns:
            tuple: (response, is_exact_match) or (None, False)
        """
        query_lower = query.lower().strip()
        words = query_lower.split()

        # Check if this is an EXPLICIT definition request
        is_explicit_definition = False
        word = None

        # Pattern matching for explicit definition requests
        definition_patterns = [
            ("meaning of ", "after"),
            ("definition of ", "after"),
            ("define ", "after"),
            ("what is the meaning of ", "after"),
            ("what does ", "before_mean"),  # "what does X mean"
            (" mean", "before"),  # "X mean" or "what does X mean"
        ]

        for pattern, extract_type in definition_patterns:
            if pattern in query_lower:
                is_explicit_definition = True
                if extract_type == "after":
                    # Get word after the pattern
                    remaining = query_lower.split(pattern)[-1].strip()
                    if remaining:
                        word = remaining.split()[0].strip("?.,!")
                elif extract_type == "before_mean":
                    # "what does X mean" - get X
                    if " mean" in query_lower:
                        middle = (query_lower.split("what does ")[-1].split(
                            " mean")[0].strip())
                        if middle:
                            word = middle.split()[-1].strip("?.,!")
                elif extract_type == "before":
                    # "X mean" - get X (but not for multi-word phrases)
                    before_mean = query_lower.split(" mean")[0].strip()
                    if before_mean and len(before_mean.split()) <= 2:
                        word = before_mean.split()[-1].strip("?.,!")
                break

        # Only do single-word lookup if query IS a single word (not part of a
        # sentence)
        if not word and len(words) == 1:
            single_word = words[0].strip("?.,!")
            if single_word in self.dict_data:
                word = single_word
                is_explicit_definition = True  # Single word lookup is explicit

        # IMPORTANT: Only return dictionary results for EXPLICIT definition
        # requests
        if not is_explicit_definition:
            return None, False

        # Exact match (only if explicit definition request)
        if word and word in self.dict_data:
            definition = self.dict_data[word]
            if isinstance(definition, list):
                return (f"**{word.capitalize()}**: {choice(definition)}", True)
            return (f"**{word.capitalize()}**: {definition}", True)

        # Fuzzy match for dictionary (only if exact_only is False AND explicit
        # request)
        if word and not exact_only:
            matches = get_close_matches(word,
                                        self.dict_data.keys(),
                                        n=1,
                                        cutoff=0.7)
            if matches:
                definition = self.dict_data[matches[0]]
                if isinstance(definition, list):
                    return (
                        f"**{matches[0].capitalize()}**: {choice(definition)}",
                        False,
                    )
                return (f"**{matches[0].capitalize()}**: {definition}", False)

        return None, False

    def search_conversation_history(self, query: str) -> str:
        """Search conversation history for similar past interactions."""
        if not HISTORY_AVAILABLE:
            return None

        try:
            results = conversation_history.conversation_manager.search_conversations(
                query, limit=3)
            if results:
                # Return the most relevant past response
                best_match = results[0]
                # Check if the past query is similar enough
                similarity = self._calculate_similarity(
                    query.lower(), best_match["user_query"].lower())
                if similarity > 0.7:
                    return best_match["ai_response"]
        except Exception:
            pass

        return None

    def search_scraped_cache(self, query: str) -> str:
        """Search cached scraping results."""
        query_lower = query.lower().strip()

        # Direct query match
        if query_lower in self.scraped_cache:
            cached = self.scraped_cache[query_lower]
            return self._format_scraped_results(cached)

        # Search for partial matches in cached queries
        for cached_query, cached_data in self.scraped_cache.items():
            # Check if query words appear in cached query
            query_words = set(query_lower.split())
            cached_words = set(cached_query.split())
            common_words = query_words & cached_words

            if len(common_words) >= 2 or (len(common_words) == 1 and
                                          len(query_words) <= 2):
                return self._format_scraped_results(cached_data)

            # Also search within results content
            for result in cached_data.get("results", []):
                content = result.get("content", "").lower()
                title = result.get("title", "").lower()
                if query_lower in content or query_lower in title:
                    return f"From cached research on '{cached_query}':\n\n{result.get('content', '')[:500]}"

        return None

    def _format_scraped_results(self, cached_data: dict) -> str:
        """Format cached scraping results for display."""
        results = cached_data.get("results", [])
        if not results:
            return None

        query = cached_data.get("query", "your query")
        response = f"📚 Found cached information on '{query}':\n\n"

        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "No title")
            content = result.get("content", "")[:200]
            response += f"{i}. **{title}**\n   {content}...\n\n"

        return response.strip()

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate word-based similarity between two strings."""
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _is_definition_query(self, query: str) -> bool:
        """Check if query is explicitly asking for a definition."""
        definition_patterns = [
            "meaning of",
            "definition of",
            "define ",
            "what is the meaning",
            "what does",
            " mean",
            "dictionary",
        ]
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in definition_patterns)

    def _is_research_query(self, query: str) -> bool:
        """Check if query looks like a research/tutorial/info request."""
        research_patterns = [
            "tutorial",
            "how to",
            "guide",
            "learn",
            "example",
            "list of",
            "types of",
            "best",
            "top",
            "history of",
            "research",
            "information about",
            "explain",
            "introduction",
        ]
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in research_patterns)

    def unified_search(self, query: str, exact_only: bool = False) -> tuple:
        """
        Search all offline sources in priority order.

        Args:
            query: The search query
            exact_only: If True, only return EXACT matches (for online mode)

        Returns:
            tuple: (response, source_name, is_exact_match) or (None, None, False) if not found
        """
        query_lower = query.lower().strip()

        # Priority 1: Time/Date queries (instant response - always exact)
        time_date_response = chat(query_lower)
        if time_date_response:
            return time_date_response, "datetime", True

        # Priority 2: Normal chat patterns (most common interactions)
        chat_response, is_exact = self.search_normal_chat(
            query, exact_only=exact_only)
        if chat_response:
            if exact_only and not is_exact:
                pass  # Skip fuzzy matches in exact_only mode
            else:
                return chat_response, "normal_chat", is_exact

        # Determine query type to adjust priorities
        is_definition = self._is_definition_query(query)
        is_research = self._is_research_query(query)

        # Priority 3A: If research query, check cached scraping FIRST
        if is_research:
            cached_response = self.search_scraped_cache(query)
            if cached_response:
                # Cached scraping is considered exact if query matches
                return cached_response, "cached_scraping", True

        # Priority 3B: Dictionary lookups (especially for definition queries)
        if is_definition or not is_research:
            dict_response, is_exact = self.search_dictionary(
                query, exact_only=exact_only)
            if dict_response:
                if exact_only and not is_exact:
                    pass  # Skip fuzzy matches in exact_only mode
                else:
                    return dict_response, "dictionary", is_exact

        # Priority 4: Cached scraping results (fallback for non-research
        # queries)
        if not is_research:
            cached_response = self.search_scraped_cache(query)
            if cached_response:
                return cached_response, "cached_scraping", True

        # Priority 5: Conversation history (personalized responses) - not exact
        if not exact_only:
            history_response = self.search_conversation_history(query)
            if history_response:
                return (
                    f"Based on our previous conversation:\n{history_response}",
                    "conversation_history",
                    False,
                )

        return None, None, False

    def refresh_scraped_cache(self):
        """Refresh the scraped cache from disk."""
        self.scraped_cache.clear()
        self._load_scraped_cache()


# Global offline knowledge base instance
_offline_kb = None


def get_offline_knowledge_base():
    """Get or create the offline knowledge base singleton."""
    global _offline_kb
    if _offline_kb is None:
        _offline_kb = OfflineKnowledgeBase()
    return _offline_kb


def refresh_offline_cache():
    """
    Refresh the offline knowledge base cache.
    Call this after new scraping results are saved.
    """
    global _offline_kb
    if _offline_kb is not None:
        _offline_kb.refresh_scraped_cache()
        print("Offline knowledge cache refreshed.")


def get_offline_reply(query):
    """Get response from local JSON data (offline fallback) - legacy function."""
    query_lower = query.lower().strip()

    if query_lower in data:
        response = data[query_lower]
    else:
        matches = get_close_matches(query_lower, data.keys(), n=2, cutoff=0.6)
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
        if query_lower in [
                "view history",
                "show history",
                "my history",
                "conversation history",
        ]:
            return get_history_summary()
        elif query_lower.startswith("search history "):
            search_term = query[14:].strip()  # Remove "search history "
            return search_history(search_term)
        elif query_lower.startswith(
                "delete history ") and "item" in query_lower:
            try:
                # Extract ID from "delete history item 123"
                parts = query_lower.split()
                if len(parts) >= 4 and parts[3].isdigit():
                    item_id = int(parts[3])
                    return delete_history_item_command(item_id)
            except BaseException:
                pass
            return "Please specify a valid history item ID to delete. Example: 'delete history item 5'"
        elif query_lower in ["clear history", "delete all history"]:
            return clear_history_command()
        elif query_lower in ["history stats", "history analytics", "my stats"]:
            return get_history_stats()

    # Handle advanced web scraping commands (support both "scrapper" and
    # "scraper")
    if SCRAPER_AVAILABLE and (query_lower.startswith("web scrapper") or
                              query_lower.startswith("web scraper")):
        return handle_web_scraping_command(query)

    # Handle scraping status/result queries
    if SCRAPER_AVAILABLE:
        if query_lower.startswith(
                "scraping status ") or query_lower.startswith("scraper status "):
            task_id = query.split()[-1]
            return get_scraping_status_command(task_id)
        elif query_lower.startswith(
                "scraping results ") or query_lower.startswith(
                    "scraper results "):
            task_id = query.split()[-1]
            return get_scraping_results_command(task_id)
        elif query_lower in [
                "active scrapers", "scraping tasks", "list scrapers"
        ]:
            return list_active_scrapers_command()
        elif query_lower in [
                "scraping notifications",
                "check completions",
                "completed scrapings",
        ]:
            return check_scraping_completions()

    # ========================================================================
    # Check internet connectivity FIRST to determine search strategy
    # ========================================================================
    internet_available = AI_AVAILABLE and ai_chat.is_online()

    # Get the unified offline knowledge base
    offline_kb = get_offline_knowledge_base()

    # ========================================================================
    # ONLINE MODE: Only use offline if EXACT MATCH found
    # ========================================================================
    if internet_available:
        # Search offline sources for EXACT matches only
        exact_response, source, is_exact = offline_kb.unified_search(
            query, exact_only=True)

        if exact_response and is_exact:
            # Found EXACT match in offline sources - use it!
            if HISTORY_AVAILABLE:
                conversation_history.add_to_history(query, exact_response,
                                                    f"offline_exact_{source}")
            return exact_response

        # No exact offline match - go to AI/Internet
        try:
            ai_response, is_ai = get_enhanced_ai_response(query)
            if is_ai and ai_response:
                # AI provided a response - this could be a command or enhanced
                # answer
                return ai_response
        except Exception as e:
            print(f"AI response failed: {e}")

        # AI failed - fallback to fuzzy offline search
        fuzzy_response, source, _ = offline_kb.unified_search(query,
                                                              exact_only=False)
        if fuzzy_response:
            if HISTORY_AVAILABLE:
                conversation_history.add_to_history(query, fuzzy_response,
                                                    f"offline_fuzzy_{source}")
            return fuzzy_response

    # ========================================================================
    # OFFLINE MODE: Search all offline sources (exact + fuzzy)
    # ========================================================================
    else:
        offline_response, source, is_exact = offline_kb.unified_search(
            query, exact_only=False)

        if offline_response:
            if HISTORY_AVAILABLE:
                match_type = "exact" if is_exact else "fuzzy"
                conversation_history.add_to_history(
                    query, offline_response, f"offline_{match_type}_{source}")
            return offline_response

    # Try legacy offline reply as last resort
    local_response = get_offline_reply(query)
    if local_response:
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, local_response,
                                                "offline_legacy")
        return local_response

    # No local response found - try basic command fallbacks
    fallback_response = get_command_fallback(query)
    if fallback_response:
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, fallback_response,
                                                "fallback")
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
        # AI will generate [COMMAND:...] tags for actions like web scraping,
        # app control, etc.
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
    if query_lower in ["open chrome", "launch chrome", "start chrome"]:
        try:
            from modules import app_control

            result = app_control.openApp("chrome")
            return "Opening Chrome..." if result else "Could not open Chrome."
        except Exception as e:
            return "I can't open Chrome right now."

    elif query_lower in ["open notepad", "launch notepad", "start notepad"]:
        try:
            from modules import app_control

            result = app_control.openApp("notepad")
            return "Opening Notepad..." if result else "Could not open Notepad."
        except Exception as e:
            return "I can't open Notepad right now."

    elif query_lower in [
            "open calculator", "launch calculator", "start calculator"
    ]:
        try:
            from modules import app_control

            result = app_control.openApp("calculator")
            return "Opening Calculator..." if result else "Could not open Calculator."
        except Exception as e:
            return "I can't open Calculator right now."

    # Basic system commands
    elif query_lower in ["volume up", "increase volume"]:
        try:
            from modules import app_control

            app_control.volumeUp()
            return "Volume increased."
        except Exception:
            return "I can't adjust volume right now."

    elif query_lower in ["volume down", "decrease volume"]:
        try:
            from modules import app_control

            app_control.volumeDown()
            return "Volume decreased."
        except Exception:
            return "I can't adjust volume right now."

    elif query_lower == "volume mute":
        try:
            from modules import app_control

            app_control.volumeMute()
            return "Volume muted."
        except Exception:
            return "I can't adjust volume right now."

    # Time/date queries (already handled in chat function, but provide
    # fallback)
    elif "time" in query_lower:
        dt = DateTime()
        return f"Current time is: {dt.currentTime()}"

    elif "date" in query_lower or "time" in query_lower:
        dt = DateTime()
        return f"time's date is: {dt.currentDate()}"

    # No fallback available
    return None


# History management functions
def get_history_summary():
    """Get a summary of recent conversation history."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."

    conversations = conversation_history.conversation_manager.get_recent_conversations(
        10)
    if not conversations:
        return "No conversation history found. Start chatting to build your history!"

    summary = f"Your Recent Conversations ({len(conversations)} shown):\n\n"

    for conv in conversations[-5:]:  # Show last 5
        timestamp = conv["timestamp"][:16]  # YYYY-MM-DD HH:MM
        summary += f"[{timestamp}] {conv['summary']}\n"

    summary += f"\nTIP: Say 'history stats' for analytics or 'search history [term]' to find specific conversations."
    return summary


def search_history(search_term):
    """Search conversation history for a specific term."""
    if not HISTORY_AVAILABLE:
        return "Conversation history feature is not available."

    if not search_term:
        return "Please specify what to search for. Example: 'search history weather'"

    results = conversation_history.conversation_manager.search_conversations(
        search_term, 5)
    if not results:
        return f"No conversations found containing '{search_term}'."

    response = f"Search results for '{search_term}' ({len(results)} found):\n\n"

    for conv in results:
        timestamp = conv["timestamp"][:16]
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

    analytics = conversation_history.conversation_manager.get_conversation_analytics(
    )
    personalization = (
        conversation_history.conversation_manager.get_personalization_data())

    stats = "Your Conversation Analytics:\n\n"
    stats += f"Total conversations: {analytics['total_conversations']}\n"
    stats += f"Conversation types: {analytics['conversation_types']}\n"
    stats += f"Common topics: {', '.join(analytics['common_topics'][:3])}\n"
    stats += f"Activity level: {personalization['preferences']['activity_level']}\n"
    stats += f"Recent activity: {personalization['recent_activity']} conversations this week\n"

    return stats


# Advanced Web Scraping Functions
def handle_web_scraping_command(query):
    """Handle web scraping commands and wait for results."""
    import time
    import re

    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available. Please check your installation."

    try:
        # Start scraping task
        start_msg = advanced_scraper.start_web_scraping(query)

        # Extract task ID from response
        task_id_match = re.search(r"Task ID: ([a-f0-9-]+)", start_msg)
        if not task_id_match:
            return start_msg  # Return initial message if no task ID found

        task_id = task_id_match.group(1)

        # Detect mode from query to set appropriate timeout
        is_deep = "--deep" in query.lower() or "-deep" in query.lower()
        is_proxy = "--proxy" in query.lower() or "-proxy" in query.lower()
        is_force = "--force" in query.lower() or "-force" in query.lower()

        # Adjust wait time based on mode
        if is_proxy:
            # 3 minutes for proxy mode (proxy validation takes ~100s)
            max_wait = 180
        elif is_deep or is_force:
            max_wait = 120  # 2 minutes for deep/force modes
        else:
            max_wait = 30  # 30 seconds for normal mode

        check_interval = 2  # Check every 2 seconds
        elapsed = 0
        last_progress = 0

        logger.info(
            f"Waiting up to {max_wait}s for scraping to complete (task: {task_id[:8]}...)"
        )

        while elapsed < max_wait:
            time.sleep(check_interval)
            elapsed += check_interval

            status = advanced_scraper.get_scraping_status(task_id)
            if not status:
                logger.warning(f"No status found for task {task_id[:8]}...")
                break

            current_status = status.get("status", "unknown")
            progress = status.get("progress", 0)

            # Log progress updates
            if progress > last_progress + 10:  # Log every 10% progress
                logger.info(
                    f"Scraping progress: {progress}% ({elapsed}s elapsed)")
                last_progress = progress

            if current_status == "completed":
                # Task completed! Fetch and format results
                logger.info(f"Scraping completed after {elapsed}s")
                results = advanced_scraper.get_scraping_results(task_id)
                if results:
                    formatted = _format_scraping_results(results)

                    # Save to history
                    if HISTORY_AVAILABLE:
                        conversation_history.add_to_history(
                            query, formatted, "web_scraping")

                    return formatted
                else:
                    logger.warning(
                        "Scraping completed but no results returned")
                break

            elif current_status == "error":
                error_msg = f"Scraping failed: {status.get('metadata', {}).get('error', 'Unknown error')}"
                logger.error(f"Scraping error: {error_msg}")
                if HISTORY_AVAILABLE:
                    conversation_history.add_to_history(query, error_msg,
                                                        "web_scraping_error")
                return error_msg

        # Timeout - check one final time for results
        logger.warning(
            f"Scraping timeout after {elapsed}s, checking for partial results..."
        )
        final_status = advanced_scraper.get_scraping_status(task_id)
        if final_status and final_status.get("status") == "completed":
            logger.info("Found completed results after timeout!")
            results = advanced_scraper.get_scraping_results(task_id)
            if results:
                formatted = _format_scraping_results(results)
                if HISTORY_AVAILABLE:
                    conversation_history.add_to_history(query, formatted,
                                                        "web_scraping")
                return formatted

        # Check for partial results even if not completed
        partial_results = None
        if final_status:
            # Try to get any available results
            try:
                partial_results = advanced_scraper.get_scraping_results(
                    task_id)
            except BaseException:
                pass

        # If we have partial results, save them to TXT file
        txt_saved = False
        txt_filepath = None
        if partial_results and len(partial_results.get("results", [])) > 0:
            try:
                # Force save to TXT even for partial results
                formatted_partial = _format_scraping_results(partial_results)
                # Extract filepath from the formatted message
                import re

                filepath_match = re.search(
                    r"Full Results Saved to File:\s*\n\s*(.+?)\n",
                    formatted_partial)
                if filepath_match:
                    txt_filepath = filepath_match.group(1).strip()
                    txt_saved = True
                    logger.info(
                        f"Saved partial results to TXT: {txt_filepath}")
            except Exception as e:
                logger.error(f"Failed to save partial results to TXT: {e}")

        # Still not complete - return instructions with TXT file info if
        # available
        timeout_msg = f"🔍 Web Scraping In Progress\n"
        timeout_msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        timeout_msg += f"Mode: {'Deep' if is_deep else 'Proxy' if is_proxy else 'Force' if is_force else 'Normal'}\n"
        timeout_msg += f"Status: {final_status.get('status', 'running') if final_status else 'unknown'}\n"
        timeout_msg += (
            f"Progress: {final_status.get('progress', 0) if final_status else 0}%\n\n"
        )

        if txt_saved and txt_filepath:
            timeout_msg += f"📄 Partial Results Saved to File:\n"
            timeout_msg += f"   {txt_filepath}\n"
            if partial_results:
                timeout_msg += f"   (Contains {len(partial_results.get('results', []))} results so far)\n\n"
            else:
                timeout_msg += f"   (Partial results saved)\n\n"

        timeout_msg += f"⏱️ Scraping is taking longer than expected (>{max_wait}s).\n"
        timeout_msg += (
            f"💡 Say 'scraping results {task_id[:8]}' to check results later.\n")
        timeout_msg += f"   Or wait for completion notification.\n"

        # Start background completion checker
        _start_completion_checker(task_id, query, is_deep, is_proxy, is_force)

        logger.info(f"Returning timeout message after {elapsed}s")
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, timeout_msg,
                                                "web_scraping")

        return timeout_msg

    except Exception as e:
        error_msg = f"ERROR: Web scraping failed: {str(e)}"
        logger.error(f"Exception in handle_web_scraping_command: {e}")
        if HISTORY_AVAILABLE:
            conversation_history.add_to_history(query, error_msg,
                                                "web_scraping_error")
        return error_msg


def _start_completion_checker(task_id, original_query, is_deep, is_proxy,
                              is_force):
    """Start a background thread to check for scraping completion and notify."""
    import threading
    import time

    def check_completion():
        """Background function to monitor scraping completion."""
        max_additional_wait = 300  # Wait up to 5 more minutes
        check_interval = 10  # Check every 10 seconds
        elapsed = 0

        logger.info(f"Started completion checker for task {task_id[:8]}")

        while elapsed < max_additional_wait:
            time.sleep(check_interval)
            elapsed += check_interval

            try:
                status = advanced_scraper.get_scraping_status(task_id)
                if not status:
                    logger.warning(f"Lost status for task {task_id[:8]}")
                    break

                current_status = status.get("status", "unknown")

                if current_status == "completed":
                    logger.info(
                        f"Background scraping completed for task {task_id[:8]} after {elapsed}s"
                    )

                    # Get final results
                    results = advanced_scraper.get_scraping_results(task_id)
                    if results:
                        # Format and save to TXT
                        formatted = _format_scraping_results(results)

                        # Create completion notification
                        mode_name = ("Deep" if is_deep else
                                     ("Proxy" if is_proxy else
                                      "Force" if is_force else "Normal"))
                        notification = f"✅ {mode_name} Web Scraping Completed!\n"
                        notification += f"━━━━━━━━━━━━━━━━━━━━\n"
                        notification += f"Query: {original_query}\n"
                        notification += f"Task ID: {task_id[:8]}...\n"
                        notification += (
                            f"Found: {len(results.get('results', []))} results\n"
                        )
                        # Approximate total time
                        notification += f"Total Time: ~{elapsed + 120}s\n\n"

                        # Extract TXT file path from formatted message
                        import re

                        filepath_match = re.search(
                            r"Full Results Saved to File:\s*\n\s*(.+?)\n",
                            formatted)
                        if filepath_match:
                            txt_path = filepath_match.group(1).strip()
                            notification += f"📄 Results saved to: {txt_path}\n\n"

                        notification += (
                            f"💡 Say 'scraping results {task_id[:8]}' to view in chat."
                        )

                        # Save notification to history
                        if HISTORY_AVAILABLE:
                            conversation_history.add_to_history(
                                f"Background completion: {original_query}",
                                notification,
                                "web_scraping_completion",
                            )

                        logger.info(
                            f"Completion notification created for task {task_id[:8]}"
                        )
                    break

                elif current_status == "error":
                    error_details = status.get(
                        "metadata", {}).get(
                        "error", "Unknown error")
                    logger.error(
                        f"Background scraping failed for task {task_id[:8]}: {error_details}"
                    )

                    # Create error notification
                    error_notification = f"❌ Web Scraping Failed\n"
                    error_notification += f"━━━━━━━━━━━━━━━━━━━━\n"
                    error_notification += f"Task ID: {task_id[:8]}...\n"
                    error_notification += f"Error: {error_details}\n"

                    if HISTORY_AVAILABLE:
                        conversation_history.add_to_history(
                            f"Background error: {original_query}",
                            error_notification,
                            "web_scraping_error",
                        )
                    break

            except Exception as e:
                logger.error(
                    f"Error in completion checker for task {task_id[:8]}: {e}")
                break

        if elapsed >= max_additional_wait:
            logger.warning(
                f"Completion checker timed out for task {task_id[:8]} after {elapsed}s"
            )

    # Start the background thread
    checker_thread = threading.Thread(target=check_completion, daemon=True)
    checker_thread.start()


def _format_scraping_results(results):
    """Format scraping results for chat display."""
    import os
    import json
    from pathlib import Path
    from datetime import datetime

    if not results or not isinstance(results, dict):
        return "No results found."

    status = results.get("status", "unknown")
    if status != "completed":
        return f"Scraping not completed. Status: {status}"

    query = results.get("query", "N/A")
    mode = results.get("mode", "normal")
    result_items = results.get("results", [])
    result_count = len(result_items)
    sources_count = results.get("metadata", {}).get("total_sources", 0)
    scraping_time = results.get("metadata", {}).get("scraping_time", 0)
    task_id = results.get("id", "unknown")
    raw_data_file = results.get("metadata", {}).get("raw_data_file", "")

    # Try to load raw data file for more detailed content
    raw_results = []
    if raw_data_file and Path(raw_data_file).exists():
        try:
            with open(raw_data_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                raw_results = raw_data.get("results", [])
                logger.info(
                    f"Loaded {len(raw_results)} items from raw data file")
        except Exception as e:
            logger.warning(f"Could not load raw data file: {e}")

    # Build detailed content string
    detailed_content = f"{'='*80}\n"
    detailed_content += f"WEB SCRAPING RESULTS - FULL REPORT\n"
    detailed_content += f"{'='*80}\n\n"
    detailed_content += f"Query: {query}\n"
    detailed_content += f"Mode: {mode}\n"
    detailed_content += f"Task ID: {task_id}\n"
    detailed_content += f"Results Found: {result_count}\n"
    detailed_content += f"Sources: {sources_count}\n"
    detailed_content += f"Scraping Time: {scraping_time:.2f} seconds\n"
    detailed_content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    detailed_content += f"{'='*80}\n\n"

    # Merge raw results with analyzed results for richer content
    url_to_raw = {
        item.get("url", ""): item for item in raw_results if item.get("url")
    }

    # Add all results with full content
    for i, item in enumerate(result_items, 1):
        title = item.get("title", "No title")
        url = item.get("url", "")
        source = item.get("source", "Unknown")
        relevance = item.get("relevance_score", 0)

        # Try to get full content from raw data
        raw_item = url_to_raw.get(url, {})
        full_content = raw_item.get("content", "")
        summary = item.get("summary", "")
        content = item.get("content", summary)

        # Use the longest content available
        best_content = full_content if len(full_content) > len(
            content) else content
        if not best_content:
            best_content = summary

        detailed_content += f"[{i}] {title}\n"
        detailed_content += f"{'-'*80}\n"
        if url:
            detailed_content += f"URL: {url}\n"
        detailed_content += f"Source: {source}\n"
        detailed_content += f"Relevance Score: {relevance}/10\n\n"

        if best_content:
            detailed_content += f"CONTENT:\n{best_content}\n\n"
        else:
            detailed_content += "No content available.\n\n"

        detailed_content += f"{'='*80}\n\n"

    # Add entities and keywords
    entities = results.get("entities", {})
    if entities:
        detailed_content += f"\nEXTRACTED ENTITIES:\n"
        detailed_content += f"{'-'*80}\n"
        for entity_type, entity_list in entities.items():
            if entity_list:
                detailed_content += f"{entity_type.upper()}: {', '.join(entity_list)}\n"
        detailed_content += "\n"

    keywords = results.get("keywords", [])
    if keywords:
        detailed_content += f"KEYWORDS: {', '.join(keywords)}\n\n"

    # Add source URLs
    all_sources = results.get("sources", [])
    if all_sources:
        detailed_content += f"\nALL SOURCE URLs ({len(all_sources)}):\n"
        detailed_content += f"{'-'*80}\n"
        for idx, src_url in enumerate(all_sources, 1):
            detailed_content += f"{idx}. {src_url}\n"

    # Calculate total content size
    content_size = len(detailed_content)

    # ALWAYS save to TXT file for all web scraping results
    if True:  # Always export to TXT
        try:
            # Create exports directory if it doesn't exist
            exports_dir = Path("temp_scraping_results/exports")
            exports_dir.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            safe_query = "".join(c if c.isalnum() or c in (" ", "_") else "_"
                                 for c in query)[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraping_{safe_query}_{timestamp}.txt"
            filepath = exports_dir / filename

            # Write content to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(detailed_content)

            logger.info(f"Exported web scraping results to TXT: {filepath}")
            logger.info(
                f"TXT file size: {content_size:,} characters, {result_count} results"
            )

            # Build chat response with file link
            response = f"🔍 Web Scraping Results\n"
            response += f"━━━━━━━━━━━━━━━━━━━━\n"
            response += f"Query: {query}\n"
            response += f"Found: {result_count} results from {sources_count} sources\n"
            response += f"Time: {scraping_time:.1f}s\n\n"

            # Show brief preview of results with content snippets
            preview_count = min(3, result_count)
            response += f"📋 Content Preview (showing {preview_count} of {result_count} results):\n\n"

            for i, item in enumerate(result_items[:preview_count], 1):
                title = item.get("title", "No title")
                url = item.get("url", "")

                # Get best content for preview
                raw_item = url_to_raw.get(url, {})
                full_content = raw_item.get("content", "")
                summary = item.get("summary", "")
                content = item.get("content", summary)
                best_content = (full_content if len(
                    full_content) > len(content) else content)
                if not best_content:
                    best_content = summary

                response += f"【{i}】 {title}\n"
                if url:
                    response += f"🔗 {url}\n"

                # Show content preview (first 300 chars)
                if best_content:
                    preview_text = best_content[:300].strip()
                    if len(best_content) > 300:
                        preview_text += "..."
                    response += f"📄 {preview_text}\n"
                response += "\n"

            if result_count > preview_count:
                response += f"... and {result_count - preview_count} more results\n\n"

            # File information
            response += f"📄 Full Results Saved to File:\n"
            response += f"   {filepath.absolute()}\n"
            response += f"   Size: {content_size:,} characters\n\n"
            response += f"💡 You can open this file to read all {result_count} results with full content!\n"

            return response

        except Exception as e:
            logger.error(f"Failed to export results to TXT file: {e}",
                         exc_info=True)
            # Fall back to showing preview in chat without file

    # Fallback: Show results in chat directly (if TXT export failed or content
    # is empty)
    response = f"🔍 Web Scraping Results\n"
    response += f"━━━━━━━━━━━━━━━━━━━━\n"
    response += f"Query: {query}\n"
    response += f"Found: {result_count} results from {sources_count} sources\n"
    response += f"Time: {scraping_time:.1f}s\n\n"

    # Display results
    for i, item in enumerate(result_items, 1):
        title = item.get("title", "No title")
        summary = item.get("summary", "")
        content = item.get("content", summary)
        source = item.get("source", "Unknown")
        url = item.get("url", "")

        response += f"【{i}】 {title}\n"

        # Show content/summary preview
        if content:
            preview = content[:400].strip()
            if len(content) > 400:
                preview += "..."
            response += f"{preview}\n\n"

        # Show URL if available
        if url:
            response += f"🔗 {url}\n"

        response += f"Source: {source}\n\n"

    # Show extracted entities
    entities = results.get("entities", {})
    if entities:
        response += f"\n📌 Key Information:\n"
        for entity_type, entity_list in entities.items():
            if entity_list:
                response += f"  {entity_type.title()}: {', '.join(entity_list[:5])}\n"

    return response


def get_scraping_status_command(task_id):
    """Get status of a scraping task."""
    if not SCRAPER_AVAILABLE:
        return "ERROR: Advanced web scraping is not available."

    try:
        status = advanced_scraper.get_scraping_status(task_id)
        if status:
            progress = status.get("progress", 0)
            status_text = status.get("status", "unknown")

            response = f"Scraping Task {task_id[:8]}...\n"
            response += f"Status: {status_text}\n"
            response += f"Progress: {progress}%\n"

            if status_text == "completed":
                response += f"Results: {status.get('results_count', 0)} items found\n"
                response += f"Sources: {status.get('sources_count', 0)} websites\n"
                response += f"Time: {status.get('metadata', {}).get('scraping_time', 'N/A'):.1f}s\n"
                response += (
                    f"\nTIP: Say 'scraping results {task_id}' to view the results."
                )
            elif status_text == "error":
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
            status = results.get("status", "unknown")
            if status != "completed":
                return f"WARNING: Task {task_id[:8]} is not completed yet. Status: {status}. Try again later."

            result_count = results.get("results_count", 0)
            response = f"Scraping Results for Task {task_id[:8]}\n"
            response += f"Query: {results.get('query', 'N/A')}\n"
            response += f"Mode: {results.get('mode', 'normal')}\n"
            response += f"Found: {result_count} results\n\n"

            # Show preview of results
            preview_results = results.get("results", [])[:5]  # Show first 5

            if preview_results:
                for i, result in enumerate(preview_results, 1):
                    title = result.get("title", "No title")[:50]
                    content = result.get("content", "")[:150]
                    source = result.get("source", "Unknown")

                    response += f"{i}. {title}\n"
                    response += f"   {content}...\n"
                    response += f"   Source: {source}\n\n"

                if result_count > 5:
                    response += f"FILE: ... and {result_count - 5} more results.\n"

                    # Check if saved to file
                    if "saved_to_file" in results.get("metadata", {}):
                        file_path = results["metadata"]["saved_to_file"]
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
            return (
                "No active scraping tasks. Start one with 'web scrapper : your query'"
            )

        response = f"Active Scraping Tasks ({len(tasks)}):\n\n"

        for task in tasks:
            task_id = task["id"][:8]
            query = task.get("query", "N/A")[:30]
            mode = task.get("mode", "normal")
            status = task.get("status", "unknown")
            progress = task.get("progress", 0)

            response += f"ID {task_id} | Query: {query}... | Mode: {mode} | Status: {status} ({progress}%)\n"

        response += f"\nTIP: Use 'scraping status [ID]' to check progress or 'scraping results [ID]' for completed tasks."
        return response
    except Exception as e:
        return f"ERROR: Failed to list scraping tasks: {str(e)}"


def check_scraping_completions():
    """Check for recent scraping completion notifications."""
    if not HISTORY_AVAILABLE:
        return "ERROR: Conversation history is not available."

    try:
        # Get recent history items related to scraping completions
        recent_history = conversation_history.get_recent_history(limit=50)

        completions = []
        for item in recent_history:
            if item.get("type") in [
                    "web_scraping_completion", "web_scraping_error"
            ]:
                completions.append(item)

        if not completions:
            return "No recent scraping completions found. All tasks may still be in progress."

        response = f"📬 Recent Scraping Completions ({len(completions)}):\n"
        response += f"━━━━━━━━━━━━━━━━━━━━\n\n"

        for i, completion in enumerate(completions[:10], 1):  # Show last 10
            timestamp = completion.get("timestamp", "Unknown")
            query = completion.get("query", "Unknown query")
            content = completion.get("response", "")

            # Extract key info from completion message
            lines = content.split("\n")
            mode_line = next((line for line in lines if "Mode:" in line), "")
            results_line = next((line for line in lines if "Found:" in line),
                                "")
            time_line = next((line for line in lines if "Total Time:" in line),
                             "")

            response += f"{i}. {timestamp}\n"
            if mode_line:
                response += f"   {mode_line}\n"
            if results_line:
                response += f"   {results_line}\n"
            if time_line:
                response += f"   {time_line}\n"

            # Extract task ID for reference
            import re

            task_match = re.search(r"Task ID: ([a-f0-9]+)", content)
            if task_match:
                task_id = task_match.group(1)
                response += f"   Task: {task_id}...\n"

            response += "\n"

        if len(completions) > 10:
            response += f"... and {len(completions) - 10} older completions.\n\n"

        response += f"💡 Say 'scraping results [task_id]' to view specific results."

        return response

    except Exception as e:
        return f"ERROR: Failed to check completions: {str(e)}"
