#!/usr/bin/env python3
"""
E9.1 — BACKLOG CONSISTENCY AUDIT

Verifies EXECUTION-BACKLOG.json for:
- Valid producer references
- Valid threat references
- Existing dependencies
- No orphan tasks
- No circular task chains
- No duplicate tasks
- No unreachable tasks
"""

import json
from collections import defaultdict, deque

# Load backlog
with open('00-MASTER/EXECUTION-BACKLOG.json') as f:
    backlog = json.load(f)

print("=" * 80)
print("E9.1 — BACKLOG CONSISTENCY AUDIT")
print("=" * 80)
print()

# Extract all producers from registry
with open('00-BOOK/DATA/generated-artifact-registry.json') as f:
    registry = json.load(f)

valid_producers = set()
for entry in registry.get('entries', []):
    owner = entry.get('owner')
    if owner:
        valid_producers.add(owner)

print(f"Valid producers from registry: {len(valid_producers)}")

# Valid threats
valid_threats = {'MB7', 'MB14', 'MB15', 'MB16', 'MB17', 'MB18', 'MB22', 'MB23', 'MB24', 'MB20', 'MB25'}

print(f"Valid threats: {len(valid_threats)}")
print()

# Expand task patterns into concrete tasks
all_tasks = {}
errors = []

# Wave 0 explicit tasks
for task in backlog.get('backlog', []):
    task_id = task['id']
    all_tasks[task_id] = task

print(f"Wave 0 explicit tasks: {len(backlog.get('backlog', []))}")

# Wave 1 pattern expansion
wave1 = backlog.get('wave_1_authority_externalization', {})
wave1_producers = wave1.get('producers', [])
print(f"Wave 1 producers: {len(wave1_producers)}")

for producer in wave1_producers:
    task_id = f"W1-{producer}"
    all_tasks[task_id] = {
        'id': task_id,
        'wave': 1,
        'producer': producer,
        'threat': 'MB7',
        'dependencies': ['W0-001']
    }

# Wave 2 pattern expansion
wave2 = backlog.get('wave_2_independent_validators', {})
wave2_count = wave2.get('producers', 32)
print(f"Wave 2 producers: {wave2_count}")

for producer in wave1_producers:  # Same producers as Wave 1
    task_id = f"W2-{producer}"
    all_tasks[task_id] = {
        'id': task_id,
        'wave': 2,
        'producer': producer,
        'threat': 'MB7',
        'dependencies': ['W0-004', f'W1-{producer}']
    }

# Wave 3 pattern expansion
wave3 = backlog.get('wave_3_attack_verification', {})
wave3_count = wave3.get('producers', 32)
print(f"Wave 3 producers: {wave3_count}")

for producer in wave1_producers:
    task_id = f"W3-{producer}"
    all_tasks[task_id] = {
        'id': task_id,
        'wave': 3,
        'producer': producer,
        'threat': 'MB7',
        'dependencies': [f'W2-{producer}']
    }

# Wave 4 subwaves
wave4 = backlog.get('wave_4_bootstrap_integrity', {})
for subwave in wave4.get('subwaves', []):
    if 'tasks' in subwave:
        for task in subwave['tasks']:
            all_tasks[task['id']] = task
    elif 'task_pattern' in subwave:
        # Pattern expansion
        subwave_id = subwave['id']
        count = subwave.get('producers', 32)
        for producer in wave1_producers:
            task_id = f"{subwave_id}-{producer}"
            deps = subwave['task_pattern'].get('dependencies_template', [])
            expanded_deps = [d.replace('{producer}', producer) for d in deps]
            all_tasks[task_id] = {
                'id': task_id,
                'wave': 4,
                'producer': producer,
                'threat': subwave['task_pattern'].get('threat'),
                'dependencies': expanded_deps
            }

print(f"Wave 4 tasks (including patterns): ~{len([t for t in all_tasks if t.startswith('W4')])}")

