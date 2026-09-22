# AGENTS.md — Root Workspace Configuration

You are an autonomous coding agent working on **Carbon Auditor**. This file is your entry point and outranks nothing except a direct, explicit instruction from the human operator in the current session. Everything else — what to build, how the environment works, and what to do next — lives in the three files indexed below. You do not have implicit knowledge of this project beyond what they contain.

## Zero-Assumptions Rule

Do not assume a library, a file, a folder, a command, or a design decision exists or is correct just because it seems standard or you've seen it in other projects. If it is not written in `docs/PRD.md`, `docs/TECH_STACK.md`, or `docs/DESIGN.md`, treat it as undefined — and undefined means you stop and ask (see Stop Conditions below), you do not invent a reasonable-sounding default.

## Modular Code Rule

**Write strictly modular code.** Do not place everything in a single file. Break down services, utilities, and components into logical, separate files (e.g. separating database logic, prompt templates, core business logic, and API routes) to maintain clean architecture and readability. Ensure this applies to everything you build.

## Core Authority Index (Progressive Disclosure)

Read these in this order, every time you start or resume work, before writing a single line of code:

1. **`docs/PRD.md`** — *what* to build and *why*. Contains the product definition, in-scope/out-of-scope boundaries (§5.1/5.2), and binary acceptance criteria (§29) for every user story. If a task's purpose is unclear, this is where the "why" lives.
2. **`docs/DESIGN.md`** — *how it's structured*. The exact folder topology, data models (DynamoDB schemas), and API contracts (request/response JSON, status codes). Treat every shape in here as exact — do not add, rename, or drop a field without a corresponding update to this file.
3. **`docs/TECH_STACK.md`** — *what to run*. The exact language/framework versions, install/run/lint/test/build/deploy commands, and the Disallowed Packages list. Never use a command, library, or version not listed here.

Do not proceed to `docs/TASKS.md` without having the current state of all three of the above in mind for the task you're about to attempt.

## How You Are Invoked — Two Modes

The operator will run you in one of two modes. **Determine which mode applies from the operator's actual wording before you start** — do not default to one without checking.

### Mode A — Single-Task Mode (default when no range is named)
The operator says something like "do the next task" or gives no scope at all. Execute **exactly one** unchecked task from `docs/TASKS.md`, then stop and report, per the Operational Loop below.

### Mode B — Batch/Phase Mode (triggered by naming a phase, a range, or "continue until X")
The operator says something like *"start work on Phase 0 and Phase 1,"* *"do everything through Phase 5,"* *"run the whole roadmap,"* or *"keep going until it's done."* In this mode:

- Execute **every unchecked task in the named range, in order, without stopping between tasks or asking for per-task confirmation.**
- Each task still individually follows the full test-first → implement → run the exact verify command → confirm green → check the box cycle. Batch mode changes *how many tasks you do before reporting back*, never *how carefully each one is done*. Do not skip a test, skip a verify command, or check a box without a genuinely green result just because you're moving faster through a batch.
- Each phase in `docs/TASKS.md` ends with a **Phase Gate** task. Do not consider a phase "done" or move into the next phase until its Phase Gate task has been run and reported green — this is your automatic checkpoint and requires no separate instruction from the operator to trigger.
- You do not need the operator to re-confirm between phases within the requested range (e.g. if asked for "Phase 0 through Phase 3," clearing Phase 0's gate is not a stopping point — proceed straight into Phase 1).
- **Batch mode never overrides the Stop Conditions below.** Hitting a real blocker mid-batch still means: stop immediately, report exactly where you are and why, and wait — you do not skip the failing task and move on to keep the batch moving, and you do not attempt more than the two fix attempts allowed before halting.
- When a batch completes (either the full named range is done, or you hit a Stop Condition), report: which tasks were completed, the final state of each Phase Gate you crossed, and — if you stopped early — the exact blocker.

If the operator's wording is genuinely ambiguous about scope, default to Mode A (safer) and state that assumption in your response rather than guessing at a wider scope.

## Operational Loop (Applies to Every Task, in Either Mode)

1. Identify the task: in Mode A, the first unchecked `- [ ]` box in `docs/TASKS.md`, in document order. In Mode B, the next unchecked box within the requested range.
2. Re-confirm against `docs/PRD.md`/`docs/DESIGN.md` that you understand what this specific task requires. If the task references a section (e.g. "§14", "§16.11"), open and read that exact section — do not rely on a paraphrase from memory.
3. If the task specifies a test-first step, write or update that test **before** writing any implementation code.
4. Implement the minimum code required to satisfy the task.
5. Run the exact command listed in the task's **Run:**/**Verify:** line — never a substitute command, and never skip this step because you're confident it will pass.
6. Confirm the result is genuinely green (all tests pass, coverage threshold met where specified, no silently-skipped tests). A partial pass is not a pass.
7. Update `docs/TASKS.md`, changing that one task's `- [ ]` to `- [x]`.
8. **In Mode A:** stop here and report what you did and the verification output. **In Mode B:** if the task just completed was a Phase Gate, report the gate result, then continue into the next phase if it's within the requested range; otherwise, proceed directly to the next unchecked task in range without a separate report per task — batch your reporting to phase-gate boundaries, not every individual checkbox.

## Stop Conditions — Halt and Await Human Input (Overrides Both Modes)

Stop immediately, do not attempt a workaround, and clearly report the blocker if any of the following occur:

- **Two consecutive cascading test failures** — you attempt a fix, run the test command, it still fails, you attempt a second fix, and it still fails. Do not attempt a third fix on your own; report both attempts and the exact failure output.
- **A required detail is missing from `docs/DESIGN.md` or `docs/PRD.md`** — e.g. a field, endpoint, or behavior the current task needs isn't specified anywhere in the three authority files. Do not invent the missing detail, even a "reasonable" one.
- **A task appears to require a package on the Disallowed List** (`docs/TECH_STACK.md` §12). Do not install it. Report the conflict.
- **A task's instructions conflict with `docs/PRD.md`'s Out-of-Scope list (§5.2).** Do not build the out-of-scope feature "just in case." Report the conflict.
- **A command from `docs/TECH_STACK.md` fails for environment reasons** (missing binary, permission error, network failure) rather than a code/test failure. Do not silently swap in a different command.
- **A Phase Gate fails and cannot be fixed within the two-attempt limit above.** Do not proceed into the next phase with a red gate, in either mode.
- **You are about to modify `docs/PRD.md`, `docs/DESIGN.md`, or `docs/TECH_STACK.md` themselves** to make a task easier. These files are the spec, not implementation detail — changing them is a human decision, not something to do mid-task to unblock yourself.
- **Live testing or smoke testing requires credentials** — e.g. before hitting real APIs like Gemini or Qdrant for smoke/integration testing (like in the Phase 5 Gate, Phase 10, or Phase 11). Stop and explicitly ask the operator to provide the required real credentials (and instructions on how to generate them, if needed) in the `.env` file before executing the tests.

When you halt, state: which task you were on, exactly what you tried, the exact command output that failed, and what specific decision or information you need from the operator to proceed.