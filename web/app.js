"use strict";
const fileInput = document.getElementById("csv-file");
const profileInput = document.getElementById("profile");
const result = document.getElementById("result");
const summary = document.getElementById("summary");
const issueList = document.getElementById("issues");
const download = document.getElementById("download");
let currentReport = null;
let currentText = "";
let generation = 0;

function display(text) {
  currentReport = null;
  download.disabled = true;
  issueList.replaceChildren();
  result.hidden = false;
  try {
    currentReport = CatalogPreflight.analyzeCsv(text, profileInput.value);
    summary.textContent = `${currentReport.data_records} data records checked · ${currentReport.errors} errors · ${currentReport.warnings} warnings`;
    if (!currentReport.issues.length) {
      const item = document.createElement("li");
      item.textContent = "No findings in these limited checks. Review the platform’s own importer before making changes to a store.";
      issueList.append(item);
    }
    for (const issue of currentReport.issues) {
      const item = document.createElement("li");
      item.className = issue.severity;
      item.textContent = `Line ${issue.row}${issue.column ? `, column ${issue.column}` : ""} · ${issue.code}: ${issue.explanation}`;
      issueList.append(item);
    }
    if (currentReport.findings_truncated) {
      const item = document.createElement("li");
      item.textContent = "The first 1,000 findings are shown. Counts include all detected findings.";
      issueList.append(item);
    }
    download.disabled = false;
  } catch (error) {
    summary.textContent = error instanceof CatalogPreflight.CsvError
      ? `Line ${error.line} · ${error.code}: ${error.message}` : "The file could not be checked. Try a smaller UTF-8 CSV.";
  }
}

fileInput.addEventListener("change", async () => {
  const request = ++generation;
  const file = fileInput.files[0];
  currentText = ""; currentReport = null; download.disabled = true;
  issueList.replaceChildren(); result.hidden = false;
  if (!file) { result.hidden = true; return; }
  if (file.size > CatalogPreflight.LIMITS.bytes) { summary.textContent = "Choose a file no larger than 2 MiB."; return; }
  summary.textContent = "Reading the file on this device…";
  try {
    const bytes = await file.arrayBuffer();
    if (request !== generation) return;
    currentText = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    display(currentText);
  } catch (_) {
    if (request === generation) summary.textContent = "Could not read UTF-8 text. Export a fresh UTF-8 CSV in your editor.";
  }
});
profileInput.addEventListener("change", () => { if (currentText) display(currentText); });
document.getElementById("sample").addEventListener("click", () => {
  generation++; fileInput.value = "";
  currentText = "Handle,Title,Variant SKU,Variant Price,Option1 Value\nlinen-shirt,Linen shirt,SHIRT-M,29.00,Medium\nlinen-shirt,,SHIRT-M,EUR 29,Medium\n";
  profileInput.value = "shopify";
  display(currentText);
});
document.getElementById("reset").addEventListener("click", () => {
  generation++; fileInput.value = ""; currentText = ""; currentReport = null;
  download.disabled = true; result.hidden = true; issueList.replaceChildren(); summary.textContent = "";
});
download.addEventListener("click", () => {
  if (!currentReport) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(currentReport, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url; link.download = "catalog-preflight-report.json"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
