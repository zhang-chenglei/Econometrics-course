(() => {
  "use strict";

  const root = document.querySelector(".agent-lab");
  if (!root) return;

  const pageId = root.dataset.labId || "lesson04-agent-lab";
  const key = (kind, id) => `${pageId}:${kind}:${id}`;
  const toast = document.createElement("div");
  toast.className = "lab-toast";
  toast.setAttribute("role", "status");
  document.body.appendChild(toast);
  let toastTimer;

  function notify(message) {
    toast.textContent = message;
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 1800);
  }

  const progressItems = [...root.querySelectorAll("[data-progress-id]")];
  const progressText = root.querySelector("[data-progress-text]");
  const progressFill = root.querySelector("[data-progress-fill]");

  function updateProgress() {
    const completed = progressItems.filter((item) => item.checked).length;
    const total = progressItems.length;
    const percent = total ? Math.round((completed / total) * 100) : 0;
    if (progressText) progressText.textContent = `${completed} / ${total} steps completed`;
    if (progressFill) progressFill.style.width = `${percent}%`;
  }

  progressItems.forEach((item) => {
    item.checked = localStorage.getItem(key("progress", item.dataset.progressId)) === "true";
    item.addEventListener("change", () => {
      localStorage.setItem(key("progress", item.dataset.progressId), String(item.checked));
      updateProgress();
    });
  });

  root.querySelectorAll("[data-note-id]").forEach((field) => {
    const saved = localStorage.getItem(key("note", field.dataset.noteId));
    if (saved !== null) field.value = saved;
    field.addEventListener("input", () => {
      localStorage.setItem(key("note", field.dataset.noteId), field.value);
    });
  });

  root.querySelectorAll("[data-design-field]").forEach((field) => {
    const saved = localStorage.getItem(key("design", field.dataset.designField));
    if (saved !== null) field.value = saved;
    field.addEventListener("input", () => {
      localStorage.setItem(key("design", field.dataset.designField), field.value);
    });
  });

  async function copyText(text, successMessage) {
    try {
      await navigator.clipboard.writeText(text.trim());
      notify(successMessage);
    } catch (_error) {
      const helper = document.createElement("textarea");
      helper.value = text.trim();
      helper.style.position = "fixed";
      helper.style.opacity = "0";
      document.body.appendChild(helper);
      helper.select();
      document.execCommand("copy");
      helper.remove();
      notify(successMessage);
    }
  }

  root.querySelectorAll("[data-copy-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (target) copyText(target.textContent, "Prompt 已复制");
    });
  });

  function designMarkdown() {
    const value = (name) => {
      const field = root.querySelector(`[data-design-field="${name}"]`);
      return field && field.value.trim() ? field.value.trim() : "（待填写）";
    };
    return [
      "# Research Design Card",
      "",
      `- **研究问题：** ${value("question")}`,
      `- **研究对象与单位：** ${value("unit")}`,
      `- **处理 / 核心解释变量：** ${value("treatment")}`,
      `- **结果变量：** ${value("outcome")}`,
      `- **目标因果参数：** ${value("estimand")}`,
      `- **理想反事实：** ${value("counterfactual")}`,
      `- **主要识别威胁：** ${value("threat")}`,
      `- **拟采用的研究设计：** ${value("strategy")}`,
      `- **识别 variation 来自：** ${value("variation")}`,
      `- **关键识别假设：** ${value("assumption")}`,
      `- **可做的诊断与证伪：** ${value("checks")}`,
      `- **结论边界：** ${value("boundary")}`,
    ].join("\n");
  }

  root.querySelectorAll("[data-copy-design]").forEach((button) => {
    button.addEventListener("click", () => copyText(designMarkdown(), "Research Design Card 已复制为 Markdown"));
  });

  root.querySelectorAll("[data-print-lab]").forEach((button) => {
    button.addEventListener("click", () => window.print());
  });

  root.querySelectorAll("[data-reset-lab]").forEach((button) => {
    button.addEventListener("click", () => {
      const confirmed = window.confirm("清除本页保存的进度、笔记与 Research Design Card？");
      if (!confirmed) return;
      Object.keys(localStorage)
        .filter((item) => item.startsWith(`${pageId}:`))
        .forEach((item) => localStorage.removeItem(item));
      progressItems.forEach((item) => { item.checked = false; });
      root.querySelectorAll("[data-note-id], [data-design-field]").forEach((field) => { field.value = ""; });
      updateProgress();
      notify("本页记录已清除");
    });
  });

  updateProgress();
})();
