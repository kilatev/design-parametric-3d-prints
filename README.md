# design-parametric-3d-prints

Design and revise functional, parameterized parts for FDM 3D printing, including organizers, holders, mounts, adapters, spacers, enclosures, cable routes, and multi-block assemblies. Use when the agent must first turn dimensional requirements or reference images into an approved three-view SVG plus an editable 1:1 DXF, then create editable FreeCAD-compatible geometry, named STEP components, print-ready STL, and final model-derived drawings; especially when fit clearances, Placement/Move assembly, support-free printing, overhang removal, bed contact, or iterative CAD revision must be verified.

See [SKILL.md](SKILL.md) for the full workflow, or the rendered [plain-language overview](https://kilatev.github.io/design-parametric-3d-prints/overview/overview.en.html) aimed at someone deciding whether to use this skill (also available in Russian, Latvian, German, and French via the language links on that page).

## Quick-start: prompt instead of skill (recommended)

Loading this as an installed skill costs context on every turn (description
match) and, once triggered, can anchor the model on its literal step order
even for tasks that don't need the full ritual. For a quick or repeat job,
skip installing the skill and instead paste
[plan/skill-as-prompt.md](plan/skill-as-prompt.md)'s content directly as your
prompt — it's the same workflow compressed to ~20 lines, with the agent
asking you for this repo's path up front instead of assuming one.

Trade-off: the short-prompt form omits the `references/`/`assets/` links and
the full validator/rule detail below. Fall back to installing the skill
(SKILL.md) for first-time use, complex multi-block assemblies, or whenever a
validator gate or edge-case rule needs the full explanation.

## Install (recommended)

Using the [`skills`](https://www.npmjs.com/package/skills) CLI, one line, no manual steps — it detects installed agents (Claude Code, Codex CLI, pi agent harness, etc.) and installs to all of them:

```sh
npx skills@latest add kilatev/design-parametric-3d-prints -a '*' -y
```

- Drop `-a '*'` to be prompted which detected agent(s) to install to instead.
- Add `-g` to install user-level (available in every project) instead of project-level.
- `npx skills@latest update design-parametric-3d-prints` later to pull updates.

## Install (manual)

If you'd rather not use an npm-based installer, `git clone` this repo directly into the target skills directory for your tool, then restart it or start a new session:

| Tool | Target directory |
| --- | --- |
| Claude Code (personal) | `~/.claude/skills/design-parametric-3d-prints` |
| Claude Code (project) | `<project>/.claude/skills/design-parametric-3d-prints` |
| Codex CLI | `$CODEX_HOME/skills/design-parametric-3d-prints` (default `~/.codex/skills`) |
| pi agent harness | `~/.pi/agent/skills/design-parametric-3d-prints` |

## Install (ChatGPT)

ChatGPT doesn't use the `skills` CLI or a filesystem clone — it's a separate upload flow: `git clone` this repo, zip the folder (the skill folder itself must be the zip's root, not its contents flattened), then in ChatGPT go to Plugins → Skills tab → Create → Upload from your computer. See [OpenAI's Skills in ChatGPT article](https://help.openai.com/en/articles/20001066-skills-in-chatgpt) for current availability/tier requirements — these have changed over time, so treat that article as authoritative rather than any fixed claim here.

## Requirements

- Python 3 (stdlib only) to run `scripts/*.py` — no `pip install` needed.
- Optional, for native 3D generation: `FreeCADCmd` / FreeCAD Python. Without it, generate BREP/STEP via any OpenCascade-compatible kernel and hand back a FreeCAD macro that rebuilds the same named blocks (see [assets/freecad-parametric-template.FCMacro](assets/freecad-parametric-template.FCMacro)).
- Optional, for the PNG live-preview workflow: ImageMagick's `convert` (SVG → PNG) and `openscad` (STL → PNG). Neither is required — only used if present.

## License

MIT — see [LICENSE](LICENSE).

## Also in this repo

`plan/*.html` are deferred design notes from earlier development — background on ideas considered and postponed, not required reading to use the skill.
