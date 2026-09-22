# LedgerLens Team Protocol

**Last Updated:** 2026-09-22  
**Phase:** PHASE 0 — FOUNDATION  
**Status:** Team Collaboration Specification

---

## 1. Overview

This document defines the collaboration workflow, agent activation policy, task assignment protocol, and engineering practices for the LedgerLens development team.

**Team Structure:** Progressive multi-agent system  
**Coordination:** MASTER / CTO orchestrates all specialist agents  
**Execution Mode:** Serial by default, parallel when safe

---

## 2. Agent Collaboration Workflow

### 2.1 Standard Work Cycle

```
PLAN
  ↓
CONTEXT
  ↓
DELEGATE
  ↓
IMPLEMENT
  ↓
VERIFY
  ↓
REVIEW
  ↓
INTEGRATE
  ↓
DOCUMENT
  ↓
UPDATE STATUS
```

### 2.2 Workflow Stages

#### PLAN
**Owner:** MASTER  
**Activity:**
- Understand requirement
- Break down into tasks
- Identify dependencies
- Determine task owner
- Define acceptance criteria
- Assess risks

**Output:** Task record in TASK_BOARD.md

---

#### CONTEXT
**Owner:** MASTER  
**Activity:**
- Gather relevant documentation
- Identify files/modules affected
- Identify interfaces
- Identify constraints
- Prepare context package for specialist

**Output:** Context brief for specialist agent

---

#### DELEGATE
**Owner:** MASTER  
**Activity:**
- Activate specialist agent if needed
- Assign task to specialist
- Provide context package
- Set acceptance criteria
- Define boundaries

**Output:** Agent activation and task assignment

---

#### IMPLEMENT
**Owner:** Specialist Agent  
**Activity:**
- Read provided context
- Implement solution
- Follow coding standards
- Write tests
- Document changes

**Output:** Implementation (code, configuration, documentation)

---

#### VERIFY
**Owner:** Specialist Agent  
**Activity:**
- Run tests
- Run linters
- Run type checkers
- Verify acceptance criteria
- Check for regressions

**Output:** Verification report

---

#### REVIEW
**Owner:** MASTER  
**Activity:**
- Inspect changes
- Verify claims
- Check architectural alignment
- Check security implications
- Run relevant tests
- Identify integration issues

**Output:** Review feedback or approval

---

#### INTEGRATE
**Owner:** MASTER  
**Activity:**
- Merge changes
- Resolve conflicts
- Update dependent modules
- Run integration tests

**Output:** Integrated codebase

---

#### DOCUMENT
**Owner:** Specialist Agent or Documentation Engineer  
**Activity:**
- Update relevant documentation
- Record decisions (DECISIONS.md)
- Update API contracts if changed
- Update architecture docs if changed

**Output:** Updated documentation

---

#### UPDATE STATUS
**Owner:** MASTER  
**Activity:**
- Mark task complete
- Update STATUS.md
- Update TASK_BOARD.md
- Record completion timestamp

**Output:** Updated project status

---

## 3. Progressive Agent Activation Policy

### 3.1 Principle

**Agents are activated only when needed for current phase work.**

Do NOT create or activate specialist agents merely because their role exists in the long-term team specification.

### 3.2 Activation Criteria

Before activating any specialist agent, the MASTER must evaluate:

1. **Why is this agent needed now?**  
   What specific work requires this specialization?

2. **What task requires it?**  
   Clear task definition with acceptance criteria

3. **What context does it need?**  
   Relevant documentation, files, interfaces

4. **What does it own?**  
   Clear ownership boundaries

5. **What agents does it depend on?**  
   Required prior work, interfaces

6. **What interfaces must already exist?**  
   Architectural boundaries, API contracts

7. **How will its work be verified?**  
   Testing strategy, review process

### 3.3 Activation Process

**Step 1:** MASTER identifies need  
**Step 2:** MASTER evaluates activation criteria  
**Step 3:** MASTER creates agent definition in `.opencode/agents/[name].md`  
**Step 4:** MASTER provides context brief  
**Step 5:** MASTER records activation in AGENTS.md  
**Step 6:** MASTER updates STATUS.md  
**Step 7:** Agent begins work

