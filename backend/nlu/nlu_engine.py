"""
Main NLU Engine for Voxa
Orchestrates intent classification, entity extraction, and action routing
"""

from typing import Dict, Optional
import os
import re
import pickle

from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor
from .context_manager import ContextManager
from .sentiment import SentimentAnalyzer

# Action handlers live in the sibling ``actions`` package. Support being
# imported either as a top-level package (``backend`` on sys.path) or as a
# sub-package, without depending on how the server is launched.
try:  # pragma: no cover - import strategy
    from actions.weather_handler import WeatherHandler
    from actions.search_handler import SearchHandler
    from actions.knowledge_base_handler import KnowledgeBaseHandler
    from actions.smalltalk_handler import SmallTalkHandler
    from actions.datetime_handler import DateTimeHandler
    from actions.calculator_handler import CalculatorHandler
    from actions.unit_handler import UnitConverterHandler
    from actions.smarthome_handler import SmartHomeHandler
except ImportError:  # pragma: no cover
    from ..actions.weather_handler import WeatherHandler
    from ..actions.search_handler import SearchHandler
    from ..actions.knowledge_base_handler import KnowledgeBaseHandler
    from ..actions.smalltalk_handler import SmallTalkHandler
    from ..actions.datetime_handler import DateTimeHandler
    from ..actions.calculator_handler import CalculatorHandler
    from ..actions.unit_handler import UnitConverterHandler
    from ..actions.smarthome_handler import SmartHomeHandler


