"""
Unit Conversion Action Handler
Offline conversions for length, mass, temperature, speed, data and time.
Understands "convert 10 km to miles", "5 kg in pounds", "100 F to C".
"""

import re
from typing import Dict, Optional, Tuple


# Conversion factors expressed relative to a base unit per category.
_LENGTH = {  # base: metre
    'm': 1.0, 'meter': 1.0, 'meters': 1.0, 'metre': 1.0,
    'km': 1000.0, 'kilometer': 1000.0, 'kilometers': 1000.0,
    'cm': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
    'mm': 0.001, 'millimeter': 0.001,
    'mi': 1609.344, 'mile': 1609.344, 'miles': 1609.344,
    'yd': 0.9144, 'yard': 0.9144, 'yards': 0.9144,
    'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
    'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254,
}
_MASS = {  # base: kilogram
    'kg': 1.0, 'kilogram': 1.0, 'kilograms': 1.0,
    'g': 0.001, 'gram': 0.001, 'grams': 0.001,
    'mg': 1e-6, 'milligram': 1e-6,
    't': 1000.0, 'tonne': 1000.0, 'ton': 1000.0,
    'lb': 0.45359237, 'lbs': 0.45359237, 'pound': 0.45359237, 'pounds': 0.45359237,
    'oz': 0.0283495, 'ounce': 0.0283495, 'ounces': 0.0283495,
}
_SPEED = {  # base: metre/second
    'mps': 1.0, 'm/s': 1.0,
    'kmh': 0.277778, 'kph': 0.277778, 'km/h': 0.277778,
    'mph': 0.44704, 'knot': 0.514444, 'knots': 0.514444,
}
_DATA = {  # base: byte
    'b': 1.0, 'byte': 1.0, 'bytes': 1.0,
    'kb': 1024.0, 'mb': 1024.0 ** 2, 'gb': 1024.0 ** 3,
    'tb': 1024.0 ** 4, 'bit': 0.125, 'bits': 0.125,
}
_TIME = {  # base: second
    's': 1.0, 'sec': 1.0, 'second': 1.0, 'seconds': 1.0,
    'min': 60.0, 'minute': 60.0, 'minutes': 60.0,
    'h': 3600.0, 'hr': 3600.0, 'hour': 3600.0, 'hours': 3600.0,
    'day': 86400.0, 'days': 86400.0, 'week': 604800.0, 'weeks': 604800.0,
}
_CATEGORIES = [
    ('length', _LENGTH), ('mass', _MASS), ('speed', _SPEED),
    ('data', _DATA), ('time', _TIME),
]
_TEMP = {'c', 'celsius', 'f', 'fahrenheit', 'k', 'kelvin'}


class UnitConverterHandler:
    """Handles unit conversion queries offline."""

    def _convert_temp(self, value: float, frm: str, to: str) -> Optional[float]:
        frm, to = frm[0], to[0]  # c/f/k
        if frm == 'c':
            celsius = value
        elif frm == 'f':
            celsius = (value - 32) * 5 / 9
        elif frm == 'k':
            celsius = value - 273.15
        else:
            return None
        if to == 'c':
            return celsius
        if to == 'f':
            return celsius * 9 / 5 + 32
        if to == 'k':
            return celsius + 273.15
        return None

    def _convert(self, value: float, frm: str, to: str) -> Tuple[Optional[float], str]:
        frm, to = frm.lower(), to.lower()
        if frm in _TEMP and to in _TEMP:
            return self._convert_temp(value, frm, to), 'temperature'
        for name, table in _CATEGORIES:
            if frm in table and to in table:
                return value * table[frm] / table[to], name
        return None, ''

    def parse(self, text: str):
        m = re.search(
            r'(-?\d+(?:\.\d+)?)\s*([a-z/°]+)\s*(?:to|in|into|=|as)\s*([a-z/°]+)',
            text.lower(),
        )
        if not m:
            return None
        value = float(m.group(1))
        frm = m.group(2).replace('°', '').strip()
        to = m.group(3).replace('°', '').strip()
        return value, frm, to

    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        text = (context or {}).get('original_text', '')
        parsed = self.parse(text)

        if not parsed:
            return {
                'success': False,
                'response': ("Tell me what to convert, e.g. "
                             "\"convert 10 km to miles\" or \"100 F to C\"."),
                'data': {},
                'action': 'unit_conversion',
                'requires_followup': True,
            }

        value, frm, to = parsed
        result, category = self._convert(value, frm, to)

        if result is None:
            return {
                'success': False,
                'response': (f"I can't convert {frm} to {to}. I support length, "
                             "mass, temperature, speed, data and time units."),
                'data': {},
                'action': 'unit_conversion',
                'requires_followup': True,
            }

        rounded = int(result) if float(result).is_integer() else round(result, 4)
        return {
            'success': True,
            'response': f"{value:g} {frm} = {rounded} {to}.",
            'data': {'value': value, 'from': frm, 'to': to,
                     'result': rounded, 'category': category},
            'action': 'unit_conversion',
            'requires_followup': False,
        }
