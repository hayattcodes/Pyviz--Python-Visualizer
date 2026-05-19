// ============================================================
//  PyViz — script.js
// ============================================================

const EXAMPLES = {
  fibonacci: `# Fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(n - 1):
        a, b = b, a + b
    return b
for i in range(8):
    print(fibonacci(i))`,

  bubble_sort: `# Bubble sort
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
numbers = [64, 34, 25, 12, 22]
sorted_nums = bubble_sort(numbers)
print(sorted_nums)`,

  recursion: `# Recursive factorial
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
print(result)`,

  list_comp: `# List comprehension
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
evens = [x for x in numbers if x % 2 == 0]
squares = [x ** 2 for x in evens]
total = sum(squares)
print(total)`,

  closures: `# Closures
def make_counter(start):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
counter = make_counter(0)
print(counter())
print(counter())
print(counter())`,

  classes: `# Classes
class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
    def is_passing(self):
        return self.grade >= 60
s = Student("Alex", 85)
print(s.name)
print(s.is_passing())`
};

let allSteps   = [];
let allOutput  = [];
let currentIdx = -1;
let playTimer  = null;
let isPlaying  = false;
let codeLines  = [];
let prevVars   = {};

const $ = id => document.getElementById(id);

function esc(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── EXAMPLE PILLS ─────────────────────────────────────────────
document.querySelectorAll(".pill[data-example]").forEach(btn => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.example;
    if (EXAMPLES[key]) {
      $("code-editor").value = EXAMPLES[key];
      updateLineNumbers();
      updateEditorInfo();
      document.querySelectorAll(".pill[data-example]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    }
  });
});

// ── LINE NUMBERS ──────────────────────────────────────────────
function updateLineNumbers() {
  const ta = $("code-editor");
  const ln = $("line-numbers");
  if (!ta || !ln) return;
  ln.innerHTML = ta.value.split("\n")
    .map((_, i) => `<div style="line-height:1.7;height:1.7em">${i+1}</div>`)
    .join("");
}

function syncLineScroll() {
  const ta = $("code-editor");
  const ln = $("line-numbers");
  if (ta && ln) ln.scrollTop = ta.scrollTop;
}

function updateEditorInfo() {
  const ta   = $("code-editor");
  const info = $("editor-info");
  if (!ta || !info) return;
  info.textContent = `${ta.value.split("\n").length} lines · Python 3`;
}

// ── BUTTONS ───────────────────────────────────────────────────
$("btn-clear").addEventListener("click", () => {
  $("code-editor").value = "";
  updateLineNumbers();
  updateEditorInfo();
  resetVisualization();
  document.querySelectorAll(".pill[data-example]").forEach(b => b.classList.remove("active"));
});

$("btn-copy").addEventListener("click", () => {
  navigator.clipboard.writeText($("code-editor").value)
    .then(() => showToast("📋 Code copied!"));
});

$("speed-slider").addEventListener("input", () => {
  $("speed-val").textContent = $("speed-slider").value + "×";
  if (isPlaying) { stopPlay(); startPlay(); }
});

// ── RUN ───────────────────────────────────────────────────────
$("btn-run").addEventListener("click", runCode);

async function runCode() {
  const code = $("code-editor").value.trim();
  if (!code) { showToast("Write some code first! ✍️"); return; }

  codeLines = $("code-editor").value.split("\n");

  const overlay = $("loading-overlay");
  overlay.style.display = "flex";
  setTimeout(() => overlay.classList.add("active"), 10);

  try {
    const res  = await fetch("/run", {
      method:  "POST",
      headers: {"Content-Type": "application/json"},
      body:    JSON.stringify({code})
    });
    const data = await res.json();

    overlay.classList.remove("active");
    setTimeout(() => { overlay.style.display = "none"; }, 200);

    if (!data.success) { showErrorState(data.error || "Something went wrong."); return; }

    allSteps  = data.steps  || [];
    allOutput = data.output || [];

    if (allSteps.length === 0) {
      showToast("No steps found. Try adding variables or print() calls!");
      return;
    }

    buildCodeMirror();
    prevVars = {};
    goToStep(0);
    setControlsEnabled(true);
    showToast(`✅ ${allSteps.length} steps ready — press ▶ to play!`);

    // show flowchart
    if (data.svg) showFlowchart(data.svg, data.static_svg);

  } catch(err) {
    overlay.classList.remove("active");
    setTimeout(() => { overlay.style.display = "none"; }, 200);
    showErrorState("Connection error — is the server running? → python3 app.py");
  }
}

