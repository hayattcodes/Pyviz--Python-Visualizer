from graphviz import Digraph
import ast

def build_flow_graph(steps):
    dot = Digraph(comment="PyViz Flow")
    dot.attr(
        rankdir = "TB",
        bgcolor = "transparent",
        pad     = "0.6",
        nodesep = "0.5",
        ranksep = "0.7"
    )

    dot.node("START", "▶  START",
        shape="ellipse", style="filled",
        fillcolor="#1A8A4A", fontcolor="#FFFFFF",
        fontname="Helvetica-Bold", fontsize="12",
        color="#145C32", penwidth="2.5", width="1.2"
    )

    prev_node  = "START"
    seen_lines = {}

    for i, step in enumerate(steps):
        node_id   = f"n{i}"
        line_num  = step.get("line", 0)
        event     = step.get("event", "line")
        variables = step.get("variables", {})
        func_name = step.get("function", "<module>")
        explanation = step.get("explanation", "")

        if event == "error":
            error_msg = step.get("error", "Unknown error")
            if len(error_msg) > 40:
                error_msg = error_msg[:40] + "..."
            dot.node(node_id,
                f"ERROR\nLine {line_num}\n{'─'*16}\n{error_msg}",
                shape="rectangle", style="filled,rounded",
                fillcolor="#7B0000", fontcolor="#FFB3B3",
                fontname="Helvetica", fontsize="10",
                color="#FF4444", penwidth="2.5"
            )
            dot.edge(prev_node, node_id, color="#FF4444", penwidth="2")
            break

        if event == "return":
            ret_val = str(step.get("return_value", "None"))
            if len(ret_val) > 20:
                ret_val = ret_val[:20] + "..."
            dot.node(node_id,
                f"RETURN\nfrom {func_name}()\nvalue: {ret_val}",
                shape="rectangle", style="filled,rounded",
                fillcolor="#2A1065", fontcolor="#C4B5FD",
                fontname="Helvetica", fontsize="10",
                color="#7C3AED", penwidth="2"
            )
            dot.edge(prev_node, node_id,
                color="#7C3AED", penwidth="2", style="dashed"
            )
            prev_node = node_id
            continue

        # build variable text
        var_lines = []
        for k, v in list(variables.items())[:3]:
            val_str = f'"{v}"' if isinstance(v, str) else repr(v)
            if len(val_str) > 18:
                val_str = val_str[:18] + "..."
            var_lines.append(f"{k} = {val_str}")
        var_text = "\n".join(var_lines) if var_lines else ""

        # detect line type from explanation
        is_condition    = any(x in explanation for x in ["🔀", "Condition", "condition"])
        is_loop_start   = any(x in explanation for x in ["🔁", "🔄", "loop", "Loop"]) 
        is_func_def     = any(x in explanation for x in ["📌", "defining", "Defining"])
        is_func_call    = any(x in explanation for x in ["📞", "Calling", "calling"])
        is_print        = any(x in explanation for x in ["🖨", "Print", "print"])

        seen_lines[line_num] = seen_lines.get(line_num, 0) + 1
        is_repeat = seen_lines[line_num] > 1

        fn_label = f"\nin {func_name}()" if func_name != "<module>" else ""

        if is_condition:
            label = f"Line {line_num}{fn_label}\n{'─'*14}\nCondition Check"
            if var_text:
                label += f"\n{'─'*14}\n{var_text}"
            dot.node(node_id, label,
                shape="diamond", style="filled",
                fillcolor="#7B4F00", fontcolor="#FDE68A",
                fontname="Helvetica-Bold", fontsize="10",
                color="#F5E86B", penwidth="2.5", width="2"
            )
            dot.edge(prev_node, node_id, color="#F5E86B", penwidth="2")

        elif is_loop_start and not is_repeat:
            label = f"Line {line_num}{fn_label}\n{'─'*14}\nLoop Start"
            if var_text:
                label += f"\n{'─'*14}\n{var_text}"
            dot.node(node_id, label,
                shape="hexagon", style="filled",
                fillcolor="#0C4A6E", fontcolor="#BAE6FD",
                fontname="Helvetica-Bold", fontsize="10",
                color="#38BDF8", penwidth="2.5"
            )
            dot.edge(prev_node, node_id, color="#38BDF8", penwidth="2")

        elif is_repeat:
            label = f"Line {line_num}{fn_label}\n{'─'*14}\nIteration {seen_lines[line_num]}"
            if var_text:
                label += f"\n{'─'*14}\n{var_text}"
            dot.node(node_id, label,
                shape="rectangle", style="filled,rounded",
                fillcolor="#0C2A4A", fontcolor="#BAE6FD",
                fontname="Helvetica", fontsize="10",
                color="#38BDF8", penwidth="2"
            )
            dot.edge(prev_node, node_id,
                color="#38BDF8", penwidth="1.5",
                style="dashed", label=f"iter {seen_lines[line_num]}"
            )

        elif is_func_def:
            label = f"Line {line_num}\n{'─'*14}\nDefine Function"
            if func_name != "<module>":
                label += f"\n{func_name}()"
            dot.node(node_id, label,
                shape="rectangle", style="filled,rounded",
                fillcolor="#1E1B4B", fontcolor="#C4B5FD",
                fontname="Helvetica-Bold", fontsize="10",
                color="#7C3AED", penwidth="2.5"
            )
            dot.edge(prev_node, node_id, color="#7C3AED", penwidth="2")

        elif is_func_call:
            label = f"Line {line_num}{fn_label}\n{'─'*14}\nFunction Call"
            if var_text:
                label += f"\n{'─'*14}\n{var_text}"
            dot.node(node_id, label,
                shape="rectangle", style="filled,rounded",
                fillcolor="#1A3A4A", fontcolor="#67E8F9",
                fontname="Helvetica-Bold", fontsize="10",
                color="#06B6D4", penwidth="2.5"
            )
            dot.edge(prev_node, node_id, color="#06B6D4", penwidth="2")

        elif is_print:
            label = f"Line {line_num}{fn_label}\n{'─'*14}\nPrint Output"
            if var_text:
                label += f"\n{'─'*14}\n{var_text}"
            dot.node(node_id, label,
                shape="parallelogram", style="filled",
                fillcolor="#064E3B", fontcolor="#6EE7B7",
                fontname="Helvetica", fontsize="10",
                color="#10B981", penwidth="2"
            )
            dot.edge(prev_node, node_id, color="#10B981", penwidth="2")

        else:
            label = f"Line {line_num}{fn_label}\n{'─'*14}"
            label += f"\n{var_text}" if var_text else "\n(executing...)"
            dot.node(node_id, label,
                shape="rectangle", style="filled,rounded",
                fillcolor="#1B3A6B", fontcolor="#E8F0FB",
                fontname="Helvetica", fontsize="10",
                color="#F5E86B", penwidth="1.5"
            )
            dot.edge(prev_node, node_id, color="#F5E86B", penwidth="1.5")

        prev_node = node_id

    dot.node("END", "⏹  END",
        shape="ellipse", style="filled",
        fillcolor="#7B0000", fontcolor="#FFFFFF",
        fontname="Helvetica-Bold", fontsize="12",
        color="#4A0000", penwidth="2.5", width="1.2"
    )
    dot.edge(prev_node, "END", color="#F5E86B", penwidth="2")

    try:
        return dot.pipe(format="svg").decode("utf-8")
    except Exception as e:
        return f"<p style='color:red;padding:20px'>Diagram error: {e}</p>"


