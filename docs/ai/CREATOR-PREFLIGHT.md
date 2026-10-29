# Creator preflight: recover context, improve the brief, agree on production

This is the **one pre-production gate** shared by every Visual Atlas recipe. The creator can describe a goal in ordinary language; they do not need to know art-pipeline or game-engine terminology. The AI performs the research, turns the request into an executable specification, offers improvements, and confirms important decisions **before expensive production**. Read the task-specific recipe only after identifying the deliverable.

## 4D working-brief reconstruction

1. **Diligence — find the actual intent.** Read the *current request and current conversation first*. Inspect attached images/source files, supplied URLs, the relevant repository and existing templates/manifests, then **relevant** prior project discussions or connected documents *if accessible and authorized*. For an external game, inspect its actual sprite/import/animation constraints. Do not browse irrelevant private files or pretend unavailable history was inspected.
2. **Description — reconstruct the user's message.** Retain the user's original wording and a concise **reconstructed AI-fluent brief** (goal, audience/gameplay, character identity, references, style, supported behavior, technical contracts, deliverables, acceptance evidence). Treat the faithful reconstruction as the operative task instruction for planning; the verbatim request remains the source of truth. Explicit constraints win over guesses or generic recipes.
3. **Delegation — decide how to produce it.** Select an existing Visual Atlas recipe, authoritative examples and validators. Delegate image generation to source-art tasks; use deterministic image tools for measured regions, pivots, alpha, frame timing and packaging. Use browser rendering for actual behavior. Do not duplicate manifests or invent unsupported builder features.
4. **Discernment — challenge assumptions.** Separate **confirmed facts**, **verified project requirements**, **inferred preferences**, **proposed enhancements**, and **unresolved blockers**. Test whether the original scope is sufficient and whether a simpler compatible deliverable would be better. Do not silently upgrade a user's request into new mandatory features.

## Preflight evidence and questions

Produce a short brief with:

- **Identity & intent:** subject, visual reference hierarchy, personality/expressions, player role, game genre and required actions.
- **Target contract:** engine/renderer if known, perspective (isometric/oblique/orthographic), direction naming and handedness, logical sprite dimensions and target on-screen scale, FPS or timed holds, transparency, pivot/feet baseline, camera/light/palette, file and license requirements.
- **Modularity & integration:** does the existing game use separate clothing/hair/equipment/skeleton layers, attachment anchors, palette swaps, hitboxes, state-machine names, atlas templates or custom import metadata? Inspect real project contracts before deciding. **Never presume layered apparel is required or unsupported.**
- **Coverage:** required states/directions, planned frame counts (variable by action), one-shots versus looping states, transition requirements, and the minimal approved prototype.
- **Evidence:** list actual source files, repository docs, selected templates, and any discovered compatibility limits, with versions/paths. Note what was unavailable.
- **Risk:** missing input that would cause rework, art style or rights issues, uncertain camera geometry, and feasibility.

**Ask specific questions only when the answer can materially change the asset architecture or create expensive rework.** Group a few independent blockers in one short message. For nonblocking details, propose a clear default with a reason. If the project already answers a question, do not ask it again. Never invent unknown game mechanics, project history, or author approval.

## The approval gate (before asset generation)

For a multi-frame character/game pack or other costly multi-asset commission:

1. Present the reconstructed brief, grounded decisions, two viable production approaches and a reasoned recommendation.
2. Present suggested enhancements as **optional proposals**, separately from the user's actual requests. The creator can accept, decline or edit them.
3. State the exact first *qualification slice* (e.g., one facing + one complete loop), intended output/QA, then the estimated remaining expansion. Do not generate hundreds of assets to qualify a technique.
4. Ask for **approval of the blueprint** or the genuinely blocking choice **before starting production**. A direct instruction to proceed after a plan is established counts as approval; don't repeatedly seek it. Small reversible exploratory drafts don't require a formal approval stage.
5. Freeze the approved contract. Record changes with reason and obtain renewed approval only for material scope, style, licensing, or compatibility changes. No background production claims.

**Production cannot start when an unresolved choice affects engine integration, intended layer ownership, or core perspective.** If the user deliberately delegates those choices, state the default and why.

## Example: sparse creator request

> "Study this link and make a full animation set for the character in my game. I attached the reference."

Reconstruct: "Produce an engine-compatible, directionally consistent character animation pack using the attached character reference, appropriate for the identified game." **Then research** whether the link defines perspective, pixel scale, layering, state names or skeleton and whether relevant prior discussions establish the character's design. If not known, ask for the *minimum architecture-changing* detail such as required engine/animation layering, then present a direction/state matrix and sample approval plan. Do **not** fabricate walk/run/hurt states, a specific engine, or clothes-layer compatibility as confirmed requirements.

## Learn from each accepted/rejected production pass

For each revision record **observation → root cause → change → regression gate → evidence**. Capture changes in this recipe or the relevant task guide, *not* a parallel checklist with a second authority. After approving the first full character, evaluate a **different held-out character** with this frozen procedure: record prompts/inputs, retries, spend, acceptance failures and interventions. Judge first-pass results before tuning; otherwise the "one-shot" claim is meaningless.