// ── CODE MIRROR ───────────────────────────────────────────────
function buildCodeMirror() {
  const mirror = $("code-mirror");
  if (!mirror) return;
  mirror.innerHTML = codeLines.map((line, i) =>
    `<div class="mirror-line" id="mirror-line-${i+1}">
       <span class="mirror-line-num">${i+1}</span>
       <span class="mirror-line-code">${esc(line)||" "}</span>
     </div>`
  ).join("");
}

// ── GO TO STEP ────────────────────────────────────────────────
function goToStep(idx) {
  if (idx < 0 || idx >= allSteps.length) return;
  if (idx === allSteps.length - 1) stopPlay();

  currentIdx = idx;
  const step = allSteps[idx];

  $("step-counter").textContent  = `Step ${idx+1} / ${allSteps.length}`;
  $("progress-fill").style.width = (((idx+1)/allSteps.length)*100) + "%";

  const fn = step.function && step.function !== "<module>"
    ? ` · in ${step.function}()` : "";
  $("step-event").textContent = step.event === "error" ? "❌ Error"
    : step.event === "return" ? `↩ Return${fn}`
    : `Executing line${fn}`;

  updateStepDesc(step);
  highlightLine(step.line);
  $("current-line-label").textContent = step.line > 0 ? `Line ${step.line}` : "—";
  updateVariables(step.variables || {});
  updateCallStack(step);
  updateOutput(idx);

  $("btn-prev").disabled  = idx <= 0;
  $("btn-first").disabled = idx <= 0;
  $("btn-next").disabled  = idx >= allSteps.length - 1;
  $("btn-last").disabled  = idx >= allSteps.length - 1;

  prevVars = {...(step.variables || {})};
}

// ── STEP DESCRIPTION ──────────────────────────────────────────
function updateStepDesc(step) {
  const desc = $("step-desc");
  if (!desc) return;

  if (step.explanation) {
    desc.innerHTML = step.explanation;
    return;
  }

  if (step.event === "error") {
    desc.innerHTML = `<span style="color:#CC2B2B">❌ ${esc(step.error)}</span>`;
    return;
  }
  if (step.event === "return") {
    desc.innerHTML = `↩ <strong>${esc(step.function)}()</strong> returned <code style="background:rgba(27,58,107,0.08);padding:1px 6px;border-radius:4px;font-family:var(--font-mono)">${esc(step.return_value||"None")}</code>`;
    return;
  }
  const count = Object.keys(step.variables||{}).length;
  const fn = step.function && step.function !== "<module>"
    ? ` inside <strong>${esc(step.function)}()</strong>` : "";
  desc.innerHTML = `Executing <strong>line ${step.line}</strong>${fn} · ${count} variable${count!==1?"s":""} in scope`;
}

// ── HIGHLIGHT ─────────────────────────────────────────────────
function highlightLine(lineNum) {
  document.querySelectorAll(".mirror-line").forEach(el => el.classList.remove("active"));
  if (lineNum > 0) {
    const el = $(`mirror-line-${lineNum}`);
    if (el) { el.classList.add("active"); el.scrollIntoView({block:"nearest",behavior:"smooth"}); }
  }
}