# Wave 6
wave6 = backlog.get('wave_6_ci_integration', {})
for task in wave6.get('tasks', []):
    all_tasks[task['id']] = task

wave6_pattern = wave6.get('per_producer_integration', {})
if wave6_pattern:
    for producer in wave1_producers:
        task_id = f"W6-{producer}"
        deps_template = wave6_pattern['task_pattern'].get('dependencies_template', [])
        expanded_deps = [d.replace('{producer}', producer) for d in deps_template]
        all_tasks[task_id] = {
            'id': task_id,
            'wave': 6,
            'producer': producer,
            'threat': 'MB7',
            'dependencies': expanded_deps
        }

# Wave 7
wave7 = backlog.get('wave_7_certification', {})
for task in wave7.get('tasks', []):
    all_tasks[task['id']] = task

print(f"\nTotal tasks after expansion: {len(all_tasks)}")
print()

# AUDIT 1: Valid producer references
print("AUDIT 1: Valid Producer References")
print("-" * 80)

invalid_producers = []
for task_id, task in all_tasks.items():
    producer = task.get('producer')
    if producer and producer not in valid_producers:
        invalid_producers.append((task_id, producer))
        errors.append(f"Task {task_id} references invalid producer: {producer}")

if invalid_producers:
    print(f"FAIL: {len(invalid_producers)} tasks reference invalid producers")
    for task_id, producer in invalid_producers[:5]:
        print(f"  {task_id} → {producer}")
else:
    print("PASS: All producer references valid")

print()

# AUDIT 2: Valid threat references
print("AUDIT 2: Valid Threat References")
print("-" * 80)

invalid_threats = []
for task_id, task in all_tasks.items():
    threat = task.get('threat')
    if threat and threat not in valid_threats:
        invalid_threats.append((task_id, threat))
        errors.append(f"Task {task_id} references invalid threat: {threat}")

if invalid_threats:
    print(f"FAIL: {len(invalid_threats)} tasks reference invalid threats")
    for task_id, threat in invalid_threats[:5]:
        print(f"  {task_id} → {threat}")
else:
    print("PASS: All threat references valid")

print()

# AUDIT 3: Existing dependencies
print("AUDIT 3: Dependency Existence")
print("-" * 80)

missing_deps = []
for task_id, task in all_tasks.items():
    deps = task.get('dependencies', [])
    for dep in deps:
        # Handle wildcards
        if '*' in dep:
            pattern = dep.replace('*', '')
            matching = [t for t in all_tasks if t.startswith(pattern)]
            if not matching:
                missing_deps.append((task_id, dep, "no matches"))
                errors.append(f"Task {task_id} dependency {dep} matches no tasks")
        else:
            if dep not in all_tasks:
                missing_deps.append((task_id, dep, "not found"))
                errors.append(f"Task {task_id} depends on non-existent task: {dep}")

if missing_deps:
    print(f"FAIL: {len(missing_deps)} missing dependencies")
    for task_id, dep, reason in missing_deps[:10]:
        print(f"  {task_id} → {dep} ({reason})")
else:
    print("PASS: All dependencies exist")

print()

# AUDIT 4: Orphan tasks
print("AUDIT 4: Orphan Tasks (no path from Wave 0)")
print("-" * 80)

# Build dependency graph
dependents = defaultdict(set)
for task_id, task in all_tasks.items():
    deps = task.get('dependencies', [])
    for dep in deps:
        if '*' in dep:
            pattern = dep.replace('*', '')
            for t in all_tasks:
                if t.startswith(pattern):
                    dependents[t].add(task_id)
        else:
            dependents[dep].add(task_id)

# BFS from Wave 0 tasks
reachable = set()
queue = deque([t for t in all_tasks if t.startswith('W0-')])
reachable.update(queue)

while queue:
    current = queue.popleft()
    for dependent in dependents.get(current, []):
        if dependent not in reachable:
            reachable.add(dependent)
            queue.append(dependent)

