const questionsEl = document.getElementById("questions");
const streakBadgeEl = document.getElementById("streak-badge");

function el(tag, opts = {}, children = []) {
  const node = document.createElement(tag);
  if (opts.className) node.className = opts.className;
  if (opts.text !== undefined) node.textContent = opts.text;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
  }
  for (const child of children) node.appendChild(child);
  return node;
}

function renderDataTable(columns, rows) {
  if (columns.length === 0) {
    return el("div", { className: "empty", text: "(no columns)" });
  }
  const table = el("table", { className: "data" });
  const thead = el("thead", {}, [
    el("tr", {}, columns.map((c) => el("th", { text: c }))),
  ]);
  const tbody = el("tbody");
  if (rows.length === 0) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", { text: "(0 rows)", attrs: { colspan: String(columns.length) } }),
      ])
    );
  } else {
    for (const row of rows) {
      tbody.appendChild(
        el(
          "tr",
          {},
          row.map((cell) => el("td", { text: cell === null ? "NULL" : String(cell) }))
        )
      );
    }
  }
  table.appendChild(thead);
  table.appendChild(tbody);
  return table;
}

function renderSchema(tables) {
  const details = el("details", { className: "schema" });
  details.open = true;
  details.appendChild(el("summary", { text: `Schema (${tables.length} table${tables.length === 1 ? "" : "s"})` }));
  for (const t of tables) {
    const block = el("div", { className: "table-block" });
    block.appendChild(el("code", { className: "ddl", text: t.ddl }));
    if (t.sample_rows.length > 0) {
      const cols = Object.keys(t.sample_rows[0]);
      const rows = t.sample_rows.map((r) => cols.map((c) => r[c]));
      block.appendChild(renderDataTable(cols, rows));
    }
    details.appendChild(block);
  }
  return details;
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

function renderQuestionCard(question) {
  const card = el("div", { className: "card" });

  const header = el("div", { className: "card-header" }, [
    el("h2", { text: question.title }),
    el("div", { className: "badges" }, [
      el("span", { className: "badge", text: question.topic.replace(/_/g, " ") }),
      el("span", { className: "badge", text: `difficulty ${question.difficulty}` }),
    ]),
  ]);
  card.appendChild(header);

  const cardLeft = el("div", { className: "card-left" }, [
    el("p", { className: "prompt", text: question.prompt }),
    renderSchema(question.tables),
  ]);

  const textarea = el("textarea", {
    className: "sql-editor",
    attrs: { placeholder: "SELECT …", spellcheck: "false" },
  });
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      textarea.value = textarea.value.slice(0, start) + "  " + textarea.value.slice(end);
      textarea.selectionStart = textarea.selectionEnd = start + 2;
    }
  });
  const runBtn = el("button", { className: "run-btn", text: "Run & Check" });
  const feedback = el("span", { className: "feedback" });
  const showAnswerBtn = el("button", { className: "show-answer-btn", text: "Show Answer" });
  showAnswerBtn.style.display = "none";
  const actions = el("div", { className: "actions" }, [runBtn, feedback, showAnswerBtn]);

  const resultArea = el("div");
  const answerArea = el("div");

  const cardRight = el("div", { className: "card-right" }, [textarea, actions, resultArea, answerArea]);

  card.appendChild(el("div", { className: "card-body" }, [cardLeft, cardRight]));

  let incorrectAttempts = 0;
  let lastReferenceSql = null;

  showAnswerBtn.addEventListener("click", () => {
    const isShowing = showAnswerBtn.textContent === "Hide Answer";
    if (isShowing) {
      answerArea.innerHTML = "";
      showAnswerBtn.textContent = "Show Answer";
    } else {
      answerArea.innerHTML = "";
      answerArea.appendChild(el("h4", { text: "Correct query" }));
      answerArea.appendChild(el("code", { className: "answer-box", text: lastReferenceSql }));
      showAnswerBtn.textContent = "Hide Answer";
    }
  });

  runBtn.addEventListener("click", async () => {
    const sql = textarea.value.trim();
    if (!sql) return;
    runBtn.disabled = true;
    runBtn.textContent = "Running…";
    feedback.textContent = "";
    feedback.className = "feedback";
    resultArea.innerHTML = "";

    try {
      const data = await fetchJSON(`/api/questions/${question.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql }),
      });

      feedback.textContent = data.correct
        ? `Correct! Level ${data.topic_level}${data.leveled_up ? " — leveled up!" : ""}`
        : `Not quite — level ${data.topic_level} (streak ${data.topic_streak}/2)`;
      feedback.className = `feedback ${data.correct ? "correct" : "incorrect"}`;

      if (data.error) {
        resultArea.appendChild(el("h4", { text: "Error" }));
        resultArea.appendChild(el("div", { className: "error-box", text: data.error }));
      } else if (data.result) {
        resultArea.appendChild(el("h4", { text: "Your result" }));
        resultArea.appendChild(renderDataTable(data.result.columns, data.result.rows));
      }

      if (!data.correct && data.expected) {
        resultArea.appendChild(el("h4", { text: "Expected result" }));
        resultArea.appendChild(renderDataTable(data.expected.columns, data.expected.rows));
      }

      lastReferenceSql = data.reference_sql;
      if (data.correct) {
        showAnswerBtn.style.display = "inline-block";
      } else {
        incorrectAttempts += 1;
        if (incorrectAttempts >= 2) {
          showAnswerBtn.style.display = "inline-block";
        }
      }

      refreshStreak();
    } catch (err) {
      feedback.textContent = "Request failed";
      feedback.className = "feedback incorrect";
      resultArea.appendChild(el("div", { className: "error-box", text: String(err) }));
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = "Run & Check";
    }
  });

  return card;
}

async function loadSession() {
  questionsEl.textContent = "Loading today's drills…";
  try {
    const questions = await fetchJSON("/api/session/today");
    questionsEl.innerHTML = "";
    for (const q of questions) {
      questionsEl.appendChild(renderQuestionCard(q));
    }
  } catch (err) {
    questionsEl.textContent = `Failed to load session: ${err}`;
  }
}

async function refreshStreak() {
  try {
    const progress = await fetchJSON("/api/progress");
    streakBadgeEl.innerHTML = "";
    streakBadgeEl.appendChild(document.createTextNode("Day streak: "));
    streakBadgeEl.appendChild(el("strong", { text: String(progress.day_streak) }));
  } catch {
    streakBadgeEl.textContent = "";
  }
}

loadSession();
refreshStreak();