// ── VARIABLES ─────────────────────────────────────────────────
function updateVariables(variables) {
  const panel = $("variables-panel");
  if (!panel) return;
  const entries = Object.entries(variables);
  if (!entries.length) {
    panel.innerHTML = `<div class="empty-state">No variables yet</div>`;
    return;
  }
  panel.innerHTML = entries.map(([key, val]) => {
    const changed = JSON.stringify(prevVars[key]) !== JSON.stringify(val);
    const type = Array.isArray(val) ? "list"
      : val === null ? "None"
      : typeof val === "number" && Number.isInteger(val) ? "int"
      : typeof val === "number" ? "float"
      : typeof val;
    const valStr = typeof val === "string" ? `"${val}"` : JSON.stringify(val);
    return `<div class="var-row${changed?" var-changed":""}">
      <span class="var-name">${esc(key)}</span>
      <span class="var-type">${type}</span>
      <span class="var-val">${esc(valStr)}</span>
    </div>`;
  }).join("");
}

// ── CALL STACK ────────────────────────────────────────────────
function updateCallStack(step) {
  const panel = $("call-stack");
  if (!panel) return;
  const frames = ["<module>"];
  if (step.function && step.function !== "<module>") frames.push(step.function);
  panel.innerHTML = [...frames].reverse().map((fn, i) => {
    const isTop = i === 0;
    return `<div class="stack-frame${isTop?" top-frame":""}">
      <span class="stack-frame-arrow">${isTop?"▶":"○"}</span>
      <span style="flex:1;font-weight:${isTop?700:500}">${esc(fn)}</span>
      ${isTop&&step.line>0?`<span style="opacity:0.6;font-size:0.7rem">line ${step.line}</span>`:""}
    </div>`;
  }).join("");
}

// ── OUTPUT ────────────────────────────────────────────────────
function updateOutput(stepIdx) {
  const panel = $("output-panel");
  if (!panel) return;
  const progress     = allSteps.length > 1 ? stepIdx/(allSteps.length-1) : 1;
  const visibleCount = Math.ceil(allOutput.length * progress);
  const visible      = allOutput.slice(0, visibleCount);
  if (!visible.length) {
    panel.innerHTML = `<div class="empty-state">No output yet</div>`;
    return;
  }
  panel.innerHTML = visible.map(line =>
    `<div style="padding:3px 0;border-bottom:1px solid rgba(27,58,107,0.06);color:#2C3E50;font-family:var(--font-mono);font-size:0.8rem">
      <span style="color:#A0AEBB;margin-right:8px;user-select:none">›</span>${esc(line)}
    </div>`
  ).join("");
  panel.scrollTop = panel.scrollHeight;
}

// ── FLOWCHART ─────────────────────────────────────────────────
function showFlowchart(svg, staticSvg) {
  window._executionSVG = svg;
  window._staticSVG    = staticSvg || svg;

  const section = $("flowchart-section");
  const body    = $("flowchart-body");
  if (!section || !body) return;

  section.style.display = "block";
  body.innerHTML = svg;

  const svgEl = body.querySelector("svg");
  if (svgEl) { svgEl.style.width="100%"; svgEl.style.height="auto"; }
}

function switchFlowTab(tab) {
  const execTab   = $("ftab-execution");
  const staticTab = $("ftab-static");
  const body      = $("flowchart-body");
  if (!body) return;

  if (tab === "execution") {
    if (execTab)   execTab.classList.add("ftab--active");
    if (staticTab) staticTab.classList.remove("ftab--active");
    body.innerHTML = window._executionSVG || "<p style='padding:20px;color:#999'>Run code first</p>";
  } else {
    if (staticTab) staticTab.classList.add("ftab--active");
    if (execTab)   execTab.classList.remove("ftab--active");
    body.innerHTML = window._staticSVG || "<p style='padding:20px;color:#999'>Run code first</p>";
  }

  const svgEl = body.querySelector("svg");
  if (svgEl) { svgEl.style.width="100%"; svgEl.style.height="auto"; }
}

// ── PLAYBACK ──────────────────────────────────────────────────
$("btn-first").addEventListener("click", () => { stopPlay(); goToStep(0); });
$("btn-prev").addEventListener("click",  () => { stopPlay(); goToStep(currentIdx-1); });
$("btn-next").addEventListener("click",  () => { stopPlay(); goToStep(currentIdx+1); });
$("btn-last").addEventListener("click",  () => { stopPlay(); goToStep(allSteps.length-1); });

