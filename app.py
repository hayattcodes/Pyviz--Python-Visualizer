from flask import Flask, render_template, request, jsonify
import traceback
from tracer    import CodeTracer
from parser    import get_structure
from visualizer import build_flow_graph

app = Flask(__name__)

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

        # block dangerous operations for safety
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
                    "error": f"'{label}' is blocked — this tool is for learning Python basics!"}), 400

        tracer    = CodeTracer()
        result    = tracer.run(code)
        steps     = result["steps"]
        output    = result["output"]
        structure = get_structure(code)
        svg       = build_flow_graph(steps)

        return jsonify({
            "success":     True,
            "steps":       steps,
            "output":      output,
            "structure":   structure,
            "svg":         svg,
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