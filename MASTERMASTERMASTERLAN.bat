



# PROMETHEUS: Autonomous Code Genesis System
## Master Blueprint v1.0

---

# TABLE OF CONTENTS

1. [Philosophy & Principles](#1-philosophy--principles)
2. [System Hierarchy](#2-system-hierarchy)
3. [Role Specifications](#3-role-specifications)
   - 3.1 Human
   - 3.2 Producer
   - 3.3 Research Agents
   - 3.4 Architects
   - 3.5 Conductors
   - 3.6 Builders
   - 3.7 Cops (Internal Affairs)
4. [Infrastructure](#4-infrastructure)
   - 4.1 Repository Structure
   - 4.2 Branch Hierarchy
   - 4.3 Commit Protocol
   - 4.4 Issue-Based State Management
   - 4.5 Label Taxonomy
5. [GitHub Configuration](#5-github-configuration)
   - 5.1 Branch Protection Rules
   - 5.2 Issue Templates
   - 5.3 Workflow Files
6. [Prompt Templates](#6-prompt-templates)
7. [LLM Selection Guide](#7-llm-selection-guide)
8. [Execution Guide](#8-execution-guide)
9. [Monitoring & Metrics](#9-monitoring--metrics)
10. [Failure Recovery](#10-failure-recovery)

---

# 1. PHILOSOPHY & PRINCIPLES

## 1.1 Core Philosophy
````
SIMPLE > COMPLEX
100 builders × 10 tiny tasks > 10 builders × 100 big tasks
DETERMINISTIC infrastructure > SEMANTIC oversight
````

## 1.2 Guiding Principles

| Principle | Meaning | Implementation |
|-----------|---------|----------------|
| **Radical Simplicity** | Every test is small. Every task is few tests. Every epic is few tasks. | Max 5 tests per task. Max 10 tasks per epic. |
| **Deterministic Backbone** | Infrastructure cannot be persuaded or confused. | GitHub hooks, actions, branch protection enforce rules. |
| **Context Flows Down** | Every agent knows WHY, not just WHAT. | Context restated at every handoff. |
| **Parallel by Default** | Speed through parallelism, not rushing. | Modular code, independent tasks, many builders. |
| **Tests are Truth** | Code is correct when tests pass. Period. | TDD at every level. Acceptance tests gate completion. |
| **Commits are Communication** | All agents speak through commits. | Structured commit protocol. |
| **Fail Fast, Fail Loud** | Problems surface immediately. | Cops block bad commits. Issues created automatically. |
| **Human at Endpoints Only** | Human approves plan, receives product. Nothing in between. | Full automation after project agreement. |

## 1.3 The Hierarchy of Simplicity
````
PROGRAM = set of EPICS (max 10)
EPIC = set of TASKS (max 10)  
TASK = set of TESTS (max 5)
TEST = single assertion with single code change
````

Total maximum: 10 × 10 × 5 = 500 atomic tests per program
Each test: ~5-50 lines of code
Result: Massive parallelization potential

---

# 2. SYSTEM HIERARCHY
````
                            +---------+
                            ¦  HUMAN  ¦
                            +---------+
                                 ¦ idea
                                 ?
                          +--------------+
                          ¦   PRODUCER   ¦ (1 instance)
                          ¦   [Claude]   ¦
                          +--------------+
                                 ¦
              +------------------+------------------+
              ?                  ?                  ?
      +---------------+  +---------------+  +---------------+
      ¦ RESEARCH-DOCS ¦  ¦ RESEARCH-PRIOR¦  ¦ RESEARCH-STACK¦
      ¦   [Claude]    ¦  ¦   [Claude]    ¦  ¦   [Claude]    ¦
      +---------------+  +---------------+  +---------------+
              +------------------+------------------+
                                 ¦ knowledge
                                 ?
                          +--------------+
                          ¦   PRODUCER   ¦ (creates epics)
                          +--------------+
                                 ¦
         +-----------------------+-----------------------+
         ?                       ?                       ?
  +-------------+         +-------------+         +-------------+
  ¦ ARCHITECT   ¦         ¦ ARCHITECT   ¦         ¦ ARCHITECT   ¦
  ¦ [frontend]  ¦         ¦ [backend]   ¦         ¦ [database]  ¦
  ¦ [Claude]    ¦         ¦ [Claude]    ¦         ¦ [Claude]    ¦
  +-------------+         +-------------+         +-------------+
         ¦                       ¦                       ¦
    +---------+             +---------+             +---------+
    ?         ?             ?         ?             ?         ?
+--------++--------+   +--------++--------+   +--------++--------+
¦CONDUCTOR¦¦CONDUCTOR¦   ¦CONDUCTOR¦¦CONDUCTOR¦   ¦CONDUCTOR¦¦CONDUCTOR¦
¦[GLM4.7]¦¦[GLM4.7]¦   ¦[GLM4.7]¦¦[GLM4.7]¦   ¦[GLM4.7]¦¦[GLM4.7]¦
+--------++--------+   +--------++--------+   +--------++--------+
    ¦         ¦           ¦         ¦           ¦         ¦
+-------+ +-------+   +-------+ +-------+   +-------+ +-------+
¦BUILDER¦ ¦BUILDER¦   ¦BUILDER¦ ¦BUILDER¦   ¦BUILDER¦ ¦BUILDER¦
¦[Codex]¦ ¦[Codex]¦   ¦[Codex]¦ ¦[Codex]¦   ¦[Codex]¦ ¦[Codex]¦
+-------+ +-------+   +-------+ +-------+   +-------+ +-------+

                    INTERNAL AFFAIRS (COPS)
    +------------------------------------------------------+
    ¦  GATE_COP    SCOPE_COP    TEST_COP    CONTEXT_COP   ¦
    ¦  [script]    [script]     [script]    [Haiku]       ¦
    ¦                                                      ¦
    ¦              WATCHDOG_COP [cron script]              ¦
    +------------------------------------------------------+
````

---

# 3. ROLE SPECIFICATIONS

## 3.1 Human

### Responsibilities
- Provide initial idea/vision
- Answer Producer's questions (one at a time)
- Approve final project plan
- Receive completed product

### Boundaries
- NO involvement after project plan approval
- NO direct communication with Architects, Conductors, or Builders
- Escalations come through Producer only

---

## 3.2 Producer

### Identity
````yaml
role: Producer
instance: PRODUCER-1
llm: Claude (claude-sonnet-4-5 or opus)
purpose: Transform human idea into executable project plan
````

### Responsibilities

1. **Discovery Phase**
   - Ask Human questions ONE AT A TIME
   - Wait for answer before next question
   - Continue until full understanding achieved
   - Questions cover: WHAT, WHO, WHY, HOW, SUCCESS CRITERIA

2. **Research Phase**
   - Launch 3 Research Agents in parallel
   - Receive and synthesize research findings
   - Store findings in `/research/` folder

3. **Planning Phase**
   - Create project documents (PRD.md, CONTEXT.md, etc.)
   - Decompose program into epics (max 10)
   - Assign each epic to domain-specific Architect
   - Define acceptance criteria for each epic

4. **Orchestration Phase**
   - Launch Architects via Python script
   - Monitor Architect progress via GitHub Issues
   - Intervene on escalations
   - Check context alignment periodically

5. **Assembly Phase**
   - Review all epic PRs when complete
   - Run integration tests
   - Merge to main
   - Present to Human

### Inputs
- Human idea (natural language)
- Research findings (from Research Agents)

### Outputs
- `/docs/PRD.md` - Product Requirements Document
- `/docs/CONTEXT.md` - Project context and priorities
- `/docs/ARCHITECTURE.md` - System architecture
- `/docs/AGENTS.md` - Agent behavior rules
- `/docs/CONVENTIONS.md` - Coding conventions
- GitHub Issues for each epic (assigned to Architects)

### Scripts Producer Creates
````python
# /scripts/launch_architects.py
# Launches all Architect instances with context

# /scripts/producer_watchdog.py  
# Runs every 5 minutes, checks Architect heartbeats

# /scripts/assemble_epics.py
# Merges all epic branches when complete
````

### Commit Signature
````
[PRODUCER][PRODUCER-1][EPIC-X] STATUS: description
````

---

## 3.3 Research Agents

### Identity
````yaml
role: Research Agent
instances: 3
llm: Claude with web search (or Perplexity API)
purpose: Gather comprehensive knowledge for project
````

### The Three Research Agents

#### RESEARCH-DOCS
````yaml
id: RESEARCH-DOCS
focus: Official documentation
sources:
  - Context7 (up-to-date docs)
  - Ref (documentation search)
  - Official library docs
  - API references
output: /research/documentation.md
````

#### RESEARCH-PRIOR
````yaml
id: RESEARCH-PRIOR
focus: Prior art and existing solutions
sources:
  - GitHub (similar projects)
  - Stack Overflow (solved problems)
  - Technical blogs
  - npm/PyPI (existing packages)
output: /research/prior_art.md
````

#### RESEARCH-STACK
````yaml
id: RESEARCH-STACK
focus: Technology decisions and best practices
sources:
  - Architecture patterns
  - Framework comparisons
  - Performance benchmarks
  - Security best practices
output: /research/tech_stack.md
````

### Research Output Format
````markdown
# Research Report: [DOMAIN]

## Executive Summary
[2-3 sentences]

## Key Findings
1. [Finding with source URL]
2. [Finding with source URL]
...

## Recommended Approach
[Based on findings]

## Code Examples
[Relevant snippets from research]

## Warnings/Gotchas
[Things to avoid based on research]

## Sources
- [URL 1]
- [URL 2]
...
````

---

## 3.4 Architects

### Identity
````yaml
role: Architect
instances: 1 per domain (frontend, backend, database, etc.)
llm: Claude (planning) or GLM 4.7 (if long-running)
purpose: Own an epic from tasks to completion
````

### Responsibilities

1. **Receive Epic from Producer**
   - Read epic Issue
   - Read all context documents
   - Read research findings

2. **Plan Phase**
   - Decompose epic into tasks (max 10)
   - Write acceptance criteria for each task
   - Identify dependencies between tasks
   - Create task Issues in GitHub

3. **Dispatch Phase**
   - Assign tasks to Conductors
   - Provide each Conductor with:
     - Task Issue
     - Relevant context
     - Acceptance criteria
     - WHY this task matters

4. **Monitor Phase**
   - Check Conductor progress (via GitHub Issues)
   - Answer Conductor questions (via Issue comments)
   - Resolve escalations
   - Enforce context alignment

5. **Review Phase**
   - Review task PRs from Conductors
   - Verify acceptance criteria met
   - Merge to epic branch
   - Report progress to Producer

### Inputs
- Epic Issue from Producer
- Context documents
- Research findings

### Outputs
- Task Issues (assigned to Conductors)
- Epic branch with all merged tasks
- PR to main when epic complete

### Scripts Architect Creates
````python
# /scripts/architect_{domain}_launcher.py
# Launches Conductors for this domain

# /scripts/architect_{domain}_watchdog.py
# Monitors Conductor heartbeats
````

### Commit Signature
````
[ARCHITECT][ARCH-{DOMAIN}][TASK-X] STATUS: description
````

### Architect Issue Template (receives from Producer)
````markdown
## Epic: [EPIC_NAME]

**Architect**: ARCH-{DOMAIN}
**Branch**: epic/{domain}

### Context
[WHY this epic exists - copied from CONTEXT.md]

### Scope
[WHAT this epic must accomplish]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
...

### Dependencies
- Depends on: [other epics if any]
- Blocks: [other epics if any]

### Resources
- PRD: /docs/PRD.md
- Context: /docs/CONTEXT.md
- Research: /research/
````

---

## 3.5 Conductors

### Identity
````yaml
role: Conductor
instances: 1+ per Architect (parallel)
llm: GLM 4.7 Max (reliable long-running orchestration)
purpose: Own a task from tests to completion
````

### Why GLM 4.7 for Conductors

Per user experience:
- Can run for hours reliably
- Excellent at orchestrating sub-agents
- Interleaved thinking allows real-time coordination
- Reliable when given structured prompts

### Responsibilities

1. **Receive Task from Architect**
   - Read task Issue
   - Read context documents
   - Understand WHY this task matters

2. **Prove Understanding**
   - Restate task in own words
   - Explain WHY to Architect
   - Write implementation tests (max 5)
   - Submit for Architect approval
   - **WAIT for approval before proceeding**

3. **Dispatch Tests to Builders**
   - Create Builder Issue for each test
   - Assign to Builder (Codex or Jules)
   - Include: test code, context, scope

4. **Monitor Builders**
   - Check builder progress every 60 seconds
   - Answer builder questions (via Issue comments)
   - If builder stuck > 10 min: intervene
   - If builder fails 3x: replace with new builder

5. **Collect Completed Tests**
   - Review builder PRs
   - Verify tests pass
   - Merge to task branch
   - Track progress

6. **Complete Task**
   - When all tests pass
   - Create PR: task branch ? epic branch
   - Notify Architect

### Inputs
- Task Issue from Architect
- Context documents

### Outputs
- Implementation tests (in task Issue)
- Builder Issues (assigned to Builders)
- Task branch with all merged tests
- PR to epic branch

### The Approval Gate

**Critical**: Conductor MUST NOT dispatch to Builders until Architect approves tests.
````
Conductor writes tests
        ¦
        ?
Conductor comments on Task Issue:
"I understand this task as: [restatement]
This matters because: [WHY]
I will test:
1. [test 1]
2. [test 2]
...
Awaiting approval."
        ¦
        ?
Architect reviews:
+-- If tests align with acceptance ? "APPROVED"
+-- If tests don't align ? "REVISE: [feedback]"
        ¦
        ?
Only after APPROVED: Conductor launches Builders
````

### Commit Signature
````
[CONDUCTOR][COND-{ID}][TASK-X][TEST-Y] STATUS: description
````

---

## 3.6 Builders

### Identity
````yaml
role: Builder
instances: Many (parallel)
llm: Codex Cloud (primary) or Jules (fallback/isolated)
purpose: Write code that passes a single test
````

### Why Codex Cloud as Primary Builder

- TypeScript SDK with structured outputs
- No hard daily cap (can overflow to API)
- GitHub Action for CI/CD integration
- Thread state for context continuity
- Higher benchmark scores than Jules

### Why Jules as Fallback

- Isolated execution (no internet)
- Plan approval before execution
- Free tier for testing
- Different failure modes (useful for fallback)

### Single Builder Pattern (Simplified from Pair)

Original design: Test-giver + Test-taker pair
Simplified: Single Builder with self-review
````
Conductor gives TEST to Builder
        ¦
        ?
Builder writes code
        ¦
        ?
Builder runs test locally (in sandbox)
        ¦
        +-- PASS ? Commit, notify Conductor
        ¦
        +-- FAIL ? Retry (max 3)
                ¦
                +-- Eventually PASS ? Commit
                ¦
                +-- 3 failures ? Create Issue, mark BLOCKED
````

### Builder Responsibilities

1. **Receive Test from Conductor**
   - Single test with expected behavior
   - Context: WHY this test matters
   - Scope: files allowed to change

2. **Write Code**
   - MINIMAL code to pass test
   - Do NOT anticipate future tests
   - Do NOT add unrequested features
   - Stay within SCOPE

3. **Verify Locally**
   - Run the test
   - If fail: debug and retry
   - Max 3 attempts

4. **Commit or Block**
   - If pass: commit with structured message
   - If blocked: create Issue, await help

### Inputs
- Test Issue from Conductor
- Single test to pass
- Scope (allowed files)
- Context (WHY)

### Outputs
- Code that passes test
- Commit to builder branch
- PR to task branch

### Commit Signature
````
[BUILDER][B-{ID}][TASK-X][TEST-Y] STATUS: description

context: [one line WHY]
scope: [allowed files]
changed: [actual files changed]
tests: passed:{n} failed:{n}
status: complete | blocked | working
````

### Builder Structured Output (for Codex SDK)
````typescript
const builderOutputSchema = {
  type: "object",
  properties: {
    status: { 
      type: "string",
      enum: ["complete", "blocked", "working"] 
    },
    test_passed: { type: "boolean" },
    files_changed: { 
      type: "array", 
      items: { type: "string" } 
    },
    code_summary: { type: "string" },
    blocked_reason: { type: "string" },
    question: { type: "string" }
  },
  required: ["status", "test_passed", "files_changed"]
};
````

---

## 3.7 Cops (Internal Affairs)

### Philosophy
````
DETERMINISTIC checks GATE semantic checks.
If format is wrong, don't waste LLM asking about context.
````

### The Five Cops

| Cop | Trigger | Type | Purpose |
|-----|---------|------|---------|
| GATE_COP | Every push | Deterministic | Format + Style validation |
| SCOPE_COP | Every push | Hybrid | File scope enforcement |
| TEST_COP | Every push | Deterministic | Run tests |
| CONTEXT_COP | On PR | Semantic (LLM) | Alignment check |
| WATCHDOG_COP | Cron (5 min) | Deterministic | Heartbeat + communication |

---

### GATE_COP

**Purpose**: Validate commit message format and code style

**Trigger**: Every push to any branch

**Checks** (all deterministic):
1. Commit message has correct header format
2. Required fields present (context, scope, changed, tests, status)
3. Linting passes (eslint, prettier, black, etc.)
4. No secrets in code (gitleaks)

**Actions**:
- PASS: Allow push
- FAIL: Block push, create Issue with specific error

**Implementation**:
````yaml
# .github/workflows/gate_cop.yml
name: Gate Cop
on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate Commit Format
        run: |
          MSG=$(git log -1 --pretty=%B)
          
          # Check header format: [LEVEL][AGENT][TASK][TEST] STATUS:
          if ! echo "$MSG" | head -1 | grep -qE '^\[(PRODUCER|ARCHITECT|CONDUCTOR|BUILDER)\]\[[A-Z0-9-]+\]\[TASK-[0-9]+\]'; then
            echo "::error::Invalid commit header format"
            echo "Expected: [LEVEL][AGENT][TASK-N][TEST-N] STATUS: description"
            exit 1
          fi
          
          # Check required fields
          for field in "context:" "scope:" "changed:" "tests:" "status:"; do
            if ! echo "$MSG" | grep -qi "^$field"; then
              echo "::error::Missing required field: $field"
              exit 1
            fi
          done
          
          echo "? Commit format valid"
      
      - name: Run Linter
        run: |
          npm ci
          npm run lint
      
      - name: Check for Secrets
        uses: gitleaks/gitleaks-action@v2
````

---

### SCOPE_COP

**Purpose**: Ensure changes stay within declared scope

**Trigger**: Every push

**Checks**:
1. Extract SCOPE from commit message
2. Extract CHANGED files from git diff
3. Compare: CHANGED must be subset of SCOPE
4. If violation: flag for review

**Actions**:
- PASS: Allow
- VIOLATION: Create Issue for Conductor review

**Implementation**:
````yaml
# .github/workflows/scope_cop.yml
name: Scope Cop
on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      
      - name: Check Scope
        run: |
          MSG=$(git log -1 --pretty=%B)
          
          # Extract declared scope
          DECLARED=$(echo "$MSG" | grep -i "^scope:" | cut -d: -f2- | tr ',' ' ' | xargs)
          
          # Get actually changed files
          CHANGED=$(git diff --name-only HEAD~1 HEAD)
          
          # Check each changed file against scope
          VIOLATIONS=""
          for file in $CHANGED; do
            IN_SCOPE=false
            for allowed in $DECLARED; do
              if [[ "$file" == $allowed* ]]; then
                IN_SCOPE=true
                break
              fi
            done
            if [ "$IN_SCOPE" = false ]; then
              VIOLATIONS="$VIOLATIONS\n- $file"
            fi
          done
          
          if [ -n "$VIOLATIONS" ]; then
            echo "::error::Scope violation - files changed outside declared scope:$VIOLATIONS"
            echo "SCOPE_VIOLATION=true" >> $GITHUB_ENV
            echo "VIOLATIONS=$VIOLATIONS" >> $GITHUB_ENV
          fi
      
      - name: Create Violation Issue
        if: env.SCOPE_VIOLATION == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const violations = process.env.VIOLATIONS;
            const commit = context.sha.substring(0, 7);
            const branch = context.ref.replace('refs/heads/', '');
            
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `?? SCOPE VIOLATION: ${branch} @ ${commit}`,
              body: `## Scope Cop Alert
              
              **Branch**: ${branch}
              **Commit**: ${commit}
              
              ### Files changed outside declared scope:
              ${violations}
              
              ### Required Action
              Conductor must review and either:
              - [ ] APPROVE scope expansion (explain why)
              - [ ] REJECT and instruct builder to revert
              
              **Auto-closing this issue marks the violation as resolved.**
              `,
              labels: ['cop-alert', 'scope-violation', 'blocking']
            });
````

---

### TEST_COP

**Purpose**: Run tests on every push

**Trigger**: Every push

**Checks**:
1. Install dependencies
2. Run test suite
3. Check coverage (if configured)

**Actions**:
- PASS: Update commit status
- FAIL: Block, create Issue

**Implementation**:
````yaml
# .github/workflows/test_cop.yml
name: Test Cop
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install Dependencies
        run: npm ci
      
      - name: Run Tests
        id: tests
        run: |
          npm test -- --json --outputFile=test-results.json || true
          
          PASSED=$(jq '.numPassedTests' test-results.json)
          FAILED=$(jq '.numFailedTests' test-results.json)
          
          echo "passed=$PASSED" >> $GITHUB_OUTPUT
          echo "failed=$FAILED" >> $GITHUB_OUTPUT
          
          if [ "$FAILED" -gt 0 ]; then
            echo "::error::$FAILED tests failed"
            exit 1
          fi
      
      - name: Report Results
        if: always()
        run: |
          echo "Tests passed: ${{ steps.tests.outputs.passed }}"
          echo "Tests failed: ${{ steps.tests.outputs.failed }}"
````

---

### CONTEXT_COP

**Purpose**: Verify PR aligns with project context (semantic check)

**Trigger**: On PR creation/update to epic/* or main

**Checks**:
1. Load CONTEXT.md
2. Get PR diff
3. Ask LLM: "Does this align?"
4. LLM must answer ALIGNED or MISALIGNED with evidence

**Actions**:
- ALIGNED: Approve PR
- MISALIGNED: Block PR, request changes

**Implementation**:
````yaml
# .github/workflows/context_cop.yml
name: Context Cop
on:
  pull_request:
    types: [opened, synchronize]
    branches:
      - main
      - 'epic/*'

jobs:
  context_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get Context and Diff
        id: gather
        run: |
          # Get project context
          CONTEXT=$(cat docs/CONTEXT.md)
          echo "context<<EOF" >> $GITHUB_OUTPUT
          echo "$CONTEXT" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT
          
          # Get PR diff (limited to 10000 chars)
          DIFF=$(git diff origin/${{ github.base_ref }}...HEAD | head -c 10000)
          echo "diff<<EOF" >> $GITHUB_OUTPUT
          echo "$DIFF" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT
      
      - name: LLM Context Check
        id: llm
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Call Claude Haiku for fast, cheap binary decision
          RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
            -H "x-api-key: $ANTHROPIC_API_KEY" \
            -H "anthropic-version: 2023-06-01" \
            -H "content-type: application/json" \
            -d '{
              "model": "claude-3-5-haiku-20241022",
              "max_tokens": 200,
              "messages": [{
                "role": "user",
                "content": "You are the Context Cop. Answer ONLY with VERDICT and EVIDENCE.\n\nPROJECT CONTEXT:\n${{ steps.gather.outputs.context }}\n\nPR DIFF:\n${{ steps.gather.outputs.diff }}\n\nDoes this PR align with the project context?\n\nFormat:\nVERDICT: ALIGNED or MISALIGNED\nEVIDENCE: [one sentence]"
              }]
            }')
          
          VERDICT=$(echo "$RESPONSE" | jq -r '.content[0].text' | grep "VERDICT:" | cut -d: -f2 | xargs)
          EVIDENCE=$(echo "$RESPONSE" | jq -r '.content[0].text' | grep "EVIDENCE:" | cut -d: -f2-)
          
          echo "verdict=$VERDICT" >> $GITHUB_OUTPUT
          echo "evidence=$EVIDENCE" >> $GITHUB_OUTPUT
      
      - name: Report Verdict
        uses: actions/github-script@v7
        with:
          script: |
            const verdict = '${{ steps.llm.outputs.verdict }}';
            const evidence = '${{ steps.llm.outputs.evidence }}';
            
            if (verdict === 'MISALIGNED') {
              await github.rest.pulls.createReview({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: context.payload.pull_request.number,
                event: 'REQUEST_CHANGES',
                body: `## ?? Context Cop: MISALIGNED\n\n**Evidence**: ${evidence}\n\nThis PR does not align with the project context. Please revise.`
              });
              core.setFailed('PR misaligned with project context');
            } else {
              await github.rest.pulls.createReview({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: context.payload.pull_request.number,
                event: 'APPROVE',
                body: `## ? Context Cop: ALIGNED\n\n**Evidence**: ${evidence}`
              });
            }
````

---

### WATCHDOG_COP

**Purpose**: Monitor agent heartbeats and extract communications

**Trigger**: Cron every 5 minutes

**Checks**:
1. For each active builder branch, check last commit time
2. If too old: alert Conductor
3. Extract any QUESTION or BLOCKED status
4. Create Issues for blocked agents

**Implementation**:
````yaml
# .github/workflows/watchdog_cop.yml
name: Watchdog Cop
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:

jobs:
  heartbeat:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Check Builder Heartbeats
        uses: actions/github-script@v7
        with:
          script: |
            const { execSync } = require('child_process');
            
            // Get all builder branches
            const branches = execSync('git branch -r | grep "builder/"')
              .toString().trim().split('\n')
              .map(b => b.trim().replace('origin/', ''));
            
            const now = Date.now();
            const WARN_THRESHOLD = 10 * 60 * 1000;  // 10 minutes
            const ALERT_THRESHOLD = 20 * 60 * 1000; // 20 minutes
            const CRITICAL_THRESHOLD = 30 * 60 * 1000; // 30 minutes
            
            for (const branch of branches) {
              if (!branch) continue;
              
              // Get last commit timestamp
              const timestamp = execSync(`git log -1 --format=%ct origin/${branch}`)
                .toString().trim();
              const lastCommit = parseInt(timestamp) * 1000;
              const age = now - lastCommit;
              
              const builderId = branch.split('/')[1];
              
              if (age > CRITICAL_THRESHOLD) {
                // Create critical issue
                await github.rest.issues.create({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  title: `?? CRITICAL: Builder ${builderId} unresponsive (${Math.round(age/60000)}min)`,
                  body: `Builder has not committed in ${Math.round(age/60000)} minutes.\n\nBranch: ${branch}\n\n**Action Required**: Conductor must replace or restart builder.`,
                  labels: ['cop-alert', 'heartbeat-critical', 'blocking']
                });
              } else if (age > ALERT_THRESHOLD) {
                console.log(`?? ALERT: ${builderId} silent for ${Math.round(age/60000)}min`);
              } else if (age > WARN_THRESHOLD) {
                console.log(`? WARNING: ${builderId} silent for ${Math.round(age/60000)}min`);
              }
            }
      
      - name: Check for Blocked Builders
        run: |
          # Scan recent commits for blocked status
          for branch in $(git branch -r | grep "builder/"); do
            MSG=$(git log -1 --pretty=%B origin/$branch)
            STATUS=$(echo "$MSG" | grep -i "^status:" | cut -d: -f2 | xargs)
            
            if [ "$STATUS" = "blocked" ]; then
              echo "::warning::Builder on $branch is BLOCKED"
              # Issue creation handled by builder's commit
            fi
          done
````

---

# 4. INFRASTRUCTURE

## 4.1 Repository Structure
````
/prometheus-project/
¦
+-- /docs/                      # Project documentation (created by Producer)
¦   +-- PRD.md                  # Product Requirements Document
¦   +-- CONTEXT.md              # Project context, priorities, WHY
¦   +-- ARCHITECTURE.md         # System architecture
¦   +-- AGENTS.md               # Agent behavior rules (for AGENTS.md readers)
¦   +-- CONVENTIONS.md          # Coding conventions, naming, style
¦   +-- GLOSSARY.md             # Project-specific terminology
¦
+-- /research/                  # Research findings (from Research Agents)
¦   +-- documentation.md        # Official docs compilation
¦   +-- prior_art.md            # Existing solutions research
¦   +-- tech_stack.md           # Technology decisions
¦
+-- /scripts/                   # Orchestration scripts
¦   +-- launch_producer.py      # Bootstrap script (human runs this)
¦   +-- launch_architects.py    # Producer creates, launches Architects
¦   +-- launch_conductors.py    # Architect creates, launches Conductors
¦   +-- launch_builder.py       # Conductor creates, launches Builder
¦   +-- producer_watchdog.py    # Producer's monitoring loop
¦   +-- architect_watchdog.py   # Architect's monitoring loop
¦   +-- conductor_watchdog.py   # Conductor's monitoring loop
¦
+-- /templates/                 # Issue and PR templates
¦   +-- epic_issue.md           # Template for epic Issues
¦   +-- task_issue.md           # Template for task Issues
¦   +-- test_issue.md           # Template for test Issues (to Builders)
¦   +-- cop_alert.md            # Template for Cop violation Issues
¦
+-- /.github/
¦   +-- /workflows/             # GitHub Actions
¦   ¦   +-- gate_cop.yml
¦   ¦   +-- scope_cop.yml
¦   ¦   +-- test_cop.yml
¦   ¦   +-- context_cop.yml
¦   ¦   +-- watchdog_cop.yml
¦   ¦
¦   +-- /ISSUE_TEMPLATE/        # Issue templates
¦   ¦   +-- epic.yml
¦   ¦   +-- task.yml
¦   ¦   +-- test.yml
¦   ¦   +-- cop_alert.yml
¦   ¦
¦   +-- CODEOWNERS              # Enforce review requirements
¦
+-- /src/                       # Source code (built by Builders)
¦   +-- /frontend/
¦   +-- /backend/
¦   +-- /database/
¦   +-- /shared/
¦
+-- /tests/                     # Test files
¦   +-- /unit/
¦   +-- /integration/
¦   +-- /e2e/
¦
+-- package.json                # (or appropriate manifest)
+-- .eslintrc                   # Linting config
+-- .prettierrc                 # Formatting config
+-- README.md                   # Project README
````

## 4.2 Branch Hierarchy
````
main (protected)
¦
+-- Protected by:
¦   - Require PR from epic/* only
¦   - Require PRODUCER-1 approval
¦   - Require all cops pass
¦   - No direct pushes
¦
+-- epic/frontend (protected)
¦   +-- Protected by:
¦   ¦   - Require PR from task/frontend-* only
¦   ¦   - Require ARCH-FRONTEND approval
¦   ¦   - Require context_cop pass
¦   ¦
¦   +-- task/frontend-login
¦   ¦   +-- Protected by:
¦   ¦   ¦   - Require PR from builder/B*-frontend-login-* only
¦   ¦   ¦   - Require COND-F1 approval
¦   ¦   ¦
¦   ¦   +-- builder/B1-frontend-login-test1
¦   ¦   +-- builder/B2-frontend-login-test2
¦   ¦   +-- builder/B3-frontend-login-test3
¦   ¦
¦   +-- task/frontend-dashboard
¦       +-- builder/B4-frontend-dashboard-test1
¦       +-- ...
¦
+-- epic/backend
¦   +-- task/backend-auth
¦   ¦   +-- builder/B5-backend-auth-test1
¦   ¦   +-- ...
¦   +-- task/backend-api
¦
+-- epic/database
    +-- ...
````

### Branch Naming Convention
````
epic/{domain}
task/{domain}-{task-slug}
builder/B{id}-{domain}-{task-slug}-test{n}
````

Examples:
- `epic/frontend`
- `task/frontend-login`
- `builder/B7-frontend-login-test2`

## 4.3 Commit Protocol

### Commit Message Format
````
[LEVEL][AGENT][TASK-N][TEST-N] STATUS: short description

context: one line explaining WHY this matters
scope: comma, separated, file, patterns, allowed
changed: actual, files, modified
tests: passed:N failed:N
status: complete | working | blocked
question: none | "actual question if blocked"
````

### Level Values
- `PRODUCER` - Producer commits
- `ARCHITECT` - Architect commits  
- `CONDUCTOR` - Conductor commits
- `BUILDER` - Builder commits

### Status Values
- `INIT` - Initial setup
- `WORKING` - In progress
- `PASS` - Test passed
- `FAIL` - Test failed (with retry)
- `BLOCKED` - Cannot proceed, need help
- `COMPLETE` - Task/test finished
- `DISPATCH` - Assigning work to subordinate
- `REVIEW` - Submitted for review
- `MERGE` - Merging PR
- `RELEASE` - Final release

### Example Commits

**Producer starting project:**
````
[PRODUCER][PRODUCER-1][EPIC-0][TEST-0] INIT: project_bootstrap

context: Email fraud detection app for elderly users
scope: /docs/, /scripts/, /.github/
changed: /docs/PRD.md, /docs/CONTEXT.md
tests: passed:0 failed:0
status: working
question: none
````

**Architect dispatching task:**
````
[ARCHITECT][ARCH-BACKEND][TASK-3][TEST-0] DISPATCH: assigned_to_conductor_b2

context: Authentication must be simple, no complex 2FA
scope: n/a
changed: none
tests: n/a
status: working
question: none
````

**Builder completing test:**
````
[BUILDER][B7][TASK-3][TEST-2] PASS: login_returns_jwt_token

context: Authentication must be simple, no complex 2FA
scope: src/api/auth.py, tests/test_auth.py
changed: src/api/auth.py, tests/test_auth.py
tests: passed:1 failed:0
status: complete
question: none
````

**Builder blocked with question:**
````
[BUILDER][B7][TASK-3][TEST-3] BLOCKED: unclear_session_requirement

context: Authentication must be simple, no complex 2FA
scope: src/api/session.py
changed: none
tests: passed:0 failed:0
status: blocked
question: "Should session timeout be 30 min or never for elderly users?"
````

## 4.4 Issue-Based State Management

Instead of a custom STATE.json, we use GitHub Issues with structured templates and labels.

### Issue Types

| Type | Created By | Assigned To | Purpose |
|------|-----------|-------------|---------|
| Epic Issue | Producer | Architect | Define epic scope and acceptance |
| Task Issue | Architect | Conductor | Define task scope and tests |
| Test Issue | Conductor | Builder | Single test to implement |
| Cop Alert | Cop workflows | Conductor/Architect | Violation notification |
| Question | Builder | Conductor | Blocked, needs answer |

### Issue as State

The state of the project is queryable via GitHub API:
````javascript
// Get all active builders
const activeBuilders = await github.rest.issues.listForRepo({
  owner, repo,
  labels: 'type:test,status:working',
  state: 'open'
});

// Get blocked items
const blocked = await github.rest.issues.listForRepo({
  owner, repo,
  labels: 'status:blocked',
  state: 'open'
});

// Get epic progress
const epicTasks = await github.rest.issues.listForRepo({
  owner, repo,
  labels: 'epic:frontend,type:task'
});
const complete = epicTasks.filter(i => 
  i.labels.some(l => l.name === 'status:complete')
);
````

## 4.5 Label Taxonomy

### Type Labels (mutually exclusive)
````yaml
type:epic       # Epic-level issue
type:task       # Task-level issue
type:test       # Individual test issue
type:cop-alert  # Cop violation
type:question   # Agent question
````

### Status Labels (mutually exclusive)
````yaml
status:planning     # Being planned
status:pending      # Waiting to start
status:working      # In progress
status:review       # Submitted for review
status:blocked      # Cannot proceed
status:complete     # Finished
````

### Domain Labels
````yaml
domain:frontend
domain:backend
domain:database
domain:infrastructure
domain:documentation
````

### Priority Labels
````yaml
priority:critical   # Blocks everything
priority:high       # Important
priority:normal     # Default
priority:low        # Nice to have
````

### Agent Labels (who owns this)
````yaml
agent:producer-1
agent:arch-frontend
agent:arch-backend
agent:cond-f1
agent:builder-7
````

### Cop Labels
````yaml
cop:gate-violation
cop:scope-violation
cop:test-failure
cop:context-misaligned
cop:heartbeat-warning
````

---

# 5. GITHUB CONFIGURATION

## 5.1 Branch Protection Rules

### main branch
````yaml
branch: main
protection:
  required_status_checks:
    strict: true
    contexts:
      - "Gate Cop"
      - "Test Cop"
      - "Context Cop"
  required_pull_request_reviews:
    required_approving_review_count: 1
    require_code_owner_reviews: true
  restrictions:
    users: []
    teams: []
  enforce_admins: true
  allow_force_pushes: false
  allow_deletions: false
````

### epic/* branches
````yaml
branch: epic/*
protection:
  required_status_checks:
    strict: true
    contexts:
      - "Gate Cop"
      - "Test Cop"
      - "Context Cop"
  required_pull_request_reviews:
    required_approving_review_count: 1
  allow_force_pushes: false
````

### task/* branches
````yaml
branch: task/*
protection:
  required_status_checks:
    strict: true
    contexts:
      - "Gate Cop"
      - "Test Cop"
      - "Scope Cop"
  required_pull_request_reviews:
    required_approving_review_count: 1
  allow_force_pushes: false
````

### builder/* branches
````yaml
branch: builder/*
protection:
  required_status_checks:
    strict: true
    contexts:
      - "Gate Cop"
      - "Test Cop"
  # No PR required - builders push directly
  # But must pass cops
````

## 5.2 Issue Templates

### Epic Issue Template
````yaml
# .github/ISSUE_TEMPLATE/epic.yml
name: Epic
description: Create a new epic for the project
labels: ["type:epic", "status:planning"]
body:
  - type: input
    id: epic-name
    attributes:
      label: Epic Name
      placeholder: e.g., User Authentication
    validations:
      required: true
  
  - type: dropdown
    id: domain
    attributes:
      label: Domain
      options:
        - frontend
        - backend
        - database
        - infrastructure
        - documentation
    validations:
      required: true
  
  - type: textarea
    id: context
    attributes:
      label: Context (WHY)
      description: Why does this epic exist? What problem does it solve?
    validations:
      required: true
  
  - type: textarea
    id: scope
    attributes:
      label: Scope (WHAT)
      description: What must this epic accomplish?
    validations:
      required: true
  
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance Criteria
      description: How do we know this epic is complete?
      value: |
        - [ ] Criterion 1
        - [ ] Criterion 2
    validations:
      required: true
  
  - type: textarea
    id: dependencies
    attributes:
      label: Dependencies
      description: Other epics this depends on or blocks
````

### Task Issue Template
````yaml
# .github/ISSUE_TEMPLATE/task.yml
name: Task
description: Create a task within an epic
labels: ["type:task", "status:planning"]
body:
  - type: input
    id: task-name
    attributes:
      label: Task Name
      placeholder: e.g., Implement login endpoint
    validations:
      required: true
  
  - type: input
    id: epic
    attributes:
      label: Parent Epic
      placeholder: "#123 or epic name"
    validations:
      required: true
  
  - type: textarea
    id: context
    attributes:
      label: Context (WHY)
      description: Why does this task matter to the epic?
    validations:
      required: true
  
  - type: textarea
    id: scope
    attributes:
      label: Scope (Files)
      description: Which files should this task touch?
      value: |
        - src/...
        - tests/...
    validations:
      required: true
  
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance Criteria
      description: How do we know this task is complete?
      value: |
        - [ ] Criterion 1
        - [ ] Criterion 2
    validations:
      required: true
  
  - type: textarea
    id: tests
    attributes:
      label: Implementation Tests
      description: Tests that will be given to Builders (filled by Conductor)
      value: |
        *To be filled by assigned Conductor*
````

### Test Issue Template (for Builders)
````yaml
# .github/ISSUE_TEMPLATE/test.yml
name: Test
description: Assign a single test to a Builder
labels: ["type:test", "status:pending"]
body:
  - type: input
    id: test-name
    attributes:
      label: Test Name
      placeholder: e.g., login_returns_jwt_token
    validations:
      required: true
  
  - type: input
    id: task
    attributes:
      label: Parent Task
      placeholder: "#456"
    validations:
      required: true
  
  - type: textarea
    id: context
    attributes:
      label: Context (WHY)
      description: Why does this test matter?
    validations:
      required: true
  
  - type: textarea
    id: test-code
    attributes:
      label: Test Code
      description: The actual test to pass
      render: python
      value: |
        def test_example():
            # Test implementation here
            pass
    validations:
      required: true
  
  - type: textarea
    id: scope
    attributes:
      label: Allowed Files
      description: Files the Builder may modify
      value: |
        - src/...
        - tests/...
    validations:
      required: true
  
  - type: input
    id: branch
    attributes:
      label: Builder Branch
      placeholder: builder/B1-task-test1
    validations:
      required: true
````

### Cop Alert Template
````yaml
# .github/ISSUE_TEMPLATE/cop_alert.yml
name: Cop Alert
description: Automated violation report from Cops
labels: ["type:cop-alert", "status:blocked", "priority:high"]
body:
  - type: dropdown
    id: cop
    attributes:
      label: Reporting Cop
      options:
        - Gate Cop
        - Scope Cop
        - Test Cop
        - Context Cop
        - Watchdog Cop
    validations:
      required: true
  
  - type: input
    id: agent
    attributes:
      label: Offending Agent
    validations:
      required: true
  
  - type: input
    id: branch
    attributes:
      label: Branch
    validations:
      required: true
  
  - type: input
    id: commit
    attributes:
      label: Commit SHA
    validations:
      required: true
  
  - type: textarea
    id: violation
    attributes:
      label: Violation Details
    validations:
      required: true
  
  - type: textarea
    id: action
    attributes:
      label: Required Action
      value: |
        - [ ] APPROVE (with explanation)
        - [ ] REJECT (instruct agent to fix)
        - [ ] ESCALATE (to next level)
````

## 5.3 CODEOWNERS
````
# .github/CODEOWNERS

# Producer owns project docs
/docs/PRD.md @producer-bot
/docs/CONTEXT.md @producer-bot

# Architects own their domains
/src/frontend/ @arch-frontend-bot
/src/backend/ @arch-backend-bot
/src/database/ @arch-database-bot

# All code requires cop approval (via status checks, not CODEOWNERS)
````

---

# 6. PROMPT TEMPLATES

## 6.1 Producer System Prompt
````markdown
# PRODUCER SYSTEM PROMPT

You are PRODUCER-1, the highest-level orchestrator in the PROMETHEUS autonomous code generation system.

## Your Identity
- Role: Producer
- Instance: PRODUCER-1
- Purpose: Transform human ideas into complete, working software

## Your Capabilities
- Ask clarifying questions
- Launch Research Agents
- Create project documentation
- Decompose programs into epics
- Launch and monitor Architects
- Assemble final product

## Phase 1: Discovery

Your first task is to understand the human's idea completely.

Rules for questioning:
1. Ask ONE question at a time
2. Wait for the answer before asking the next question
3. Never use sub-questions (a, b, c)
4. Questions should be conversational, like a dialogue
5. Continue until you understand: WHAT, WHO, WHY, HOW, SUCCESS

Question categories to cover:
- What is being built? (product description)
- Who is it for? (target users, their characteristics)
- Why does it need to exist? (problem being solved)
- How should it work? (key features, user flows)
- What does success look like? (measurable criteria)
- What are the constraints? (tech stack, timeline, budget)
- What should it NOT do? (explicit exclusions)

When you have complete understanding, say:
"I believe I understand the project. Let me restate it for confirmation."

Then provide:
````
## Project Summary

### WHAT
[Product description]

### WHO  
[Target users and their characteristics]

### WHY
[Problem being solved, value proposition]

### HOW
[Key features, user flows, technical approach]

### SUCCESS CRITERIA
[Measurable outcomes]

### CONSTRAINTS
[Limitations, exclusions]

### PROPOSED EPICS
1. [Epic 1 - brief description]
2. [Epic 2 - brief description]
...

Do you approve this project plan?
````

## Phase 2: Research

After human approval, launch Research Agents:
```python
# You will output this command
LAUNCH_RESEARCH:
  - agent: RESEARCH-DOCS
    focus: "Official documentation for [technologies]"
  - agent: RESEARCH-PRIOR  
    focus: "Existing solutions for [problem domain]"
  - agent: RESEARCH-STACK
    focus: "Best practices for [architecture type]"
```

Wait for research to complete. Synthesize findings.

## Phase 3: Documentation

Create the following files:

1. `/docs/PRD.md` - Full product requirements
2. `/docs/CONTEXT.md` - The WHY, priorities, decision rules
3. `/docs/ARCHITECTURE.md` - System design, data flow
4. `/docs/AGENTS.md` - Rules for all agents (for AGENTS.md readers)
5. `/docs/CONVENTIONS.md` - Coding standards, naming

## Phase 4: Epic Creation

For each epic, create a GitHub Issue using the epic template.

Assign each epic to the appropriate domain Architect:
- Frontend epic ? ARCH-FRONTEND
- Backend epic ? ARCH-BACKEND
- Database epic ? ARCH-DATABASE
- etc.

## Phase 5: Launch Architects

Output the launch command:
```python
LAUNCH_ARCHITECTS:
  - architect: ARCH-FRONTEND
    epic_issue: "#1"
    context: "[summary of frontend epic]"
  - architect: ARCH-BACKEND
    epic_issue: "#2"
    context: "[summary of backend epic]"
  ...
```

## Phase 6: Monitor

Every 5 minutes (via watchdog script), check:
1. Are all Architects still active? (heartbeat)
2. Are there any escalations? (Issues labeled 'escalate-to-producer')
3. Is context being maintained? (spot check)

Intervene if:
- Architect silent > 20 minutes
- Scope creep detected
- Context drift detected

## Phase 7: Assembly

When all Architects report COMPLETE:
1. Review all epic branches
2. Run integration tests
3. Resolve any conflicts
4. Merge to main
5. Create release commit
6. Present to human

## Commit Format

All your commits must follow:
````
[PRODUCER][PRODUCER-1][EPIC-N][TEST-N] STATUS: description

context: [project-level why]
scope: [files you're touching]
changed: [files actually changed]
tests: passed:N failed:N
status: [working|complete]
question: none
````

## Communication

- To Human: Direct conversation (Phase 1 only)
- To Research Agents: Launch commands
- To Architects: GitHub Issues
- Receive from Architects: GitHub Issue comments, PRs
````

## 6.2 Architect System Prompt
````markdown
# ARCHITECT SYSTEM PROMPT

You are ARCH-{DOMAIN}, an Architect in the PROMETHEUS system.

## Your Identity
- Role: Architect
- Instance: ARCH-{DOMAIN}
- Domain: {DOMAIN}
- Purpose: Own an epic from planning to completion

## Your Context
Epic: {EPIC_TITLE}
Issue: #{EPIC_ISSUE_NUMBER}
Branch: epic/{domain}

Project Context:
{CONTENT_OF_CONTEXT_MD}

## Your Responsibilities

### 1. Understand the Epic
- Read the epic Issue completely
- Read /docs/CONTEXT.md - understand the WHY
- Read /docs/CONVENTIONS.md - know the standards
- Read /research/ - know what's been learned

### 2. Decompose into Tasks
Create tasks that are:
- SMALL: Max 5 tests each
- INDEPENDENT: Minimal dependencies
- CLEAR: Unambiguous acceptance criteria
- SCOPED: Specific files to touch

For each task, create a GitHub Issue using the task template.
Maximum 10 tasks per epic.

### 3. Write Acceptance Criteria
Each task needs criteria that are:
- MEASURABLE: Can be verified by running code
- SPECIFIC: No ambiguity
- COMPLETE: Cover all requirements

Example:
````
Task: Implement login endpoint

Acceptance Criteria:
- [ ] POST /api/login accepts {email, password}
- [ ] Returns JWT token on valid credentials
- [ ] Returns 401 on invalid credentials
- [ ] Token expires in 24 hours
- [ ] Rate limited to 5 attempts per minute
````

### 4. Assign to Conductors
Assign each task Issue to a Conductor.
Include in the assignment:
- Task Issue number
- WHY this task matters (context)
- Acceptance criteria
- Allowed file scope

### 5. Approve Conductor Plans
When a Conductor submits their implementation tests:
- Verify tests align with acceptance criteria
- Verify scope is appropriate
- Verify context is understood

If aligned: Comment "APPROVED - proceed"
If not: Comment "REVISE: [specific feedback]"

DO NOT let Conductors proceed without approval.

### 6. Monitor Progress
Check every 5 minutes (via watchdog):
- Conductor heartbeats
- Blocked items (Issues with 'status:blocked')
- Escalations (Issues with 'escalate-to-architect')

### 7. Review Task PRs
When Conductor creates PR to epic branch:
- Verify all acceptance criteria met
- Verify tests pass
- Verify code follows conventions
- Merge if good

### 8. Complete Epic
When all tasks merged:
- Create PR: epic/{domain} ? main
- Request Producer review
- Commit: [ARCHITECT][ARCH-{DOMAIN}][EPIC-N][] COMPLETE: epic_finished

## Commit Format
````
[ARCHITECT][ARCH-{DOMAIN}][TASK-N][TEST-N] STATUS: description

context: [epic-level why]
scope: [task files]
changed: [actual files]
tests: n/a
status: [working|complete]
question: none
````

## The Approval Gate

CRITICAL: You are the quality gate between Producer vision and Builder execution.

If Conductor's tests don't align with acceptance:
? They will build the wrong thing
? The whole task fails
? Time and cost wasted

Take approval seriously. Be specific in feedback.
````

## 6.3 Conductor System Prompt
````markdown
# CONDUCTOR SYSTEM PROMPT

You are COND-{ID}, a Conductor in the PROMETHEUS system.

## Your Identity
- Role: Conductor
- Instance: COND-{ID}
- LLM: GLM 4.7 Max
- Purpose: Own a task from tests to completion

## Your Context
Task: {TASK_TITLE}
Issue: #{TASK_ISSUE_NUMBER}
Branch: task/{domain}-{slug}
Architect: ARCH-{DOMAIN}

Project Context:
{WHY_FROM_CONTEXT_MD}

Task Acceptance Criteria:
{CRITERIA_FROM_TASK_ISSUE}

## Your Responsibilities

### 1. Prove Understanding
Before doing ANY work, you must demonstrate understanding.

Comment on the task Issue:
````
## My Understanding

### Restatement
[Task in your own words]

### Why This Matters
[Connection to project context]

### Proposed Implementation Tests
1. `test_[name]`: [what it verifies]
2. `test_[name]`: [what it verifies]
...

### File Scope
- [files I will instruct Builders to modify]

Awaiting approval from ARCH-{DOMAIN}.
````

DO NOT proceed until Architect comments "APPROVED".

### 2. Create Builder Issues
After approval, for each test:
- Create a Test Issue using the template
- Include the actual test code
- Include the WHY (context)
- Include the allowed file scope
- Assign to an available Builder
- Create branch: builder/B{id}-{task-slug}-test{n}

### 3. Monitor Builders
Every 60 seconds, check:
- Builder commits (heartbeat)
- Builder status (working/blocked/complete)
- Test results

If Builder blocked:
- Read their question from commit or Issue
- Answer in Issue comment
- Update status to unblocked

If Builder silent > 10 minutes:
- Prompt them via Issue comment
- If no response in 5 more minutes: replace

If Builder fails 3 times:
- Create new Builder Issue with same test
- Assign to different Builder
- Note the failure in original Issue

### 4. Verify and Merge
When Builder reports COMPLETE:
- Pull their branch
- Run the test locally (if possible)
- Verify only allowed files changed
- Create PR: builder branch ? task branch
- Merge

### 5. Complete Task
When all tests merged to task branch:
- Run full test suite for task
- Verify acceptance criteria met
- Create PR: task branch ? epic branch
- Comment on task Issue: "COMPLETE - PR #{pr_number}"
- Request Architect review

## Commit Format
````
[CONDUCTOR][COND-{ID}][TASK-N][TEST-N] STATUS: description

context: [task-level why]
scope: n/a (conductors don't write code)
changed: none
tests: n/a
status: [working|complete]
question: none
````

## Builder Communication Protocol

Since some Builders (Codex) can't "talk back" interactively, communication happens through:

1. **Builder ? Conductor**: Structured commit messages and Issue comments
2. **Conductor ? Builder**: Issue comments and new Issues

When a Builder commits with `status: blocked` and `question: "..."`:
1. Create an Issue comment answering the question
2. The watchdog will notify the Builder
3. Builder reads the answer and continues

## The Forcing Function

You MUST prove understanding before Builders run.

Why? Because:
- Builder LLM calls cost money
- Builder time is parallel and valuable
- Wrong tests = wrong code = wasted everything

Your implementation tests ARE the specification.
If your tests are wrong, the code will be wrong.
Take the approval gate seriously.
````

## 6.4 Builder System Prompt
````markdown
# BUILDER SYSTEM PROMPT

You are BUILDER-{ID}, a Builder in the PROMETHEUS system.

## Your Identity
- Role: Builder
- Instance: B-{ID}
- LLM: Codex Cloud (or Jules)
- Purpose: Write code that passes a single test

## Your Context
Test: {TEST_NAME}
Issue: #{TEST_ISSUE_NUMBER}
Branch: builder/B{id}-{task-slug}-test{n}
Conductor: COND-{CONDUCTOR_ID}

Why This Test Matters:
{CONTEXT_FROM_TEST_ISSUE}

Allowed Files:
{SCOPE_FROM_TEST_ISSUE}

Test Code:
````
{ACTUAL_TEST_CODE}
````

## Your Responsibilities

### 1. Understand the Test
Read the test code carefully.
Understand EXACTLY what it's checking.
Do NOT add functionality beyond what the test requires.

### 2. Write Code
Write the MINIMUM code necessary to pass the test.

Rules:
- Only modify files in your allowed scope
- Follow project conventions (/docs/CONVENTIONS.md)
- No extra features
- No anticipated future needs
- Simple, clear, minimal

### 3. Verify
Run the test in your sandbox.

If PASS:
- Commit with status: complete
- Create PR to task branch

If FAIL:
- Read the error
- Fix the code
- Retry (max 3 attempts)

### 4. Handle Being Stuck
If you cannot figure out how to pass the test after 3 attempts:
- Commit with status: blocked
- Include your question
- Wait for Conductor response

## Commit Format (CRITICAL)

Every commit MUST follow this format exactly:
````
[BUILDER][B-{ID}][TASK-N][TEST-N] STATUS: short_description

context: {one line from test issue context}
scope: {allowed files from test issue}
changed: {files you actually modified}
tests: passed:{0 or 1} failed:{0 or 1}
status: complete | working | blocked
question: none | "your question if blocked"
````

## Structured Output (for Codex SDK)

If using Codex SDK, output this JSON:
```json
{
  "status": "complete | working | blocked",
  "test_passed": true | false,
  "files_changed": ["path/to/file.py"],
  "code_summary": "What I did in one sentence",
  "blocked_reason": null | "Why I'm stuck",
  "question": null | "My question for Conductor"
}
```

## Communication

You communicate through commits and Issues.

To ask a question:
1. Commit with `status: blocked` and `question: "your question"`
2. The Watchdog Cop will see this
3. Your Conductor will answer in the Test Issue
4. Read the Issue for the answer
5. Continue work

DO NOT guess if you're unsure.
DO NOT expand scope.
DO NOT add unrequested features.

Ask and wait.

## Example Session

1. Receive test Issue #789
2. Read test: `test_login_returns_token`
3. Create branch: `builder/B7-backend-auth-test2`
4. Write code in `src/api/auth.py`
5. Run test: FAIL (missing import)
6. Fix import
7. Run test: PASS
8. Commit:
````
[BUILDER][B-7][TASK-3][TEST-2] PASS: login_returns_token

context: Authentication must be simple for elderly users
scope: src/api/auth.py, tests/test_auth.py
changed: src/api/auth.py
tests: passed:1 failed:0
status: complete
question: none
````
9. Create PR to task/backend-auth
10. Done - await next test or conductor merge
````

## 6.5 Cop System Prompts

### Context Cop Prompt (only cop with LLM)
````markdown
# CONTEXT COP SYSTEM PROMPT

You are the Context Cop, a semantic validator in the PROMETHEUS system.

## Your Purpose
Verify that code changes align with project context.

## Your Input
1. PROJECT CONTEXT (from /docs/CONTEXT.md)
2. PR DIFF (code changes)

## Your Output
EXACTLY this format, nothing else:
````
VERDICT: ALIGNED | MISALIGNED
EVIDENCE: [One sentence explaining why]
````

## Rules
- Be strict. If there's any doubt, say MISALIGNED.
- Look for scope creep (features nobody asked for)
- Look for context drift (solving different problems)
- Look for principle violations (complexity where simplicity required)

## Examples

Context: "App must be simple for elderly users, large fonts, high contrast"
Diff: Adds a complex settings menu with 20 options
? VERDICT: MISALIGNED
? EVIDENCE: Complex settings menu contradicts simplicity requirement for elderly users.

Context: "Backend API for user authentication"
Diff: Adds JWT token generation for login endpoint
? VERDICT: ALIGNED
? EVIDENCE: JWT authentication directly implements the required user authentication API.

Context: "No complex 2FA, simple password only"
Diff: Adds WebAuthn hardware key support
? VERDICT: MISALIGNED
? EVIDENCE: Hardware key authentication violates explicit constraint against complex 2FA.
````

---

# 7. LLM SELECTION GUIDE

## Role-to-LLM Mapping

| Role | Primary LLM | Reason | Fallback |
|------|-------------|--------|----------|
| Producer | Claude Sonnet/Opus | Deep reasoning, project understanding | GPT-4 |
| Research Agents | Claude + Web Search | Research capability | Perplexity API |
| Architects | Claude Sonnet | Planning, decomposition | GLM 4.7 Max |
| Conductors | GLM 4.7 Max | Long-running reliability, orchestration | Claude Sonnet |
| Builders | Codex Cloud | Async, SDK, no hard cap, best benchmarks | Jules (isolated) |
| Context Cop | Claude Haiku | Fast, cheap, binary output | GPT-4 Mini |

## LLM Invocation Methods

### Claude (Producer, Architects, Research)
````python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=8192,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": user_message}]
)
````

### GLM 4.7 Max (Conductors)
````python
import requests

response = requests.post(
    "https://api.z.ai/v1/chat/completions",
    headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
    json={
        "model": "glm-4.7-max",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 8192
    }
)
````

### Codex Cloud (Builders)
````typescript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread();

const result = await thread.run(builderPrompt, {
    outputSchema: builderOutputSchema
});
````

### Jules (Fallback Builders)
````python
import requests

# Create session
response = requests.post(
    "https://jules.googleapis.com/v1alpha/sessions",
    headers={"X-Goog-Api-Key": JULES_API_KEY},
    json={
        "source": f"sources/github/{owner}/{repo}",
        "prompt": builder_prompt
    }
)
session_id = response.json()["name"].split("/")[-1]

# Poll for completion
while True:
    status = requests.get(
        f"https://jules.googleapis.com/v1alpha/sessions/{session_id}/activities",
        headers={"X-Goog-Api-Key": JULES_API_KEY}
    )
    if is_complete(status.json()):
        break
    time.sleep(30)
````

### Claude Haiku (Context Cop)
````python
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=200,
    messages=[{"role": "user", "content": context_cop_prompt}]
)
````

## Cost Estimates

| Role | Calls/Project | Tokens/Call | Cost/Call | Total |
|------|---------------|-------------|-----------|-------|
| Producer | ~50 | ~4000 | ~$0.06 | ~$3 |
| Research (×3) | ~10 each | ~8000 | ~$0.12 | ~$3.60 |
| Architects (×3) | ~30 each | ~4000 | ~$0.06 | ~$5.40 |
| Conductors (×10) | ~50 each | ~2000 | ~$0.002 | ~$1 |
| Builders (×50) | ~5 each | ~4000 | ~$0.04 | ~$10 |
| Context Cop | ~30 | ~1000 | ~$0.001 | ~$0.03 |

**Estimated total for medium project: ~$25-50**

---

# 8. EXECUTION GUIDE

## 8.1 Prerequisites

### Required Accounts
- [ ] GitHub (with Actions enabled)
- [ ] Anthropic API key (Claude)
- [ ] Z.ai API key (GLM 4.7)
- [ ] OpenAI API key (Codex)
- [ ] Google API key (Jules) - optional fallback

### Required Setup
- [ ] Node.js 20+
- [ ] Python 3.11+
- [ ] Git configured with SSH

## 8.2 Repository Initialization
````bash
# 1. Create repository
gh repo create prometheus-{project-name} --public --clone
cd prometheus-{project-name}

# 2. Create directory structure
mkdir -p docs research scripts templates .github/workflows .github/ISSUE_TEMPLATE src tests

# 3. Copy workflow files
# (Copy all .yml files from section 5.3)

# 4. Copy issue templates
# (Copy all templates from section 5.2)

# 5. Set secrets
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."
gh secret set ZAI_API_KEY --body "..."
gh secret set OPENAI_API_KEY --body "sk-..."
gh secret set JULES_API_KEY --body "..." # optional

# 6. Initial commit
git add .
git commit -m "[PRODUCER][PRODUCER-1][EPIC-0][TEST-0] INIT: repository_setup

context: PROMETHEUS autonomous code generation
scope: entire repository
changed: .github/, docs/, scripts/, templates/
tests: passed:0 failed:0
status: working
question: none"

git push origin main

# 7. Set up branch protection (via GitHub UI or API)
# See section 5.1 for rules
````

## 8.3 Launch Producer
````bash
# Create launch script
cat > scripts/launch_producer.py << 'EOF'
import anthropic
import os

PRODUCER_SYSTEM_PROMPT = """
[Insert full Producer system prompt from section 6.1]
"""

def launch_producer():
    client = anthropic.Anthropic()
    
    print("=" * 60)
    print("PROMETHEUS PRODUCER INITIALIZED")
    print("=" * 60)
    print("\nI am PRODUCER-1. I will help you build your software.")
    print("Let's start with understanding what you want to create.\n")
    
    messages = []
    
    # Discovery phase - conversation with human
    while True:
        # Get producer's question/response
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=2048,
            system=PRODUCER_SYSTEM_PROMPT,
            messages=messages + [{"role": "user", "content": "Continue the discovery conversation. Ask your next question or provide the project summary if ready."}] if messages else [{"role": "user", "content": "Start the discovery phase. Ask your first question about what the human wants to build."}]
        )
        
        producer_message = response.content[0].text
        print(f"\nPRODUCER: {producer_message}\n")
        messages.append({"role": "assistant", "content": producer_message})
        
        # Check if producer is asking for approval
        if "Do you approve this project plan?" in producer_message:
            human_input = input("HUMAN: ")
            if human_input.lower() in ["yes", "y", "approved", "approve"]:
                messages.append({"role": "user", "content": "APPROVED. Proceed to research phase."})
                break
            else:
                messages.append({"role": "user", "content": human_input})
        else:
            human_input = input("HUMAN: ")
            messages.append({"role": "user", "content": human_input})
    
    print("\n" + "=" * 60)
    print("PROJECT APPROVED - LAUNCHING RESEARCH PHASE")
    print("=" * 60)
    
    # Continue with research, planning, etc.
    # (Implementation continues...)

if __name__ == "__main__":
    launch_producer()
EOF

# Run it
python scripts/launch_producer.py
````

## 8.4 Monitoring Dashboard
````bash
# Simple monitoring script
cat > scripts/dashboard.py << 'EOF'
import subprocess
import json
from datetime import datetime

def get_open_issues():
    result = subprocess.run(
        ["gh", "issue", "list", "--json", "number,title,labels,assignees,state"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def get_branches():
    result = subprocess.run(
        ["git", "branch", "-r", "--format=%(refname:short)"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n')

def print_dashboard():
    print("\n" + "=" * 70)
    print(f"PROMETHEUS DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    issues = get_open_issues()
    
    # Count by type
    epics = [i for i in issues if any(l['name'] == 'type:epic' for l in i['labels'])]
    tasks = [i for i in issues if any(l['name'] == 'type:task' for l in i['labels'])]
    tests = [i for i in issues if any(l['name'] == 'type:test' for l in i['labels'])]
    blocked = [i for i in issues if any(l['name'] == 'status:blocked' for l in i['labels'])]
    
    print(f"\n?? ISSUES")
    print(f"   Epics:   {len(epics)}")
    print(f"   Tasks:   {len(tasks)}")
    print(f"   Tests:   {len(tests)}")
    print(f"   Blocked: {len(blocked)} ??" if blocked else f"   Blocked: 0 ?")
    
    branches = get_branches()
    epic_branches = [b for b in branches if 'epic/' in b]
    task_branches = [b for b in branches if 'task/' in b]
    builder_branches = [b for b in branches if 'builder/' in b]
    
    print(f"\n?? BRANCHES")
    print(f"   Epic:    {len(epic_branches)}")
    print(f"   Task:    {len(task_branches)}")
    print(f"   Builder: {len(builder_branches)}")
    
    if blocked:
        print(f"\n?? BLOCKED ITEMS")
        for issue in blocked:
            print(f"   #{issue['number']}: {issue['title']}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    print_dashboard()
EOF
````

## 8.5 Full Execution Flow
````
1. Human runs: python scripts/launch_producer.py

2. Producer asks questions (one at a time)
   Human answers each question

3. Producer presents project summary
   Human approves

4. Producer launches Research Agents (parallel)
   - RESEARCH-DOCS gathers documentation
   - RESEARCH-PRIOR finds existing solutions
   - RESEARCH-STACK evaluates tech choices

5. Producer synthesizes research
   Creates: PRD.md, CONTEXT.md, ARCHITECTURE.md, AGENTS.md, CONVENTIONS.md

6. Producer creates Epic Issues
   Assigns each to domain Architect

7. Producer launches Architects (parallel)
   Each Architect:
   - Reads epic + context
   - Creates Task Issues (max 10)
   - Assigns to Conductors

8. Each Architect launches Conductors (parallel)
   Each Conductor:
   - Reads task + context
   - Proves understanding (writes tests)
   - Awaits Architect approval
   - Launches Builders after approval

9. Each Conductor launches Builders (parallel)
   Each Builder:
   - Receives single test
   - Writes code to pass test
   - Commits with structured message
   - Creates PR to task branch

10. Cops run on every push/PR
    - GATE_COP: format + style
    - SCOPE_COP: file scope
    - TEST_COP: run tests
    - CONTEXT_COP: semantic alignment (PRs only)
    - WATCHDOG_COP: heartbeats (cron)

11. Conductors merge Builder PRs ? task branch
    Create PR: task ? epic

12. Architects merge Conductor PRs ? epic branch
    Create PR: epic ? main

13. Producer reviews all epic PRs
    Runs integration tests
    Merges to main

14. Producer creates release commit
    Presents to Human

DONE.
````

---

# 9. MONITORING & METRICS

## 9.1 Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Builder heartbeat | < 10 min | > 20 min |
| Conductor heartbeat | < 15 min | > 30 min |
| Architect heartbeat | < 30 min | > 60 min |
| Test pass rate | > 80% | < 50% |
| Cop violation rate | < 10% | > 25% |
| Builder replacement rate | < 5% | > 15% |
| Task completion time | < 2 hours | > 4 hours |
| Epic completion time | < 1 day | > 2 days |

## 9.2 Watchdog Queries
````python
# Check agent health
def check_agent_health(agent_type, threshold_minutes):
    issues = gh_api.list_issues(
        labels=f"type:{agent_type},status:working"
    )
    
    now = datetime.now()
    for issue in issues:
        last_update = parse_datetime(issue.updated_at)
        age = (now - last_update).total_seconds() / 60
        
        if age > threshold_minutes:
            alert(f"{agent_type} #{issue.number} silent for {age:.0f} min")

# Check for blocked items
def check_blocked():
    blocked = gh_api.list_issues(labels="status:blocked", state="open")
    
    for issue in blocked:
        age = (now - parse_datetime(issue.created_at)).total_seconds() / 60
        
        if age > 30:
            escalate(issue)

# Run every 5 minutes
schedule.every(5).minutes.do(lambda: [
    check_agent_health("test", 10),
    check_agent_health("task", 15),
    check_agent_health("epic", 30),
    check_blocked()
])
````

---

# 10. FAILURE RECOVERY

## 10.1 Builder Failure

**Symptom**: Builder stuck, fails 3x, or silent > 30 min

**Recovery**:
1. Conductor marks Builder Issue as `status:failed`
2. Conductor creates new Test Issue with same test
3. Assigns to different Builder
4. Notes failure in original Issue for learning

## 10.2 Conductor Failure

**Symptom**: Conductor silent > 60 min or all Builders stuck

**Recovery**:
1. Architect creates Issue `escalate-to-architect`
2. Architect reviews Conductor's progress
3. Option A: Restart Conductor with additional context
4. Option B: Manually complete remaining tests
5. Option C: Reassign task to new Conductor

## 10.3 Architect Failure

**Symptom**: Architect silent > 2 hours or all Conductors stuck

**Recovery**:
1. Producer receives escalation
2. Producer reviews Architect's progress
3. Option A: Provide additional context/clarification
4. Option B: Decompose epic differently
5. Option C: Manual intervention

## 10.4 Integration Failure

**Symptom**: Epic PRs conflict or integration tests fail

**Recovery**:
1. Producer identifies conflicting changes
2. Creates Issue for relevant Architects
3. Architects coordinate on resolution
4. May require re-scoping of tasks
5. Rebuild affected components

## 10.5 Context Drift

**Symptom**: Context Cop flags MISALIGNED repeatedly

**Recovery**:
1. Producer reviews CONTEXT.md
2. Check if context needs updating (legitimate evolution)
3. If drift: Identify drifting agent
4. Re-inject context via Issue comment
5. Request agent to restate understanding

## 10.6 Full System Recovery

**Symptom**: Multiple cascading failures

**Recovery**:
1. Producer pauses all agents (via Issues)
2. Run dashboard to assess state
3. Identify root cause (usually context drift or bad decomposition)
4. Fix root cause
5. Restart from last known good state
6. Resume agents

---

# APPENDIX A: Quick Reference Card
````
+----------------------------------------------------------------+
¦                    PROMETHEUS QUICK REFERENCE                   ¦
+----------------------------------------------------------------¦
¦                                                                ¦
¦  HIERARCHY                                                     ¦
¦  Human ? Producer ? Architects ? Conductors ? Builders         ¦
¦                                                                ¦
¦  LIMITS                                                        ¦
¦  Epics per program: max 10                                     ¦
¦  Tasks per epic: max 10                                        ¦
¦  Tests per task: max 5                                         ¦
¦                                                                ¦
¦  BRANCHES                                                      ¦
¦  main                                                          ¦
¦  +-- epic/{domain}                                            ¦
¦      +-- task/{domain}-{slug}                                 ¦
¦          +-- builder/B{n}-{domain}-{slug}-test{n}            ¦
¦                                                                ¦
¦  COMMIT FORMAT                                                 ¦
¦  [LEVEL][AGENT][TASK-N][TEST-N] STATUS: description           ¦
¦  context: ...                                                  ¦
¦  scope: ...                                                    ¦
¦  changed: ...                                                  ¦
¦  tests: passed:N failed:N                                      ¦
¦  status: complete|working|blocked                              ¦
¦  question: none|"..."                                          ¦
¦                                                                ¦
¦  COPS                                                          ¦
¦  GATE_COP: format + style (every push)                        ¦
¦  SCOPE_COP: file scope (every push)                           ¦
¦  TEST_COP: run tests (every push)                             ¦
¦  CONTEXT_COP: alignment (PRs only)                            ¦
¦  WATCHDOG_COP: heartbeats (cron 5min)                         ¦
¦                                                                ¦
¦  LLMs                                                          ¦
¦  Producer: Claude                                              ¦
¦  Architects: Claude                                            ¦
¦  Conductors: GLM 4.7 Max                                       ¦
¦  Builders: Codex Cloud                                         ¦
¦  Context Cop: Claude Haiku                                     ¦
¦                                                                ¦
¦  APPROVAL GATES                                                ¦
¦  1. Human approves project plan                                ¦
¦  2. Architect approves Conductor tests                         ¦
¦  3. Conductor approves Builder code                            ¦
¦  4. Architect approves task PR                                 ¦
¦  5. Producer approves epic PR                                  ¦
¦                                                                ¦
¦  ESCALATION PATH                                               ¦
¦  Builder ? Conductor ? Architect ? Producer ? Human            ¦
¦                                                                ¦
+----------------------------------------------------------------+
````

---

# APPENDIX B: Checklist for Launch
````
PRE-LAUNCH
? Repository created
? All secrets configured
? Branch protection rules set
? Workflow files in place
? Issue templates in place
? CONVENTIONS.md drafted (coding standards)

LAUNCH
? Run launch_producer.py
? Complete discovery conversation
? Approve project plan
? Verify research completes
? Verify docs created

MONITORING
? Dashboard accessible
? Cop workflows running
? Watchdog cron active
? Escalation Issues appearing when needed

POST-COMPLETION
? All tests pass
? Integration tests pass
? Context Cop approved all PRs
? Main branch has release commit
? Human has received product
````

--


END OF PROMETHEUS MASTER BLUEPRINT v1.0


*** EXTXRA NOTE ON THE I.A. WATCH DOGS/COPS ***

The I.A. Watchdogs are triggered deterministicly
if the the bulders present task to conductor who agrees it works
conductors commits it to the branch
this triggers the an I.A. watch dog to review the code adversarially
if this does not pass then it is returned back to the conductor by the I.A.. will devise a test qustion turning the conductore in to the test answer side of the pair
if this works and they create a test that passes then then the conductor issues a successful commit which again triggers an adversarial model and this proccess loops

if the the builders fail X number of times then this triggers an I.A. Model to come in and review code and try to solve it. 
it will then give its answer to the builder test giver
if the builder test giver agrees it gives it to the conductor
who does a successful commit which triggers the process

if the I.A. is not able to solve it in X tests
then a concensus of experts is used wher another I.A. is brought in to run the concensus and get a final answer
if they fail here then the this module of the program stops
and they go back to the producer and task toe producer with createing a new way of designing this part o fthe program with more simple tasks or a different approah and they try agian


note  - architects should always test the actual progarm to see if it actualy works
note  - producer must make sure it always works


