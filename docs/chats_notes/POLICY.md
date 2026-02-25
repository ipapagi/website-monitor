# Chat Notes Policy for Website-Monitor Project

## Obligation
Every AI agent working on this project **MUST** create session notes in `docs/chats_notes/`.

## Naming Convention
**Format:** `YYYY-MM-DD_<descriptive_name>.md`

**Examples:**
- `2026-02-17_case_inquiry_and_charge_investigation.md`
- `2026-02-18_weekly_report_refactoring.md`
- `2026-02-20_api_endpoint_testing.md`

## File Location
```
docs/chats_notes/<filename>.md
```

## Minimum Content Required

Every chat notes file MUST include:

### 1. Header Section
```markdown
# Chat Session: <Descriptive Title>
**Date:** YYYY-MM-DD  
**Status:** [Active Investigation / Completed / In Progress]  
**Primary Goal:** <Brief description of main objective>
```

### 2. Session Summary
- Main objectives completed (✅ checkmarks)
- Key discoveries
- Problems solved

### 3. Scripts/Functions Created
For each new script/function:
- Name & location
- Purpose
- Usage examples
- Key features

### 4. Technical Insights
- Discoveries about the codebase
- Important distinctions found
- Architecture decisions
- Issues encountered & resolved

### 5. Reference Section
- QueryId mappings (if relevant)
- Field explanations
- Common patterns used

### 6. Notes for Next Session
- If returning to similar topic
- Potential enhancements
- Related work from other sessions
- Quick reference commands

---

## Update Trigger
Create or update notes file when:
- ✅ Starting work on a new topic
- ✅ Significant discoveries made
- ✅ New scripts/functions created
- ✅ Session is ending OR context limit approaching
- ✅ Major bugs fixed or architecture decisions made

## For Next Agent Reviewing This Project

Before starting work:
1. **Check `docs/chats_notes/`** for relevant previous sessions
2. **Read the session date closest to your topic** 
3. **Extract key decisions & discoveries**
4. **Continue work with full context**

---

## Benefits

✅ **Persistent Knowledge:** Survives between chat sessions  
✅ **Onboarding:** New agents understand project history  
✅ **Debugging:** Reference for "why was this decision made?"  
✅ **Quick Reference:** Common commands & patterns  
✅ **Change Tracking:** See what evolved over time  

---

## Important: This is NOT Optional

This policy ensures:
- No repeated investigation of same problems
- Smooth transitions between sessions
- Clear audit trail of decisions
- Faster onboarding of new contributors

**Every agent must follow this.**

---

*Last Updated: 2026-02-17*  
*Policy Version: 1.0*
