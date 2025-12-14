"""
Conversation History Module - Persistent Chat History with Summaries

Stores conversation summaries and highlights in JSON format for user experience
refinement and personalization. Provides functionality to view, manage, and
leverage conversation history.

Features:
    - Automatic conversation summarization
    - JSON-based persistent storage
    - History viewing and deletion
    - User experience personalization
    - Conversation analytics

Dependencies:
    - json: JSON file operations
    - os: File system operations
    - datetime: Timestamp handling
"""

import json
import os
import datetime
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter

# History storage configuration
HISTORY_FILE = 'userData/conversation_history.json'
MAX_CONVERSATIONS = 1000  # Maximum conversations to store
MAX_SUMMARY_LENGTH = 200  # Maximum characters in summary

# Setup logging
logger = logging.getLogger('VocalXpert.ConversationHistory')

class ConversationHistory:
    """Manages conversation history with summaries and analytics."""

    def __init__(self):
        """Initialize conversation history manager."""
        self.history_file = HISTORY_FILE
        self._ensure_history_file()
        self.history = self._load_history()

    def _ensure_history_file(self):
        """Ensure history file and directory exist."""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'conversations': [],
                    'metadata': {
                        'total_conversations': 0,
                        'created_at': datetime.datetime.now().isoformat(),
                        'last_updated': datetime.datetime.now().isoformat()
                    }
                }, f, indent=2, ensure_ascii=False)

    def _load_history(self) -> Dict:
        """Load conversation history from file."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Reset history if corrupted or missing
            logger.warning("Conversation history file corrupted or missing, resetting to default")
            default_history = {
                'conversations': [],
                'metadata': {
                    'total_conversations': 0,
                    'created_at': datetime.datetime.now().isoformat(),
                    'last_updated': datetime.datetime.now().isoformat()
                }
            }
            # Overwrite corrupted file with default
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(default_history, f, indent=2, ensure_ascii=False)
            return default_history

    def _save_history(self):
        """Save conversation history to file."""
        self.history['metadata']['last_updated'] = datetime.datetime.now().isoformat()
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def _generate_summary(self, user_query: str, ai_response: str) -> str:
        """
        Generate a concise summary of the conversation exchange.

        Args:
            user_query: User's input message
            ai_response: AI's response

        Returns:
            Summary string
        """
        # Extract key elements
        query_words = user_query.lower().split()
        response_words = ai_response.lower().split()

        # Identify conversation type
        conversation_type = self._classify_conversation(user_query, ai_response)

        # Create summary based on type
        if conversation_type == 'command':
            summary = f"Executed command: {user_query[:50]}..."
        elif conversation_type == 'question':
            summary = f"Answered: {user_query[:50]}..."
        elif conversation_type == 'conversation':
            summary = f"Chat: {user_query[:30]}... → {ai_response[:30]}..."
        else:
            summary = f"Interaction: {user_query[:40]}..."

        return summary[:MAX_SUMMARY_LENGTH]

    def _classify_conversation(self, user_query: str, ai_response: str) -> str:
        """Classify the type of conversation."""
        query_lower = user_query.lower()

        # Check for commands
        command_indicators = ['open', 'launch', 'start', 'run', 'play', 'search', 'calculate',
                            'set timer', 'volume', 'shutdown', 'restart', 'weather', 'news']
        if any(indicator in query_lower for indicator in command_indicators):
            return 'command'

        # Check for questions
        question_indicators = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you']
        if any(indicator in query_lower for indicator in question_indicators):
            return 'question'

        # Check for AI command format
        if '[COMMAND:' in ai_response:
            return 'command'

        return 'conversation'

    def add_conversation(self, user_query: str, ai_response: str, source: str = 'ai_chat'):
        """
        Add a conversation exchange to history.

        Args:
            user_query: User's input message
            ai_response: AI's response
            source: Source of the response ('ai_chat', 'offline', etc.)
        """
        if not user_query.strip() or not ai_response.strip():
            return

        # Generate summary
        summary = self._generate_summary(user_query, ai_response)

        # Create conversation entry
        conversation = {
            'id': len(self.history['conversations']) + 1,
            'timestamp': datetime.datetime.now().isoformat(),
            'user_query': user_query,
            'ai_response': ai_response,
            'summary': summary,
            'source': source,
            'conversation_type': self._classify_conversation(user_query, ai_response)
        }

        # Add to history
        self.history['conversations'].append(conversation)
        self.history['metadata']['total_conversations'] = len(self.history['conversations'])

        # Maintain maximum limit
        if len(self.history['conversations']) > MAX_CONVERSATIONS:
            self.history['conversations'] = self.history['conversations'][-MAX_CONVERSATIONS:]

        # Save to file
        self._save_history()

    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversations.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation dictionaries
        """
        conversations = self.history['conversations']
        return conversations[-limit:] if conversations else []

    def get_conversations_by_type(self, conv_type: str, limit: int = 20) -> List[Dict]:
        """
        Get conversations filtered by type.

        Args:
            conv_type: Type of conversation ('command', 'question', 'conversation')
            limit: Maximum number to return

        Returns:
            List of matching conversations
        """
        filtered = [conv for conv in self.history['conversations']
                   if conv.get('conversation_type') == conv_type]
        return filtered[-limit:] if filtered else []

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search conversations by query.

        Args:
            query: Search term
            limit: Maximum results to return

        Returns:
            List of matching conversations
        """
        query_lower = query.lower()
        matches = []

        for conv in self.history['conversations']:
            if (query_lower in conv['user_query'].lower() or
                query_lower in conv['ai_response'].lower() or
                query_lower in conv['summary'].lower()):
                matches.append(conv)

        return matches[-limit:] if matches else []

    def get_conversation_analytics(self) -> Dict:
        """
        Get analytics about conversation history.

        Returns:
            Dictionary with analytics data
        """
        conversations = self.history['conversations']
        if not conversations:
            return {'total': 0, 'types': {}, 'sources': {}, 'daily_count': {}}

        # Count by type
        types = Counter(conv.get('conversation_type', 'unknown') for conv in conversations)

        # Count by source
        sources = Counter(conv.get('source', 'unknown') for conv in conversations)

        # Daily activity
        daily_counts = defaultdict(int)
        for conv in conversations:
            date = conv['timestamp'][:10]  # YYYY-MM-DD
            daily_counts[date] += 1

        # Most common topics (simple keyword extraction)
        all_queries = ' '.join(conv['user_query'] for conv in conversations[-100:])  # Last 100
        words = [word.lower() for word in all_queries.split() if len(word) > 3]
        common_words = Counter(words).most_common(10)

        return {
            'total_conversations': len(conversations),
            'conversation_types': dict(types),
            'sources': dict(sources),
            'daily_activity': dict(daily_counts),
            'common_topics': [word for word, count in common_words if count > 1]
        }

    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a specific conversation by ID.

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if deleted, False if not found
        """
        for i, conv in enumerate(self.history['conversations']):
            if conv['id'] == conversation_id:
                del self.history['conversations'][i]
                self.history['metadata']['total_conversations'] -= 1
                self._save_history()
                return True
        return False

    def clear_all_history(self):
        """Clear all conversation history."""
        self.history['conversations'] = []
        self.history['metadata']['total_conversations'] = 0
        self._save_history()

    def get_personalization_data(self) -> Dict:
        """
        Get data for personalizing user experience.

        Returns:
            Dictionary with personalization insights
        """
        analytics = self.get_conversation_analytics()

        # Extract preferences
        preferences = {
            'preferred_topics': analytics.get('common_topics', [])[:5],
            'interaction_style': 'command_heavy' if analytics.get('conversation_types', {}).get('command', 0) > 50 else 'conversational',
            'activity_level': 'high' if analytics.get('total_conversations', 0) > 100 else 'moderate' if analytics.get('total_conversations', 0) > 20 else 'low'
        }

        return {
            'analytics': analytics,
            'preferences': preferences,
            'recent_activity': len([conv for conv in self.history['conversations']
                                  if self._is_recent(conv['timestamp'])])
        }

    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """Check if timestamp is within recent days."""
        try:
            conv_date = datetime.datetime.fromisoformat(timestamp)
            now = datetime.datetime.now()
            return (now - conv_date).days <= days
        except:
            return False

    def export_history(self, filename: str = None) -> str:
        """
        Export conversation history to a file.

        Args:
            filename: Optional filename, defaults to timestamped name

        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'conversation_history_export_{timestamp}.json'

        export_path = os.path.join('userData', filename)
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

        return export_path

# Global instance
conversation_manager = ConversationHistory()

def add_to_history(user_query: str, ai_response: str, source: str = 'ai_chat'):
    """Convenience function to add conversation to history."""
    conversation_manager.add_conversation(user_query, ai_response, source)

def get_recent_history(limit: int = 10) -> List[Dict]:
    """Get recent conversation history."""
    return conversation_manager.get_recent_conversations(limit)

def view_history():
    """Display conversation history in readable format."""
    conversations = conversation_manager.get_recent_conversations(20)

    if not conversations:
        print("No conversation history found.")
        return

    print("\n=== CONVERSATION HISTORY ===")
    print(f"Total conversations: {len(conversation_manager.history['conversations'])}")
    print("-" * 50)

    for conv in conversations:
        timestamp = conv['timestamp'][:19]  # Remove microseconds
        print(f"[{timestamp}] {conv['conversation_type'].upper()}")
        print(f"User: {conv['user_query']}")
        print(f"AI: {conv['ai_response'][:100]}{'...' if len(conv['ai_response']) > 100 else ''}")
        print(f"Summary: {conv['summary']}")
        print("-" * 30)

def delete_history_item(conversation_id: int) -> bool:
    """Delete a specific conversation by ID."""
    return conversation_manager.delete_conversation(conversation_id)

def clear_history():
    """Clear all conversation history."""
    conversation_manager.clear_all_history()
    print("Conversation history cleared.")

def get_user_insights():
    """Get insights about user behavior and preferences."""
    analytics = conversation_manager.get_conversation_analytics()

    print("\n=== USER INSIGHTS ===")
    print(f"Total conversations: {analytics['total_conversations']}")
    print(f"Conversation types: {analytics['conversation_types']}")
    print(f"Common topics: {analytics['common_topics'][:5]}")
    print(f"Activity level: {conversation_manager.get_personalization_data()['preferences']['activity_level']}")

if __name__ == "__main__":
    # Test functions
    print("Conversation History Module Test")
    view_history()
    get_user_insights()