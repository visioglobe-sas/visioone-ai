---
name: migrate-to-visioone
description: Migrates an existing app from a legacy Visioglobe SDK (VisioWeb, VisioWeb Essential, VisioMove Essential iOS/Android V2) to the VisioOne SDK. Use when the user asks to migrate, port, upgrade or move a Visioglobe map integration to VisioOne, or when a project uses visioweb, VisioWebEssential or VMEMapController and the user wants VisioOne.
---

# Migrating to VisioOne

> **Preview (v0.1).** The mapping notes in `references/migration-map.json` are still in French, the language of the migration guide until its English version is published. Translate them for the user when you quote them.

This skill targets **`@visioglobe/visioone` 1.1.0**. It covers VisioWeb, VisioWeb Essential and VisioMove Essential **V2** (`VMEMapController`). VisioMove Essential 1.x (`VMEMapView`) is out of scope: say so if you find it.

## Sources (use only these)

- `references/migration-map.json`: 620 entries, one per public API element of the legacy SDKs (`sdk`: `visioweb`, `visioweb-essential`, `visiomove-essential-v2`), with its VisioOne equivalent (established on 1.0.9 by the guide, every cited symbol re-checked against the 1.1.0 declarations) (`visioone`, `null` when there is none), a `status`, a `note` explaining the mapping and `guide`, the migration guide sections that detail it. Statuses:
  - `direct`: same role, simple rename;
  - `different`: covered by an API of a different shape (other carrier object, other signature, promise or exception instead of a callback…);
  - `workaround`: no dedicated API, but the need can be rebuilt with the public API (the note says how);
  - `none`: no equivalent in VisioOne's public API;
  - `not-applicable`: legacy-only notion that no longer applies (lifecycle handled differently, internal mechanism…).

  The file is large: search it (e.g. with `grep` or `jq` on `legacy`) instead of reading it whole.
- The VisioOne migration guide in the official documentation: https://my.visioglobe.com/docs/VisioOne/docs/index.html
- `../integrate-visioone-sdk/references/api-recipes.md` (how to write each VisioOne feature correctly) and `../integrate-visioone-sdk/references/mobile-webview.md` (WebView shell and native↔JS bridge for mobile V2 apps).
- The public example integration repos listed in `../integrate-visioone-sdk/SKILL.md` (Vue 3 for web apps; Android and iOS for VisioMove Essential V2 apps), to see the target VisioOne app end to end. They are VisioOne apps, not migrations: use them for structure and patterns, never as a source of legacy→VisioOne mappings.
- The TypeScript declarations of the installed `@visioglobe/visioone` package. They are the authoritative API surface: never write a VisioOne call that is not declared there.

Never use a mapping that is not in `migration-map.json` or the guide. If a legacy call has no entry, treat it as `none`.

## Steps

1. **Detect the legacy SDK**
   - VisioWeb: `new visioweb.Mapviewer()`, `mapviewer.initialize(...)`.
   - VisioWeb Essential: `new VisioWebEssential(...)`, `setParameters(...)`, `createMapviewer()`, `essential.route`.
   - VisioMove Essential V2: `VMEMapControllerBuilder`, `VMEMapController`, `loadMapData()` / `loadMapView()`.
   - VisioMove Essential 1.x (`VMEMapView`): out of scope, stop and say so.

2. **Inventory the usages**: list every legacy symbol used, with file and line, and attach each one to its entry in `migration-map.json`. Group them by use case: bootstrap, POI search, POI popup, routing/accessibility/turn-by-turn, multi-building, floor selector, events, language, POI creation.

3. **Propose a migration plan, by use case**, and wait for the user's approval before changing any file. The plan states:
   - what migrates directly (`direct`);
   - what needs rework (`different`, `workaround`) and how;
   - what VisioOne does not provide (`none`), with the linked guide section. Examples: automatic re-routing on deviation, fine-grained offline cache, POI clustering, the "closest" multi-destination strategy;
   - for mobile V2 apps: the target is **not a line-by-line translation**. VisioOne has no native SDK: the app embeds VisioOne in a WebView and talks to it through a native↔JS bridge (`mobile-webview.md`). Plan the shell and the bridge first, then each use case.

4. **Migrate in batches**, one use case at a time, using only the mappings from step 2. Leave business logic untouched.
   - Code that becomes useless (`not-applicable`) is removed, and the summary says so.
   - For every `none` symbol, and every `workaround` you could not implement safely, leave a comment instead of inventing code:
     `// TODO Migration: no VisioOne equivalent for <legacy symbol> — see <guide section>`
   - Apply the 1.0.6+ rules: the map identifier is `vg_maphash` (no `hash` alias); call `venue.refreshCustomData()` before reading custom data; positions are WGS84 `{ latitude, longitude }`.

5. **Validate** with the guide's validation checklist: the project builds, the map loads on the user's real map (`createView()` included), and every `TODO Migration` is listed in the summary.

6. **Summarize**: what was migrated, the remaining `TODO Migration` items with their guide links, and the tests the user must run on their real map.

## Guardrails

- Never change files before the user has approved the plan (step 3).
- Never invent a VisioOne API. Check every call against the installed declarations.
- Never remove legacy code that has no migrated equivalent: comment it with a `TODO Migration` instead.