$("btn-play").addEventListener("click", () => {
  if (isPlaying) { stopPlay(); return; }
  if (currentIdx >= allSteps.length-1) goToStep(0);
  startPlay();
});

function startPlay() {
  isPlaying = true;
  $("btn-play").textContent = "⏸";
  const delay = [900,600,380,220,100][parseInt($("speed-slider").value)-1];
  playTimer = setInterval(() => {
    if (currentIdx >= allSteps.length-1) { stopPlay(); return; }
    goToStep(currentIdx+1);
  }, delay);
}

function stopPlay() {
  isPlaying = false;
  clearInterval(playTimer);
  playTimer = null;
  const btn = $("btn-play");
  if (btn) btn.textContent = "▶";
}

function setControlsEnabled(on) {
  ["btn-first","btn-prev","btn-play","btn-next","btn-last"]
    .forEach(id => { $(id).disabled = !on; });
}

// ── RESET ─────────────────────────────────────────────────────
function resetVisualization() {
  stopPlay();
  allSteps=[]; allOutput=[]; currentIdx=-1; codeLines=[]; prevVars={};
  $("step-counter").textContent  = "Step 0 / 0";
  $("step-event").textContent    = "Ready";
  $("step-desc").innerHTML       = "Press <strong>Visualize</strong> to start tracing your code.";
  $("progress-fill").style.width = "0%";
  $("current-line-label").textContent = "—";
  $("call-stack").innerHTML      = `<div class="empty-state">No active calls</div>`;
  $("variables-panel").innerHTML = `<div class="empty-state">No variables yet</div>`;
  $("output-panel").innerHTML    = `<div class="empty-state">No output yet</div>`;
  $("code-mirror").innerHTML     = `<div class="empty-state">Run your code to see execution highlights</div>`;
  const fc = $("flowchart-section");
  if (fc) fc.style.display = "none";
  setControlsEnabled(false);
}

function showErrorState(msg) {
  const d = $("step-desc");
  if (d) d.innerHTML = `<span style="color:#CC2B2B">❌ ${esc(msg)}</span>`;
  showToast("❌ " + msg);
}

// ── TOAST ─────────────────────────────────────────────────────
function showToast(message) {
  let t = document.getElementById("pyviz-toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "pyviz-toast";
    t.style.cssText = `
      position:fixed;bottom:28px;right:28px;z-index:9999;
      background:#1B3A6B;border:1.5px solid rgba(245,232,107,0.5);
      color:#fff;padding:11px 22px;border-radius:10px;
      font-family:'Montserrat',sans-serif;font-size:13px;font-weight:600;
      box-shadow:0 8px 32px rgba(27,58,107,0.35);
      opacity:0;transform:translateY(8px);
      transition:all 0.28s cubic-bezier(0.16,1,0.3,1);
      pointer-events:none;
    `;
    document.body.appendChild(t);
  }
  t.textContent = message;
  t.style.opacity = "1";
  t.style.transform = "translateY(0)";
  clearTimeout(t._t);
  t._t = setTimeout(() => {
    t.style.opacity = "0";
    t.style.transform = "translateY(8px)";
  }, 2800);
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const ta = $("code-editor");
  if (!ta) return;

  ta.addEventListener("input",  () => { updateLineNumbers(); updateEditorInfo(); });
  ta.addEventListener("scroll", syncLineScroll);

  ta.addEventListener("keydown", e => {
    if (e.key === "Tab") {
      e.preventDefault();
      const s = ta.selectionStart;
      ta.value = ta.value.substring(0,s) + "    " + ta.value.substring(ta.selectionEnd);
      ta.selectionStart = ta.selectionEnd = s + 4;
      updateLineNumbers();
    }
    if ((e.metaKey||e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      runCode();
    }
  });

  updateLineNumbers();
  updateEditorInfo();
  resetVisualization();
});