---
name: kb-init
description: "Build or refresh the project's knowledge base in fondue/kb/: an index of every module and project skill, and one card per module saying what it offers, where a new thing plugs in, and what not to rebuild. spec and hunt roles read it before they design, and keep it current. Use when the User asks to initialize, build, rebuild or refresh the knowledge base, or to map the codebase for fondue."
license: MIT
metadata:
  owner: "Jakub Sobolewski"
  version: 1
  status: "young - run on one Java project so far; update in place as runs teach us"
---

# kb-init - map the codebase once, cheaply

The knowledge base is defined in `protocol/kb.md` at the plugin root, `../../protocol/kb.md` from this skill's directory. Read it first. This skill is the run that creates it, or rebuilds it after the code drifted away from it. `kb.py` below means `python3 <plugin root>/protocol/kb/kb.py`, run from the project root.

The User runs this in their own session. It is not a spec: no roles, no review. The User is the reviewer.

## The run
1. **Modules.** Run `kb.py modules`. If it finds none, stop and tell the User that `kb.py` reads Maven and Gradle projects with sources under `<module>/src/main`, and that this project's layout is not supported yet. Show the User the module list when it looks wrong: too few, or a module that is really two. A module that is really two can keep its build and still get two cards: lines in `fondue/kb/parts.txt` (protocol/kb.md) give its packages cards of their own. The User picks the parts.
2. **What is already there.** If `fondue/kb/cards/` exists, this is a refresh. `kb.py status` shows how far each card has drifted. Offer `kb.py write --since <the oldest verified-at>` for the drifted modules, or `--all` to rebuild every card. A card that exists goes into its rewrite, so a rebuild changes only what the code changed.
3. **The cost, before spending it.** Run `kb.py estimate` for what step 4 will write: no argument for `--all`, the same `--since <sha>` for a refresh. Tell the User the figure and the model (`sonnet` unless they name one), and wait for their go. Why: cost is the User's call, and this is the one step that spends tokens.
4. **Write.** Note the time as `date +%Y-%m-%dT%H:%M:%S` prints it. Run `kb.py write --all`, or the refresh from step 2, with `--model` if the User named one. It packs each module, makes one tool-less call per card, six at a time, and writes `index.md`. A run of 30-40 modules takes a few minutes, so give the command a long timeout. A card that fails is named at the end. Run `kb.py write <those ids>` once more.
5. **Check.** Run `kb.py status` until it reads `clean`.
   - A dead name means the writer quoted a name the code does not have. Fix it in the card by hand: drop the backticks if it is a library type, or correct the name.
   - A card over the limit belongs to a module that does too much for one card. Tell the User. Splitting it, the module or only its card through `parts.txt`, is their call.
6. **Report.**
   - Give the User the real cost: `kb.py usage --since <the time from step 4>`.
   - Ask them to check the extension points of two or three cards for modules they know well. Those are the entries most likely to be incomplete, and the ones a wrong card costs most on.
   - Offer one line in the project's `CLAUDE.md`, so sessions outside fondue use the knowledge base too: `Before designing a change, read fondue/kb/index.md and the cards it points to.`
7. **Commit only when the User asks:** `git add fondue/kb`, on its own. The `.gitignore` that `write` created keeps `.packs/` and `.runs/` out.

## What this skill does not do
- **Write or change project skills.** A card points to the skills that cover its module, and `index.md` lists them all, but what a skill says is the User's to change.
- **Read code itself.** Every card comes from the packed input, so the run costs one call per card and nothing more. Opening files to "improve" a card turns the run into the agent loop the tool exists to avoid.
