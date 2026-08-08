"""
Weather Action Handler
Retrieves weather information from external APIs
"""

import re
import requests
from typing import Dict, Optional
import os
from datetime import datetime


_LOC_STOPWORDS = {
    'the', 'today', 'tomorrow', 'tonight', 'now', 'currently', 'right',
    'this', 'morning', 'afternoon', 'evening', 'week', 'weekend', 'like',
    'whats', "what's", 'what', 'is', 'it', 'there', 'here', 'outside',
}


def extract_location(text: str) -> Optional[str]:
    """Pull a place name out of a weather query, ignoring filler words."""
    if not text:
        return None
    t = text.strip().rstrip('?.!')
    m = re.search(r'\b(?:in|at|for|near|of)\s+([A-Za-z][A-Za-z .\'-]+)$', t, re.I) \
        or re.search(r'\b(?:in|at|for|near|of)\s+([A-Za-z][A-Za-z .\'-]+?)'
                     r'(?:\s+(?:today|tomorrow|tonight|now|this|right))', t, re.I)
    if not m:
        return None
    words = [w for w in m.group(1).split() if w.lower() not in _LOC_STOPWORDS]
    location = ' '.join(words).strip()
    return location.title() if location else None


class WeatherHandler:
    """
    Handles weather-related queries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Use OpenWeatherMap API (free tier available)
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY', 'demo')
        self.base_url = 'https://api.openweathermap.org/data/2.5'
        
        # Fallback mock data for demo
        self.use_mock = (self.api_key == 'demo')
    
    def get_mock_weather(self, location: str) -> Dict:
        """Return mock weather data for demo purposes"""
        return {
            'location': location,
            'temperature': 72,
            'unit': 'F',
            'condition': 'Partly Cloudy',
            'humidity': 65,
            'wind_speed': 8,
            'forecast': 'Clear skies expected',
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }
    
    def get_current_weather(self, location: str, units: str = 'imperial') -> Dict:
        """
        Get current weather for a location
        
        Args:
            location: City name or coordinates
            units: 'imperial' (F) or 'metric' (C)
        
        Returns:
            Weather data dictionary
        """
        if self.use_mock:
            return self.get_mock_weather(location)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': units
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'location': data['name'],
                'temperature': round(data['main']['temp']),
                'unit': 'F' if units == 'imperial' else 'C',
                'condition': data['weather'][0]['description'].title(),
                'humidity': data['main']['humidity'],
                'wind_speed': round(data['wind']['speed']),
                'forecast': data['weather'][0]['main'],
                'timestamp': datetime.now().isoformat(),
                'source': 'openweathermap'
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Weather API error: {e}")
            return self.get_mock_weather(location)
        except Exception as e:
            print(f"Weather processing error: {e}")
            return self.get_mock_weather(location)
    
    def get_forecast(self, location: str, days: int = 3, units: str = 'imperial') -> Dict:
        """
        Get weather forecast for a location
        
        Args:
            location: City name
            days: Number of days (1-5)
            units: 'imperial' or 'metric'
        
        Returns:
            Forecast data dictionary
        """
        if self.use_mock:
            return {
                'location': location,
                'forecast': [
                    {'day': 'Today', 'temp_high': 75, 'temp_low': 62, 'condition': 'Sunny'},
                    {'day': 'Tomorrow', 'temp_high': 73, 'temp_low': 60, 'condition': 'Cloudy'},
                    {'day': 'Day 3', 'temp_high': 70, 'temp_low': 58, 'condition': 'Rainy'},
                ],
                'source': 'mock'
            }
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': units,
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Process forecast data
            daily_forecasts = []
            current_day = None
            day_data = {'temps': [], 'conditions': []}
            
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                day = dt.strftime('%A')
                
                if current_day != day:
                    if current_day is not None:
                        daily_forecasts.append({
                            'day': current_day,
                            'temp_high': max(day_data['temps']),
                            'temp_low': min(day_data['temps']),
                            'condition': max(set(day_data['conditions']), key=day_data['conditions'].count)
                        })
                    
                    current_day = day
                    day_data = {'temps': [], 'conditions': []}
                
                day_data['temps'].append(item['main']['temp'])
                day_data['conditions'].append(item['weather'][0]['main'])
            
            return {
                'location': data['city']['name'],
                'forecast': daily_forecasts[:days],
                'source': 'openweathermap'
            }
        
        except Exception as e:
            print(f"Forecast error: {e}")
            return self.get_forecast(location, days, units)  # Return mock
    
    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        """
        Main handler for weather queries
        
        Args:
            entities: Extracted entities
            context: Conversation context
        
        Returns:
            Response dictionary
        """
        # Prefer a location parsed directly from the user's phrasing, then
        # fall back to extracted entities, then conversation context.
        original_text = (context or {}).get('original_text', '')
        location = extract_location(original_text)

        if not location:
            location = entities.get('normalized', {}).get('location')

        if not location and context:
            location = context.get('location')

        if not location:
            location = 'New York'  # Default location
        
        # Get weather data
        weather_data = self.get_current_weather(location)
        
        # Format response
        response_text = (
            f"The weather in {weather_data['location']} is currently "
            f"{weather_data['temperature']}°{weather_data['unit']} and {weather_data['condition']}. "
            f"Humidity is {weather_data['humidity']}% with winds at {weather_data['wind_speed']} mph."
        )
        
        return {
            'success': True,
            'response': response_text,
            'data': weather_data,
            'action': 'weather_query',
            'requires_followup': False
        }

