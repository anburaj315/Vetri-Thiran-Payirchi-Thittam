/* EduGenie frontend: one form, five tasks, talks to the FastAPI backend. */
const TASKS = {
    qa: {
        label: "Your question:",
        placeholder: "Which is the largest ocean?",
        title: "Answer",
        rows: 3,
        call: (v) => fetch(`/qa?question=${encodeURIComponent(v)}`),
        render: (d) => renderText(d.answer),
    },
    explain: {
        label: "Concept to explain:",
        placeholder: "Photosynthesis",
        title: "Explanation",
        rows: 3,
        call: (v) => postJSON("/explain", { topic: v }),
        render: (d) => renderText(d.explanation),
    },
    quiz: {
        label: "Topic or passage for the quiz:",
        placeholder: "Pythagoras Theorem",
        title: "Quiz",
        rows: 4,
        call: (v) => postJSON("/quiz", { text: v }),
        render: (d) => renderQuiz(d.quiz),
    },
    summary: {
        label: "Paste the text to summarize:",
        placeholder: "Paste a long paragraph or article here…",
        title: "Summary",
        rows: 10,
        call: (v) => postJSON("/summarize", { text: v }),
        render: (d) => renderText(d.summary),
    },
    path: {
        label: "Topic you want a learning path for:",
        placeholder: "SQL",
        title: "Learning Path",
        rows: 3,
        call: (v) => postJSON("/learn/recommendations", { topic: v }),
        render: (d) => renderText(d.recommendations),
    },
};

const $ = (id) => document.getElementById(id);
const form = $("taskForm");
const taskSel = $("task");
const input = $("userInput");
const label = $("inputLabel");
const btn = $("submitBtn");
const card = $("resultCard");
const title = $("resultTitle");
const loader = $("loader");
const output = $("output");

function postJSON(url, body) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

function escapeHTML(s) {
    return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* Minimal, safe Markdown -> HTML (headings, bold, italics, code, bullet lists). */
function inline(s) {
    return s
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[\s(])\*(?!\s)(.+?)\*(?=[\s).,;:!?]|$)/g, "$1<em>$2</em>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderText(text) {
    const lines = escapeHTML(String(text || "")).split(/\r?\n/);
    let html = "";
    let inList = false;
    const closeList = () => { if (inList) { html += "</ul>"; inList = false; } };

    for (const raw of lines) {
        const line = raw.trimEnd();
        const bullet = line.match(/^\s*[*\-•]\s+(.*)$/);
        const heading = line.match(/^\s*(#{1,4})\s+(.*)$/);
        if (bullet) {
            if (!inList) { html += "<ul>"; inList = true; }
            html += `<li>${inline(bullet[1])}</li>`;
        } else if (heading) {
            closeList();
            html += `<h3>${inline(heading[2])}</h3>`;
        } else if (line.trim() === "") {
            closeList();
        } else {
            closeList();
            html += `<p>${inline(line.trim())}</p>`;
        }
    }
    closeList();
    output.innerHTML = html || "<p>No content returned.</p>";
}

function renderQuiz(quiz) {
    output.innerHTML = "";
    const answered = new Array(quiz.length).fill(false);
    let score = 0;
    const scoreEl = document.createElement("div");
    scoreEl.className = "score";

    quiz.forEach((q, qi) => {
        const box = document.createElement("div");
        box.className = "quiz-q";
        const qText = document.createElement("p");
        qText.textContent = `Q${qi + 1}. ${q.question}`;
        box.appendChild(qText);

        const feedback = document.createElement("p");
        feedback.className = "feedback";

        q.options.forEach((opt) => {
            const row = document.createElement("label");
            row.className = "option";
            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = `q${qi}`;
            radio.value = opt;
            row.appendChild(radio);
            row.appendChild(document.createTextNode(opt));
            row.dataset.value = opt;

            radio.addEventListener("change", () => {
                if (answered[qi]) return;
                answered[qi] = true;
                const correct = opt === q.answer;
                if (correct) score += 1;
                box.querySelectorAll("input").forEach((r) => (r.disabled = true));
                box.querySelectorAll(".option").forEach((el) => {
                    if (el.dataset.value === q.answer) el.classList.add("correct");
                });
                if (!correct) row.classList.add("wrong");
                feedback.className = "feedback " + (correct ? "ok" : "bad");
                feedback.textContent = correct ? "✅ Correct!" : `❌ Not quite. Correct answer: ${q.answer}`;
                if (answered.every(Boolean)) {
                    scoreEl.textContent = `Your score: ${score} / ${quiz.length}`;
                }
            });
            box.appendChild(row);
        });
        box.appendChild(feedback);
        output.appendChild(box);
    });
    output.appendChild(scoreEl);
}

function showError(message) {
    output.innerHTML = "";
    const div = document.createElement("div");
    div.className = "error";
    div.textContent = message;
    output.appendChild(div);
}

function applyTask() {
    const t = TASKS[taskSel.value];
    label.innerHTML = `<strong>${t.label}</strong>`;
    input.placeholder = t.placeholder;
    input.rows = t.rows;
}

taskSel.addEventListener("change", applyTask);
applyTask();

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const value = input.value.trim();
    if (!value) return;

    const t = TASKS[taskSel.value];
    title.textContent = t.title;
    card.classList.remove("hidden");
    output.innerHTML = "";
    loader.classList.remove("hidden");
    btn.disabled = true;

    try {
        const res = await t.call(value);
        let data = {};
        try { data = await res.json(); } catch (_) { /* non-JSON error body */ }
        if (!res.ok) {
            const detail = data.error || (Array.isArray(data.detail) ? "Invalid input." : data.detail);
            throw new Error(detail || `Request failed (${res.status})`);
        }
        t.render(data);
    } catch (err) {
        showError(err.message || "Something went wrong. Please try again.");
    } finally {
        loader.classList.add("hidden");
        btn.disabled = false;
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
});