### 3.4 Planned Activation Schedule

**Phase 0:**
- MASTER / CTO ✅ (2026-09-22)
- System Architect ✅ (2026-09-22)
- Documentation / Context Engineer ✅ (2026-09-22)

**Phase 1:**
- Database Engineer (when database schema needed)
- Backend Engineer (when API implementation begins)

**Phase 2:**
- Blockchain Engineer (when blockchain adapters needed)
- Graph / Intelligence Engineer (when graph engine needed)

**Phase 3:**
- Frontend Engineer (when UI implementation begins)
- QA / Test Engineer (when comprehensive testing needed)

**Phase 4:**
- VASP / Entity Intelligence Engineer (when attribution engine needed)
- Risk Engineer (when risk scoring needed)

**Phase 5:**
- AI / Copilot Engineer (when LLM integration needed)

**Phase 6-7:**
- Security Engineer (security audit)
- Release / Documentation Engineer (as needed)

---

## 4. Task Assignment Protocol

### 4.1 Task Record Format

Every task must be documented in `tasks/TASK_BOARD.md` with:

```markdown
### TASK-[PHASE]-[NUMBER]: [Title]
**Owner:** [Agent]  
**Status:** [Status]  
**Priority:** [Priority]  
**Started:** [Date]  
**Dependencies:** [Task IDs or "None"]

**Objective:**  
[What must be accomplished]

**Files/Modules:**
- [File paths or module names]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

**Progress:**
- [x] Completed item
- [ ] Pending item

**Risks:**
[Identified risks and mitigation]
```

### 4.2 Task Status Values

| Status | Meaning |
|--------|---------|
| BACKLOG | Task defined but not yet ready to start |
| READY | Task ready to begin (dependencies met) |
| IN_PROGRESS | Task currently being worked on |
| BLOCKED | Task cannot proceed due to external blocker |
| REVIEW | Task complete, awaiting MASTER review |
| VERIFIED | Task reviewed and verified by MASTER |
| COMPLETE | Task finished and integrated |

### 4.3 Priority Levels

| Priority | Meaning |
|----------|---------|
| HIGH | Critical path for current phase |
| MEDIUM | Important but not blocking |
| LOW | Nice to have, can be deferred |

### 4.4 Task Dependencies

**Before starting a task:**
- Verify all dependencies are COMPLETE
- If dependency blocked, task status becomes BLOCKED
- MASTER resolves dependency conflicts

---

## 5. File Ownership Rules

### 5.1 Principle

Each specialist owns specific domains. Multiple agents must NOT simultaneously redesign the same file.

### 5.2 Ownership Boundaries

See AGENTS.md for complete ownership mapping.

**Examples:**
- Backend Engineer owns `backend/`
- Database Engineer owns `database/`, `migrations/`, `supabase/`
- Frontend Engineer owns `frontend/`
- Blockchain Engineer owns `services/blockchain/`, `services/tracing/`
- Documentation Engineer owns `docs/` (except architecture docs)
- System Architect owns `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`

### 5.3 Cross-Cutting Changes

When multiple domains need the same change:

**Step 1:** Discuss the interface first  
**Step 2:** Owner implements their side  
**Step 3:** Consumer adapts to interface  
**Step 4:** QA validates both sides

**Example: Backend changes API contract**

1. Backend Engineer proposes new API contract
2. MASTER reviews and approves
3. Documentation Engineer updates `docs/API_CONTRACT.md`
4. Backend Engineer implements backend changes
5. Frontend Engineer adapts frontend to new contract
6. QA Engineer validates end-to-end

**Never allow:**
- Backend Engineer and Frontend Engineer independently inventing incompatible contracts
- Multiple agents simultaneously editing the same file
- Competing implementations of the same domain logic

---

## 6. Parallel vs. Serial Execution

### 6.1 Default Mode: SERIAL

**Serial execution is the default mode.**

