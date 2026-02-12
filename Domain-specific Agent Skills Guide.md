# Domain-Specific Agent Skills

A comprehensive guide to creating and structuring domain-specific Agent Skills, demonstrated through the **Wikipedia Research Agent** example.

---

## What Are Domain-Specific Agent Skills?

Domain-specific Agent Skills are reusable, filesystem-based capabilities that equip Claude with deep expertise in a specific domain. Unlike general prompts, Skills are:

- **Persistent** - Loaded once, available across conversations
- **Modular** - Combine multiple skills for complex workflows
- **Efficient** - Progressive disclosure minimizes context impact
- **Extensible** - Compose with other skills and tools

### Why Domain-Specific Skills Matter

**General Claude:** Can answer questions about Wikipedia, but slowly and from memory.

**Claude + Wikipedia Research Skill:** Actively fetches current Wikipedia data, extracts structured information, compares topics, and produces JSON for integration—all automatically when relevant.

---

## The Wikipedia Research Agent: A Case Study

The **Wikipedia Research Agent** demonstrates best practices for domain-specific skills:

```
┌─────────────────────────────────────────────────────────┐
│         DOMAIN-SPECIFIC AGENT SKILL FRAMEWORK            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  LEVEL 1: Metadata (Always Loaded)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │ name: wikipedia-research-agent                   │   │
│  │ description: Perform Wikipedia research...       │   │
│  │ (YAML frontmatter, ~100 tokens, always ready)    │   │
│  └──────────────────────────────────────────────────┘   │
│                      ↓ (When triggered)                 │
│  LEVEL 2: Instructions (Loaded On-Demand)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │ # Wikipedia Research Agent Skill                 │   │
│  │ ## Quick Start                                   │   │
│  │ python agent.py search -q "topic"                │   │
│  │ ## Key Capabilities                              │   │
│  │ - Search & disambiguation                        │   │
│  │ - Content extraction                             │   │
│  │ - Summarization                                  │   │
│  │ (<5000 tokens, contextual and focused)           │   │
│  └──────────────────────────────────────────────────┘   │
│                      ↓ (If needed)                      │
│  LEVEL 3: Resources (Filesystem Only)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ MODULE_REFERENCE.md - Technical specs            │   │
│  │ EXAMPLES.md - 14 practical scenarios             │   │
│  │ (No token cost, loaded via bash as needed)       │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Creating Your Own Domain-Specific Skill

### Step 1: Define Your Domain & Metadata

Start with clear, discoverable metadata:

```yaml
---
name: your-domain-skill
description: What this skill does and when Claude should use it. Include both capabilities and trigger conditions. Max 1024 chars.
---
```

**Example (Wikipedia Research):**
```yaml
---
name: wikipedia-research-agent
description: Perform fast, verifiable Wikipedia research with summarization, comparison, and structured extraction. Use when you need accurate encyclopedia information, topic comparisons, or to extract structured data (infoboxes) from Wikipedia pages. Provides JSON output for integration with other tools.
---
```

**Good metadata:**
- ✅ Specific about what it does
- ✅ Clear about when Claude should use it
- ✅ Mentions key capabilities
- ✅ Notes output formats (JSON, etc.)

**Weak metadata:**
- ❌ "Helps with research" (vague)
- ❌ "Use for everything" (too broad)
- ❌ No trigger conditions mentioned
- ❌ Doesn't mention integration capability

### Step 2: Write Core Instructions (SKILL.md)

Your main skill file contains:

#### A. Quick Start (Essential)
Show 3-5 most common operations immediately:

```markdown
## Quick Start

```bash
python agent.py search -q "Python programming"
python agent.py summarize -q "Photosynthesis" --bullets 5
python agent.py compare "Topic1" "Topic2"
python agent.py infobox -q "Croatia"
python agent.py status
```
```

#### B. Key Capabilities Overview
List 3-5 core capabilities with brief explanations:

```markdown
## Key Capabilities

