#!/usr/bin/env python3
"""
MB18+ DISCOVERY ENGINE

Auto-discovers failure modes not yet cataloged in MB7-MB17.
Clusters homologous failures and assigns MB18+ identifiers.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Load existing threat knowledge
KNOWN_THREATS = {
    'MB7': 'Generator Authority Independence',
    'MB14': 'Fresh-Clone Bootstrap Dependency',
    'MB15': 'Template Explosion Risk',
    'MB16': 'Short-Word False Match',
    'MB17': 'Authority Governance Gap'
}

# Failure pattern signatures
failure_patterns = []

# 1. Scan generated-artifact-registry for structural vulnerabilities
print("=" * 80)
print("MB18+ DISCOVERY PHASE")
print("=" * 80)
print()

with open('00-BOOK/DATA/generated-artifact-registry.json') as f:
    registry = json.load(f)

# Pattern detection data structures
input_classification_gaps = defaultdict(int)
deterministic_claims = defaultdict(list)
validation_gaps = defaultdict(list)
lifecycle_risks = defaultdict(list)
certification_role_gaps = defaultdict(list)

for entry in registry.get('entries', []):
    artifact_id = entry.get('artifact_id', 'UNKNOWN')
    owner = entry.get('owner', 'UNKNOWN')

    # Check input classification completeness
    input_closure = entry.get('input_closure', [])
    input_classification = entry.get('input_classification', {})

    for inp in input_closure:
        if inp not in input_classification:
            input_classification_gaps[owner] += 1
            failure_patterns.append({
                'signature': 'UNCLASSIFIED_INPUT',
                'artifact': artifact_id,
                'owner': owner,
                'detail': f'Input "{inp}" has no classification'
            })

    # Check deterministic claim vs environmental dependencies
    deterministic = entry.get('deterministic', False)
    env_deps = entry.get('environmental_dependencies', [])

    if deterministic and env_deps:
        deterministic_claims[owner].append(artifact_id)
        failure_patterns.append({
            'signature': 'DETERMINISTIC_WITH_ENV_DEPS',
            'artifact': artifact_id,
            'owner': owner,
            'detail': f'Claims deterministic but has env_deps: {env_deps}'
        })

    # Check validation coverage
    validation_owner = entry.get('validation_owner')
    independent_validation = entry.get('independent_validation')

    if not validation_owner and not independent_validation:
        validation_gaps[owner].append(artifact_id)
        failure_patterns.append({
            'signature': 'NO_VALIDATION_OWNER',
            'artifact': artifact_id,
            'owner': owner,
            'detail': 'Neither validation_owner nor independent_validation declared'
        })

    # Check lifecycle risks
    lifecycle = entry.get('lifecycle', 'UNKNOWN')
    regeneration_command = entry.get('regeneration_command')

    if lifecycle == 'REGENERATED' and not regeneration_command:
        lifecycle_risks[owner].append(artifact_id)
        failure_patterns.append({
            'signature': 'REGENERATED_WITHOUT_COMMAND',
            'artifact': artifact_id,
            'owner': owner,
            'detail': 'Lifecycle is REGENERATED but no regeneration_command'
        })

    # Check certification role clarity
    cert_role = entry.get('certification_role')
    canonical_role = entry.get('canonical_identity_role', 'UNKNOWN')

    if canonical_role == 'CANONICAL' and not cert_role:
        certification_role_gaps[owner].append(artifact_id)
        failure_patterns.append({
            'signature': 'CANONICAL_WITHOUT_CERT_ROLE',
            'artifact': artifact_id,
            'owner': owner,
            'detail': 'Canonical identity but no certification_role declared'
        })

# Cluster homologous failures
signature_clusters = defaultdict(list)
for pattern in failure_patterns:
    signature_clusters[pattern['signature']].append(pattern)

print(f"Total failure patterns discovered: {len(failure_patterns)}")
print(f"Unique failure signatures: {len(signature_clusters)}")
print()

# Assign MB18+ identifiers
mb_assignments = {}
mb_counter = 18

print("FAILURE SIGNATURE CLUSTERS:")
print("-" * 80)

for sig in sorted(signature_clusters.keys()):
    instances = signature_clusters[sig]
    affected_owners = set(p['owner'] for p in instances)

    mb_id = f"MB{mb_counter}"
    mb_assignments[sig] = mb_id
    mb_counter += 1

    print(f"\n{mb_id}: {sig}")
    print(f"  Instances: {len(instances)}")
    print(f"  Affected producers: {len(affected_owners)}")
    print(f"  Producers: {', '.join(sorted(affected_owners))}")

print()
print("=" * 80)

# Write discovery report
discovery_report = {
    'artifact_id': 'UCOS-MB18-DISCOVERY-001',
    'discovery_date': '2026-09-01',
    'methodology': 'Structural analysis of generated-artifact-registry.json',
    'known_threats': KNOWN_THREATS,
    'newly_discovered_threats': {},
    'total_failure_instances': len(failure_patterns),
    'unique_signatures': len(signature_clusters),
    'failure_patterns': failure_patterns
}

for sig, mb_id in mb_assignments.items():
    instances = signature_clusters[sig]
    discovery_report['newly_discovered_threats'][mb_id] = {
        'name': sig,
        'instance_count': len(instances),
        'affected_producers': sorted(set(p['owner'] for p in instances)),
        'severity': 'TBD',
        'description': 'Auto-discovered from registry structural analysis'
    }

with open('00-MASTER/mb18-discovery-report.json', 'w') as f:
    json.dump(discovery_report, f, indent=2)

print(f"Discovery report written to: 00-MASTER/mb18-discovery-report.json")
print(f"Total MB threats cataloged: {len(KNOWN_THREATS) + len(mb_assignments)}")
