# InstaReaper Finish Design

Date: 2026-06-06

## Objective

Finish the checked-in InstaReaper repository into a runnable, source-controlled project that can be completed autonomously in small, verified increments. The repository currently contains substantial functionality and documentation, but it is missing key runtime pieces and includes placeholder behavior that prevents it from being considered complete.

This design defines:

- what "finished" means for this repository
- how the recovery and completion work should be decomposed
- how an hourly automation should select, implement, verify, and commit tasks
- which planning artifacts the automation will use and update

## Current State Summary

The repository contains:

- a PyQt desktop GUI shell
- Reddit scraping logic
- video validation and thumbnail generation
- Instagram posting logic
- scheduler logic
- packaging and installer scripts
- several summary and documentation files

The repository is not currently complete as checked in. The most important confirmed issues are:

- required runtime module `data.database` is missing from source control
- the app cannot boot from source because imports fail without that module
- some GUI behavior is still explicitly marked as future-phase or coming soon
- scheduler logic still includes placeholder behavior for important state
- several docs overstate completion and do not match the checked-in code
- referenced files such as scheduler test utilities are missing

## Definition of Done

The project is considered finished when all of the following are true:

1. The application boots from source without missing-module errors.
2. The missing persistence layer is reconstructed and integrated.
3. The scraper, GUI, and Instagram posting flows are runnable from source.
4. The scheduler no longer relies on placeholder logic for critical behavior.
5. Core runtime state is persisted consistently enough for the documented flows.
6. Task-focused tests and smoke checks pass for each recovered subsystem.
7. Build and usage documentation reflects the actual source state.
8. Work is committed incrementally in green, reviewable steps.
9. No pushes are made automatically.

## Recommended Completion Approach

Three approaches were considered:

### Approach A: Single Hourly Finisher Automation

One cron automation runs every hour, inspects the repository planning artifacts, picks the next unfinished task, implements it, runs verification, and commits only if the task is green.

Pros:

- simplest operating model
- closest match to the requested workflow
- easy to audit through commits and plan updates

Cons:

- requires a careful task ledger and bounded task sizing
- a bad task definition can waste a run

### Approach B: Phase-Based Automations

Separate automations handle reconstruction, stabilization, and documentation/update phases.

Pros:

- strong control over which type of work runs when
- easier to pause or redirect by phase

Cons:

- more moving pieces
- more bookkeeping
- higher chance of plan drift

### Approach C: Thread Wake-Up Workflow

Use a recurring heartbeat on the thread and continue interactively each hour.

Pros:

- strong human visibility
- easy mid-course correction

Cons:

- not truly autonomous
- depends on continued conversational context instead of a stable task ledger

### Recommendation

Use Approach A: a single hourly finisher automation backed by a design doc, an implementation plan, and a machine-friendly task ledger.

## Delivery Strategy

The project should be recovered and finished in small, commit-sized tasks. Each hourly run should complete at most one task. The early tasks should focus on restoring the minimum runnable core before trying to extend or polish behavior.

The likely task groups are:

1. Reconstruct missing persistence/runtime infrastructure.
2. Restore source-level application boot.
3. Make scraper and database integration runnable.
4. Make GUI loading and state updates consistent with persisted data.
5. Repair scheduler state and posting persistence behavior.
6. Reconcile documentation and build paths with reality.
7. Add regression tests and smoke checks for recovered functionality.

## Automation Execution Model

The automation acts like a cautious release engineer. Each hourly run must:

1. Read the design, plan, and task ledger.
2. Select the next task whose status is `pending` and whose dependencies are satisfied.
3. Confirm there is no unrelated dirty working-tree state that would make the task unsafe.
4. Implement only that task's scoped work.
5. Run the task's required verification commands and any obvious targeted checks.
6. Commit only if verification passes.
7. Update the plan/ledger to reflect the completed task.
8. Stop after one successful task.

The automation must not:

- push commits
- silently start a second task in the same run
- commit red or partially verified work
- overwrite unrelated user changes
- wander outside the current task's scope

## Task Outcomes

Every task run should end in one of these states:

- `completed`: implementation finished, verification passed, commit created
- `blocked`: cannot proceed because of a real blocker or repeated failure
- `deferred`: task depends on unfinished prerequisite work and should wait

To avoid loops, if the same task hits the same blocker repeatedly across multiple runs, the automation should mark it blocked and record the reason instead of retrying forever.

## Planning Artifacts

The automation will rely on three repository files:

1. `docs/superpowers/specs/2026-06-06-instareaper-finish-design.md`
2. `docs/superpowers/plans/2026-06-06-instareaper-finish-plan.md`
3. `docs/superpowers/plans/2026-06-06-instareaper-task-ledger.md`

The design doc explains the system.

The implementation plan contains the ordered, human-readable work breakdown.

The task ledger is the machine-friendly record the automation reads and updates on each run.

## Task Ledger Shape

Each ledger entry should include:

- task id
- title
- status
- dependencies
- verification commands
- expected commit message
- notes from the latest run

Statuses should be limited to:

- `pending`
- `in_progress`
- `completed`
- `blocked`
- `deferred`

This keeps the automation state model simple and deterministic.

## Verification and Commit Policy

Each task must declare the command(s) required to prove it is green. Verification may include:

- targeted `py_compile`
- focused module import checks
- script execution smoke tests
- task-specific behavioral checks

A task may be committed only if:

- the intended code changes are present
- its required verification passes
- no known failing check for that task remains unresolved

Each successful run should produce exactly one commit tied to the completed task.

## Safety Rules

The automation should always:

- inspect `git status` before modifying files
- preserve unrelated user changes
- prefer small tasks over broad refactors
- stop when a task expands beyond its declared scope

The automation should never:

- push
- rewrite history
- auto-resolve ambiguous product decisions by inventing new features

## Risks and Mitigations

### Risk: Missing original local-only files

Mitigation:

- reconstruct behavior from current module interfaces and docs
- prioritize re-establishing the persistence layer and boot path first

### Risk: Documentation and code disagree

Mitigation:

- treat code plus runtime verification as source of truth
- update docs only after actual behavior is restored

### Risk: Tasks become too large for one run

Mitigation:

- decompose tasks aggressively
- enforce one green commit per run

### Risk: Infinite retries on the same blocker

Mitigation:

- record blocker notes in the ledger
- mark repeated blockers explicitly

## Success Criteria for the Automation System

The finishing system itself is successful when:

- it can autonomously pick the next valid task
- each run stays bounded to one task
- each successful run ends in a green commit
- the ledger remains up to date
- no pushes occur automatically

## Immediate Next Step

Write the implementation plan and task ledger, then create an hourly cron automation that follows them exactly: pick the next task, implement it, verify it, commit if green, and stop.
