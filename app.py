from flask import Flask, render_template, request, jsonify
from tracer     import CodeTracer
from parser     import get_structure
from visualizer import build_flow_graph, build_static_flowchart

app = Flask(__name__, static_folder='static', template_folder='templates')


def explain_step(step, code_lines):
    try:
        line_num    = step.get("line", 0)
        event       = step.get("event", "line")
        variables   = step.get("variables", {})
        function    = step.get("function", "<module>")

        if line_num > 0 and line_num <= len(code_lines):
            code_line = code_lines[line_num - 1].strip()
        else:
            code_line = ""

        if event == "error":
            return f"❌ An error occurred: {step.get('error', 'Unknown error')}"

        if event == "return":
            return f"↩️ The function '{function}' finished and returned: {step.get('return_value', 'None')}"

        if code_line.startswith("def "):
            func_name = code_line.replace("def ", "").split("(")[0]
            return f"📌 Defining a new function called '{func_name}'. The code inside won't run yet — it only runs when you call the function."

        elif code_line.startswith("class "):
            class_name = code_line.replace("class ", "").split(":")[0].split("(")[0]
            return f"📦 Creating a new class called '{class_name}'. A class is like a blueprint for creating objects."

        elif code_line.startswith("for "):
            return f"🔁 Starting a for loop — Python will repeat the code inside this block once for each item in the sequence."

        elif code_line.startswith("while "):
            return f"🔄 Starting a while loop — Python will keep repeating this block as long as the condition stays True."

        elif code_line.startswith("if "):
            return f"🔀 Checking a condition on line {line_num} — Python is deciding which path to take based on True or False."

        elif code_line.startswith("elif "):
            return f"🔀 Checking another condition — the previous one was False, so Python is trying this one now."

        elif code_line.startswith("else:"):
            return f"🔀 All previous conditions were False — running the else block as a fallback."

        elif code_line.startswith("return "):
            val = code_line.replace("return ", "")
            return f"↩️ Returning '{val}' back to wherever this function was called from."

        elif code_line.startswith("print("):
            return f"🖨️ Printing output to the console. Check the Output box to see the result!"

        elif code_line.startswith("import ") or code_line.startswith("from "):
            return f"📥 Importing a module — loading extra tools and functions to use in your code."

        elif code_line.startswith("#"):
            return f"💬 This is a comment — a note for humans. Python completely ignores it when running."

        elif code_line.startswith("break"):
            return f"🛑 Break — immediately exiting the current loop."

        elif code_line.startswith("continue"):
            return f"⏭️ Continue — skipping the rest of this iteration and going back to the top of the loop."

        elif code_line.startswith("try:"):
            return f"🛡️ Try block — attempting to run this code and catching any errors that happen."

        elif code_line.startswith("except"):
            return f"🚨 Exception caught — an error occurred and Python is now handling it."

        elif "+=" in code_line:
            var_name = code_line.split("+=")[0].strip()
            value    = variables.get(var_name, "unknown")
            return f"➕ Adding to '{var_name}' — its new value is now {repr(value)}."

        elif "-=" in code_line:
            var_name = code_line.split("-=")[0].strip()
            value    = variables.get(var_name, "unknown")
            return f"➖ Subtracting from '{var_name}' — its new value is now {repr(value)}."

        elif "=" in code_line and "==" not in code_line and "!=" not in code_line and ">=" not in code_line and "<=" not in code_line:
            parts    = code_line.split("=")
            var_name = parts[0].strip()
            value    = variables.get(var_name.split("[")[0].strip(), None)
            if value is not None:
                return f"📝 Setting variable '{var_name}' to {repr(value)}. Variables are like labelled boxes in memory that store information."
            else:
                return f"📝 Creating or updating variable '{var_name}'. Variables store information in memory."

        elif "(" in code_line and ")" in code_line:
            func_called = code_line.split("(")[0].strip().split("=")[-1].strip()
            return f"📞 Calling the function '{func_called}' — Python jumps into that function, runs its code, then comes back here."

        else:
            if variables:
                var_summary = ", ".join(
                    f"{k} = {repr(v)}" for k, v in list(variables.items())[:3]
                )
                return f"⚙️ Executing line {line_num}. Variables in memory: {var_summary}"
            else:
                return f"⚙️ Executing line {line_num}. No variables stored yet."

    except Exception:
        return f"⚙️ Executing line {step.get('line', '?')}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_code():
    try:
        data = request.get_json()
        code = data.get("code", "").strip()

        if not code:
            return jsonify({"success": False,
                "error": "Write some code first!"}), 400

        if len(code) > 5000:
            return jsonify({"success": False,
                "error": "Code too long — keep it under 5000 characters."}), 400

        blocked = [
            ("import os",         "os module"),
            ("import subprocess", "subprocess"),
            ("__import__",        "dynamic import"),
            ("open(",             "file access"),
            ("socket",            "network access"),
            ("shutil",            "shutil module"),
        ]
        for keyword, label in blocked:
            if keyword in code:
                return jsonify({"success": False,
                    "error": f"'{label}' is blocked for safety!"}), 400

        tracer    = CodeTracer()
        result    = tracer.run(code)
        steps     = result["steps"]
        output    = result["output"]
        structure = get_structure(code)

        code_lines = code.split("\n")
        for step in steps:
            step["explanation"] = explain_step(step, code_lines)

        svg        = build_flow_graph(steps)
        static_svg = build_static_flowchart(code)

        return jsonify({
            "success":     True,
            "steps":       steps,
            "output":      output,
            "structure":   structure,
            "svg":         svg,
            "static_svg":  static_svg,
            "total_steps": len(steps),
            "has_error":   any(s.get("event") == "error" for s in steps)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error":   f"Server error: {str(e)}"
        }), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("\n🐍  PyViz is starting up...")
    print("➜   Open http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)