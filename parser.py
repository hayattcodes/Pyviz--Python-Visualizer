import ast

def get_structure(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "items": [{"type": "syntax_error", "message": str(e), "line": e.lineno}],
            "total_lines": 0,
            "complexity": 0,
            "complexity_label": "Error"
        }

    structure = []
    complexity = 1

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            structure.append({
                "type": "function",
                "name": node.name,
                "line": node.lineno,
                "args": args
            })

        elif isinstance(node, ast.AsyncFunctionDef):
            structure.append({
                "type": "async_function",
                "name": node.name,
                "line": node.lineno
            })

        elif isinstance(node, ast.If):
            complexity += 1
            structure.append({
                "type":     "if_block",
                "line":     node.lineno,
                "has_else": len(node.orelse) > 0
            })

        elif isinstance(node, ast.For):
            complexity += 1
            structure.append({"type": "for_loop", "line": node.lineno})

        elif isinstance(node, ast.While):
            complexity += 1
            structure.append({"type": "while_loop", "line": node.lineno})

        elif isinstance(node, ast.ClassDef):
            structure.append({
                "type": "class",
                "name": node.name,
                "line": node.lineno
            })

        elif isinstance(node, ast.Try):
            complexity += 1
            structure.append({"type": "try_except", "line": node.lineno})

    lines = [l for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]

    return {
        "items":            structure,
        "total_lines":      len(lines),
        "complexity":       complexity,
        "complexity_label": _label(complexity)
    }

def _label(score):
    if score <= 2:  return "Simple"
    if score <= 5:  return "Moderate"
    if score <= 10: return "Complex"
    return "Very Complex"