Tasks are completed sequentially:
1. Task A assigned and completed
2. MASTER reviews and integrates
3. Task B assigned and completed
4. MASTER reviews and integrates

**Rationale:**
- Ensures architectural consistency
- Prevents conflicts
- Allows MASTER review between phases
- Reduces integration complexity

### 6.2 When Parallel Execution is Allowed

Parallel execution allowed ONLY when:

1. ✅ Tasks are genuinely independent
2. ✅ Ownership boundaries are explicit
3. ✅ Shared interfaces are already defined
4. ✅ No two agents modifying the same files
5. ✅ MASTER has verified integration risk is low

**Example: Safe parallel work**
- Database Engineer creates schema
- Documentation Engineer creates ROADMAP.md
- (No shared files, no dependencies)

### 6.3 When Parallel Execution is FORBIDDEN

**Never allow parallel execution when:**

❌ Two agents designing the same interface  
❌ Competing database schemas  
❌ Competing API contracts  
❌ Duplicate domain models  
❌ Conflicting architectural implementations  
❌ Simultaneous uncontrolled edits to shared files

**Example: Unsafe parallel work**
- Backend Engineer implementing API routes
- Frontend Engineer implementing API client
- (Must wait for API contract to be finalized first)

### 6.4 MASTER Approval Required

Before authorizing parallel execution, MASTER must:

1. Verify tasks are truly independent
2. Confirm ownership boundaries
3. Check for hidden dependencies
4. Assess integration risk
5. Plan integration verification

---

## 7. Review Gates

### 7.1 MASTER Review Checklist

Before approving any significant feature, MASTER must verify:

**ARCHITECTURE:**
- [ ] Does this respect existing boundaries?
- [ ] Is logic duplicated?
- [ ] Is this extensible?
- [ ] Does this follow single source of truth principle?

**CORRECTNESS:**
- [ ] Does it work as specified?
- [ ] What happens on malformed input?
- [ ] What happens when external providers fail?
- [ ] Are error paths handled?

**SECURITY:**
- [ ] Are credentials protected?
- [ ] Can users access data they should not?
- [ ] Is external data validated?
- [ ] Are secrets excluded from logs?

**DATA:**
- [ ] Is the data model consistent?
- [ ] Are migrations reversible?
- [ ] Are indexes appropriate?

**OBSERVABILITY:**
- [ ] Can failures be diagnosed?
- [ ] Are relevant events logged?
- [ ] Are errors meaningful?

**UX:**
- [ ] Does the UI accurately represent uncertainty?
- [ ] Are explanations understandable?
- [ ] Is loading state handled?

**AI (Phase 5):**
- [ ] Is the model grounded in case data?
- [ ] Can it hallucinate unsupported claims?
- [ ] Can every claim be traced to underlying data?

**TESTING:**
- [ ] Do tests exist?
- [ ] Do tests pass?
- [ ] Are edge cases covered?

**DOCUMENTATION:**
- [ ] Is documentation updated?
- [ ] Are API contracts synchronized?
- [ ] Are decisions recorded?

### 7.2 Phase Gate Reviews

At the end of each phase, MASTER conducts full phase review:

1. Verify all phase tasks COMPLETE
2. Verify phase acceptance criteria met
3. Run full test suite
4. Update STATUS.md
5. Update ROADMAP.md
6. Prepare next phase plan
7. **STOP and await explicit authorization for next phase**

---

## 8. Definition of Done

A feature is NOT complete merely because code exists.

A feature is complete only when:

- [ ] Implementation exists and works
- [ ] Architecture remains coherent
- [ ] Tests exist and pass
- [ ] Error paths are handled
- [ ] Security implications are considered
- [ ] Documentation is updated
- [ ] API contracts are synchronized
- [ ] No obvious regression exists
- [ ] Acceptance criteria are satisfied
- [ ] STATUS.md is updated
- [ ] TASK_BOARD.md is updated
- [ ] MASTER has reviewed and approved
- [ ] Agent ownership is respected
- [ ] No secrets committed

