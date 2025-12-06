"""
Math Function Module - Safe Mathematical Operations

Handles voice-commanded mathematical operations including:
    - Basic arithmetic (add, subtract, multiply, divide)
    - Number conversions (binary, hexadecimal, octal)
    - Power and square root calculations
    - Factorial operations
    - Trigonometric functions

Security: Uses AST-based safe_eval() instead of dangerous eval()
to prevent code injection attacks.
"""

import math
import ast
import operator

# Safe math evaluator - replaces dangerous eval()
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.Invert: operator.invert,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval(expr):
    """Safely evaluate a mathematical expression string."""
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)
    except Exception:
        raise ValueError(f"Invalid expression: {expr}")

def _eval_node(node):
    """Recursively evaluate AST nodes for safe math operations."""
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(operand)
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

def basicOperations(text):
	if 'root' in text:
		temp = text.rfind(' ')
		num = int(text[temp+1:])
		return round(math.sqrt(num),2)

	text = text.replace('plus', '+')
	text = text.replace('minus', '-')
	text = text.replace('x', '*')
	text = text.replace('multiplied by', '*')
	text = text.replace('multiply', '*')
	text = text.replace('divided by', '/')
	text = text.replace('to the power', '**')
	text = text.replace('power', '**')
	result = safe_eval(text)
	return round(result,2)

def bitwiseOperations(text):
	if 'right shift' in text:
		temp = text.rfind(' ')
		num = int(text[temp+1:])
		return num>>1
	elif 'left shift' in text:
		temp = text.rfind(' ')
		num = int(text[temp+1:])
		return num<<1
	text = text.replace('and', '&')
	text = text.replace('or', '|')
	text = text.replace('not of', '~')
	text = text.replace('not', '~')
	text = text.replace('xor', '^')
	result = safe_eval(text)
	return result

def conversions(text):
	temp = text.rfind(' ')
	num = int(text[temp+1:])
	if 'bin' in text:
		return bin(num)[2:]
	elif 'hex' in text:
		return hex(num)[2:]
	elif 'oct' in text:
		return oct(num)[2:]

def trigonometry(text):
	temp = text.replace('degree','')
	temp = text.rfind(' ')
	deg = int(text[temp+1:])
	rad = (deg * math.pi) / 180
	if 'sin' in text:
		return round(math.sin(rad),2)
	elif 'cos' in text:
		return round(math.cos(rad),2)
	elif 'tan' in text:
		return round(math.tan(rad),2)

def factorial(n):
	if n==1 or n==0: return 1
	else: return n*factorial(n-1)

def logFind(text):
	temp = text.rfind(' ')
	num = int(text[temp+1:])
	return round(math.log(num,10),2)

def isHaving(text, lst):
	for word in lst:
		if word in text:
			return True
	return False

def perform(text):
	text = text.replace('math','')
	if "factorial" in text: return str(factorial(int(text[text.rfind(' ')+1:])))
	elif isHaving(text, ['sin','cos','tan']): return str(trigonometry(text))
	elif isHaving(text, ['bin','hex','oct']): return str(conversions(text))
	elif isHaving(text, ['shift','and','or','not']): return str(bitwiseOperations(text))
	elif 'log' in text: return str(logFind(text))
	else: return str(basicOperations(text))

# print(round(math.log(1,10),2))