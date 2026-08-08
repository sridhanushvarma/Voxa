"""
Entity Extraction Engine for Voxa
Extracts entities like locations, dates, times, numbers, etc.
"""

import re
from typing import Dict, List
from datetime import datetime, timedelta
import nltk
from nltk import pos_tag, ne_chunk
from nltk.tokenize import word_tokenize

# Download optional NLTK data lazily; the extractor degrades gracefully if any
# corpus is unavailable (regex extraction still works fully offline).
for _path, _pkg in [
    ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
    ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
    ('chunkers/maxent_ne_chunker', 'maxent_ne_chunker'),
    ('chunkers/maxent_ne_chunker_tab', 'maxent_ne_chunker_tab'),
    ('corpora/words', 'words'),
    ('tokenizers/punkt', 'punkt'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
]:
    try:
        nltk.data.find(_path)
    except LookupError:
        try:
            nltk.download(_pkg, quiet=True)
        except Exception:
            pass


class EntityExtractor:
    """
    Multi-strategy entity extractor
    """
    
    def __init__(self):
        self.entity_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict:
        """Initialize regex patterns for common entities"""
        return {
            'location': [
                r'\b(?:in|at|for|near)\s+([A-Za-z][a-zA-Z]+(?:[\s-][A-Z][a-z]+)*)',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+weather',
                r'\bweather\s+(?:in|at|for)\s+([A-Za-z][a-zA-Z\s]+?)(?:\s+(?:today|tomorrow|now)|[?.!]|$)',
            ],
            'date': [
                r'\b(today|tomorrow|yesterday)\b',
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(next|last)\s+(week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b',
            ],
            'time': [
                r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',
                r'\b(morning|afternoon|evening|night|noon|midnight)\b',
                r'\bat\s+(\d{1,2})\s*(am|pm)\b',
            ],
            'number': [
                r'\b(\d+(?:\.\d+)?)\b',
                r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b',
            ],
            'temperature': [
                r'\b(\d+)\s*(?:degrees?|°)\s*(celsius|fahrenheit|c|f)?\b',
            ],
            'device': [
                r'\b(light|lights|lamp|thermostat|door|lock|camera|tv|television)\b',
                r'\b(bedroom|living room|kitchen|bathroom|garage)\s+(light|lights|lamp)\b',
            ],
            'query': [
                r'(?:search|google|find|look up|lookup)\s+(?:for\s+)?(.+)',
                r'(?:who|what|where|when|why|how)\s+(?:is|are|was|were)\s+(.+)',
                r'(?:tell me about|information about|info on)\s+(.+)',
            ]
        }
    
    def extract_with_patterns(self, text: str) -> Dict[str, List[Dict]]:
        """Extract entities using regex patterns"""
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            matches = []
            
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity_value = match.group(1) if match.groups() else match.group(0)
                    
                    matches.append({
                        'value': entity_value.strip(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.8,
                        'method': 'pattern'
                    })
            
            if matches:
                # Remove duplicates and sort by position
                unique_matches = []
                seen_values = set()
                
                for match in sorted(matches, key=lambda x: x['start']):
                    if match['value'].lower() not in seen_values:
                        unique_matches.append(match)
                        seen_values.add(match['value'].lower())
                
                entities[entity_type] = unique_matches
        
        return entities
    
    def extract_with_nltk(self, text: str) -> Dict[str, List[Dict]]:
        """Extract named entities using NLTK"""
        entities = {
            'person': [],
            'organization': [],
            'location': [],
            'gpe': []  # Geo-political entity
        }
        
        try:
            # Tokenize and tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Named entity recognition
            chunks = ne_chunk(pos_tags, binary=False)
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_type = chunk.label().lower()
                    entity_value = ' '.join(c[0] for c in chunk)
                    
                    if entity_type in entities:
                        entities[entity_type].append({
                            'value': entity_value,
                            'confidence': 0.7,
                            'method': 'nltk'
                        })
        except Exception as e:
            print(f"NLTK extraction error: {e}")
        
        # Remove empty entity types
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def normalize_date(self, date_str: str) -> str:
        """Normalize date strings to ISO format"""
        date_str_lower = date_str.lower()
        today = datetime.now()
        
        # Handle relative dates
        if date_str_lower == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str_lower == 'tomorrow':
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_str_lower == 'yesterday':
            return (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Handle day names
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if date_str_lower in days:
            target_day = days.index(date_str_lower)
            current_day = today.weekday()
            days_ahead = (target_day - current_day) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        return date_str
    
    def normalize_time(self, time_str: str) -> str:
        """Normalize time strings to 24-hour format"""
        time_str_lower = time_str.lower()
        
        # Handle named times
        time_map = {
            'morning': '09:00',
            'afternoon': '14:00',
            'evening': '18:00',
            'night': '21:00',
            'noon': '12:00',
            'midnight': '00:00'
        }
        
        if time_str_lower in time_map:
            return time_map[time_str_lower]
        
        # Handle HH:MM format
        match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str_lower)
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute}"
        
        return time_str
    
    def extract(self, text: str, intent: str = None) -> Dict:
        """
        Extract all entities from text
        
        Returns:
            {
                'entities': Dict[str, List[Dict]],
                'normalized': Dict[str, any],
                'count': int
            }
        """
        # Extract with patterns
        pattern_entities = self.extract_with_patterns(text)
        
        # Extract with NLTK
        nltk_entities = self.extract_with_nltk(text)
        
        # Merge entities
        all_entities = {}
        
        # Add pattern-based entities
        for entity_type, matches in pattern_entities.items():
            if entity_type not in all_entities:
                all_entities[entity_type] = []
            all_entities[entity_type].extend(matches)
        
        # Add NLTK entities (merge location and GPE)
        if 'location' in nltk_entities or 'gpe' in nltk_entities:
            if 'location' not in all_entities:
                all_entities['location'] = []
            
            all_entities['location'].extend(nltk_entities.get('location', []))
            all_entities['location'].extend(nltk_entities.get('gpe', []))
        
        for entity_type in ['person', 'organization']:
            if entity_type in nltk_entities:
                all_entities[entity_type] = nltk_entities[entity_type]
        
        # Normalize entities
        normalized = {}
        
        if 'date' in all_entities and all_entities['date']:
            normalized['date'] = self.normalize_date(all_entities['date'][0]['value'])
        
        if 'time' in all_entities and all_entities['time']:
            normalized['time'] = self.normalize_time(all_entities['time'][0]['value'])
        
        if 'location' in all_entities and all_entities['location']:
            normalized['location'] = all_entities['location'][0]['value']
        
        if 'temperature' in all_entities and all_entities['temperature']:
            normalized['temperature'] = all_entities['temperature'][0]['value']
        
        if 'device' in all_entities and all_entities['device']:
            normalized['device'] = all_entities['device'][0]['value']
        
        if 'query' in all_entities and all_entities['query']:
            normalized['query'] = all_entities['query'][0]['value']
        
        # Count total entities
        total_count = sum(len(matches) for matches in all_entities.values())
        
        return {
            'entities': all_entities,
            'normalized': normalized,
            'count': total_count
        }

