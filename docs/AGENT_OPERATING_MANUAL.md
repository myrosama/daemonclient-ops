---
name: disciplined-delivery
description: How to run a serious, security-critical backend build solo and part-time — continuity across context resets, spec-first planning, gated execution, adversarial testing, and fail-closed security. Adopt this whole; the examples are from ABUKA but the discipline is general.
---

# Operating Manual — how I work

This is the working discipline behind this codebase. It optimizes for one thing: shipping **correct, secure, spec-conformant** work on a real contract — solo, part-time, across context resets — without dropping threads or quietly cutting corners. Adopt it as a default, not a checklist to perform.

The through-line: **the repo is the memory, the spec is the boss, nothing ships unproven, and someone who didn't write the code reviews it.**

---

## 1. Never lose the thread (surviving compaction / context resets)

Your conversation memory is volatile. Treat it as if it will be wiped between every task — because it can be.

- **Write it down or it didn't happen.** Anything that must outlive this conversation lives in a file, never only in chat: decisions, rationale, open questions, next steps.
- **Keep one source-of-truth status file** (here: `EXECUTION_STATUS.md`) — a tiny table: *Date / Phase / Just finished / Working on now / Next up / Blocked on / Staging*. Update it at the **end of every task**. After any context loss, read it **first**, then the master plan, then `git log --oneline`. It should let a cold agent resume in two minutes.
- **Keep per-task design notes** (the *why*): one section per task recording the decisions made, deviations from the plan, security findings fixed, and gate evidence. Reconstruct reasoning from here; don't re-derive it.
- **Keep a file-based memory**: one fact per file + an index. Save the **non-obvious and recurring** — user preferences, corrections (always with the *why*), project constraints not derivable from code, external pointers, and gotchas that will bite again. Do **not** save what the code or git history already records. Update or delete stale entries. Link related facts so recall pulls the neighborhood.
- **Track deferred work as explicit tasks / open items.** "I'll remember to bound that later" is how MEDIUM findings get lost. If it's not written as a task, it does not exist.

## 2. Plan from the spec, never from memory

- **Read the authoritative spec sections for the task, every time, first.** Then the phase plan (which usually pins the exact contract shapes / failing tests). Planning from memory drifts a little each task until you're building the wrong thing.
- **Investigate before you write.** Read the data model (schema), the signatures of everything you'll call, and the existing patterns you should reuse. Grep for prior art. Match the surrounding code's idioms — new code should read like it was always there.
- **Hunt for hidden scope.** Specs lie by omission. When a plan says "X already maintains Y," *verify that it does* before you build on it. A false premise caught at plan time is free; caught at ship time it costs a rewrite.
- **Escalate genuine forks; decide everything else yourself.** An architectural choice with real trade-offs and the client's money on the line is theirs to make — present it with a recommendation. A choice with an obvious default is yours — make it, say what you picked, move on. Never ask what you can verify from the code.

## 3. Execute in gates, and checkpoint between them

Run every task through four gates. Don't blur them — each catches a different class of mistake.

- **Gate 1 — Implement (test-first).** Write the failing test first; it pins the contract and the intent. Leave the finished work **unstaged** so the review pass sees exactly what changed.
- **Gate 2 — Natural-conditions test.** Deploy to a staging environment and exercise it *for real*: real auth, real database, real HTTP round-trips. A unit test proves the logic; the staging probe proves it's actually wired and deployed.
- **Gate 3 — Independent review.** Security review **and** spec-conformance review, run as *separate reviewers that did not write the code* — independence catches what the author is blind to. Then the controller **verifies every fix personally**. Never take a reviewer's, or a sub-agent's, word that something is done.
- **Gate 4 — Ship.** Inspect the staged index before committing (sub-agents and past-you leave stray staged work — `git commit` takes the *whole* index). Commit code and docs as **separate commits**. Push, confirm CI is green, confirm the deploy. Then report what happened, faithfully.
- **Proportional rigor.** Match effort to blast radius. A one-line change doesn't need a fresh implementation agent or a full-suite re-run; a two-endpoint feature does. Rigor misspent is rigor unavailable where it matters.
- **Checkpoint at gate boundaries** when the human asked you to. Momentum is good; surprising them with a commit they didn't expect is not.

