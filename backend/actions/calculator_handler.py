"""
Calculator Action Handler
Safe arithmetic evaluation using an AST whitelist (no eval()).
Understands natural-language math like "what is 15% of 200" or
"5 plus 3 times 2" and "square root of 144".
"""

import ast
import math
import operator
import re
from typing import Dict


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_FUNCS = {
    'sqrt': math.sqrt, 'abs': abs, 'round': round,
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'log': math.log, 'log10': math.log10, 'exp': math.exp,
    'floor': math.floor, 'ceil': math.ceil, 'factorial': math.factorial,
    'pow': pow, 'max': max, 'min': min,
}
_CONSTS = {'pi': math.pi, 'e': math.e, 'tau': math.tau}

# Natural language -> operator normalisation
_WORD_REPLACEMENTS = [
    (r'\bplus\b|\badded to\b|\band\b(?=\s*\d)', '+'),
    (r'\bminus\b|\bsubtract(?:ed)?(?:\s+by)?\b|\bless\b', '-'),
    (r'\b(?:times|multiplied by|x)\b', '*'),
    (r'\bdivided by\b|\bover\b', '/'),
    (r'\b(?:to the power of|power of|raised to|\^)\b', '**'),
    (r'\bmod(?:ulo)?\b', '%'),
    (r'\bsquare root of\b|\broot of\b', 'sqrt'),
    (r'\bsquared\b', '**2'),
    (r'\bcubed\b', '**3'),
]


class CalculatorHandler:
    """Evaluates mathematical expressions safely and offline."""

    def _normalize(self, text: str) -> str:
        t = text.lower()
        # Strip conversational lead-ins
        t = re.sub(r'^(what(?:\'s| is)|calculate|compute|evaluate|solve|tell me)\s+',
                   '', t).strip()
        t = t.rstrip('?.! ')
        # Percent forms: "15% of 200" / "18 percent of 250" -> "(15/100)*200"
        t = re.sub(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*of\s*(\d+(?:\.\d+)?)',
                   r'(\1/100)*\2', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*(?:%|percent)', r'(\1/100)', t)
        for pattern, repl in _WORD_REPLACEMENTS:
            t = re.sub(pattern, repl, t)
        t = t.replace('×', '*').replace('÷', '/')
        return t.strip()

    def _eval(self, node):
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("unsupported constant")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](self._eval(node.left),
                                           self._eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](self._eval(node.operand))
        if isinstance(node, ast.Name) and node.id in _CONSTS:
            return _CONSTS[node.id]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _FUNCS:
            args = [self._eval(a) for a in node.args]
            return _FUNCS[node.func.id](*args)
        raise ValueError("unsupported expression")

    def evaluate(self, expression: str):
        expr = self._normalize(expression)
        if not re.search(r'\d', expr):
            return None
        # Only allow a safe character set
        if not re.fullmatch(r'[0-9eptaisqrtcofnxlg_.,()+\-*/%\s]+', expr):
            return None
        try:
            tree = ast.parse(expr, mode='eval')
            result = self._eval(tree)
        except Exception:
            return None
        if isinstance(result, float):
            if math.isinf(result) or math.isnan(result):
                return None
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 6)
        return result

    def handle(self, entities: Dict, context: Dict = None) -> Dict:
        text = (context or {}).get('original_text', '')
        result = self.evaluate(text)

        if result is None:
            return {
                'success': False,
                'response': ("I couldn't work that out. Try something like "
                             "\"calculate 12 * (3 + 4)\" or \"what is 15% of 200\"."),
                'data': {},
                'action': 'calculate',
                'requires_followup': True,
            }

        return {
            'success': True,
            'response': f"The answer is {result}.",
            'data': {'result': result, 'expression': self._normalize(text)},
            'action': 'calculate',
            'requires_followup': False,
        }
