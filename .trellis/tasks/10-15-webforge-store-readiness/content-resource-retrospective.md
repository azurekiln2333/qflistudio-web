# Bug Analysis: inline media rejected by CSS

## 1. Root Cause Category
Categories B (cross-layer contract) and D (coverage gap). Source replacement
made SVGs self-contained, but some unquoted CSS data URLs contained raw
whitespace. Chromium discarded the whole background declaration although the
SVG decoded when loaded directly.

A later review also found a synthetic WOFF2 header with no usable font tables.
It produced no network 404, so resource checks alone missed it. The source now
requires an original generated font and a real `document.fonts.load` oracle.

## 2. Why earlier fixes failed
Removing network URLs proved only resource location. The first browser probe
also tolerated absent companion assets and used weaker background checks.
Later strict checks showed `backgroundImage=none`. A controlled browser probe
kept the same SVG and quoted its URL; the declaration then survived and decoded.
That distinguished source syntax from a selector/oracle mistake.

## 3. Prevention Mechanisms
| Priority | Mechanism | Action |
| --- | --- | --- |
| P0 | Source fix | Quote/encode CSS data URLs across the owning CSS sources |
| P0 | Browser verification | Require computed image URL and actual decode |
| P0 | Resource integrity | Reject requests that fail or return HTTP >=400; only exact lesson006/path teaching exception |
| P1 | Repeatability | Retain generators, lock browser dependency and compare repeated emit hashes |

## 4. Systematic Expansion
The scan includes all HTML/CSS source modules and supplement lessons. Companion
CSS/JS/fonts and JSON fetches must work in the delivered single HTML document;
runner-only HTTP fixtures cannot make an incomplete import appear functional.
Each example uses a new browser context to reveal storage dependencies.

## 5. Knowledge Capture
- [x] frontend/content-import.md documents the consumer-syntax and decode checks.
- [x] Independent markup oracle checks inline image and CSS background decode.
- [x] Runner rejects external requests and unexpected missing resources.
- [x] Final per-entry report remains the acceptance record; an intermediate
  successful source scan is not a release pass.
