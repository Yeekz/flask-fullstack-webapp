"use strict";

window.taskflowFetch = async function (url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (!["GET", "HEAD", "OPTIONS"].includes((options.method || "GET").toUpperCase())) {
    headers.set("X-CSRF-Token", document.querySelector('meta[name="csrf-token"]').content);
  }
  try {
    const response = await fetch(url, { ...options, headers, credentials: "same-origin" });
    if (!response.headers.get("content-type")?.includes("application/json")) {
      return { json: async () => ({ success: false, error: "Le serveur est indisponible. Rechargez la page puis réessayez." }) };
    }
    return response;
  } catch {
    return { json: async () => ({ success: false, error: "Connexion interrompue. Réessayez quand le réseau est disponible." }) };
  }
};
