document.addEventListener("DOMContentLoaded", () => {
  const sid = document.body.dataset.sid;

  // ----- Duration slider value mirror + scrollable header controls
  const durationForm = document.querySelector(".duration-form");
  if (durationForm) {
    const range = durationForm.querySelector('input[type="range"]');
    const label = durationForm.querySelector(".duration-value");
    range.addEventListener("input", () => { label.textContent = `${range.value}m`; });
  }

  // Keyboard navigation
  const blocks = [...document.querySelectorAll("section.block")];
  let idx = 0;
  const go = (i) => {
    idx = Math.max(0, Math.min(blocks.length - 1, i));
    blocks[idx].scrollIntoView({ behavior: "smooth", block: "start" });
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { go(idx + 1); }
    if (e.key === "ArrowLeft")  { go(idx - 1); }
    if (e.key.toLowerCase() === "m") {
      const bid = blocks[idx].id;
      fetch(`/session/${sid}/toggle-covered/${bid}`, { method: "POST" }).then(() => location.reload());
    }
    if (e.key.toLowerCase() === "g") {
      const bid = blocks[idx].id;
      gen(bid);
    }
    if (e.key === "?") {
      const h = document.getElementById("help");
      h.hidden = !h.hidden;
    }
  });

  // MCQ buttons
  document.querySelectorAll(".btn.gen").forEach(btn => {
    btn.addEventListener("click", () => gen(btn.dataset.bid));
  });

function renderMCQs(bid, mcqs) {
  const host = document.getElementById(`mcq-${bid}`);
  host.innerHTML = "";
  mcqs.forEach((q, i) => {
    const wrap = document.createElement("div");
    wrap.className = "mcq-item";
    const opts = q.options.map((o, j) => `<div class="opt">${String.fromCharCode(65+j)}. ${o}</div>`).join("");
    wrap.innerHTML = `
      <div class="qhead">Q${i+1}. ${q.question}</div>
      <div class="opts">${opts}</div>
      <div class="mcq-actions">
        <button class="btn small asked" data-index="${i}">Mark as asked</button>
        <button class="btn small outline show">Show answer</button>
        <span class="answer" hidden><strong>Answer:</strong> ${q.answer}</span>
      </div>
    `;
    host.appendChild(wrap);

    // asked
    wrap.querySelector("button.asked").addEventListener("click", () => {
      fetch(`/session/${sid}/mcq_asked/${bid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(q)
      }).then(() => {
        wrap.classList.add("asked-done");
        wrap.querySelector("button.asked").disabled = true;
      }).catch(()=>{});
    });

    // show/hide answer
    const showBtn = wrap.querySelector("button.show");
    const ans = wrap.querySelector(".answer");
    showBtn.addEventListener("click", () => {
      const vis = ans.hasAttribute("hidden");
      if (vis) { ans.removeAttribute("hidden"); showBtn.textContent = "Hide answer"; }
      else { ans.setAttribute("hidden",""); showBtn.textContent = "Show answer"; }
    });
  });
}

  function gen(bid) {
    const out = document.getElementById(`mcq-${bid}`);
    out.textContent = "Generating…";
    fetch(`/session/${sid}/mcq/${bid}`, { method: "POST" })
      .then(r => r.json())
      .then(js => renderMCQs(bid, js))
      .catch(() => out.textContent = "Failed to generate.");
  }
});
