/**
 * board.js — Kanban board interactions.
 * Creates / edits / deletes tasks and moves them between columns
 * via the REST API without page reload.
 * PROJECT_ID is injected by the template before this script loads.
 */

(function () {
  "use strict";

  const PROJECT_ID = document.querySelector(".board-page").dataset.projectId;
  const API = `/api/projects/${PROJECT_ID}/tasks`;

  // ---- Modal elements ----
  const modal = document.getElementById("modal-task");
  const modalTitle = document.getElementById("modal-task-title");
  const form = document.getElementById("form-task");
  const taskId = document.getElementById("task-id");
  const taskTitle = document.getElementById("task-title");
  const taskDesc = document.getElementById("task-desc");
  const taskStatus = document.getElementById("task-status");
  const taskPriority = document.getElementById("task-priority");
  const taskDue = document.getElementById("task-due");
  const taskError = document.getElementById("task-error");
  const btnSubmit = document.getElementById("btn-submit-task");
  const btnCancel = document.getElementById("btn-cancel-task");
  const btnNew = document.getElementById("btn-new-task");

  // ---- Open / close modal ----
  btnNew.addEventListener("click", () => openModal());
  btnCancel.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

  function openModal(task = null) {
    form.reset();
    showError("");
    if (task) {
      modalTitle.textContent = "Modifier la tâche";
      btnSubmit.textContent = "Enregistrer";
      taskId.value = task.id;
      taskTitle.value = task.title;
      taskDesc.value = task.description || "";
      taskStatus.value = task.status;
      taskPriority.value = task.priority;
      taskDue.value = task.due_date || "";
    } else {
      modalTitle.textContent = "Créer une tâche";
      btnSubmit.textContent = "Créer";
      taskId.value = "";
    }
    modal.classList.remove("hidden");
  }

  function closeModal() {
    modal.classList.add("hidden");
  }

  function showError(msg) {
    taskError.textContent = msg;
    taskError.classList.toggle("hidden", !msg);
  }

  // ---- Submit create / update ----
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = taskId.value;
    const payload = {
      title: taskTitle.value.trim(),
      description: taskDesc.value.trim(),
      status: taskStatus.value,
      priority: taskPriority.value,
      due_date: taskDue.value || null,
    };

    const url = id ? `${API}/${id}` : API;
    const method = id ? "PUT" : "POST";

    const res = await window.taskflowFetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const json = await res.json();
    if (!json.success) { showError(json.error || "Erreur inconnue."); return; }

    closeModal();
    if (id) {
      updateTaskCard(json.data);
    } else {
      appendTaskCard(json.data);
    }
  });

  // ---- Wire existing move / edit / delete buttons (server-rendered) ----
  document.querySelectorAll(".btn-move").forEach(wireMoveBtn);
  document.querySelectorAll(".btn-edit-task").forEach(wireEditBtn);
  document.querySelectorAll(".btn-delete-task").forEach(wireDeleteBtn);

  function wireMoveBtn(btn) {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const target = btn.dataset.target;
      const res = await window.taskflowFetch(`${API}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: target }),
      });
      const json = await res.json();
      if (!json.success) { alert(json.error || "Erreur."); return; }
      updateTaskCard(json.data);
    });
  }

  function wireEditBtn(btn) {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const res = await window.taskflowFetch(`${API}/${id}`);
      const json = await res.json();
      if (!json.success) { alert(json.error || "Erreur."); return; }
      openModal(json.data);
    });
  }

  function wireDeleteBtn(btn) {
    btn.addEventListener("click", async () => {
      if (!confirm("Supprimer cette tâche ?")) return;
      const id = btn.dataset.id;
      const res = await window.taskflowFetch(`${API}/${id}`, { method: "DELETE" });
      const json = await res.json();
      if (!json.success) { alert(json.error || "Erreur."); return; }
      const card = document.querySelector(`.task-card[data-id="${id}"]`);
      if (card) {
        const col = card.closest(".kanban-col");
        card.remove();
        updateColCount(col);
      }
    });
  }

  // ---- DOM helpers ----
  function buildTaskCard(task) {
    const card = document.createElement("div");
    card.className = `task-card priority-${task.priority}`;
    card.dataset.id = task.id;
    card.dataset.status = task.status;

    const prevTarget = task.status === "todo" ? null : (task.status === "doing" ? "todo" : "doing");
    const nextTarget = task.status === "done" ? null : (task.status === "todo" ? "doing" : "done");
    const prevLabel = task.status === "doing" ? "← Reculer" : "← Reculer";
    const nextLabel = task.status === "todo" ? "Avancer →" : "Avancer →";

    card.innerHTML = `
      <div class="task-card-header">
        <span class="priority-badge priority-${task.priority}">${task.priority}</span>
        <div class="task-actions">
          <button class="btn-icon btn-edit-task" data-id="${task.id}" title="Éditer">✎</button>
          <button class="btn-icon btn-delete-task" data-id="${task.id}" title="Supprimer">✕</button>
        </div>
      </div>
      <h4 class="task-title">${escHtml(task.title)}</h4>
      ${task.description ? `<p class="task-desc">${escHtml(task.description)}</p>` : ""}
      ${task.due_date ? `<p class="task-due">📅 ${escHtml(task.due_date)}</p>` : ""}
      <div class="task-move-buttons">
        ${prevTarget ? `<button class="btn-move" data-id="${task.id}" data-target="${prevTarget}">${prevLabel}</button>` : ""}
        ${nextTarget ? `<button class="btn-move" data-id="${task.id}" data-target="${nextTarget}">${nextLabel}</button>` : ""}
      </div>
    `;

    card.querySelectorAll(".btn-move").forEach(wireMoveBtn);
    card.querySelectorAll(".btn-edit-task").forEach(wireEditBtn);
    card.querySelectorAll(".btn-delete-task").forEach(wireDeleteBtn);
    return card;
  }

  function appendTaskCard(task) {
    const col = document.getElementById(`col-${task.status}`);
    if (!col) return;
    const card = buildTaskCard(task);
    col.appendChild(card);
    updateColCount(col.closest(".kanban-col"));
  }

  function updateTaskCard(task) {
    const existing = document.querySelector(`.task-card[data-id="${task.id}"]`);
    if (!existing) { appendTaskCard(task); return; }

    const oldCol = existing.closest(".kanban-col");
    const newColCards = document.getElementById(`col-${task.status}`);
    const newCard = buildTaskCard(task);

    existing.replaceWith(newCard);

    // If status changed, move to correct column
    if (existing.dataset.status !== task.status) {
      newColCards.appendChild(newCard);
    }

    updateColCount(oldCol);
    if (newColCards) updateColCount(newColCards.closest(".kanban-col"));
  }

  function updateColCount(colEl) {
    if (!colEl) return;
    const status = colEl.dataset.status;
    const count = colEl.querySelectorAll(".task-card").length;
    const counter = document.getElementById(`count-${status}`);
    if (counter) counter.textContent = count;
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
