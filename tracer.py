import sys
import copy
import io

class CodeTracer:
    def __init__(self):
        self.steps = []
        self.output_lines = []

    def trace(self, frame, event, arg):
        if event == "line":
            clean_vars = {}
            # manually copy each variable instead of deepcopying the whole frame
            for key, value in frame.f_locals.items():
                if key.startswith("__"):
                    continue
                try:
                    if isinstance(value, (int, float, str, bool, type(None))):
                        clean_vars[key] = value
                    elif isinstance(value, list):
                        clean_vars[key] = list(value)
                    elif isinstance(value, dict):
                        clean_vars[key] = dict(value)
                    elif isinstance(value, tuple):
                        clean_vars[key] = tuple(value)
                except Exception:
                    pass  # skip anything we can't safely copy

            self.steps.append({
                "line":      frame.f_lineno,
                "variables": clean_vars,
                "event":     "line",
                "function":  frame.f_code.co_name
            })

        elif event == "return":
            if frame.f_code.co_name != "<module>":
                clean_vars = {}
                for key, value in frame.f_locals.items():
                    if key.startswith("__"):
                        continue
                    try:
                        if isinstance(value, (int, float, str, bool, type(None))):
                            clean_vars[key] = value
                        elif isinstance(value, list):
                            clean_vars[key] = list(value)
                        elif isinstance(value, dict):
                            clean_vars[key] = dict(value)
                        elif isinstance(value, tuple):
                            clean_vars[key] = tuple(value)
                    except Exception:
                        pass

                self.steps.append({
                    "line":         frame.f_lineno,
                    "variables":    clean_vars,
                    "event":        "return",
                    "return_value": repr(arg),
                    "function":     frame.f_code.co_name
                })

        return self.trace

    def run(self, code):
        self.steps = []
        self.output_lines = []

        captured = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured

        sys.settrace(self.trace)

        try:
            compiled = compile(code, "<student_code>", "exec")
            exec(compiled)

        except SyntaxError as e:
            self.steps.append({
                "line":       e.lineno or 0,
                "variables":  {},
                "event":      "error",
                "error":      f"Syntax Error on line {e.lineno}: {e.msg}",
                "error_type": "syntax"
            })

        except Exception as e:
            self.steps.append({
                "line":       -1,
                "variables":  {},
                "event":      "error",
                "error":      f"{type(e).__name__}: {str(e)}",
                "error_type": "runtime"
            })

        finally:
            sys.settrace(None)
            sys.stdout = original_stdout
            raw = captured.getvalue().split("\n")
            self.output_lines = [l for l in raw if l]

        return {
            "steps":  self.steps,
            "output": self.output_lines
        }