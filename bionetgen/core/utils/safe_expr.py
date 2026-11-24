"""Fold constant parameter expressions to numbers without evaluating untrusted code.

``sympy.sympify`` on a string ends in Python ``eval``, so it must never see text taken
from a model file as is. ``fold_numeric`` first checks the expression with ``ast`` and
passes it to SymPy only if it is plain arithmetic on numbers, names and a short list of
math functions. Anything else is returned unchanged, as text.
"""

import ast

# Math functions that may appear in BNGL parameter expressions.
_ALLOWED_FUNCS = frozenset(
    {
        "exp",
        "ln",
        "log",
        "log10",
        "log2",
        "sqrt",
        "abs",
        "Abs",
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "asinh",
        "acosh",
        "atanh",
        "min",
        "max",
        "Min",
        "Max",
        "rint",
        "floor",
        "ceiling",
    }
)
_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.BitXor)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)
# Longest expression we hand to SymPy; real parameter expressions are far shorter.
_MAX_LENGTH = 1000


def _is_safe(node) -> bool:
    if isinstance(node, ast.Expression):
        return _is_safe(node.body)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return not node.id.startswith("_")
    if isinstance(node, ast.BinOp):
        return (
            isinstance(node.op, _ALLOWED_BINOPS)
            and _is_safe(node.left)
            and _is_safe(node.right)
        )
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, _ALLOWED_UNARYOPS) and _is_safe(node.operand)
    if isinstance(node, ast.Call):
        return (
            isinstance(node.func, ast.Name)
            and node.func.id in _ALLOWED_FUNCS
            and not node.keywords
            and all(_is_safe(arg) for arg in node.args)
        )
    return False


def is_safe_expression(text) -> bool:
    """True if ``text`` is plain arithmetic that may be passed to ``sympy.sympify``."""
    if not isinstance(text, str) or len(text) > _MAX_LENGTH:
        return False
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except (SyntaxError, ValueError):
        return False
    return _is_safe(tree)


def fold_numeric(text):
    """Return ``text`` as a numeric string if it is a constant expression, else unchanged.

    BNGL writes powers as ``^``; SymPy reads ``^`` as a power, as before this check.
    """
    if not is_safe_expression(text):
        return text
    try:
        import sympy

        sval = sympy.sympify(text)
        if sval.is_Number:
            return str(float(sval))
        if sval.is_constant():
            return str(float(sval.evalf()))
    except Exception:
        pass
    return text