### 1. Capability Name
- What it does
- Example: `command`

### 2. Next Capability
...
```

#### C. Architecture Diagram
Show how components work together:

```markdown
## Architecture

```
Input → Component1 → Component2 → Output
(with line counts, dependencies)
```
```

#### D. Performance Metrics
Real benchmarks (not estimates):

```markdown
## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| First run | 50s | Cold fetch |
| Cached | <1s | 50x improvement |
```
```

#### E. Integration Examples
Show how to use with other systems:

```markdown
## Integration Examples

### CI/CD Pipeline
```bash
python agent.py search -q "topic" --format json > data.json
```

### PowerShell
```powershell
$result = python agent.py search -q "topic" --format json | ConvertFrom-Json
```
```

#### F. Error Handling & Recovery
How failures are handled gracefully:

```markdown
## Error Handling

| Failure | Recovery | Impact |
|---------|----------|--------|
| Timeout | Auto retry | Delayed but works |
| Not found | Suggest alternatives | User guidance |
```
```

### Step 3: Create Technical Reference (MODULE_REFERENCE.md)

For skills with multiple components, document each:

```markdown
# Module Reference

## Component 1: [Name] (Line Count)

**Purpose:** What it does

**Input:**
```python
parameter: type = "description"
```

**Output:**
```python
{
  "field": "value",
  "structured": true
}
```

**Key Functions:**
- `function_1(params)` - Description
- `function_2(params)` - Description

**Performance:**
| Scenario | Time |
|----------|------|
| Best case | Xs |
| Typical | Ys |

**Configuration:**
```json
{
  "setting": "value"
}
```
```

Each component should cover:
- ✅ Clear purpose
- ✅ Input/output contracts
- ✅ Function signatures
- ✅ Real performance data
- ✅ Configuration options

### Step 4: Create Practical Examples (EXAMPLES.md)

Real-world scenarios with working code:

```markdown
# Examples

## Example 1: Scenario Description

**Situation:** What the user is trying to accomplish

**Steps:**
```bash
Step 1 command
Step 2 command
```

**Output:**
```
What the user sees
```

