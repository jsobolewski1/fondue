# Integrations - the agent contract and first-run setup

Read by the Arbiter of any fondue skill that seats roles (spec, hunt), at `start` and whenever the roster names an agent. Roles never read it.

A role runs on Claude, through the Agent tool (see the engine's `Starting a role`, `protocol/engine.md`), or on any other agent the User has registered. The engine needs the same few things from every agent. How one agent does them is written in its **adapter**: one file per agent, following the contract below.

## Where adapters live
```
~/.config/fondue/integrations/agents/
  <name>.md          one adapter; <name> is how roster.md names the agent
  <script>           any script an adapter names, next to it
```
The folder is per user, not per project, because which agents a person has and how they reach them are facts about their machine. `~/.config` stands for `$XDG_CONFIG_HOME` when that is set. Why not under `~/.claude/`: Claude Code treats that tree as sensitive and refuses or prompts for every file it writes there, so setup could not record what it verified. Claude needs no adapter. If the folder exists, setup has been done, and an empty folder means a Claude-only setup.

The adapters that ship with fondue are the other `.md` files in this folder, `integrations/agents/` at the plugin root. Setup copies one into the User's folder, and the copy is what the Arbiter uses. Why a copy: the User's adapter is verified against the User's installation, and a plugin update must not replace it unverified.

## The contract
An adapter has these sections, in this order. Every claim about how the agent behaves is a RESULT under the engine's Research rule, with the agent version it was verified on. The agent is a mechanism this spec does not control, and its flags change between versions.

1. **Detect** - read-only commands that find the agent and tell whether it can be used: installed where, which version, signed in or not. They spend no tokens.
2. **Start** - the command that starts a new session non-interactively, in the project directory, with the spawn prompt, and never waits on stdin. Where the session handle is printed.
3. **Turn** - the command that sends `Your turn.` to that same session, and how to send a different prompt the same way, for an advisor's follow-up (engine: Advisors).
4. **Reply** - where the role's final message is, as one clean line, or an advisor's whole final message, without banners or traces.
5. **Skills** - how the role gets its skills. The engine's default works for any agent that can read files: the prompt says `Read <skill dir>/SKILL.md and follow it as the <name> skill.` in place of `Load the <name> skill.`
6. **Permissions** - how the role gets what the engine requires of a role: read the project, write the spec folder and the code, run the build, commit. How that is set on Start, and again on every Turn if the setting does not carry over to a continued session. And how to Start a read-only session, for an advisor (engine: Advisors).
7. **Model and effort** - the flags, and how fondue's efforts (`low` … `max`) map to the agent's.
8. **Stats** - the command that prints one turn's tokens and minutes, or `none`. With `none`, the `stats.md` row carries `-` in its Tokens and Time cells, never an estimate.
9. **Verify** - a two-turn check: a first turn, then a continued turn whose answer depends on the first. It shows that Turn continues the session rather than starting a new one.
10. **Gotchas** - anything else that has bitten, as a RESULT.

## Running a role on an adapter
The Arbiter runs Start and Turn with the Bash tool and `run_in_background: true`. A turn runs for minutes, far longer than a foreground command may. The notification that the command finished is the reply. The Arbiter reads the Reply location and handles the line as the engine's `On every reply` says. It records the session handle on the role's `roster.md` line as `| session <handle>`, and runs the adapter's Stats for `stats.md`.

## First-run setup
At `start`, before the roster is fixed, the Arbiter checks for `~/.config/fondue/integrations/agents/`. If it is missing:

1. **Detect.** Run the Detect section of every shipped adapter. Tell the User what was found: the agent, where it lives, its version, and whether it is signed in.
2. **Choose.** Ask the User which of the found agents to register, and whether they use any other agent that has no shipped adapter: one round of questions (engine: Asking the User).
3. **Write.** For a shipped adapter: copy it, with the scripts it names, and re-run each RESULT the installed version may have changed. For any other agent: write the adapter with the User, section by section under the contract, with the shipped adapters as the model.
4. **Verify.** Run each adapter's Verify, and tell the User beforehand that it spends a few tokens on the agent's account. An adapter that fails is not saved. The User hears what failed.
5. **Create the folder**, empty if nothing was registered, so the next `start` does not ask again.

When the folder exists but the roster names an agent with no adapter, the Arbiter runs steps 1-4 for that agent alone. The User can ask for the same at any time to add an agent.