class NLUEngine:
    """
    Main NLU Engine that coordinates all NLU components
    """
    
    def __init__(self, model_path: Optional[str] = None):
        # Initialize NLU components
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.context_manager = ContextManager()
        self.sentiment_analyzer = SentimentAnalyzer()

        # Initialize action handlers
        self.action_handlers = {
            'weather': WeatherHandler(),
            'web_search': SearchHandler(),
            'knowledge_base': KnowledgeBaseHandler(),
            'small_talk': SmallTalkHandler(),
            'datetime': DateTimeHandler(),
            'calculator': CalculatorHandler(),
            'unit_conversion': UnitConverterHandler(),
            'smart_home': SmartHomeHandler(),
        }

        # Short follow-up phrases that should inherit the previous intent
        self._followup_re = re.compile(
            r'^\s*(and|what about|how about|also|then)\b|\b(too|as well|there)\s*\??\s*$',
            re.IGNORECASE,
        )
        
        # Train or load model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.train_default_model()
    
    def train_default_model(self):
        """Train the intent classifier with default data"""
        try:
            self.intent_classifier.train()
            print("✅ NLU model trained successfully")
        except Exception as e:
            print(f"⚠️  Model training warning: {e}")
    
    def process(self, text: str, session_id: str, user_id: str = None) -> Dict:
        """
        Process user input through the complete NLU pipeline
        
        Args:
            text: User input text
            session_id: Session identifier
            user_id: Optional user identifier
        
        Returns:
            Complete NLU response with intent, entities, and action result
        """
        # Get or create session
        session = self.context_manager.get_session(session_id)
        if not session:
            session = self.context_manager.create_session(session_id, user_id)
        
        # Get context
        context = self.context_manager.get_context(session_id)
        context['original_text'] = text
        
        # Resolve coreferences using context
        resolved_text = self.context_manager.resolve_coreference(session_id, text)

        # Sentiment of the user's message
        sentiment = self.sentiment_analyzer.analyze(text)

        # Step 1: Intent Classification
        intent_result = self.intent_classifier.classify(resolved_text)

        # Follow-up inheritance: short phrases like "and tomorrow?" or
        # "what about Paris?" keep the previous intent for continuity.
        last_intent = context.get('last_intent')
        if (last_intent and last_intent in self.action_handlers
                and self._followup_re.search(text)
                and (intent_result['intent'] in ('unknown', 'small_talk')
                     or intent_result['confidence'] < 0.5)):
            intent_result = {
                'intent': last_intent,
                'confidence': max(intent_result['confidence'], 0.6),
                'all_scores': intent_result.get('all_scores', {}),
                'method': 'context-followup',
                'metadata': self.intent_classifier.intent_metadata.get(last_intent, {}),
            }

        # Step 2: Entity Extraction
        entity_result = self.entity_extractor.extract(resolved_text, intent_result['intent'])
        
        # Step 3: Check if clarification is needed
        needs_clarification = self.context_manager.should_clarify(
            session_id, intent_result, entity_result
        )
        
        if needs_clarification:
            clarification_prompt = self.context_manager.get_clarification_prompt(
                session_id, intent_result, entity_result
            )
            
            response = {
                'success': True,
                'response': clarification_prompt,
                'data': {},
                'action': 'clarification',
                'requires_followup': True
            }
        else:
            # Step 4: Route to appropriate action handler
            response = self.route_to_action(intent_result, entity_result, context)
        
        # Step 5: Update context
        turn_data = {
            'user_input': text,
            'intent': intent_result,
            'entities': entity_result,
            'response': response['response'],
            'action': response.get('action')
        }
        
        self.context_manager.update_session(session_id, turn_data)
        
        # Step 6: Compile complete response
        complete_response = {
            'text': text,
            'resolved_text': resolved_text,
            'intent': intent_result,
            'entities': entity_result,
            'sentiment': sentiment,
            'response': response['response'],
            'action_result': response,
            'session_id': session_id,
            'context': {
                'location': context.get('location'),
                'last_intent': intent_result['intent']
            },
            'metadata': {
                'needs_clarification': needs_clarification,
                'confidence': intent_result['confidence'],
                'processing_method': intent_result['method']
            }
        }

        return complete_response
    
    def route_to_action(self, intent_result: Dict, entity_result: Dict, context: Dict) -> Dict:
        """
        Route the request to the appropriate action handler
        
        Args:
            intent_result: Intent classification result
            entity_result: Entity extraction result
            context: Conversation context
        
        Returns:
            Action handler response
        """
        intent = intent_result['intent']

        # Intent names map 1:1 to action-handler keys.
        if intent in self.action_handlers:
            return self.action_handlers[intent].handle(entity_result, context)

        # Unknown intent: give a genuinely useful, capability-aware reply
        # instead of a dead end.
        suggestions = (
            "I'm not sure I caught that. Here's what I can help with:\n\n"
            "🕐 **Time & date** — \"what time is it?\"\n"
            "🧮 **Math** — \"calculate 15% of 240\"\n"
            "📐 **Conversions** — \"convert 10 km to miles\"\n"
            "🌤️ **Weather** — \"weather in Tokyo\"\n"
            "🔍 **Web search** — \"search for the James Webb telescope\"\n"
            "📚 **About me** — \"what can you do?\"\n\n"
            "Try rephrasing, or ask one of the above."
        )
        return {
            'success': False,
            'response': suggestions,
            'data': {'suggestions': True},
            'action': 'unknown',
            'requires_followup': True,
        }
    
    def add_training_data(self, intent: str, utterances: list):
        """Add new training utterances for an intent"""
        self.intent_classifier.add_training_utterances(intent, utterances)
    
    def retrain(self):
        """Retrain the intent classifier"""
        self.intent_classifier.train()
        return True
    
    def get_intents(self) -> Dict:
        """Get all available intents with metadata"""
        return self.intent_classifier.intent_metadata
    
    def get_training_data(self) -> Dict:
        """Get current training data"""
        return dict(self.intent_classifier.training_data)
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        self.intent_classifier.save_model(filepath)
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        self.intent_classifier.load_model(filepath)
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        return self.context_manager.get_session_stats(session_id)
    
    def cleanup_sessions(self):
        """Clean up expired sessions"""
        return self.context_manager.cleanup_expired_sessions()

