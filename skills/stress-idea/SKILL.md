---
name: stress-idea
description: stress the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any adversarial interviewer phrases.
---

Interview the user with `AskUserQuestion` until you share a full understanding. Model the design as a **tree**: each decision branches into the ones that depend on it.

Work in **rounds**. The **frontier** = every decision whose prerequisites are settled — the questions askable *now* without guessing. Ask the whole frontier in one round: number each question and give your recommended answer, then wait. A question depending on one still open belongs to a *later* round.

Each round's answers settle decisions and push the frontier outward. Recompute it, ask again.

**Facts are your job, decisions are the user's.** When a frontier question needs a fact from the environment (filesystem, tools), dispatch a sub-agent — never ask the user something you can look up. Don't block: a running lookup is an unsettled prerequisite, so only questions downstream of it wait; ask the rest of the frontier now.

Done when the frontier is empty: every branch visited, nothing silently assumed. Do not act until the user confirms the shared understanding.
