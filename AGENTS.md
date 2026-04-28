## Autonomy Contract

Do not stop after one attempt.

For every task:
1. Inspect the relevant files.
2. Make the smallest coherent change.
3. Run the relevant test/build/lint command.
4. If it fails, diagnose and fix.
5. Repeat until one of these is true:
   - the requested behavior is working,
   - a blocker is proven with exact error output,
   - continuing would require unavailable resources or unsafe changes.

Never end with “you can now test it” if you have access to tools.

Before stopping, report:
- files changed
- commands run
- result
- remaining blocker (if any)




---

## Delegation Rules (Subagents)

Use subagents to avoid stalling or overloading a single reasoning chain.

### When to Delegate

Spawn a subagent when:
- the task splits into independent concerns (UI vs API vs data)
- investigation is needed before implementation
- repeated retries are failing without new insight
- browser testing or reproduction is required
- large file or multi-file analysis is needed

Do NOT delegate:
- trivial edits
- single-file changes with clear scope
- tasks that require tight iteration (edit → test → fix)


---

## Types of Subagents

### 1. Investigator
Purpose: gather facts before changes

Allowed actions:
- read files
- search codebase
- inspect logs
- use browser tools to reproduce issues

Output must include:
- exact files/lines involved
- root cause hypothesis
- confidence level

Must NOT modify code.


---

### 2. Implementer
Purpose: execute a clearly defined change

Input must include:
- exact files to modify
- expected outcome

Must:
- make minimal edits
- avoid scope creep

Must NOT redefine the problem.


---

### 3. Tester
Purpose: validate behavior

Allowed actions:
- run build/test commands
- use browser automation
- verify UI/UX behavior

Output must include:
- steps taken
- pass/fail result
- exact error output if failing

Browser Testing

Purpose: validate behavior with the strongest available verification path.

Priority order:
1. Playwright MCP browser automation
2. Existing Playwright test suite
3. CLI Playwright script written for this task
4. App build/lint/typecheck
5. Static inspection only if all runtime paths are blocked

The Tester must not skip browser validation merely because MCP browser access is unavailable. It must attempt the next fallback.

---

### 4. Refiner (optional)
Purpose: fix failing implementations

Triggered when:
- tests fail after implementation

Must:
- diagnose failure
- apply targeted fix
- re-run tests


---

## Delegation Flow

Default loop:

1. Investigator → understand problem
2. Implementer → apply fix
3. Tester → verify
4. Refiner → (only if needed)

Repeat until done condition is satisfied.


---

## Control Rules

- Maximum 1 active subagent at a time
- Always wait for subagent output before proceeding
- Do not recursively spawn subagents (no nesting)
- If 2 consecutive cycles fail, spawn Investigator again before continuing
- If no progress after 3 full cycles, declare blocker with evidence


---

## Completion Criteria

A task is only complete when:
- behavior is verified via test, build, or browser
- no obvious next step is available using current tools

If tools are available, continue.


---

## Anti-Stall Rules

Do not stop because:
- “it should work”
- “changes look correct”
- “user can verify”

Only stop with:
- verified success
- or explicit blocker with evidence


---

## Reporting Format

At the end of each cycle:

- Step: (Investigate / Implement / Test / Refine)
- Actions taken:
- Files touched:
- Commands run:
- Result:
- Next step:

Do not summarize broadly. Stay operational.


## Browser / Playwright Availability Rules

A subagent may not report “browser not available” until it has proven that with commands.

Before declaring browser unavailable, it must try:

1. Check available MCP/tools.
2. Check package scripts:
   - `cat package.json`
   - look for `test`, `e2e`, `playwright`, `dev`
3. Check installed binaries:
   - `npx playwright --version`
   - `npm ls @playwright/test playwright`
4. If Playwright is missing but Node is available, report:
   - exact install command needed
   - whether installing is safe for this repo
5. If browser MCP is unavailable, fall back to CLI Playwright if present.
6. If CLI Playwright is unavailable, fall back to app-level tests/build.
7. If no browser path exists, provide exact proof.

Forbidden blocker phrase:

> browser not available

Allowed blocker format:

> Browser verification blocked because `[exact command/tool]` failed with `[exact error]`. I attempted `[fallbacks]`.
>
> 




## Current Project Context

**Goal:** CLI-first + HTML preview tools for curating Traktor DJ collection.

**Working features:**
- NML parser (4525 tracks)
- Missing file scanner with Everything HTTP API integration
- HTML preview generator with interactive selection
- Apply changes with backup
- Duplicate detection

**Key files:**
- `src/missing.py` - Missing file scanner, Everything integration
- `src/preview.py` - HTML preview generator
- `src/everything.py` - Everything HTTP API client
- `traktor-tools/config.toml` - Config with search roots

**Known issues:**
- Browser connection flaky (workaround: use direct HTTP URL)
- Short titles like "4D" can match multiple files
- Network drives (Y:, Z:) not searched

**Commands:**
```bash
python src/cli.py preview --remove-self-matches  # Generate preview
python src/cli.py apply selections/...json        # Apply changes
```