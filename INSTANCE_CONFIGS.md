# INSTANCE CONFIGURATIONS

## How to Use This File

Each configuration specifies which models to use for each role in the hierarchy.

**Format:**
```yaml
group_name:
  architect: <model_name>
  orchestrator: <model_name>
  test_taker: <implementation>
  boot_message: <how to initialize>
```

---

## GROUP 1: AMAZON_Q (Recommended)

```yaml
architect: Amazon Q (Claude Sonnet 4.5)
orchestrator: Amazon Q (Claude Haiku 4.5)
test_taker: Jules Sessions (Google)

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: Claude (Anthropic)
  GROUP: AMAZON_Q
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Claude section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: Claude (Anthropic)
  GROUP: AMAZON_Q
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Claude section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - Architect uses Sonnet for complex reasoning
  - Orchestrator uses Haiku for efficiency
  - Jules handles actual code generation
  - Best for production use
```

---

## GROUP 2: CLAUDE_NATIVE

```yaml
architect: Claude Opus 4
orchestrator: Claude Sonnet 4
test_taker: Claude Haiku 4

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: Claude (Anthropic)
  GROUP: CLAUDE_NATIVE
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Claude section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: Claude (Anthropic)
  GROUP: CLAUDE_NATIVE
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Claude section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: Claude (Anthropic)
  GROUP: CLAUDE_NATIVE
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Claude section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - All Claude, no Jules
  - Opus for architect (most capable)
  - Sonnet for orchestrator (balanced)
  - Haiku for test_takers (fast, cheap)
  - Good for non-Jules workflows
```

---

## GROUP 3: OPENAI

```yaml
architect: GPT-5.2 XHigh
orchestrator: GPT-5.2 Medium
test_taker: GPT-5.1 Mini

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: GPT (OpenAI)
  GROUP: OPENAI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → GPT section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: GPT (OpenAI)
  GROUP: OPENAI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → GPT section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: GPT (OpenAI)
  GROUP: OPENAI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → GPT section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - GPT-5.2 for architect (strategic)
  - GPT-5.2 Medium for orchestrator (efficient)
  - GPT-5.1 Mini for test_takers (fast)
  - Good for OpenAI-only environments
```

---

## GROUP 4: GEMINI

```yaml
architect: Gemini 3 Pro
orchestrator: Gemini 3 Flash
test_taker: Gemini 3 Flash Lite

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: Gemini (Google)
  GROUP: GEMINI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Gemini section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: Gemini (Google)
  GROUP: GEMINI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Gemini section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: Gemini (Google)
  GROUP: GEMINI
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Gemini section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - Gemini Pro for architect (creative)
  - Gemini Flash for orchestrator (fast)
  - Gemini Flash Lite for test_takers (efficient)
  - Good for Google ecosystem
```

---

## GROUP 5: DEEPSEEK

```yaml
architect: DeepSeek R1
orchestrator: DeepSeek V3
test_taker: DeepSeek Coder

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: DeepSeek (Chinese)
  GROUP: DEEPSEEK
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: DeepSeek (Chinese)
  GROUP: DEEPSEEK
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: DeepSeek (Chinese)
  GROUP: DEEPSEEK
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - DeepSeek R1 for architect (reasoning)
  - DeepSeek V3 for orchestrator (general)
  - DeepSeek Coder for test_takers (specialized)
  - Good for technical precision
```

---

## GROUP 6: QWEN

```yaml
architect: Qwen 2.5 72B
orchestrator: Qwen 2.5 32B
test_taker: Qwen 2.5 Coder 7B

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: Qwen (Chinese)
  GROUP: QWEN
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: Qwen (Chinese)
  GROUP: QWEN
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: Qwen (Chinese)
  GROUP: QWEN
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → DeepSeek/Qwen section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - Qwen 72B for architect (large context)
  - Qwen 32B for orchestrator (balanced)
  - Qwen Coder 7B for test_takers (specialized)
  - Good for mathematical rigor
```

---

## GROUP 7: MISTRAL

```yaml
architect: Mistral Large
orchestrator: Mistral Medium
test_taker: Codestral

boot_architect: |
  YOU ARE: ARCHITECT
  MODEL: Mistral (European)
  GROUP: MISTRAL
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Mistral section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_orchestrator: |
  YOU ARE: ORCHESTRATOR
  MODEL: Mistral (European)
  GROUP: MISTRAL
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Mistral section
  
  Execute BOOT SEQUENCE.
  BEGIN.

boot_test_taker: |
  YOU ARE: TEST_TAKER
  MODEL: Mistral (European)
  GROUP: MISTRAL
  
  Load:
  1. AGENT_FRAMEWORK_V2.md
  2. MODEL_OPTIMIZATIONS.md → Mistral section
  
  Execute BOOT SEQUENCE.
  BEGIN.

notes: |
  - Mistral Large for architect (strategic)
  - Mistral Medium for orchestrator (efficient)
  - Codestral for test_takers (code-specialized)
  - Good for pragmatic, efficient workflows
```

---

## HYBRID CONFIGURATIONS

### HYBRID 1: Best of Breed
```yaml
architect: Claude Opus 4 (best reasoning)
orchestrator: GPT-5.2 Medium (best efficiency)
test_taker: Jules Sessions (best code generation)

notes: |
  - Use best model for each role
  - Higher cost but maximum quality
  - Recommended for critical projects
```

### HYBRID 2: Cost-Optimized
```yaml
architect: Claude Sonnet 4 (good reasoning, lower cost)
orchestrator: GPT-5.1 Mini (fast, cheap)
test_taker: DeepSeek Coder (specialized, cheap)

notes: |
  - Balance quality and cost
  - Good for high-volume work
  - Recommended for experimentation
```

### HYBRID 3: Speed-Optimized
```yaml
architect: Gemini 3 Flash (fast, creative)
orchestrator: Mistral Medium (fast, pragmatic)
test_taker: Qwen Coder 7B (fast, specialized)

notes: |
  - Optimize for speed
  - Good for rapid prototyping
  - Recommended for time-sensitive work
```

---

## SELECTION GUIDE

**Choose based on:**

| Priority | Recommended Group |
|----------|-------------------|
| Production quality | AMAZON_Q or CLAUDE_NATIVE |
| Cost efficiency | DEEPSEEK or QWEN |
| Speed | MISTRAL or GEMINI |
| OpenAI ecosystem | OPENAI |
| Google ecosystem | GEMINI or AMAZON_Q (Jules) |
| Technical precision | DEEPSEEK or QWEN |
| Creative solutions | GEMINI or CLAUDE_NATIVE |
| Pragmatic execution | MISTRAL |

**Mixing models:**
- Architect: Use most capable (reasoning is critical)
- Orchestrator: Use balanced (efficiency matters)
- Test_taker: Use specialized (code quality matters)

---

**END OF INSTANCE CONFIGURATIONS**
