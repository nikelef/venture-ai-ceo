const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { analyzeCsv, parseCsv, CsvError, LIMITS } = require("../web/catalog.js");

test("CSV parser handles BOM, CRLF, escaped quotes, multiline and trailing empty fields", () => {
  const records = parseCsv('\uFEFFname,description,last\r\n"shirt","two\r\nlines and ""quotes""",\r\n');
  assert.deepEqual(records.map(item => item.cells), [["name", "description", "last"], ["shirt", 'two\nlines and "quotes"', ""]]);
  assert.equal(records[1].line, 2);
  assert.equal(parseCsv("a,b\n\"two\nlines\",x\nnext,y")[2].line, 4);
});
test("invalid quoting and NUL data fail with safe diagnostics", () => {
  for (const text of ['a\n"unclosed', 'a\nunquoted"quote', 'a\n"closed"trailing', "a\0b"])
    assert.throws(() => parseCsv(text), CsvError);
});
test("resource ceilings reject oversized files, records, cells and columns", () => {
  assert.throws(() => parseCsv("x".repeat(LIMITS.bytes + 1)), /2 MiB/);
  assert.throws(() => parseCsv("a\n" + "x\n".repeat(LIMITS.rows + 1)), /10,000/);
  assert.throws(() => parseCsv("x".repeat(LIMITS.cell + 1)), /20,000/);
  assert.throws(() => parseCsv(new Array(101).fill("x").join(",")), /100-column/);
});
test("structural problems are located without exporting any source content", () => {
  const report = analyzeCsv("Private heading,Private heading\nPRIVATE-CELL-ABC\n");
  assert.ok(report.issues.some(item => item.code === "DUPLICATE_HEADER"));
  assert.ok(report.issues.some(item => item.code === "COLUMN_COUNT" && item.row === 2));
  const encoded = JSON.stringify(report);
  assert.ok(!encoded.includes("PRIVATE-CELL-ABC"));
  assert.ok(!encoded.includes("Private heading"));
  assert.equal(report.import_success_guaranteed, false);
});
test("legacy and current catalog aliases detect variant collisions and price formats", () => {
  for (const header of ["Handle,Title,Variant SKU,Variant Price,Option1 Value", "URL handle,Title,SKU,Price,Option1 value"]) {
    const report = analyzeCsv(header + "\nshirt,Shirt,SHIRT-M,20.00,Medium\nshirt,,SHIRT-M,EUR 20,Medium");
    assert.deepEqual(report.issues.map(item => item.code).sort(), ["PRICE_FORMAT", "REPEATED_SKU", "REPEATED_VARIANT"]);
  }
});
test("image continuation rows do not create false duplicate variants", () => {
  const report = analyzeCsv("Handle,Title,Variant SKU,Variant Price,Option1 Value,Image Src\nshirt,Shirt,SKU,12.00,Medium,https://example.org/1.jpg\nshirt,,,,,https://example.org/2.jpg");
  assert.equal(report.errors, 0);
  assert.equal(report.warnings, 0);
});
test("formula warnings never evaluate or echo the input", () => {
  const report = analyzeCsv("heading\n=PRIVATE_FORMULA()", "generic");
  assert.ok(report.issues.some(item => item.code === "FORMULA_LIKE"));
  assert.ok(!JSON.stringify(report).includes("PRIVATE_FORMULA"));
});
test("generic profile does not apply catalog assumptions and handles empty files", () => {
  assert.equal(analyzeCsv("", "generic").issues[0].code, "EMPTY_FILE");
  assert.equal(analyzeCsv("a,b\nx,y", "generic").issues.length, 0);
  assert.throws(() => analyzeCsv("a,b", "unknown"), TypeError);
});
test("findings are bounded and counts still cover all rows", () => {
  const report = analyzeCsv("heading\n" + "=formula\n".repeat(2000), "generic");
  assert.equal(report.issues.length, LIMITS.issues);
  assert.equal(report.findings_truncated, true);
  assert.ok(report.warnings >= 2000);
});
test("catalog code keeps file content local; page permits only the consented collector", () => {
  const app = readFileSync(require.resolve("../web/app.js"), "utf8");
  assert.ok(!/innerHTML|outerHTML|insertAdjacentHTML|eval\s*\(|new Function|fetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|localStorage|sessionStorage/.test(app));
  const html = readFileSync(require.resolve("../web/index.html"), "utf8");
  const config = readFileSync(require.resolve("../web/experiment-config.js"), "utf8");
  if (config.includes('endpoint:""')) assert.ok(html.includes("connect-src 'none'"));
  else assert.match(html, /connect-src https:\/\/[a-z0-9.-]+\.aws\.neon\.tech;/);
  assert.ok(html.includes("form-action 'none'"));
  assert.ok(!/checkout\.stripe|<iframe\b/.test(html));
});
