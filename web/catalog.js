/* Original local-only CSV preflight. No requests, telemetry, or code evaluation. */
(function (root) {
  "use strict";
  const LIMITS = Object.freeze({ bytes: 2 * 1024 * 1024, rows: 10000, columns: 100, cell: 20000, issues: 1000 });
  class CsvError extends Error {
    constructor(code, line, message) { super(message); this.name = "CsvError"; this.code = code; this.line = line; }
  }
  function parseCsv(source) {
    if (typeof source !== "string") throw new TypeError("CSV must be text");
    if (new TextEncoder().encode(source).length > LIMITS.bytes) throw new CsvError("FILE_LIMIT", 1, "File exceeds the 2 MiB limit.");
    if (source.includes("\0")) throw new CsvError("NUL_BYTE", 1, "The file contains a null byte; check its encoding.");
    const text = source.replace(/^\uFEFF/, "");
    const records = [];
    let fields = [], field = "", state = "plain", line = 1, start = 1, touched = false;
    function cell() {
      fields.push(field); field = ""; state = "plain";
      if (fields.length > LIMITS.columns) throw new CsvError("COLUMN_LIMIT", start, "File exceeds the 100-column limit.");
    }
    function record() {
      cell(); records.push({ line: start, cells: fields }); fields = []; touched = false;
      if (records.length > LIMITS.rows + 1) throw new CsvError("ROW_LIMIT", start, "File exceeds 10,000 data records.");
    }
    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      if (state === "quoted") {
        if (char === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; } else state = "closed";
        } else if (char === "\r" || char === "\n") {
          if (char === "\r" && text[i + 1] === "\n") i++;
          field += "\n"; line++;
        } else field += char;
      } else if (char === ",") { cell(); touched = true; }
      else if (char === "\r" || char === "\n") {
        if (char === "\r" && text[i + 1] === "\n") i++;
        record(); line++; start = line;
      } else if (state === "closed") {
        throw new CsvError("AFTER_QUOTE", line, "Only a comma or line ending may follow a closing quote.");
      } else if (char === '"') {
        if (field) throw new CsvError("STRAY_QUOTE", line, "A quote appears inside an unquoted field.");
        state = "quoted"; touched = true;
      } else { field += char; touched = true; }
      if (field.length > LIMITS.cell) throw new CsvError("CELL_LIMIT", start, "A field exceeds 20,000 characters.");
    }
    if (state === "quoted") throw new CsvError("UNCLOSED_QUOTE", start, "A quoted field has no closing quote.");
    if (touched || fields.length || field || state === "closed") record();
    return records;
  }
  const ALIASES = Object.freeze({
    "url handle": "handle", "handle": "handle", "title": "title", "variant sku": "sku", "sku": "sku",
    "variant price": "price", "price": "price", "image src": "image", "product image url": "image",
    "option1 value": "option1", "option2 value": "option2", "option3 value": "option3"
  });
  function analyzeCsv(text, profile = "shopify") {
    if (!["shopify", "generic"].includes(profile)) throw new TypeError("Unknown check profile");
    const records = parseCsv(text);
    const report = { version: 1, profile, status: "limited_preflight", data_records: Math.max(0, records.length - 1),
      columns: records.length ? records[0].cells.length : 0, errors: 0, warnings: 0, issues: [],
      findings_truncated: false, contains_cell_values: false, import_success_guaranteed: false };
    function issue(severity, row, column, code, explanation) {
      report[severity === "error" ? "errors" : "warnings"]++;
      if (report.issues.length < LIMITS.issues) report.issues.push({ severity, row, column, code, explanation });
      else report.findings_truncated = true;
    }
    if (!records.length) { issue("error", 1, null, "EMPTY_FILE", "The file has no header record."); return report; }
    const header = records[0].cells, normalized = header.map(value => value.trim().toLowerCase()), seen = new Set(), mapping = {};
    normalized.forEach((name, index) => {
      if (!name) issue("error", 1, index + 1, "EMPTY_HEADER", "This column has no heading.");
      if (seen.has(name)) issue("error", 1, index + 1, "DUPLICATE_HEADER", "Two headings match after trimming and case normalization.");
      seen.add(name);
      if (header[index] !== header[index].trim()) issue("warning", 1, index + 1, "HEADER_SPACE", "A heading has leading or trailing whitespace.");
      const alias = ALIASES[name];
      if (profile === "shopify" && alias) {
        if (mapping[alias] !== undefined) issue("error", 1, index + 1, "AMBIGUOUS_HEADER", "More than one column maps to the same catalog field.");
        else mapping[alias] = index;
      }
    });
    if (header.length === 1) issue("warning", 1, 1, "SINGLE_COLUMN", "Only one column was found. This checker expects commas, not semicolons or tabs.");
    if (records.length === 1) issue("warning", 1, null, "NO_DATA", "The file contains a header but no data records.");
    if (profile === "shopify") {
      for (const key of ["handle", "title"]) if (mapping[key] === undefined)
        issue("warning", 1, null, "CATALOG_HEADER_ABSENT", "A common catalog heading is absent. Review the platform format and whether this is a new-product or update file.");
    }
    const skus = new Map(), variants = new Map();
    for (const record of records.slice(1)) {
      const cells = record.cells, row = record.line;
      if (cells.every(value => !value.trim())) { issue("warning", row, null, "EMPTY_RECORD", "This data record is empty."); continue; }
      if (cells.length !== header.length) { issue("error", row, null, "COLUMN_COUNT", "This record has a different number of fields from the header."); continue; }
      cells.forEach((value, index) => {
        if (/^\s*[=+@-]/.test(value)) issue("warning", row, index + 1, "FORMULA_LIKE", "This value resembles a spreadsheet formula. Review before opening it in spreadsheet software; text may also match this heuristic.");
      });
      if (profile !== "shopify") continue;
      const get = key => mapping[key] === undefined ? "" : cells[mapping[key]].trim();
      const price = get("price"), sku = get("sku"), handle = get("handle");
      if (price && !/^\d+(\.\d+)?$/.test(price)) issue("warning", row, mapping.price + 1, "PRICE_FORMAT", "Review this price: expected a nonnegative number using a decimal point, without a currency symbol.");
      if (sku) {
        if (skus.has(sku)) issue("warning", row, mapping.sku + 1, "REPEATED_SKU", "This SKU appeared in an earlier record. Some workflows permit this; review its intended meaning.");
        else skus.set(sku, row);
      }
      const options = [get("option1"), get("option2"), get("option3")];
      // Repeated handles in image-only continuation rows are legitimate.
      if (handle && options.some(Boolean)) {
        const signature = JSON.stringify([handle, ...options]);
        if (variants.has(signature)) issue("warning", row, mapping.handle + 1, "REPEATED_VARIANT", "An earlier row has the same handle and option values. Review a possible variant collision.");
        else variants.set(signature, row);
      }
    }
    return report;
  }
  const api = Object.freeze({ LIMITS, CsvError, parseCsv, analyzeCsv });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CatalogPreflight = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
