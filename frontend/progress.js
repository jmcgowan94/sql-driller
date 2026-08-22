const MAX_LEVEL = 5;

function el(tag, opts = {}, children = []) {
  const node = document.createElement(tag);
  if (opts.className) node.className = opts.className;
  if (opts.text !== undefined) node.textContent = opts.text;
  for (const child of children) node.appendChild(child);
  return node;
}

async function loadProgress() {
  const res = await fetch("/api/progress");
  const data = await res.json();

  const dayStreakEl = document.getElementById("day-streak");
  dayStreakEl.textContent =
    data.day_streak > 0
      ? `${data.day_streak} day${data.day_streak === 1 ? "" : "s"} in a row. Keep it going!`
      : "No streak yet — solve a question today to start one.";

  const topicsEl = document.getElementById("topics");
  topicsEl.innerHTML = "";
  for (const t of data.topics) {
    const pct = Math.round((t.level / MAX_LEVEL) * 100);
    const row = el("div", { className: "topic-row" }, [
      el("span", { className: "topic-name", text: t.topic.replace(/_/g, " ") }),
      el("div", { className: "level-track" }, [
        el("div", { className: "level-fill", text: "" }),
      ]),
      el("span", { className: "level-label", text: `L${t.level}/${MAX_LEVEL}` }),
    ]);
    row.querySelector(".level-fill").style.width = `${pct}%`;
    topicsEl.appendChild(row);
  }

  const historyEl = document.getElementById("history");
  historyEl.innerHTML = "";
  if (data.recent_attempts.length === 0) {
    historyEl.appendChild(el("p", { className: "empty", text: "No attempts yet." }));
    return;
  }
  const table = el("table", { className: "history-table" });
  const thead = el("thead", {}, [
    el("tr", {}, [
      el("th", { text: "Question" }),
      el("th", { text: "Topic" }),
      el("th", { text: "Difficulty" }),
      el("th", { text: "Result" }),
      el("th", { text: "When" }),
    ]),
  ]);
  const tbody = el("tbody");
  for (const a of data.recent_attempts) {
    const pill = el("span", {
      className: a.correct ? "pass-pill" : "fail-pill",
      text: a.correct ? "correct" : "incorrect",
    });
    const resultCell = el("td");
    resultCell.appendChild(pill);
    tbody.appendChild(
      el("tr", {}, [
        el("td", { text: a.question_id }),
        el("td", { text: a.topic.replace(/_/g, " ") }),
        el("td", { text: String(a.difficulty) }),
        resultCell,
        el("td", { text: a.timestamp }),
      ])
    );
  }
  table.appendChild(thead);
  table.appendChild(tbody);
  historyEl.appendChild(table);
}

loadProgress();