## Example 2: Another Scenario
...
```

Include:
- ✅ 10-15 realistic scenarios
- ✅ Multiple languages (bash, Python, PowerShell)
- ✅ Both success and error cases
- ✅ Integration patterns
- ✅ Performance monitoring examples

### Step 5: Organize for Progressive Disclosure

```
your-skill/
├── SKILL.md              # Level 1-2 (always + trigger load)
├── MODULE_REFERENCE.md   # Level 3 (filesystem reference)
├── EXAMPLES.md          # Level 3 (filesystem reference)
└── README.md            # Optional: overview for developers
```

**Progressive loading:**
- Claude discovers skill via metadata (~100 tokens)
- When relevant, reads SKILL.md instructions (<5k tokens)
- Accesses MODULE_REFERENCE.md/EXAMPLES.md only if needed (no token cost)

---

## Best Practices for Domain-Specific Skills

### 1. Be Specific, Not General
```markdown
❌ WEAK: "Tool for processing documents"
✅ GOOD: "Extract named entities, key phrases, and sentiment from business emails with JSON output for integration with CRM systems"
```

### 2. Include Real Metrics
```markdown
❌ WEAK: "Fast and efficient"
✅ GOOD: "Cold fetch ~50s (one-time), cached retrieval <1s (50x improvement), 87% cache hit rate"
```

### 3. Show Integration Paths
```markdown
❌ WEAK: "Outputs structured data"
✅ GOOD: "JSON output for CI/CD pipelines, PowerShell integration, Python subprocess calls, REST API forwarding"
```

### 4. Document Failure Modes
```markdown
❌ WEAK: "Works reliably"
✅ GOOD: "Timeouts retry 3x with exponential backoff, falls back to alternative method, clear error messages guide users"
```

### 5. Organize by Cognitive Load
- **Quick Start:** Immediate, copy-paste ready
- **Capabilities:** 5-minute read  
- **Architecture:** 10-minute deep dive
- **References:** Lookup-only content (filesystem)

### 6. Use Progressive Disclosure
```
┌─ Metadata (What it does, when to use) ◄─── Always in context
├─ Instructions (How to use it) ◄─── Loaded when triggered  
└─ References (Details, examples) ◄─── Loaded on-demand, no token cost
```

---

## Wikipedia Research Skill: Anatomy

Here's how the Wikipedia skill demonstrates these principles:

### Metadata (Level 1)
```yaml
name: wikipedia-research-agent
description: Perform fast, verifiable Wikipedia research...
```
**Why:** Claude knows the skill exists and when to use it from the start.

### Instructions (Level 2)
- Quick Start: 5 commands users can run immediately
- Capabilities: 5 clearly separated abilities
- Architecture: 4-module pipeline explained
- Performance: Real benchmarks (50x, 2x speedup)
- Integration: CI/CD, PowerShell, Python examples
- Testing: 21/21 passing, what was validated

**Why:** When Claude decides to use Wikipedia research, it has everything needed to execute in <5k tokens.

### References (Level 3)
- **MODULE_REFERENCE.md:** Detailed function signatures, I/O contracts, configuration schemas
- **EXAMPLES.md:** 14 real scenarios from simple to complex

**Why:** Claude loads these only if it needs specific technical details (e.g., exact function parameters) or more examples. No token penalty if not needed.

---

## Key Differences: Skills vs. Prompts

| Aspect | Prompt | Skill |
|--------|--------|-------|
| **Scope** | Single conversation | Persistent, reusable |
| **Context Cost** | Every mention | Loaded progressively |
| **Execution** | Claude generates code | Skill runs actual code |
| **Data** | From memory | Fresh, from APIs |
| **Integration** | Manual | Automatic when relevant |
| **Updates** | Recreate each time | Skill updated once |
| **Example** | "Tell me about X" | Fetch, parse, summarize X |

---

## Skill Deployment Targets

### Claude API
```bash
# Upload custom skill
curl -X POST https://api.claude.com/v1/skills \
  -F "skill=@your-skill.zip"

# Use in conversations
python your_app.py --skill wikipedia-research-agent
```

### Claude Code
```
~/.claude/skills/
└── wikipedia-research-agent/
    ├── SKILL.md
    ├── MODULE_REFERENCE.md
    └── EXAMPLES.md
```
*Claude discovers automatically*

### Agent SDK
```yaml
allowed_tools:
  - "Skill"
  
skills_config:
  - name: wikipedia-research-agent
    path: .claude/skills/wikipedia-research-agent