---

## 9. Communication Patterns

### 9.1 Agent-to-MASTER

**When to communicate:**
- Task complete, requesting review
- Blocked by dependency
- Discovered architectural issue
- Need clarification on requirements
- Security concern identified

**Communication format:**
```
STATUS: [IN_PROGRESS | BLOCKED | REVIEW | COMPLETE]
TASK: TASK-P0-003
SUMMARY: [Brief summary]
DETAILS: [Detailed explanation]
NEXT: [What happens next]
```

### 9.2 MASTER-to-Agent

**When to communicate:**
- Task assignment
- Context provision
- Review feedback
- Approval
- Clarification
- Course correction

**Communication format:**
```
AGENT: [Agent name]
ACTION: [ASSIGN | REVIEW | APPROVE | CLARIFY | CORRECT]
TASK: TASK-P0-003
DETAILS: [Explanation]
CONTEXT: [Relevant files, documentation]
ACCEPTANCE: [Criteria for completion]
```

### 9.3 Agent-to-Agent

**Direct agent-to-agent communication is NOT standard.**

Agents communicate through MASTER coordination.

**Exception:** When MASTER explicitly authorizes agents to collaborate on interface definition.

---

## 10. Context Management

### 10.1 Context Documents

**Project Memory:**
- docs/MASTER_BOOTSTRAP.md (governing specification)
- docs/PROJECT_BRIEF.md (mission and scope)
- docs/STATUS.md (current state)
- AGENTS.md (team structure)
- tasks/TASK_BOARD.md (current work)

**Architecture:**
- docs/ARCHITECTURE.md (system design)
- docs/DOMAIN_MODEL.md (entities)
- docs/API_CONTRACT.md (interfaces)
- docs/DATA_MODEL.md (database)
- docs/DECISIONS.md (ADRs)

**Standards:**
- docs/SECURITY_MODEL.md (security)
- docs/TEAM_PROTOCOL.md (this document)
- docs/ROADMAP.md (phases)

### 10.2 Minimum Necessary Context

**Do not dump the entire repository into an agent context.**

For each agent, provide only:
- Task objective
- Relevant files
- Relevant documentation sections
- Interface contracts
- Constraints
- Expected outputs

### 10.3 Context Updates

**After completing work:**
- Update STATUS.md (current state)
- Update TASK_BOARD.md (task completion)
- Update DECISIONS.md (if architectural decision made)
- Update relevant documentation files

**Do NOT:**
- Duplicate information across documents
- Put temporary reasoning in permanent architecture docs
- Modify stable architecture without MASTER approval

---

## 11. Failure and Conflict Resolution

### 11.1 Task Failures

**If implementation fails:**

1. Specialist reports to MASTER with failure reason
2. MASTER evaluates root cause
3. Options:
   - Adjust approach
   - Provide additional context
   - Reassign task
   - Defer task
   - Escalate to architectural decision

**If same approach fails twice:**
- Do NOT keep trying incrementally
- Diagnose root cause
- Try fundamentally different approach
- Consult architectural decisions

### 11.2 Agent Conflicts

**If two agents produce conflicting implementations:**

1. MASTER reviews both implementations
2. MASTER evaluates against architecture
3. MASTER selects one approach or defines hybrid
4. Losing agent adapts to winning approach
5. MASTER documents decision in DECISIONS.md

**Prevention:**
- Serial execution by default
- Clear ownership boundaries
- Interface-first design

### 11.3 Architectural Conflicts

**If specialist proposes change conflicting with architecture:**

1. Specialist explains rationale to MASTER
2. MASTER evaluates against architectural principles
3. Options:
   - Reject proposal (follow existing architecture)
   - Accept proposal (update architecture documents)
   - Defer decision (requires more analysis)

**Document outcome:**
- If architecture changes: update ARCHITECTURE.md, record ADR in DECISIONS.md
- If proposal rejected: record rationale

---

## 12. Version Control Practices

### 12.1 Commit Standards

