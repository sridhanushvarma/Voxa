"""
Knowledge Base Action Handler
Handles queries about system capabilities and internal knowledge
"""

from typing import Dict, List
import json


class KnowledgeBaseHandler:
    """
    Handles knowledge base queries
    """
    
    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> Dict:
        """Initialize the knowledge base with default content"""
        return {
            'capabilities': {
                'question': 'What can you do?',
                'answer': """I'm Voxa, your voice-enabled smart assistant! Here's what I can help you with:

🌤️ **Weather**: Get current weather and forecasts for any location
🔍 **Web Search**: Search for information on any topic
💬 **Conversation**: Chat with me about various topics
🏠 **Smart Home** (Coming Soon): Control your smart devices
🌍 **Multilingual** (Coming Soon): Support for multiple languages

Just ask me anything, and I'll do my best to help!""",
                'keywords': ['capabilities', 'what can you do', 'help', 'features', 'commands']
            },
            'weather_help': {
                'question': 'How do I check weather?',
                'answer': """To check the weather, you can ask me questions like:
- "What's the weather in New York?"
- "Will it rain tomorrow?"
- "How's the weather today?"
- "Temperature in San Francisco"

I'll provide current conditions, temperature, humidity, and wind information!""",
                'keywords': ['weather help', 'how to check weather', 'weather commands']
            },
            'search_help': {
                'question': 'How do I search?',
                'answer': """To search for information, try:
- "Search for Python tutorials"
- "What is machine learning?"
- "Tell me about climate change"
- "Who is Albert Einstein?"

I'll search the web and provide you with relevant information!""",
                'keywords': ['search help', 'how to search', 'search commands']
            },
            'voice_help': {
                'question': 'How do I use voice?',
                'answer': """Voice features:
🎤 **Voice Input**: Click the microphone button to speak your query
🔊 **Voice Output**: Toggle the speaker button to hear responses
🗣️ **Natural Speech**: Just speak naturally, I'll understand!

Make sure your browser has microphone permissions enabled.""",
                'keywords': ['voice help', 'how to use voice', 'microphone', 'speech']
            },
            'about': {
                'question': 'What is Voxa?',
                'answer': """Voxa is an advanced voice-enabled smart chatbot with:
- Natural Language Understanding (NLU)
- Intent recognition with confidence scores
- Entity extraction
- Multi-turn conversation context
- Voice input and output
- Real-time responses

Built with Flask, React, and modern NLP technologies!""",
                'keywords': ['about', 'what is voxa', 'about voxa', 'info']
            },
            'privacy': {
                'question': 'How is my data handled?',
                'answer': """Your privacy is important:
- Conversations are stored temporarily for context
- Sessions expire after 30 minutes of inactivity
- No personal data is shared with third parties
- Voice data is processed locally when possible
- You can clear your session anytime""",
                'keywords': ['privacy', 'data', 'security', 'personal information']
            },
            'machine_learning': {
                'question': 'What is machine learning?',
                'answer': """Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. 

Key concepts:
- **Supervised Learning**: Learning from labeled data
- **Unsupervised Learning**: Finding patterns in unlabeled data
- **Neural Networks**: Models inspired by the human brain
- **Deep Learning**: Advanced neural networks with multiple layers

ML powers many modern applications like voice assistants, recommendation systems, and autonomous vehicles!""",
                'keywords': ['machine learning', 'ml', 'artificial intelligence', 'ai']
            },
            'natural_language_processing': {
                'question': 'What is NLP?',
                'answer': """Natural Language Processing (NLP) is a field of AI that helps computers understand, interpret, and generate human language.

Key NLP tasks:
- **Intent Recognition**: Understanding what the user wants
- **Entity Extraction**: Identifying important information (names, dates, locations)
- **Sentiment Analysis**: Determining emotional tone
- **Text Classification**: Categorizing text into topics
- **Machine Translation**: Converting between languages

I use NLP to understand your questions and provide relevant answers!""",
                'keywords': ['nlp', 'natural language processing', 'language understanding']
            }
        }
    
    def search_knowledge_base(self, query: str) -> Dict:
        """Search the knowledge base for relevant information"""
        query_lower = query.lower()
        
        # Find best match
        best_match = None
        best_score = 0
        
        for key, item in self.knowledge_base.items():
            score = 0
            
            # Check keywords
            for keyword in item['keywords']:
                if keyword in query_lower:
                    score += 2
            
            # Check question similarity
            if any(word in query_lower for word in item['question'].lower().split()):
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = item
        
        return best_match if best_score > 0 else None
    
    def get_all_topics(self) -> List[str]:
        """Get list of all available topics"""
        return [item['question'] for item in self.knowledge_base.values()]
    
    def add_knowledge(self, key: str, question: str, answer: str, keywords: List[str]):
        """Add new knowledge to the base"""
        self.knowledge_base[key] = {
            'question': question,
            'answer': answer,
            'keywords': keywords
        }
    
    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        """
        Main handler for knowledge base queries
        
        Args:
            entities: Extracted entities
            context: Conversation context
        
        Returns:
            Response dictionary
        """
        # Get query from entities or use original text
        query = entities.get('normalized', {}).get('query', '')
        
        # Search knowledge base
        result = self.search_knowledge_base(query)
        
        if result:
            response_text = result['answer']
            success = True
        else:
            # Provide general help
            response_text = self.knowledge_base['capabilities']['answer']
            success = True
        
        return {
            'success': success,
            'response': response_text,
            'data': {
                'matched_topic': result['question'] if result else 'General Help',
                'available_topics': self.get_all_topics()
            },
            'action': 'knowledge_base_query',
            'requires_followup': False
        }

