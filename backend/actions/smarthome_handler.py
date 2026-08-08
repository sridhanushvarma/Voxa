"""
Smart Home Action Handler (simulated)
Maintains an in-memory virtual home so device commands feel responsive
without requiring any real hardware or external service.
"""

import re
from typing import Dict


class SmartHomeHandler:
    """Simulated smart-home controller."""

    def __init__(self):
        self.state = {
            'lights': {'living room': False, 'bedroom': False, 'kitchen': False},
            'thermostat': 72,
            'door': 'locked',
            'fan': False,
        }

    def _room(self, text: str) -> str:
        for room in self.state['lights']:
            if room in text or room.replace(' ', '') in text:
                return room
        if 'bedroom' in text:
            return 'bedroom'
        if 'kitchen' in text:
            return 'kitchen'
        return 'living room'

    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        text = (context or {}).get('original_text', '').lower()

        if re.search(r'\b(turn on|switch on|enable)\b.*\b(light|lights|lamp)\b', text):
            room = self._room(text)
            self.state['lights'][room] = True
            resp = f"💡 Turned on the {room} lights."
        elif re.search(r'\b(turn off|switch off|disable)\b.*\b(light|lights|lamp)\b', text):
            room = self._room(text)
            self.state['lights'][room] = False
            resp = f"💡 Turned off the {room} lights."
        elif re.search(r'\b(turn on|switch on)\b.*\bfan\b', text):
            self.state['fan'] = True
            resp = "🌀 Fan is now on."
        elif re.search(r'\b(turn off|switch off)\b.*\bfan\b', text):
            self.state['fan'] = False
            resp = "🌀 Fan is now off."
        elif re.search(r'\b(lock)\b.*\bdoor\b', text):
            self.state['door'] = 'locked'
            resp = "🔒 Front door locked."
        elif re.search(r'\b(unlock|open)\b.*\bdoor\b', text):
            self.state['door'] = 'unlocked'
            resp = "🔓 Front door unlocked."
        else:
            m = re.search(r'(\d{2,3})\s*(?:degrees?|°)?', text)
            if m and ('temperature' in text or 'thermostat' in text or 'set' in text):
                self.state['thermostat'] = int(m.group(1))
                resp = f"🌡️ Thermostat set to {self.state['thermostat']}°."
            else:
                resp = ("I can control lights, the fan, the thermostat and the "
                        "door. Try \"turn on the bedroom lights\".")

        return {
            'success': True,
            'response': resp,
            'data': {'state': self.state},
            'action': 'smart_home',
            'requires_followup': False,
        }
