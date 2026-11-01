#!/usr/bin/env node
// Task-local static audit of the existing CSS oracle cases.
// Flags checks that are not anchored to a literal expected value, and checks
// whose expected value depends on the host viewport width.
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const src = readFileSync(resolve(repo, 'scripts/web_markup_assertions.mjs'), 'utf8');

const start = src.indexOf("// CSS examples (100)");
const end = src.indexOf('// Public entry');
const css = src.slice(start, end);

const blocks = css.split(/CSS_CASES\.set\('([^']+)'/).slice(1);
const rows = [];
for (let i = 0; i < blocks.length; i += 2) {
  const id = blocks[i];
  const body = blocks[i + 1];
  const calls = [...body.matchAll(/addCheck\(([\s\S]*?)\);/g)].map((m) => m[1].replace(/\s+/g, ' '));
  const flags = [];
  for (const c of calls) {
    if (/!== *'none'/.test(c)) flags.push(`non-none: ${c.slice(0, 90)}`);
    if (/!== *null|!== *undefined/.test(c)) flags.push(`non-null: ${c.slice(0, 90)}`);
    if (/> *0[^.\d]/.test(c)) flags.push(`positive: ${c.slice(0, 90)}`);
    if (/\|\|/.test(c)) flags.push(`or-fallback: ${c.slice(0, 90)}`);
    if (/< *1\)|<= *1\)|< *10/.test(c)) flags.push(`threshold-only: ${c.slice(0, 90)}`);
    if (/viewportSize|innerWidth/.test(c)) flags.push(`viewport-bound: ${c.slice(0, 90)}`);
    if (/\.length *> *0|length !== 0/.test(c)) flags.push(`non-empty: ${c.slice(0, 90)}`);
  }
  // `.includes(` used against a computed string that has no literal value pair
  for (const c of calls) {
    if (/includes\(/.test(c) && !/===|!==/.test(c)) flags.push(`substring-only: ${c.slice(0, 90)}`);
  }
  rows.push({ id, checks: calls.length, flags: [...new Set(flags)] });
}

const totalChecks = rows.reduce((s, r) => s + r.checks, 0);
const weakRows = rows.filter((r) => r.flags.length);
let md = '# Existing CSS oracle — static quality audit\n\n';
md += `Source: scripts/web_markup_assertions.mjs (read-only). Cases: ${rows.length}. addCheck calls: ${totalChecks}.\n\n`;
md += `Cases with at least one non-literal / host-bound expectation: ${weakRows.length}/${rows.length}.\n\n`;
for (const r of weakRows) {
  md += `## ${r.id} (${r.checks} checks)\n`;
  for (const f of r.flags) md += `- ${f}\n`;
  md += '\n';
}
const minChecks = [...rows].sort((a, b) => a.checks - b.checks).slice(0, 8);
md += `Fewest checks: ${minChecks.map((r) => `${r.id}=${r.checks}`).join(', ')}\n`;
console.log(md);