```

### claude.ai
1. Create skill files
2. Zip as `skill.zip`
3. Settings → Features → Upload Skill
4. Available in conversations with code execution

---

## Common Pitfalls to Avoid

### ❌ Making Skills Too General
```yaml
# BAD
name: general-information-skill
description: Helps with information tasks
```
Claude won't know when to use it automatically.

```yaml
# GOOD
name: wikipedia-research-agent
description: Search Wikipedia, extract infoboxes, generate summaries, compare topics with JSON export for automation
```

### ❌ Insufficient Metadata
Without clear descriptions and trigger conditions, Claude won't use the skill automatically.

### ❌ Confusing Quick Start
If your examples don't work copy-paste ready, users abandon the skill.

### ❌ Missing Integration Info
Developers won't use skills unless they see CI/CD, API, or automation examples.

### ❌ No Error Handling Documentation
Skills should clearly state failure recovery strategies.

### ❌ Irrelevant Performance Data
Benchmarks on an artificial example don't help. Show real-world metrics.

---

## Checklist: Is Your Skill Domain-Specific Enough?

- ✅ Does it have a clear, focused domain? (Wikipedia, code review, data analysis, etc.)
- ✅ Can Claude automatically recognize when to use it? (Specific trigger conditions?)
- ✅ Does it do something Claude can't do alone? (Fetch live data, run tools, access APIs?)
- ✅ Is the description specific enough? (Not generic/vague)
- ✅ Does it include real, measured performance data?
- ✅ Are there 5+ real-world examples?
- ✅ Is error recovery documented?
- ✅ Can developers integrate it easily? (JSON, APIs, CLI?)

---

## Real-World Implementation Patterns

### Pattern 1: API-Based Skill
```
Domain: External API access (Wikipedia, Reddit, HackerNews, etc.)
Key: Fetch real data, cache results, provide structured output
Example: Wikipedia Research Agent (this skill)
```

### Pattern 2: Data Processing Skill
```
Domain: Transform or analyze structured data
Key: Parse, validate, extract, aggregate
Example: CSV analyzer, JSON transformer, log analyzer
```

### Pattern 3: Code Analysis Skill
```
Domain: Review, analyze, or refactor code
Key: Parse syntax, check patterns, suggest improvements
Example: Code reviewer, security analyzer, performance profiler
```

### Pattern 4: Document Generation Skill
```
Domain: Create or modify documents
Key: Template rendering, structure validation, batch operations
Example: Report generator, contract builder, email formatter
```

### Pattern 5: Integration Hub Skill
```
Domain: Connect multiple services
Key: API orchestration, data mapping, workflow automation
Example: CRM sync, database migration, CI/CD trigger
```

---

## Measuring Skill Effectiveness

Track these metrics to understand if your skill is domain-specific enough:

| Metric | Good Range | Warning Sign |
|--------|-----------|--------------|
| **Trigger Specificity** | Claude uses skill 70%+ of the time when relevant | <30% - too generic |
| **Documentation Clarity** | Users complete examples in <5 minutes | >15 minutes - unclear |
| **Error Recovery Rate** | 95%+ of failures handled gracefully | <80% - needs better handling |
| **Integration Adoption** | 3+ external integrations | 0 - too standalone |
| **Performance Improvement** | Measurable vs. without skill | No difference - doesn't add value |

---

## Next Steps

1. **Define Your Domain** - What specific expertise should Claude have?
2. **Create Metadata** - Clear, discoverable description
3. **Write Instructions** - Quick start, capabilities, architecture
4. **Document Technical Details** - References, configurations
5. **Build Examples** - Real scenarios from your domain
6. **Test Triggers** - Does Claude use it automatically?
7. **Gather Feedback** - Refine based on usage patterns
8. **Iterate** - Update skill as domain evolves

---

## Reference: Wikipedia Research Agent Structure

```
SKILL.md
├── YAML Metadata (name, description)
├── Quick Start (5 commands)
├── Key Capabilities (5 features explained)
├── Architecture Overview (4-module pipeline)
├── Performance Characteristics (real benchmarks)
├── Error Handling & Resilience (failure modes)
├── Integration Capabilities (CI/CD, PowerShell, Python)
├── Production Readiness (10-point checklist)
├── When to Use This Skill (scenarios)
└── Limitations (what it doesn't do)

MODULE_REFERENCE.md
├── SearchModule (function signatures, performance)
├── FetchModule (caching strategy, config)
├── ParseModule (input/output contracts)
├── SummarizeModule (algorithms explained)
├── CLI Agent (commands, formats)
└── Dependency List

EXAMPLES.md
├── Example 1: Quick Research
├── Example 2: Data Extraction
├── Example 3: Topic Comparison
├── ... (14 scenarios total)
└── Best Practices & Troubleshooting
```

Each level serves a purpose and appears at the right time (progressive disclosure).

---

**Created:** February 12, 2026  
**Domain Example:** Wikipedia Research & Browsing CLI Agent  
**Use This Guide:** To create your own domain-specific Agent Skills  
**Questions?** Check MODULE_REFERENCE.md for technical details, or EXAMPLES.md for practical use cases
