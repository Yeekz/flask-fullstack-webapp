/**
 * dashboard.js — project creation & deletion without page reload.
 * Uses fetch() against the REST API /api/projects.
 */

(function () {
  "use strict";

  const modal = document.getElementById("modal-project");
  const btnNew = document.getElementById("btn-new-project");
  const btnCancel = document.getElementById("btn-cancel-project");
  const form = document.getElementById("form-project");
  const projName = document.getElementById("proj-name");
  const projDesc = document.getElementById("proj-desc");
  const projError = document.getElementById("proj-error");
  const grid = document.getElementById("projects-grid");
  const emptyMsg = document.getElementById("empty-msg");
  let selectedColor = "#6366f1";

  // Color picker
  document.querySelectorAll(".color-swatch").forEach((swatch) => {
    swatch.addEventListener("click", () => {
      document.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("selected"));
      swatch.classList.add("selected");
      selectedColor = swatch.dataset.color;
    });
  });

  btnNew.addEventListener("click", () => modal.classList.remove("hidden"));
  btnCancel.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

  function closeModal() {
    modal.classList.add("hidden");
    form.reset();
    selectedColor = "#6366f1";
    document.querySelectorAll(".color-swatch").forEach((s, i) => {
      s.classList.toggle("selected", i === 0);
    });
    showError("");
  }

  function showError(msg) {
    projError.textContent = msg;
    projError.classList.toggle("hidden", !msg);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = projName.value.trim();
    if (!name) { showError("Le nom est requis."); return; }

    const res = await window.taskflowFetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: projDesc.value.trim(), color: selectedColor }),
    });
    const json = await res.json();

    if (!json.success) { showError(json.error || "Erreur inconnue."); return; }

    appendProjectCard(json.data);
    if (emptyMsg) emptyMsg.remove();
    closeModal();
  });

  function appendProjectCard(p) {
    const card = document.createElement("article");
    card.className = "project-card";
    card.dataset.id = p.id;
    card.style.borderTop = `4px solid ${p.color}`;
    card.innerHTML = `
      <div class="project-card-header">
        <h3><a href="/projects/${p.id}">${escHtml(p.name)}</a></h3>
        <button class="btn-icon btn-delete-project" data-id="${p.id}" title="Supprimer">✕</button>
      </div>
      <p class="project-desc">${escHtml(p.description || "Aucune description.")}</p>
      <span class="badge">0 tâche</span>
    `;
    card.querySelector(".btn-delete-project").addEventListener("click", handleDelete);
    grid.appendChild(card);
  }

  // Wire existing delete buttons (server-rendered cards)
  document.querySelectorAll(".btn-delete-project").forEach((btn) => {
    btn.addEventListener("click", handleDelete);
  });

  async function handleDelete(e) {
    const id = e.currentTarget.dataset.id;
    if (!confirm("Supprimer ce projet et toutes ses tâches ?")) return;

    const res = await window.taskflowFetch(`/api/projects/${id}`, { method: "DELETE" });
    const json = await res.json();
    if (!json.success) { alert(json.error || "Erreur lors de la suppression."); return; }

    const card = grid.querySelector(`[data-id="${id}"]`);
    if (card) card.remove();
    if (!grid.querySelector(".project-card")) {
      const p = document.createElement("p");
      p.id = "empty-msg";
      p.className = "empty-state";
      p.textContent = "Aucun projet pour l'instant. Créez-en un !";
      grid.appendChild(p);
    }
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