def build_static_flowchart(code):
    dot = Digraph(comment="Static Flowchart")
    dot.attr(
        rankdir = "TB",
        bgcolor = "transparent",
        pad     = "0.5",
        nodesep = "0.4",
        ranksep = "0.6"
    )
    dot.attr("node", fontname="Helvetica", fontsize="11")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        dot.node("err",
            f"Syntax Error\nLine {e.lineno}: {e.msg}",
            shape="rectangle", style="filled,rounded",
            fillcolor="#7B0000", fontcolor="#FFB3B3",
            color="#FF4444"
        )
        try:
            return dot.pipe(format="svg").decode("utf-8")
        except:
            return "<p style='color:red'>Chart error</p>"

    dot.node("start", "▶ START",
        shape="ellipse", style="filled",
        fillcolor="#1A8A4A", fontcolor="#FFFFFF",
        color="#145C32", penwidth="2.5"
    )

    prev  = "start"
    count = 0

    for node in ast.walk(tree):
        nid = f"ast_{count}"

        if isinstance(node, ast.FunctionDef):
            dot.node(nid, f"Function\n{node.name}()",
                shape="rectangle", style="filled,rounded",
                fillcolor="#1E1B4B", fontcolor="#C4B5FD",
                color="#7C3AED", penwidth="2"
            )
            dot.edge(prev, nid, color="#7C3AED", penwidth="2")
            prev = nid
            count += 1

        elif isinstance(node, ast.If):
            dot.node(nid, f"If Condition\nLine {node.lineno}",
                shape="diamond", style="filled",
                fillcolor="#7B4F00", fontcolor="#FDE68A",
                color="#F5E86B", penwidth="2.5"
            )
            dot.edge(prev, nid, color="#F5E86B", penwidth="2")

            yes_id = f"yes_{count}"
            dot.node(yes_id, "True Branch",
                shape="rectangle", style="filled,rounded",
                fillcolor="#064E3B", fontcolor="#6EE7B7",
                color="#10B981"
            )
            dot.edge(nid, yes_id, label="Yes", color="#10B981")

            if node.orelse:
                no_id = f"no_{count}"
                dot.node(no_id, "False Branch",
                    shape="rectangle", style="filled,rounded",
                    fillcolor="#7B0000", fontcolor="#FFB3B3",
                    color="#FF4444"
                )
                dot.edge(nid, no_id, label="No", color="#FF4444")

            prev = yes_id
            count += 1

        elif isinstance(node, (ast.For, ast.While)):
            loop_type = "For Loop" if isinstance(node, ast.For) else "While Loop"
            dot.node(nid, f"{loop_type}\nLine {node.lineno}",
                shape="hexagon", style="filled",
                fillcolor="#0C4A6E", fontcolor="#BAE6FD",
                color="#38BDF8", penwidth="2.5"
            )
            dot.edge(prev, nid, color="#38BDF8", penwidth="2")
            dot.edge(nid, nid,
                label="repeat", color="#38BDF8",
                style="dashed", penwidth="1.5"
            )
            prev = nid
            count += 1

        elif isinstance(node, ast.ClassDef):
            dot.node(nid, f"Class\n{node.name}",
                shape="rectangle", style="filled,rounded",
                fillcolor="#1A3A4A", fontcolor="#67E8F9",
                color="#06B6D4", penwidth="2"
            )
            dot.edge(prev, nid, color="#06B6D4", penwidth="2")
            prev = nid
            count += 1

    dot.node("end", "⏹ END",
        shape="ellipse", style="filled",
        fillcolor="#7B0000", fontcolor="#FFFFFF",
        color="#4A0000", penwidth="2.5"
    )
    dot.edge(prev, "end", color="#F5E86B", penwidth="2")

    try:
        return dot.pipe(format="svg").decode("utf-8")
    except Exception as e:
        return f"<p style='color:red'>Static chart error: {e}</p>"