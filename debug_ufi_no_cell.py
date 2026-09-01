#!/usr/bin/env python3
"""
Instrumented UFI trace for "no" cell failure diagnosis.

Adds debug output at cell validation point to show exact runtime state.
"""

import json
import os
import re
import sys

# Copy relevant UFI code with instrumentation

REPO = "/Users/bipin/Desktop/UCOS-CONSOLIDATION"
MIN_SLOT = 6
CELL_CLEAN = re.compile(r"^[`*_\s]+|[`*_\s]+$")

def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()

def cell_is_derived_instrumented(cell: str, corpus: set, allowed_cells: set, lengths: list) -> bool:
    """Instrumented version showing exact runtime evaluation."""
    print(f"\n{'='*60}")
    print(f"CELL_IS_DERIVED EVALUATION")
    print(f"{'='*60}")
    print(f"Input cell (repr):     {repr(cell)}")
    print(f"Input cell (str):      '{cell}'")
    print(f"Input cell length:     {len(cell)}")

    c = CELL_CLEAN.sub("", cell).strip()
    print(f"After CELL_CLEAN+strip: '{c}'")
    print(f"Cleaned length:        {len(c)}")
    print(f"Cleaned repr:          {repr(c)}")

    print(f"\nCONDITION CHECKS:")
    print(f"  1. Empty check: not c = {not c}")

    in_allowed = c in allowed_cells
    print(f"  2. In allowed_cells: {in_allowed}")
    if not in_allowed and len(allowed_cells) < 50:
        print(f"     allowed_cells contents: {sorted(allowed_cells)}")
    else:
        print(f"     allowed_cells size: {len(allowed_cells)}")
        # Show subset around "no"
        subset = sorted([x for x in allowed_cells if len(x) < 10])
        print(f"     Short cells in allowed_cells: {subset}")

    in_corpus = c in corpus
    print(f"  3. In corpus: {in_corpus}")
    if not in_corpus and len(c) < 10:
        corpus_subset = sorted([x for x in corpus if len(x) < 10])[:20]
        print(f"     Short strings in corpus (first 20): {corpus_subset}")

    if not c or in_allowed or in_corpus:
        print(f"\nRESULT: TRUE (condition 1, 2, or 3 passed)")
        return True

    substring_match = len(c) >= MIN_SLOT and any(c in s for s in corpus)
    print(f"  4. Substring check: len(c)={len(c)} >= MIN_SLOT={MIN_SLOT} = {len(c) >= MIN_SLOT}")
    if len(c) >= MIN_SLOT:
        print(f"     Substring in corpus: {substring_match}")
    else:
        print(f"     SKIPPED (length < MIN_SLOT)")

    if substring_match:
        print(f"\nRESULT: TRUE (condition 4 passed)")
        return True

    concat_check = len(c) > 40
    print(f"  5. Concatenation check: len(c)={len(c)} > 40 = {concat_check}")
    if not concat_check:
        print(f"     SKIPPED (length <= 40)")

    print(f"\nRESULT: FALSE (all conditions failed)")
    print(f"{'='*60}\n")
    return False

# Load manifest and check for "no"
manifest_path = os.path.join(REPO, "00-BOOK/DATA/context-template-manifest.json")
manifest = json.loads(read(manifest_path))

print("MANIFEST ANALYSIS")
print("="*60)
print(f"Manifest path: {manifest_path}")
print(f"allowed_cells count: {len(manifest.get('allowed_cells', []))}")
print(f"\nSearching for 'no' in allowed_cells:")

allowed_cells_list = manifest.get("allowed_cells", [])
for i, cell in enumerate(allowed_cells_list):
    if cell.lower() == "no" or "no" in cell.lower():
        print(f"  Line {i}: {repr(cell)}")

if "no" in allowed_cells_list:
    print(f"\n'no' FOUND in allowed_cells at index: {allowed_cells_list.index('no')}")
else:
    print(f"\n'no' NOT FOUND in allowed_cells")

print(f"\nSearching for 'YES' in allowed_cells:")
if "YES" in allowed_cells_list:
    print(f"'YES' FOUND at index: {allowed_cells_list.index('YES')}")
else:
    print(f"'YES' NOT FOUND")

print(f"\nShort entries (len <= 5) in allowed_cells:")
short_entries = [x for x in allowed_cells_list if len(x) <= 5]
print(f"  {short_entries}")

# Simulate UFI processing
allowed_cells_set = set(allowed_cells_list)
corpus = set()  # Empty for this test - we're testing allowed_cells only

print("\n\nSIMULATED CELL VALIDATION")
print("="*60)

# Test cells
test_cells = [
    "no",
    " no ",
    "YES",
    " YES ",
    "Role",
    "Class"
]

for test_cell in test_cells:
    result = cell_is_derived_instrumented(test_cell, corpus, allowed_cells_set, [])
    print(f"Final result for {repr(test_cell)}: {result}\n")