**Commit messages:**
```
[TASK-P0-003] Create SECURITY_MODEL.md

- Document security principles
- Define credential management strategy
- Specify API security requirements
```

**Format:**
- Prefix with task ID
- Concise summary line (<72 chars)
- Detailed explanation if needed

### 12.2 Branch Strategy (Future)

**For MVP:**
- Single `main` branch initially
- Direct commits allowed during Phase 0-1

**Future:**
- Feature branches (`feature/TASK-P1-005-case-api`)
- Pull requests for review
- Main branch protected

### 12.3 Commit Safety

**Before committing:**
- Run `git status`
- Run `git diff`
- Verify no secrets included
- Verify only intended files staged
- Run linters/tests if applicable

**Never commit:**
- `.env` files
- API keys
- Database credentials
- Private keys
- Passwords

---

## 13. Testing Protocol

### 13.1 Test Ownership

**Unit Tests:** Owned by implementing specialist  
**Integration Tests:** Owned by implementing specialist  
**End-to-End Tests:** Owned by QA Engineer (Phase 3+)

### 13.2 Test Requirements

**For every feature:**
- Unit tests for business logic
- Integration tests for API endpoints
- Error case tests
- Edge case tests

**Test naming:**
```python
def test_calculate_risk_score_with_malicious_association():
    # Given: wallet with known malicious association
    # When: calculate_risk_score called
    # Then: risk score includes malicious factor
```

### 13.3 Test Execution

**Before marking task complete:**
- Run relevant tests
- Verify tests pass
- Check code coverage (target: 80%+)
- Run linters (Python: ruff, black; JS: eslint, prettier)
- Run type checkers (Python: mypy; TS: tsc)

---

## 14. Documentation Standards

### 14.1 Code Documentation

**Python:**
```python
def calculate_risk_score(wallet: Wallet, context: RiskContext) -> RiskScore:
    """Calculate explainable risk score for wallet.
    
    Args:
        wallet: Wallet to analyze
        context: Additional context (transactions, patterns, entities)
    
    Returns:
        RiskScore with factors and evidence
    
    Raises:
        ValidationError: If wallet data invalid
    """
```

**TypeScript:**
```typescript
/**
 * Fetch case details from backend API
 * @param caseId - UUID of the case
 * @returns Promise resolving to Case object
 * @throws APIError if request fails
 */
async function fetchCase(caseId: string): Promise<Case> {
```

### 14.2 Architecture Documentation

**When to update:**
- New module added
- Interface changed
- Technology decision made
- Security requirement added

**Files to update:**
- ARCHITECTURE.md (system design)
- API_CONTRACT.md (if API changed)
- DECISIONS.md (if decision made)

### 14.3 Documentation Ownership

- **System Architect:** ARCHITECTURE.md, DECISIONS.md
- **Documentation Engineer:** PROJECT_BRIEF.md, TEAM_PROTOCOL.md, ROADMAP.md, STATUS.md, SECURITY_MODEL.md
- **Backend Engineer:** Backend code comments, API docs
- **Frontend Engineer:** Frontend code comments, component docs

---

## 15. Quality Standards

### 15.1 Code Quality

**Principles:**
- DRY (Don't Repeat Yourself)
- SOLID principles
- Clear naming
- Single responsibility
- Testability

**Tools:**
- Python: black (formatting), ruff (linting), mypy (type checking)
- TypeScript: prettier (formatting), eslint (linting), tsc (type checking)

### 15.2 Security Quality

**Every feature:**
- Input validation
- Authentication/authorization checks
- Error handling
- No secrets in code
- No sensitive data in logs

### 15.3 Performance Quality

**Consider:**
- Database query optimization
- API response time (<2s for standard requests)
- Blockchain API rate limits
- Caching strategies
- Background job efficiency

---

## Protocol Status

**Phase 0:** Team protocol documented ✅  
**Phase 1+:** Protocol enforcement begins

---

**Document Status:** Team collaboration specification  
**Approval Required:** MASTER / CTO  
**Dependencies:** AGENTS.md, STATUS.md, ARCHITECTURE.md
