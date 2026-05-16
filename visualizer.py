from graphviz import Digraph

def build_flow_graph(steps):
    dot = Digraph(comment="Code Flow")

    dot.attr(
        rankdir  = "TB",
        bgcolor  = "transparent",
        pad      = "0.5",
        nodesep  = "0.4",
        ranksep  = "0.6"
    )

    dot.attr("node",
        shape     = "box",
        style     = "filled,rounded",
        fillcolor = "#1B3A6B",
        fontcolor = "#FFFFFF",
        fontname  = "Helvetica",
        fontsize  = "11",
        color     = "#F5E86B",
        penwidth  = "2"
    )

    dot.attr("edge",
        color     = "#F5E86B",
        penwidth  = "1.5",
        arrowsize = "0.8"
    )

    prev_node  = None
    seen_lines = {}

    for i, step in enumerate(steps):
        node_id = f"s{i}"

        if step.get("event") == "error":
            dot.node(node_id,
                f"ERROR\nLine {step.get('line','?')}\n{'─'*16}\n{step.get('error','unknown')}",
                fillcolor="#CC2B2B",
                color="#FF6B6B",
                fontcolor="#FFFFFF"
            )
            if prev_node:
                dot.edge(prev_node, node_id, color="#CC2B2B")
            break

        if step.get("event") == "return":
            dot.node(node_id,
                f"return from {step.get('function','?')}\nvalue: {step.get('return_value','None')}",
                fillcolor="#2A5298",
                color="#F5E86B",
                fontcolor="#F5E86B"
            )
            if prev_node:
                dot.edge(prev_node, node_id, color="#F5E86B")
            prev_node = node_id
            continue

        vars_dict = step.get("variables", {})
        var_lines = []
        for k, v in vars_dict.items():
            val = f'"{v}"' if isinstance(v, str) else repr(v)
            var_lines.append(f"{k} = {val}")

        var_text  = "\n".join(var_lines) if var_lines else "(no variables yet)"
        func_name = step.get("function", "<module>")
        func_part = f"\nin {func_name}()" if func_name != "<module>" else ""
        label     = f"Line {step['line']}{func_part}\n{'─'*18}\n{var_text}"

        line_num = step["line"]
        seen_lines[line_num] = seen_lines.get(line_num, 0) + 1
        is_repeat = seen_lines[line_num] > 1

        if is_repeat:
            dot.node(node_id, label,
                fillcolor="#1A8A4A",
                color="#F5E86B",
                fontcolor="#FFFFFF"
            )
            if prev_node:
                dot.edge(prev_node, node_id,
                    color="#4ADE80",
                    label=f"iter {seen_lines[line_num]}"
                )
        else:
            dot.node(node_id, label)
            if prev_node:
                dot.edge(prev_node, node_id)

        prev_node = node_id

    try:
        return dot.pipe(format="svg").decode("utf-8")
    except Exception as e:
        return f"<p style='color:red'>Diagram error: {e}</p>"