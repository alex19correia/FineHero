# GEMINI Rules

This document outlines the rules and guidelines for AI behavior, promoting safety and consistency in interactions.

## Global Rules

General rules for the AI's behavior, promoting safety and consistency.

### confirm_before_destructive_commands
**Description:** Always ask for user confirmation before executing commands that modify or delete files, or change system state (e.g., 'rm', 'git reset').

### no_hardcoded_secrets
**Description:** Prohibit writing hardcoded secrets or API keys into files. Use environment variables or a secure secret management tool instead.

### enforce_style_guide
**Description:** Adhere to established coding style guides for the project's language (e.g., PEP 8 for Python, Prettier for JavaScript).

### workspace_sandboxing
**Description:** All file system operations should be restricted to the project's workspace directory unless explicitly permitted by the user.

## Tool Restrictions

Specific restrictions on tool usage to prevent unintended consequences.

### run_shell_command
**Restriction:** Avoid using shell commands that can have system-wide impact without clear user consent and understanding. Prefer safer, more specific tools when available.

### git
**Restriction:** Do not 'git push' changes to a remote repository without explicit user confirmation on the exact changes to be pushed.

## Prompt Guidelines

Guidelines for interpreting and responding to user prompts.

### clarify_ambiguity
**Description:** If a user's request is ambiguous or lacks detail, ask clarifying questions before taking action.

### explain_plan
**Description:** For multi-step tasks, briefly explain the plan of action to the user before starting.

### state_assumptions
**Description:** If you have to make an assumption to proceed, state the assumption clearly to the user.

### prefer_user_code_style
**Description:** When modifying code, mimic the style, structure, and conventions of the existing codebase.

### consult_rules_and_docs
**Description:** Before executing a complex task, review `gemini_rules.json` and any relevant project documentation to ensure compliance and accuracy.

### self_correct_and_learn
**Description:** If a mistake is made, analyze the cause and update internal knowledge or suggest rule improvements to prevent recurrence.

## Development Rules

### code_review_process
**Description:** Run the codeRabbit CLI by running the command: `coderabbit --prompt-only -t uncommitted`. It's a long running task and might take a while. Check every 2 minutes if it's complete and once its complete review and validate critical fixes and recommended fixes, while ignoring nits or unnecessary changes. Then fix those and run coderabbit again. You can run this loop for up to 3 times.

### When Creating New Documents

**Before Creating a New Document:**
1. Check if master document already exists
2. If yes, update existing document instead of creating new
3. If no, create in appropriate subfolder (CURRENT/IMPLEMENTATION/REFERENCE)

**Document Naming:**
- Use descriptive names: `user_authentication_implementation.md`
- Include dates in planning docs: `sprint_plan_2025_11_11.md`
- Never use version numbers: `strategy_v2.md` ❌

**Content Organization:**
- Keep master documents comprehensive
- Keep planning documents focused and time-bound
- Reference master documents from planning docs

### When Updating Documents

**Master Documents (CURRENT/):**
- Update in place with new information
- Include change history at bottom
- Mark significant updates with dates

**Implementation Documents (IMPLEMENTATION/):**
- Update as development progresses
- Archive completed sections to REFERENCE/
- Delete expired planning documents

### When Deleting Documents

**Planning Documents (After Implementation):**
- Delete immediately after completion
- Don't keep "just in case" copies
- Use Git history if you need to reference old content

**Draft Documents (After Approval):**
- Delete once final version is approved
- Keep only the final approved version
- Reference Git history for change tracking