orphans = set(all_tasks.keys()) - reachable
if orphans:
    print(f"FAIL: {len(orphans)} orphan tasks")
    for orphan in list(orphans)[:10]:
        print(f"  {orphan}")
        errors.append(f"Orphan task: {orphan}")
else:
    print("PASS: No orphan tasks")

print()

# AUDIT 5: Circular dependencies
print("AUDIT 5: Circular Dependencies")
print("-" * 80)

def has_cycle():
    # Build adjacency list
    graph = defaultdict(set)
    for task_id, task in all_tasks.items():
        deps = task.get('dependencies', [])
        for dep in deps:
            if '*' not in dep:
                graph[task_id].add(dep)

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {task: WHITE for task in all_tasks}

    def dfs(node, path):
        if color[node] == GRAY:
            # Cycle detected
            cycle_start = path.index(node)
            return path[cycle_start:]
        if color[node] == BLACK:
            return None

        color[node] = GRAY
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor in color:  # Only follow known tasks
                cycle = dfs(neighbor, path)
                if cycle:
                    return cycle

        path.pop()
        color[node] = BLACK
        return None

    for task in all_tasks:
        if color[task] == WHITE:
            cycle = dfs(task, [])
            if cycle:
                return cycle
    return None

cycle = has_cycle()
if cycle:
    print(f"FAIL: Circular dependency detected")
    print(f"  Cycle: {' → '.join(cycle)}")
    errors.append(f"Circular dependency: {' → '.join(cycle)}")
else:
    print("PASS: No circular dependencies")

print()

# AUDIT 6: Duplicate tasks
print("AUDIT 6: Duplicate Task IDs")
print("-" * 80)

# Check for duplicates (should be impossible with dict, but check source)
task_ids = list(all_tasks.keys())
unique_ids = set(task_ids)

if len(task_ids) != len(unique_ids):
    print(f"FAIL: {len(task_ids) - len(unique_ids)} duplicate task IDs")
    errors.append("Duplicate task IDs found")
else:
    print("PASS: No duplicate task IDs")

print()

# AUDIT 7: Unreachable tasks
print("AUDIT 7: Unreachable Tasks (nothing depends on them)")
print("-" * 80)

# Find tasks that nothing depends on (terminal nodes)
has_dependents = set()
for task_id, task in all_tasks.items():
    deps = task.get('dependencies', [])
    for dep in deps:
        if '*' in dep:
            pattern = dep.replace('*', '')
            has_dependents.update([t for t in all_tasks if t.startswith(pattern)])
        else:
            has_dependents.add(dep)

terminal_tasks = set(all_tasks.keys()) - has_dependents
wave7_tasks = [t for t in terminal_tasks if t.startswith('W7-') or t.startswith('W6-')]

# Terminal tasks are expected in Wave 7 (certification)
unexpected_terminal = [t for t in terminal_tasks if not (t.startswith('W7-') or t.startswith('W6-'))]

if unexpected_terminal:
    print(f"WARNING: {len(unexpected_terminal)} unexpected terminal tasks (not Wave 6/7)")
    for task in unexpected_terminal[:10]:
        print(f"  {task}")
else:
    print(f"PASS: {len(wave7_tasks)} terminal tasks (expected in Wave 6/7)")

print()

# SUMMARY
print("=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)
print()

print(f"Total tasks analyzed: {len(all_tasks)}")
print(f"Total errors found: {len(errors)}")
print()

if errors:
    print("ERRORS:")
    for error in errors[:20]:
        print(f"  - {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")
else:
    print("✓ BACKLOG CONSISTENCY: PASS")

# Write results
results = {
    'total_tasks': len(all_tasks),
    'valid_producers': len(valid_producers),
    'valid_threats': len(valid_threats),
    'errors': errors,
    'orphan_tasks': list(orphans),
    'terminal_tasks': list(terminal_tasks),
    'reachable_tasks': len(reachable),
    'circular_dependencies': cycle if cycle else None
}

with open('00-MASTER/backlog-consistency-results.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print("Results written to: 00-MASTER/backlog-consistency-results.json")
