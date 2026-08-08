"""
Context Manager for Voxa
Maintains multi-turn conversation context and session state
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ContextManager:
    """
    Manages conversation context across multiple turns
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
    
    def create_session(self, session_id: str, user_id: str = None) -> Dict:
        """Create a new conversation session"""
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'turns': [],
            'context': {
                'location': None,
                'last_intent': None,
                'last_entities': {},
                'preferences': {},
                'variables': {}
            },
            'metadata': {
                'total_turns': 0,
                'intents_history': [],
                'language': 'en'
            }
        }
        
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get existing session or None"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session has expired
            if datetime.now() - session['last_activity'] > self.session_timeout:
                self.delete_session(session_id)
                return None
        
        return session
    
    def update_session(self, session_id: str, turn_data: Dict):
        """Update session with new turn data"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        # Add turn to history
        turn = {
            'turn_number': session['metadata']['total_turns'] + 1,
            'timestamp': datetime.now().isoformat(),
            'user_input': turn_data.get('user_input', ''),
            'intent': turn_data.get('intent', {}),
            'entities': turn_data.get('entities', {}),
            'response': turn_data.get('response', ''),
            'action': turn_data.get('action', None)
        }
        
        session['turns'].append(turn)
        session['metadata']['total_turns'] += 1
        
        # Update context
        if turn_data.get('intent'):
            session['context']['last_intent'] = turn_data['intent']['intent']
            session['metadata']['intents_history'].append(turn_data['intent']['intent'])
        
        if turn_data.get('entities'):
            session['context']['last_entities'] = turn_data['entities']
            
            # Update persistent context values
            normalized = turn_data['entities'].get('normalized', {})
            if 'location' in normalized:
                session['context']['location'] = normalized['location']
        
        return True
    
    def get_context(self, session_id: str) -> Dict:
        """Get current context for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {}
        
        return session['context']
    
    def set_context_variable(self, session_id: str, key: str, value):
        """Set a context variable"""
        session = self.get_session(session_id)
        
        if session:
            session['context']['variables'][key] = value
            return True
        
        return False
    
    def get_context_variable(self, session_id: str, key: str, default=None):
        """Get a context variable"""
        session = self.get_session(session_id)
        
        if session:
            return session['context']['variables'].get(key, default)
        
        return default
    
    def get_last_intent(self, session_id: str) -> Optional[str]:
        """Get the last recognized intent"""
        session = self.get_session(session_id)
        
        if session:
            return session['context']['last_intent']
        
        return None
    
    def get_last_entities(self, session_id: str) -> Dict:
        """Get entities from the last turn"""
        session = self.get_session(session_id)
        
        if session:
            return session['context']['last_entities']
        
        return {}
    
    def get_conversation_history(self, session_id: str, last_n: int = 5) -> List[Dict]:
        """Get recent conversation turns"""
        session = self.get_session(session_id)
        
        if session:
            return session['turns'][-last_n:]
        
        return []
    
    def resolve_coreference(self, session_id: str, text: str) -> str:
        """
        Resolve pronouns and references using context
        Simple implementation - can be enhanced with advanced NLP
        """
        session = self.get_session(session_id)
        
        if not session:
            return text
        
        context = session['context']
        text_lower = text.lower()
        
        # Resolve location references
        if context.get('location'):
            if re.search(r'\b(there|that place|that city)\b', text_lower):
                text = re.sub(
                    r'\b(there|that place|that city)\b',
                    context['location'],
                    text,
                    flags=re.IGNORECASE
                )
        
        # Resolve "it" references based on last intent
        last_intent = context.get('last_intent')
        if last_intent and re.search(r'\bit\b', text_lower):
            # Context-aware resolution
            if last_intent == 'weather':
                text = re.sub(r'\bit\b', 'the weather', text, flags=re.IGNORECASE)
        
        return text
    
    def should_clarify(self, session_id: str, current_intent: Dict, current_entities: Dict) -> bool:
        """
        Determine if clarification is needed based on context
        """
        # Low confidence intent
        if current_intent.get('confidence', 0) < 0.5:
            return True
        
        # Missing required entities
        metadata = current_intent.get('metadata', {})
        
        if metadata.get('requires_location') and not current_entities.get('normalized', {}).get('location'):
            # Check if location is in context
            session = self.get_session(session_id)
            if session and not session['context'].get('location'):
                return True
        
        if metadata.get('requires_query') and not current_entities.get('normalized', {}).get('query'):
            return True
        
        return False
    
    def get_clarification_prompt(self, session_id: str, current_intent: Dict, current_entities: Dict) -> str:
        """Generate clarification prompt"""
        metadata = current_intent.get('metadata', {})
        
        if metadata.get('requires_location'):
            return "I need to know the location. Which city are you asking about?"
        
        if metadata.get('requires_query'):
            return "What would you like me to search for?"
        
        if current_intent.get('confidence', 0) < 0.5:
            return "I'm not sure I understood that correctly. Could you rephrase?"
        
        return "Could you provide more details?"
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session['last_activity'] > self.session_timeout
        ]
        
        for sid in expired:
            self.delete_session(sid)

        return len(expired)
    # (re is imported at module top)
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {}
        
        return {
            'total_turns': session['metadata']['total_turns'],
            'duration_minutes': (datetime.now() - session['created_at']).total_seconds() / 60,
            'intents_used': list(set(session['metadata']['intents_history'])),
            'last_activity': session['last_activity'].isoformat()
        }

