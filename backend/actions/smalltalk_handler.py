"""
Small Talk Action Handler
Handles casual conversation and greetings
"""

import random
from typing import Dict
from datetime import datetime


class SmallTalkHandler:
    """
    Handles small talk and casual conversation
    """
    
    def __init__(self):
        self.responses = self._initialize_responses()
    
    def _initialize_responses(self) -> Dict:
        """Initialize response templates for different small talk types"""
        return {
            'greeting': [
                "Hello! How can I assist you today?",
                "Hi there! What can I help you with?",
                "Greetings! I'm Voxa, your smart assistant. How may I help?",
                "Hey! Ready to help you with anything you need!",
                "Good to see you! What would you like to know?"
            ],
            'greeting_morning': [
                "Good morning! Hope you're having a great start to your day!",
                "Morning! How can I brighten your day?",
                "Good morning! What can I help you with today?"
            ],
            'greeting_afternoon': [
                "Good afternoon! How's your day going?",
                "Afternoon! What can I do for you?",
                "Good afternoon! Ready to assist you!"
            ],
            'greeting_evening': [
                "Good evening! How can I help you tonight?",
                "Evening! What brings you here?",
                "Good evening! Hope you had a great day!"
            ],
            'how_are_you': [
                "I'm functioning perfectly, thank you for asking! How can I help you?",
                "I'm doing great! Ready to assist you with anything you need!",
                "All systems operational! What can I do for you today?",
                "I'm excellent, thanks! How about you? What can I help with?"
            ],
            'thank_you': [
                "You're welcome! Happy to help!",
                "My pleasure! Let me know if you need anything else!",
                "Glad I could help! Feel free to ask me anything!",
                "Anytime! That's what I'm here for!",
                "You're very welcome! Is there anything else I can assist with?"
            ],
            'goodbye': [
                "Goodbye! Have a great day!",
                "See you later! Feel free to come back anytime!",
                "Farewell! It was nice chatting with you!",
                "Take care! I'll be here whenever you need me!",
                "Bye! Looking forward to our next conversation!"
            ],
            'compliment': [
                "Thank you! I appreciate that! How can I help you today?",
                "That's very kind of you! What can I do for you?",
                "Thanks! I'm here to make your life easier!",
                "I'm glad you think so! What would you like to know?"
            ],
            'name': [
                "I'm Voxa, your voice-enabled smart assistant!",
                "My name is Voxa! I'm here to help you with information and tasks!",
                "I'm Voxa - your friendly AI assistant!"
            ],
            'creator': [
                "I was created as an advanced voice-enabled chatbot with NLU capabilities!",
                "I'm a smart assistant built with modern AI and NLP technologies!",
                "I was developed to help users with voice and text interactions!"
            ],
            'joke': [
                "Why did the AI go to school? To improve its learning algorithms! 😄",
                "What do you call a chatbot that sings? A-Dell! 🎵",
                "Why don't robots ever get lost? They always follow their GPS - General Problem Solving! 🤖",
                "How does a computer get drunk? It takes screenshots! 📸"
            ],
            'default': [
                "That's interesting! Tell me more, or ask me something I can help with!",
                "I see! Is there anything specific you'd like to know?",
                "Noted! How else can I assist you?",
                "Interesting! What would you like to do next?"
            ]
        }
    
    def detect_smalltalk_type(self, text: str) -> str:
        """Detect the type of small talk"""
        text_lower = text.lower()
        
        # Greetings with time of day
        hour = datetime.now().hour
        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            if 'morning' in text_lower or (5 <= hour < 12):
                return 'greeting_morning'
            elif 'afternoon' in text_lower or (12 <= hour < 17):
                return 'greeting_afternoon'
            elif 'evening' in text_lower or (17 <= hour < 22):
                return 'greeting_evening'
            else:
                return 'greeting'
        
        # How are you
        if any(phrase in text_lower for phrase in ['how are you', "what's up", 'wassup', 'how do you do']):
            return 'how_are_you'
        
        # Thank you
        if any(word in text_lower for word in ['thank', 'thanks', 'appreciate']):
            return 'thank_you'
        
        # Goodbye
        if any(word in text_lower for word in ['bye', 'goodbye', 'see you', 'farewell', 'later']):
            return 'goodbye'
        
        # Compliments
        if any(word in text_lower for word in ['nice', 'great', 'awesome', 'cool', 'amazing', 'excellent', 'good job']):
            return 'compliment'
        
        # Name
        if any(phrase in text_lower for phrase in ['your name', 'who are you', 'what are you called']):
            return 'name'
        
        # Creator
        if any(phrase in text_lower for phrase in ['who made you', 'who created you', 'who built you']):
            return 'creator'
        
        # Joke
        if any(word in text_lower for word in ['joke', 'funny', 'laugh']):
            return 'joke'
        
        return 'default'
    
    def get_response(self, smalltalk_type: str) -> str:
        """Get a random response for the small talk type"""
        responses = self.responses.get(smalltalk_type, self.responses['default'])
        return random.choice(responses)
    
    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        """
        Main handler for small talk
        
        Args:
            entities: Extracted entities
            context: Conversation context
        
        Returns:
            Response dictionary
        """
        # Get original text from context if available
        original_text = context.get('original_text', '') if context else ''
        
        # Detect small talk type
        smalltalk_type = self.detect_smalltalk_type(original_text)
        
        # Get response
        response_text = self.get_response(smalltalk_type)
        
        return {
            'success': True,
            'response': response_text,
            'data': {
                'smalltalk_type': smalltalk_type,
                'is_greeting': smalltalk_type.startswith('greeting'),
                'is_farewell': smalltalk_type == 'goodbye'
            },
            'action': 'small_talk',
            'requires_followup': False
        }

