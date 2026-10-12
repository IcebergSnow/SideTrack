// Vercel's HTML integration, loaded separately to keep the CSP free of inline scripts.
if (!["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname)) {
  window.va = window.va || function () {
    (window.vaq = window.vaq || []).push(arguments);
  };

  const script = document.createElement("script");
  script.src = "/_vercel/insights/script.js";
  script.defer = true;
  document.head.appendChild(script);
}
