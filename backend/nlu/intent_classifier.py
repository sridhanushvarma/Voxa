"""
Intent Classification Engine for Voxa
Hybrid classifier: calibrated ML (word + char TF-IDF -> Logistic Regression)
blended with rule-based pattern scoring and a fuzzy-match fallback so short
or misspelled inputs still resolve sensibly. Fully offline.
"""

import re
import pickle
from difflib import SequenceMatcher
from typing import Dict, List
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion

import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


def _ensure_nltk():
    """Download required NLTK corpora lazily and quietly."""
    for path, pkg in [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
        ('corpora/wordnet', 'wordnet'),
        ('corpora/omw-1.4', 'omw-1.4'),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass


_ensure_nltk()


class IntentClassifier:
    """Multi-strategy intent classifier with calibrated confidence scoring."""

    def __init__(self):
        try:
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.lemmatizer = None
            self.stop_words = set()

        self.ml_classifier = None
        self.intent_patterns = {}
        self.training_data = defaultdict(list)
        self.intent_metadata = {}
        self._initialize_default_intents()

    # ------------------------------------------------------------------ data
    def _initialize_default_intents(self):
        self.add_intent_pattern('weather', [
            r'\b(weather|temperature|forecast|rain|raining|snow|snowing|sunny|cloudy|humidity|wind)\b',
            r'\b(hot|cold|warm|cool|freezing)\s+(today|tomorrow|tonight|outside)',
            r'\b(will it|is it going to|gonna)\s+(rain|snow)\b',
        ])
        self.add_training_utterances('weather', [
            "What's the weather like?", "How's the weather today?",
            "Will it rain tomorrow?", "What's the temperature?",
            "Is it going to snow?", "Weather forecast for today",
            "Tell me the weather", "What's the forecast?",
            "Is it sunny outside?", "How hot is it in London?",
            "Weather in Tokyo", "Do I need an umbrella today?",
            "Is it cold outside?", "What's the humidity right now?",
        ])

        self.add_intent_pattern('web_search', [
            r'\b(search|google|find|look up|lookup|browse)\b',
            r'\b(who is|who was|what is|what are|where is|when is|why is|how is)\b',
            r'\b(tell me about|information about|info on|read about|news about)\b',
        ])
        self.add_training_utterances('web_search', [
            "Search for Python tutorials", "Google machine learning",
            "Find information about AI", "Look up quantum computing",
            "Who is Elon Musk?", "What is blockchain?",
            "Tell me about climate change", "Search the web for recipes",
            "Find news about space", "Look up the capital of France",
            "Who won the world cup?", "What is the speed of light?",
        ])

        self.add_intent_pattern('knowledge_base', [
            r'\b(what can you do|your capabilities|what are you able|features)\b',
            r'\b(how do i use|how to use|help|commands|guide|tutorial)\b',
            r'\b(who are you|what are you|about you|your name)\b',
            r'\b(explain|describe|define)\b',
        ])
        self.add_training_utterances('knowledge_base', [
            "What can you do?", "Help me", "Show me commands",
            "What are your capabilities?", "How do I use this?",
            "Explain machine learning", "What is NLP?", "Who are you?",
            "What is your name?", "Tell me about yourself",
            "How do you work?", "What features do you have?",
        ])

        self.add_intent_pattern('small_talk', [
            r'\b(hello|hi|hey|yo|greetings|good morning|good afternoon|good evening|howdy)\b',
            r'\b(how are you|how(\'s| is) it going|what\'s up|wassup|sup)\b',
            r'\b(thank you|thanks|thank u|appreciate|cheers)\b',
            r'\b(bye|goodbye|see you|see ya|farewell|good night|cya)\b',
            r'\b(joke|make me laugh|something funny|tell me a joke)\b',
            r'\b(nice|great job|awesome|cool|well done|love you)\b',
        ])
        self.add_training_utterances('small_talk', [
            "Hello", "Hi there", "Hey", "How are you?", "What's up?",
            "Thank you", "Thanks a lot", "Goodbye", "See you later",
            "That's great", "Tell me a joke", "You're awesome",
            "Good morning", "Good night", "Nice to meet you",
            "How's it going?", "Make me laugh",
        ])

        self.add_intent_pattern('smart_home', [
            r'\b(turn on|turn off|switch on|switch off|dim|brighten)\b.*\b(light|lights|lamp|fan|ac)\b',
            r'\b(set|adjust|change|raise|lower)\b.*\b(temperature|thermostat|volume)\b',
            r'\b(lock|unlock|open|close)\b.*\b(door|doors|garage|gate)\b',
        ])
        self.add_training_utterances('smart_home', [
            "Turn on the lights", "Switch off the bedroom light",
            "Set temperature to 72 degrees", "Lock the front door",
            "Dim the living room lights", "Turn off the fan",
            "Unlock the garage", "Lower the thermostat",
        ])

        self.add_intent_pattern('datetime', [
            r'\bwhat(\'s| is) the (time|date)\b',
            r'\bwhat (time|day|date) is it\b',
            r'\b(current|today\'s) (time|date)\b',
            r'\bwhat day is (it|today|tomorrow)\b',
            r'\b(time|date) (right )?now\b',
            r'\bwhat\'s today\b',
        ])
        self.add_training_utterances('datetime', [
            "What time is it?", "What's the time?", "What's the date today?",
            "What day is it?", "Tell me the time", "Current date please",
            "What is today's date?", "What day is tomorrow?",
            "Give me the time", "What's today?", "Is it Monday?",
            "What time is it right now?",
        ])

        self.add_intent_pattern('calculator', [
            r'\bcalculate\b|\bcompute\b|\bevaluate\b|\bsolve\b',
            r'\d+\s*(plus|minus|times|divided by|x|\+|\-|\*|/|\^)\s*\d+',
            r'\bwhat(\'s| is)\s+\d',
            r'\b(square root|sqrt|factorial|percent|% of)\b',
            r'\bhow much is\b.*\d',
        ])
        self.add_training_utterances('calculator', [
            "Calculate 5 plus 3", "What is 12 times 4?",
            "What's 100 divided by 4?", "Compute 2 to the power of 10",
            "Square root of 144", "What is 15% of 200?",
            "How much is 45 minus 17?", "Solve 7 * (3 + 2)",
            "What's 9 squared?", "Evaluate 3.5 + 2.1",
            "10 plus 20 minus 5", "What is 2 + 2?",
        ])

        self.add_intent_pattern('unit_conversion', [
            r'\bconvert\b.*\b(to|in|into)\b',
            r'\d+\s*(km|m|cm|mm|mi|miles?|ft|feet|inch|inches|yards?|kg|g|mg|lb|lbs|pounds?|oz|ounces?|c|f|k|celsius|fahrenheit|kelvin|mph|kmh|kph|gb|mb|kb|tb)\b.*\b(to|in|into)\b',
            r'\bhow many\b.*\b(in|per)\b',
        ])
        self.add_training_utterances('unit_conversion', [
            "Convert 10 km to miles", "5 kg in pounds",
            "100 F to C", "How many cm in a meter?",
            "Convert 32 fahrenheit to celsius", "2 miles to kilometers",
            "Convert 1 gb to mb", "60 mph in kmh",
            "Convert 3 hours to minutes", "10 inches to cm",
        ])

        self.intent_metadata = {
            'weather': {'description': 'Weather and forecast queries',
                        'requires_location': True, 'action': 'weather', 'icon': '🌤️'},
            'web_search': {'description': 'Web search and information lookup',
                           'requires_query': True, 'action': 'web_search', 'icon': '🔍'},
            'knowledge_base': {'description': 'Built-in knowledge & capabilities',
                               'requires_query': False, 'action': 'knowledge_base', 'icon': '📚'},
            'small_talk': {'description': 'Casual conversation and greetings',
                           'requires_query': False, 'action': 'small_talk', 'icon': '💬'},
            'smart_home': {'description': 'Smart home device control (simulated)',
                           'requires_device': True, 'action': 'smart_home', 'icon': '🏠'},
            'datetime': {'description': 'Current time, date and weekday',
                         'requires_query': False, 'action': 'datetime', 'icon': '🕐'},
            'calculator': {'description': 'Arithmetic and math evaluation',
                           'requires_query': False, 'action': 'calculator', 'icon': '🧮'},
            'unit_conversion': {'description': 'Convert between units',
                                'requires_query': False, 'action': 'unit_conversion', 'icon': '📐'},
        }

    # ------------------------------------------------------------- utilities
    def preprocess_text(self, text: str) -> str:
        text = text.lower()
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
        cleaned = []
        for tok in tokens:
            if not tok.isalnum() or tok in self.stop_words:
                continue
            cleaned.append(self.lemmatizer.lemmatize(tok) if self.lemmatizer else tok)
        result = ' '.join(cleaned)
        return result if result.strip() else text  # never return empty

    def add_intent_pattern(self, intent: str, patterns: List[str]):
        self.intent_patterns.setdefault(intent, []).extend(patterns)

    def add_training_utterances(self, intent: str, utterances: List[str]):
        self.training_data[intent].extend(utterances)

    # -------------------------------------------------------------- training
    def train(self):
        if not self.training_data:
            raise ValueError("No training data available")

        X, y = [], []
        for intent, utterances in self.training_data.items():
            for utt in utterances:
                X.append(self.preprocess_text(utt))
                y.append(intent)

        self.ml_classifier = Pipeline([
            ('features', FeatureUnion([
                ('word', TfidfVectorizer(analyzer='word', ngram_range=(1, 2),
                                         sublinear_tf=True, min_df=1)),
                ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4),
                                         sublinear_tf=True, min_df=1)),
            ])),
            ('clf', LogisticRegression(max_iter=1000, C=8.0,
                                       class_weight='balanced')),
        ])
        self.ml_classifier.fit(X, y)
        return True

    # ------------------------------------------------------------ inference
    def classify_with_rules(self, text: str) -> Dict[str, float]:
        text_lower = text.lower()
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            hits = sum(1 for p in patterns if re.search(p, text_lower))
            if hits:
                scores[intent] = min(0.55 + 0.25 * hits, 1.0)
        return scores

    def classify_with_ml(self, text: str) -> Dict[str, float]:
        if self.ml_classifier is None:
            return {}
        proba = self.ml_classifier.predict_proba([self.preprocess_text(text)])[0]
        return dict(zip(self.ml_classifier.classes_, proba.astype(float)))

    def classify_with_fuzzy(self, text: str) -> Dict[str, float]:
        """Fallback: best fuzzy ratio against training utterances."""
        text_lower = text.lower().strip()
        if not text_lower:
            return {}
        best = {}
        for intent, utterances in self.training_data.items():
            top = 0.0
            for utt in utterances:
                r = SequenceMatcher(None, text_lower, utt.lower()).ratio()
                top = max(top, r)
            if top >= 0.6:
                best[intent] = top
        return best

    def classify(self, text: str, threshold: float = 0.35) -> Dict:
        rule_scores = self.classify_with_rules(text)
        ml_scores = self.classify_with_ml(text)
        fuzzy_scores = self.classify_with_fuzzy(text)

        all_intents = set(rule_scores) | set(ml_scores) | set(fuzzy_scores)
        combined = {}
        for intent in all_intents:
            r = rule_scores.get(intent, 0.0)
            m = ml_scores.get(intent, 0.0)
            f = fuzzy_scores.get(intent, 0.0)
            if ml_scores:
                score = 0.55 * m + 0.30 * r + 0.15 * f
                # Strong rule + ML agreement boosts confidence
                if r > 0 and m >= 0.4:
                    score = min(1.0, score + 0.15)
            else:
                score = max(r, f)
            combined[intent] = round(float(score), 4)

        if combined:
            intent_name, confidence = max(combined.items(), key=lambda kv: kv[1])
            if confidence < threshold:
                intent_name, confidence = 'unknown', confidence
        else:
            intent_name, confidence = 'unknown', 0.0

        return {
            'intent': intent_name,
            'confidence': float(confidence),
            'all_scores': combined,
            'method': 'hybrid' if ml_scores else 'rule+fuzzy',
            'metadata': self.intent_metadata.get(intent_name, {}),
        }

    # ----------------------------------------------------------- persistence
    def save_model(self, filepath: str):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'ml_classifier': self.ml_classifier,
                'intent_patterns': self.intent_patterns,
                'training_data': dict(self.training_data),
                'intent_metadata': self.intent_metadata,
            }, f)

    def load_model(self, filepath: str):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        self.ml_classifier = data['ml_classifier']
        self.intent_patterns = data['intent_patterns']
        self.training_data = defaultdict(list, data['training_data'])
        self.intent_metadata = data['intent_metadata']