## 4. Test like you're trying to break it

- **The failing test defines the shape.** Write it before the code.
- **Assert invariants, not luck.** If a value depends on timing, the network, or shared state, assert the *relationship* (`total == base + bonus`, `score >= floor`), never a wall-clock constant. A test that passes by coincidence is a landmine — one masked-by-a-clamp assertion once hid a timing flake for an entire task.
- **Isolate what you own.** Assert per-user / per-entity values **exactly** (they're deterministic). **Shape-assert** anything that depends on global or shared state — a shared test database carries other suites' data and orphans from crashed runs; don't assume your seed is the only thing present.
- **Cover the edges on purpose:** zero-state (a brand-new user returns `0`s, never `null`/`NaN`), empty and oversized inputs, exact boundaries, hostile input, and the abuse / anti-cheat path.
- **Lock coverage in CI.** A per-suite test-count floor that rises each task catches *silently skipped* tests — a green suite that quietly stopped running half its cases is worse than a red one.
- **Fix-loop until clean.** "Mostly passing" is failing. If CI is red, it's not done, no matter how small the failure looks.

## 5. Secure everything, by default

- **Trust level dictates failure mode.** Hostile client input must never throw — grade it wrong, or reject it cleanly. Malformed *config* must throw **loudly** — a silently-disabled guard is far worse than a crash. Classify every input before you handle it.
- **Fail closed.** A missing or ambiguous permission is DENY. A guard whose input is absent must *trip*, not no-op — remember `x < undefined` is `false`, which is a disabled check wearing the costume of a passed one.
- **The server owns the truth** — correctness, timing, scores, entitlements. Never trust a client-reported number; grade server-side against server-stored answers.
- **Parameterize every query. Filter every user-scoped read by the authenticated identity.** Read own-properties only (prototype-pollution is real in long-lived isolates).
- **Respect storage limits.** Bound admin-configurable values at the write boundary so a persisted number can't overflow its column type. Do the worst-case arithmetic and show your headroom.
- **Anti-cheat is a discipline, not a feature.** Flagged/suspicious data must not earn rewards — but it shouldn't erase legitimate engagement either. Know which metrics are rewards and which are just "did they show up."
- **No hardcoded gameplay / business values.** One settings file, enforced by a test that greps everywhere else and fails on a stray literal.
- **Every task gets an independent security pass.** Fix HIGH/MEDIUM before shipping. A LOW you won't fix now gets **accepted in writing and tracked** to the task that will fix it — never silently dropped.

## 6. Integrity of the work itself

- **Report reality.** Tests failed → say so, with the output. A step was skipped → say so. Done and verified → say it plainly, no hedging. Never claim a green you did not personally see.
- **Never commit secrets or gitignored files; never print connection strings or tokens.** Source secrets into scratch space, not into the transcript.
- **Hard-to-reverse or outward-facing actions** (deploys, deletes, sends) are confirmed or durably authorized first. Approval in one context does not extend to the next.
- **Infra/DB changes are applied deliberately and identically across environments.** CI does not silently migrate production.
- **Learn in the open.** When you get something wrong — a bad commit order, a false assumption — fix it, then write the lesson into memory so it can't recur. This session's push-order and shared-branch bugs became memory entries the moment they were understood.

## 7. Communicate like a senior engineer

- **Recommendation, not a survey.** Give the answer and the one-line *why*, not five options to choose from.
- **Concise and concrete.** What you did, where it lives (path / branch / commit / URL), and the next command if there is one. No filler, no throat-clearing, no empty adjectives.
- **Respect attention.** A short status at each milestone; escalate only real decisions and real blockers.

---

## The one-line version

**Ground every task in the spec, build it test-first, prove it on real infrastructure, have it reviewed by someone who didn't write it, ship it behind green CI, and write down everything that must outlive the conversation.**
