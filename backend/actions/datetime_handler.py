"""
Date & Time Action Handler
Answers questions about the current time, date, weekday and simple date math.
"""

from typing import Dict
from datetime import datetime, timedelta


WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']


class DateTimeHandler:
    """Handles time / date queries entirely offline using the server clock."""

    def _ordinal(self, n: int) -> str:
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        text = (context or {}).get('original_text', '').lower()
        now = datetime.now()

        wants_date = any(w in text for w in
                         ['date', 'day', 'today', 'month', 'year', 'weekday'])
        wants_time = any(w in text for w in
                         ['time', 'clock', 'hour', "o'clock", 'now'])

        date_str = (
            f"{WEEKDAYS[now.weekday()]}, "
            f"{now.strftime('%B')} {self._ordinal(now.day)}, {now.year}"
        )
        time_str = now.strftime('%I:%M %p').lstrip('0')

        if 'tomorrow' in text:
            d = now + timedelta(days=1)
            response = (f"Tomorrow is {WEEKDAYS[d.weekday()]}, "
                        f"{d.strftime('%B')} {self._ordinal(d.day)}, {d.year}.")
        elif 'yesterday' in text:
            d = now - timedelta(days=1)
            response = (f"Yesterday was {WEEKDAYS[d.weekday()]}, "
                        f"{d.strftime('%B')} {self._ordinal(d.day)}, {d.year}.")
        elif wants_time and not wants_date:
            response = f"It's currently {time_str}."
        elif wants_date and not wants_time:
            response = f"Today is {date_str}."
        else:
            response = f"It's {time_str} on {date_str}."

        return {
            'success': True,
            'response': response,
            'data': {
                'iso': now.isoformat(),
                'date': now.strftime('%Y-%m-%d'),
                'time': now.strftime('%H:%M:%S'),
                'weekday': WEEKDAYS[now.weekday()],
            },
            'action': 'datetime_query',
            'requires_followup': False,
        }
