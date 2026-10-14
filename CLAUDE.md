# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repository is

A Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) publishing one plugin, `visioone` (`plugins/visioone/`), with two skills: `integrate-visioone-sdk` and `migrate-to-visioone`. This repository is meant to be **public**.

## Rules

- **Content sources.** Only already-public material is allowed:
  - the official VisioOne documentation published on my.visioglobe.com, including the public migration guide;
  - the TypeScript declarations of the published `@visioglobe/visioone` npm package;
  - the public sample repositories `visioglobe-sas/VisioOneMeet*` (Android, iOS, Flutter, React Native, Vue).

  Never copy internal material: client names, private repository URLs, internal tickets, internal analyses.
- **Language.** English only. Temporary exception: the `note` fields of `migration-map.json` are in French until the English migration guide is published.
- **Versions.** The plugin follows its own semver (`plugin.json` and `marketplace.json` must stay in sync). The targeted `@visioglobe/visioone` version is stated in each skill and in the README; when it changes, update every "Known pitfalls" note against the new changelog and type declarations.
- **No invented APIs.** Every VisioOne symbol cited in a skill must exist in the TypeScript declarations of the targeted version.
- **`references/migration-map.json` is generated** from the public guide's API correspondence appendix, never edited by hand.

## Checks

```
claude plugin validate . --strict
claude plugin validate plugins/visioone --strict
```

Regenerate the migration map after any change to the guide's API correspondence appendix (fails if a cited VisioOne symbol is not declared in the package):

```
python3 -I scripts/build_migration_map.py <correspondance-api.md> <node_modules/@visioglobe/visioone> plugins/visioone/skills/migrate-to-visioone/references/migration-map.json
```

The recipes in `integrate-visioone-sdk/references/api-recipes.md` end with a verification block listing every cited symbol and its declaration file: update it with the recipes.
