# VisioOne

Official Visioglobe plugin to integrate the [VisioOne](https://www.npmjs.com/package/@visioglobe/visioone) indoor mapping SDK into your project, and to migrate existing apps from legacy Visioglobe SDKs to VisioOne.

> **Status: preview.** Targets `@visioglobe/visioone` 1.1.0. The migration notes are in French until the English migration guide is published.

## Skills

| Skill | What it does |
|---|---|
| `integrate-visioone-sdk` | Adds VisioOne to a web project: installation, a minimal integration module and a usage example. Covers 3D indoor/outdoor maps, POIs, multimodal routing, theming and localization, and embedding the map in a native app through a WebView (Android, iOS, Flutter, React Native). |
| `migrate-to-visioone` | Migrates a VisioWeb, VisioWeb Essential or VisioMove Essential V2 app to VisioOne. It inventories the legacy calls, maps each one to its VisioOne equivalent using the official migration guide, and proposes a plan for your approval before changing any file. |
| `report-visioone-bug` | Prepares a bug report about the VisioOne SDK, a Visioglobe map or this plugin: checks it is not a misuse, collects the versions, error and a minimal reproduction, and removes tokens and other secrets. You submit the report yourself through [Visioglobe support](https://my.visioglobe.com/support). |

Ask Claude, for example: *"Integrate VisioOne in this project"*, *"Migrate this VisioWeb app to VisioOne"* or *"Report this VisioOne bug to Visioglobe"*.

## What the plugin contains and does

The plugin contains only skills: instructions and reference documents, written from the public VisioOne documentation and the TypeScript declarations of the published npm package. It has no hooks, no MCP server and no scripts. It does not collect or send any data: bug reports are only drafted, and you decide what to submit. When you use a skill, Claude may read and edit files in your project and suggest installing `@visioglobe/visioone` from npm, as with any coding task.

## Install (Claude Code)

```
/plugin marketplace add visioglobe-sas/visioone-ai
/plugin install visioone@visioone-ai
```

## Documentation

- VisioOne documentation: https://my.visioglobe.com/docs/VisioOne/docs/index.html
- API reference: https://my.visioglobe.com/docs/VisioOne/APIdocs/index.html
- Support and bug reports: https://my.visioglobe.com/support (the `report-visioone-bug` skill drafts the report)

## License

This plugin and its skills are licensed under the Apache License 2.0. The VisioOne SDK (`@visioglobe/visioone`) is proprietary software distributed under its own terms.
