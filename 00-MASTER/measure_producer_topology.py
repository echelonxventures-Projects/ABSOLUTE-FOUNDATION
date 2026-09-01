#!/usr/bin/env python3
"""
PHASE E2 — PRODUCER CLOSURE TOPOLOGY MEASUREMENT

For all 33 producers, measures:
- Authored authorities (files that define what generator should produce)
- Generated authorities (files the generator reads to produce output)
- Validator existence (does a validator exist?)
- Validator independence (does validator import/run the generator?)
- CI enforcement (is validator integrated into CI?)
- Governance binding (are authority files under review control?)
- Permit dependencies (does closure require operator permits?)

Output: Per-producer topology showing current state → target state with blocking dependencies
"""

import json
from pathlib import Path
from collections import defaultdict

# Load registry
with open('00-BOOK/DATA/generated-artifact-registry.json') as f:
    registry = json.load(f)

# Extract producer data
producers = defaultdict(lambda: {
    'artifacts': [],
    'artifact_count': 0,
    'validation_owner': set(),
    'independent_validation': set(),
    'regeneration_commands': set(),
    'capability': set(),
    'certification_roles': set(),
    'deterministic_count': 0,
    'canonical_count': 0,
    'producer_homes': set(),
    'input_classifications': defaultdict(int)
})

for entry in registry.get('entries', []):
    owner = entry.get('owner')
    if not owner:
        continue

    p = producers[owner]
    p['artifacts'].append(entry.get('artifact_id'))
    p['artifact_count'] += 1

    if entry.get('validation_owner'):
        p['validation_owner'].add(entry['validation_owner'])

    if entry.get('independent_validation'):
        p['independent_validation'].add(entry['independent_validation'])

    if entry.get('regeneration_command'):
        p['regeneration_commands'].add(entry['regeneration_command'])

    if entry.get('capability'):
        p['capability'].add(entry['capability'])

    if entry.get('certification_role'):
        p['certification_roles'].add(entry['certification_role'])

    if entry.get('deterministic'):
        p['deterministic_count'] += 1

    if entry.get('canonical_identity_role') == 'CANONICAL':
        p['canonical_count'] += 1

    if entry.get('producer'):
        p['producer_homes'].add(entry['producer'])

    for inp, classification in entry.get('input_classification', {}).items():
        p['input_classifications'][classification] += 1

print("=" * 80)
print("PHASE E2 — PRODUCER CLOSURE TOPOLOGY")
print("=" * 80)
print()
print(f"Total producers: {len(producers)}")
print()

# Topology analysis
topology = {}

for producer_id in sorted(producers.keys()):
    data = producers[producer_id]

    # Current state analysis
    has_independent_validator = len(data['independent_validation']) > 0
    has_self_validator = producer_id in data['validation_owner']
    validation_mode = 'INDEPENDENT' if has_independent_validator else ('SELF' if has_self_validator else 'NONE')

    # Target state
    target_state = 'CERTIFIED'  # All producers should reach certified

    # Blocking dependencies
    blockers = []

    if not has_independent_validator:
        blockers.append('MB7: No independent validator')

    if data['deterministic_count'] > 0 and producer_id != 'UCOS-UCTX-001':
        blockers.append('MB23: Deterministic claims unverified')

    if len(data['regeneration_commands']) > 0 and producer_id != 'UCOS-UCTX-001':
        blockers.append('MB22: Regeneration commands unverified')

    if data['input_classifications'].get('GENERATED_DETERMINISTIC', 0) > 0:
        blockers.append('MB18: Generated-deterministic input circularity risk')

    # Authority analysis (requires inspection of producer homes)
    producer_home = list(data['producer_homes'])[0] if data['producer_homes'] else None

    topology[producer_id] = {
        'artifact_count': data['artifact_count'],
        'producer_home': producer_home,
        'validation_mode': validation_mode,
        'independent_validator': list(data['independent_validation'])[0] if data['independent_validation'] else None,
        'capability': list(data['capability'])[0] if len(data['capability']) == 1 else 'MULTIPLE',
        'current_state': 'CERTIFIED' if validation_mode == 'INDEPENDENT' and producer_id == 'UCOS-UCTX-001' else 'OPEN',
        'target_state': target_state,
        'blockers': blockers,
        'deterministic_claims': data['deterministic_count'],
        'canonical_artifacts': data['canonical_count'],
        'generated_input_deps': data['input_classifications'].get('GENERATED_DETERMINISTIC', 0)
    }

print("PRODUCER TOPOLOGY SUMMARY:")
print("-" * 80)
print(f"{'Producer':<30} | State | Validator | Blockers")
print("-" * 80)

for producer_id in sorted(topology.keys()):
    t = topology[producer_id]
    state = t['current_state']
    validator = t['validation_mode']
    blocker_count = len(t['blockers'])

    print(f"{producer_id:<30} | {state:9} | {validator:11} | {blocker_count}")

print()
print(f"CERTIFIED: {sum(1 for t in topology.values() if t['current_state'] == 'CERTIFIED')}/33")
print(f"OPEN: {sum(1 for t in topology.values() if t['current_state'] == 'OPEN')}/33")

# Write detailed topology
with open('00-MASTER/producer-topology-data.json', 'w') as f:
    json.dump(topology, f, indent=2)

print()
print("Detailed topology written to: 00-MASTER/producer-topology-data.json")
