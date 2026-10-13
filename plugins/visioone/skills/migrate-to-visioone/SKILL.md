---
name: migrate-to-visioone
description: Migrates an existing app from a legacy Visioglobe SDK (VisioWeb, VisioWeb Essential, VisioMove Essential iOS/Android V2) to the VisioOne SDK. Use when the user asks to migrate, port, upgrade or move a Visioglobe map integration to VisioOne, or when a project uses visioweb, VisioWebEssential or VMEMapController and the user wants VisioOne.
---

# Migrating to VisioOne

> **Draft (v0.1).** This skill depends on `references/migration-map.json`, which is not shipped yet. Until it is, run steps 1 to 3 only (detection, inventory, migration plan), then stop and tell the user that automated code changes are not available in this version.

This skill targets **`@visioglobe/visioone` 1.0.9**. It covers VisioWeb, VisioWeb Essential and VisioMove Essential **V2** (`VMEMapController`). VisioMove Essential 1.x (`VMEMapView`) is out of scope: say so if you find it.

## Sources (use only these)

- `references/migration-map.json`: one entry per legacy API symbol, with its VisioOne equivalent, a status (`direct`, `partial`, `absent`, `integrator`), the minimum VisioOne version and a link to the migration guide section that justifies it.
- The VisioOne migration guide in the official documentation: https://my.visioglobe.com/docs/VisioOne/docs/index.html
- The TypeScript declarations of the installed `@visioglobe/visioone` package. They are the authoritative API surface: never write a VisioOne call that is not declared there.

Never use a mapping that is not in `migration-map.json` or the guide. If a legacy call has no entry, treat it as `absent`.

## Steps

1. **Detect the legacy SDK**
   - VisioWeb: `new visioweb.Mapviewer()`, `mapviewer.initialize(...)`.
   - VisioWeb Essential: `new VisioWebEssential(...)`, `setParameters(...)`, `createMapviewer()`, `essential.route`.
   - VisioMove Essential V2: `VMEMapControllerBuilder`, `VMEMapController`, `loadMapData()` / `loadMapView()`.
   - VisioMove Essential 1.x (`VMEMapView`): out of scope, stop and say so.

2. **Inventory the usages**: list every legacy symbol used, with file and line, and attach each one to its entry in `migration-map.json`. Group them by use case: bootstrap, POI search, POI popup, routing/accessibility/turn-by-turn, multi-building, floor selector, events, language, POI creation.

3. **Propose a migration plan, by use case**, and wait for the user's approval before changing any file. The plan states:
   - what migrates directly;
   - what needs rework (`partial`) and why;
   - what VisioOne does not provide (`absent`) or leaves to the integrator (`integrator`), with the linked guide section. Examples: automatic re-routing on deviation, fine-grained offline cache, POI clustering, the "closest" multi-destination strategy;
   - for mobile V2 apps: the target is **not a line-by-line translation**. VisioOne has no native SDK: the app embeds VisioOne in a WebView and talks to it through a native↔JS bridge. Plan the shell and the bridge first, then each use case.

4. **Migrate in batches**, one use case at a time, using only the mappings from step 2. Leave business logic untouched.
   - For every `absent` or `partial` symbol, leave a comment instead of inventing code:
     `// TODO Migration: no VisioOne equivalent for <legacy symbol> — see <guide section URL>`
   - Apply the 1.0.6+ rules: the map identifier is `vg_maphash` (no `hash` alias); call `venue.refreshCustomData()` before reading custom data; positions are WGS84 `{ latitude, longitude }`.

5. **Validate** with the guide's validation checklist: the project builds, the map loads on the user's real map (`createView()` included), and every `TODO Migration` is listed in the summary.

6. **Summarize**: what was migrated, the remaining `TODO Migration` items with their guide links, and the tests the user must run on their real map.

## Guardrails

- Never change files before the user has approved the plan (step 3).
- Never invent a VisioOne API. Check every call against the installed declarations.
- Never remove legacy code that has no migrated equivalent: comment it with a `TODO Migration` instead.
