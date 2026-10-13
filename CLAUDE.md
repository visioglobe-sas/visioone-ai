# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repository is

A Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) publishing one plugin, `visioone` (`plugins/visioone/`), with two skills: `integrate-visioone-sdk` and `migrate-to-visioone`. This repository is meant to be **public**.

## Rules

- **Content sources.** Everything in this repository must come from the public VisioOne documentation, including the public migration guide. Never copy internal material: client names, private repository URLs, internal tickets, internal analyses.
- **Language.** English only.
- **Versions.** The plugin follows its own semver (`plugin.json` and `marketplace.json` must stay in sync). The targeted `@visioglobe/visioone` version is stated in each skill and in the README; when it changes, update every "Known pitfalls" note against the new changelog and type declarations.
- **No invented APIs.** Every VisioOne symbol cited in a skill must exist in the TypeScript declarations of the targeted version.
- **`references/migration-map.json` is generated** from the public guide's API correspondence appendix, never edited by hand.

## Checks

```
claude plugin validate . --strict
claude plugin validate plugins/visioone --strict
```
