import { COPYRIGHT_YEAR } from "./config.js";

document.addEventListener("DOMContentLoaded", () => {
  const yearEl = document.getElementById("copyright-year");
  if (yearEl) {
    yearEl.textContent = COPYRIGHT_YEAR;
  }
});