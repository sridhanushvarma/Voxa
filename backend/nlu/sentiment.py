"""
Lexicon-based Sentiment Analyzer
Lightweight, offline, dependency-free. Handles negation and intensifiers.
"""

import re
from typing import Dict

_POSITIVE = {
    'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful',
    'love', 'loved', 'like', 'liked', 'happy', 'glad', 'pleased', 'perfect',
    'best', 'brilliant', 'cool', 'nice', 'helpful', 'thanks', 'thank', 'super',
    'enjoy', 'enjoyed', 'fun', 'beautiful', 'incredible', 'delighted', 'win',
}
_NEGATIVE = {
    'bad', 'terrible', 'awful', 'horrible', 'hate', 'hated', 'dislike', 'sad',
    'angry', 'upset', 'worst', 'poor', 'broken', 'useless', 'stupid', 'annoying',
    'frustrated', 'frustrating', 'disappointed', 'wrong', 'fail', 'failed',
    'slow', 'bug', 'buggy', 'crash', 'error', 'sucks', 'lame', 'boring',
}
_INTENSIFIERS = {'very', 'really', 'extremely', 'so', 'super', 'absolutely', 'totally'}
_NEGATIONS = {'not', 'no', "n't", 'never', 'without', 'hardly', 'barely'}


class SentimentAnalyzer:
    """Returns a polarity label with a normalized score in [-1, 1]."""

    def analyze(self, text: str) -> Dict:
        tokens = re.findall(r"[a-z']+", (text or '').lower())
        score = 0.0
        negate = False
        intensity = 1.0

        for tok in tokens:
            if tok in _NEGATIONS:
                negate = True
                continue
            if tok in _INTENSIFIERS:
                intensity = 1.6
                continue
            val = 0.0
            if tok in _POSITIVE:
                val = 1.0
            elif tok in _NEGATIVE:
                val = -1.0
            if val:
                if negate:
                    val = -val
                score += val * intensity
                negate = False
                intensity = 1.0

        norm = max(-1.0, min(1.0, score / 3.0))
        if norm > 0.15:
            label = 'positive'
        elif norm < -0.15:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'label': label,
            'score': round(norm, 3),
            'emoji': {'positive': '😊', 'negative': '😟', 'neutral': '😐'}[label],
        }
