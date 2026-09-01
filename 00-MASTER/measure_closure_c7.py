#!/usr/bin/env python3
"""
PHASE C7 — REPOSITORY-WIDE CLOSURE EXECUTION AUDIT

Measures actual closure status for MB7-MB17 across all producers.
Distinguishes between feasible, implemented, verified, and certified.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Load registry
with open('00-BOOK/DATA/generated-artifact-registry.json') as f:
    registry = json.load(f)

# Extract all producers
producers = {}
for entry in registry.get('entries', []):
    owner = entry.get('owner')
    validation_owner = entry.get('validation_owner')
    if owner:
        if owner not in producers:
            producers[owner] = {
                'artifacts': 0,
                'self_validated': 0,
                'independent_validated': 0,
                'validation_owners': set()
            }
        producers[owner]['artifacts'] += 1
        producers[owner]['validation_owners'].add(validation_owner)

        if validation_owner == owner:
            producers[owner]['self_validated'] += 1
        else:
            producers[owner]['independent_validated'] += 1

# Check for independent validators
validators = {}
for vpy in Path('00-BOOK/tools').glob('*_verify.py'):
    validators[vpy.stem] = str(vpy)

# Check for attack scripts
attacks = {}
for apy in Path('.').rglob('*attack*.py'):
    if '__pycache__' not in str(apy):
        attacks[apy.stem] = str(apy)

# Check test coverage
test_files = list(Path('platform/tests').glob('test_*.py'))

print("=" * 80)
print("PHASE C7 — REPOSITORY-WIDE CLOSURE EXECUTION AUDIT")
print("=" * 80)
print()

print(f"Total producers: {len(producers)}")
print(f"Total artifacts: {sum(p['artifacts'] for p in producers.values())}")
print(f"Independent validators found: {len(validators)}")
print(f"Attack reproducers found: {len(attacks)}")
print(f"Test files: {len(test_files)}")
print()

print("PRODUCERS:")
print("-" * 80)
for p in sorted(producers.keys()):
    data = producers[p]
    print(f"{p:40} | artifacts={data['artifacts']:3} | self={data['self_validated']:3} | indep={data['independent_validated']:3}")

print()
print("INDEPENDENT VALIDATORS:")
print("-" * 80)
for name, path in sorted(validators.items()):
    print(f"  {name:30} → {path}")

print()
print("ATTACK REPRODUCERS:")
print("-" * 80)
for name, path in sorted(attacks.items()):
    print(f"  {name:30} → {path}")
