"""
Web Search Action Handler
Performs web searches and returns summarized results
"""

import requests
from typing import Dict, List, Optional
import os
from bs4 import BeautifulSoup


class SearchHandler:
    """
    Handles web search queries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Use DuckDuckGo Instant Answer API (no key required) or Google Custom Search
        self.api_key = api_key or os.getenv('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        # Use DuckDuckGo as fallback (free, no API key)
        self.use_duckduckgo = not (self.api_key and self.search_engine_id)
    
    def search_duckduckgo(self, query: str) -> Dict:
        """Search using DuckDuckGo Instant Answer API"""
        try:
            url = 'https://api.duckduckgo.com/'
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            abstract = data.get('Abstract', '')
            answer = data.get('Answer', '')
            definition = data.get('Definition', '')
            
            # Get related topics
            related = []
            for topic in data.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and 'Text' in topic:
                    related.append(topic['Text'])
            
            # Combine results
            result_text = answer or abstract or definition or "No direct answer found."
            
            return {
                'query': query,
                'answer': result_text,
                'related': related,
                'source': 'DuckDuckGo',
                'url': data.get('AbstractURL', '')
            }
        
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return {
                'query': query,
                'answer': f"I found some information about {query}, but couldn't retrieve details at the moment.",
                'related': [],
                'source': 'fallback',
                'url': ''
            }
    
    def search_google(self, query: str) -> Dict:
        """Search using Google Custom Search API"""
        try:
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': 3
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get('items', [])[:3]:
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'url': item.get('link', '')
                })
            
            # Create summary
            if results:
                answer = results[0]['snippet']
                related = [r['title'] for r in results[1:]]
            else:
                answer = "No results found."
                related = []
            
            return {
                'query': query,
                'answer': answer,
                'related': related,
                'source': 'Google',
                'url': results[0]['url'] if results else '',
                'results': results
            }
        
        except Exception as e:
            print(f"Google search error: {e}")
            return self.search_duckduckgo(query)
    
    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        """
        Main handler for search queries
        
        Args:
            entities: Extracted entities
            context: Conversation context
        
        Returns:
            Response dictionary
        """
        # Get search query from entities
        query = entities.get('normalized', {}).get('query')
        
        if not query:
            # Try to extract from raw entities
            if 'query' in entities.get('entities', {}):
                query = entities['entities']['query'][0]['value']
        
        if not query:
            return {
                'success': False,
                'response': "I'm not sure what you want me to search for. Could you be more specific?",
                'data': {},
                'action': 'search_query',
                'requires_followup': True
            }
        
        # Perform search
        if self.use_duckduckgo:
            search_results = self.search_duckduckgo(query)
        else:
            search_results = self.search_google(query)
        
        # Format response
        response_text = f"Here's what I found about {query}: {search_results['answer']}"
        
        if search_results.get('related'):
            response_text += f"\n\nRelated topics: {', '.join(search_results['related'][:2])}"
        
        return {
            'success': True,
            'response': response_text,
            'data': search_results,
            'action': 'web_search',
            'requires_followup': False
        }

