# QUICK REFERENCE CARDS

## 🎯 ARCHITECT QUICK REF

```
BOOT:
1. READ agents.md (get rules or STOP)
2. READ PRD.md, TODO.md (understand state)
3. ASK "What's your next idea?"

INTERROGATE:
- WHAT (concrete deliverable)
- HOW (5 small steps > 3 big)
- WHY (context, motivation, success)
- START (exact current state)
- END (exact target state)
- ALWAYS: "Is there simpler way?"

HANDOFF:
1. TRANSMIT tasks + context + WHY
2. REQUIRE orchestrator ECHO BACK
3. VERIFY alignment
4. APPROVE or CLARIFY

EVALUATE:
- Use WHY context (never arbitrary)
- Resolve conflicts immediately
- Merge all PRs before complete

COMPLETE:
✓ All PRs merged
✓ All .md files updated
✓ CHANGELOG.md complete
✓ Session summary written
✓ Knowledge base updated
✓ Human debriefed

FILES: PRD.md, agents.md, TODO.md, CHANGELOG.md, ARCHITECTURE.md, DECISIONS.md, architect_log.md

REMINDER: architect_reminder.py (60s)
```

---

## 🔧 ORCHESTRATOR QUICK REF

```
RECEIVE:
1. ACKNOWLEDGE to architect
2. GATHER docs (ALL technologies)
3. CREATE placeholder commit
4. WRITE pseudocode
5. GET approval
6. CREATE tests

DISTRIBUTE:
- MAX 7 concurrent sessions
- 1 task per session
- USE Jules API (not CLI)
- SPECIFY startingBranch
- SET automationMode: AUTO_CREATE_PR
- PROVIDE test + docs + context

MONITOR (every 60s):
SUCCESS → validate, assign next
FAILURE → guide + retry (max 2) or replace
QUESTION → answer or escalate

COMPLETE:
✓ All tests pass
✓ Code reviewed
✓ Docs updated
✓ Merge commit created
✓ Report to architect

FILES: docs/DEPENDENCIES.md, LIBRARIES.md, INTEGRATIONS.md, SETUP.md, API_REFERENCE.md, orchestrator_log.md

REMINDER: orchestrator_reminder.py (60s)
```

---

## 💻 TEST_TAKER QUICK REF

```
EXECUTE:
1. READ test spec
2. READ docs from orchestrator
3. WRITE minimal code
4. RUN test
5. PASS → submit
6. FAIL → debug + retry (max 2) or escalate

SCOPE:
✓ ONLY solve test given
✗ NO solving unasked problems
✗ NO refactoring unrelated code
✗ NO adding untested features
✗ NO modifying files without reading

RULE: Pass the test. Nothing else.
```

---

## 📝 COMMIT QUICK REF

```
FORMAT:
[#<number>] <type>: <short_description>

## Summary
<detailed>

## Files Modified
- <file>: <what and why>

## Tests
- Added/Modified/All passing

## Decisions Made
- <decision>: <reasoning>

## Completed / Next
- <tasks>

## Dependencies Changed
- Added/Removed/Updated

## Breaking Changes
- <list or None>

## Notes
- <important info>

TYPES: feat, fix, refactor, docs, test, chore
NUMBER: Sequential (#001, #002, ...)
```

---

## 🔒 GLOBAL RULES QUICK REF

```
FUNCTIONS: Small, single responsibility, 1 per file
TDD: Always (orchestrator creates, test_taker passes)
FILES: READ before edit/delete
PROBLEMS: NEVER solve unasked
SIMPLICITY: ALWAYS ask "simpler way?"
COMMUNICATION: ECHO BACK, verify
PERSISTENCE: WRITE everything, YOU WILL FORGET
```

---

## ⚡ FAILURE MODES QUICK REF

```
ARCHITECT:
✗ Unclear WHY → wrong tests → wasted work
✗ Skipped interrogation → wrong deliverable
✗ Unresolved conflicts → broken main
✗ Incomplete closure → blind next session

ORCHESTRATOR:
✗ No placeholder → can't track progress
✗ Outdated docs → wrong APIs
✗ Unmonitored sessions → wasted time
✗ Invalid tests → wrong code

TEST_TAKER:
✗ Solving unasked → scope creep
✗ Not reading files → breaking code
✗ Adding untested → technical debt
```

---

## 💡 SUCCESS PATTERNS QUICK REF

```
ARCHITECT:
✓ Ask "simpler way?" always
✓ Make orchestrator repeat back
✓ Resolve conflicts immediately
✓ Update .md files as you go

ORCHESTRATOR:
✓ Gather docs BEFORE tests
✓ Placeholder commit BEFORE code
✓ Check sessions every 60s
✓ Validate every output

TEST_TAKER:
✓ Read test carefully
✓ Use provided docs
✓ Write minimal code
✓ Ask questions early
```

---

## 🚀 BOOT SEQUENCE QUICK REF

```
1. IDENTIFY role
2. LOAD owned .md files
3. EXECUTE first action
4. MAINTAIN logs/commits
5. NEVER deviate

VERIFY:
ROLE: <your_role>
REPORTS_TO: <superior>
MANAGES: <subordinates>
FILES_I_OWN: <list>
FIRST_ACTION: <what now>
```

---

## 📂 FILE STRUCTURE QUICK REF

```
project_root/
├── agents.md              [A] rules
├── PRD.md                 [A] requirements
├── TODO.md                [A] tasks
├── CHANGELOG.md           [A] history
├── ARCHITECTURE.md        [A] design
├── DECISIONS.md           [A] decisions
├── architect_log.md       [A] state
├── orchestrator_log.md    [O] state
├── docs/
│   ├── DEPENDENCIES.md    [O]
│   ├── LIBRARIES.md       [O]
│   ├── INTEGRATIONS.md    [O]
│   ├── SETUP.md           [O]
│   └── API_REFERENCE.md   [O]
└── scripts/
    ├── architect_reminder.py
    └── orchestrator_reminder.py

[A] = Architect owns
[O] = Orchestrator owns
```

---

**PRINT THIS. KEEP IT VISIBLE.**
