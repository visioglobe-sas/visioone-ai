---
name: integrate-visioone-sdk
description: Integrates the VisioOne SDK (Visioglobe) into the current web project — 3D indoor/outdoor maps, POIs, multimodal routing. Use when the user asks to add, integrate or set up VisioOne, the Visioglobe SDK or a Visioglobe map in their project. For migrating an existing VisioWeb, VisioWeb Essential or VisioMove Essential app, use migrate-to-visioone instead.
---

# Integrating the VisioOne SDK

VisioOne is Visioglobe's web SDK (JavaScript/TypeScript) for loading and exploring 3D maps built with VisioMapEditor: POI management, multimodal routing, customizable markers and a fully overridable UI.

This skill targets **`@visioglobe/visioone` 1.1.0**. If the project already uses another version, read that version's changelog before applying the notes below.

## Official sources (use only these, never guess others)

- **npm package**: https://www.npmjs.com/package/@visioglobe/visioone
- **Documentation** (getting started, samples): https://my.visioglobe.com/docs/VisioOne/docs/index.html
- **API reference**: https://my.visioglobe.com/docs/VisioOne/APIdocs/index.html
- **Demo app**: https://cdn.visioglobe.com/visioone/latest/apps/demo/

Once the package is installed, its TypeScript declarations (`node_modules/@visioglobe/visioone`) are the authoritative API surface. Check every method, option and event you use against them. If something is not declared there, do not use it.

If information you need (map hash, custom map server URL, authorization token) is not in these sources, ask the user instead of making it up.

## Bundled references

Read the relevant section before writing code for a feature. Do not load whole files when one section is enough.

- `references/api-recipes.md`: task-oriented recipes checked against the 1.1.0 declarations: loading and view, camera, POI search and events, highlighting, runtime POIs, floors and explore mode, routing (accessible, multi-destination, step-by-step, restyling, custom navigation markers, kiosk origin, rerouting), images/labels/markers/lines/surfaces, UI parts and theming, localization, custom data, position tracking and geofencing, occupancy, map server and URL parameters. Section 12 is a checklist of cross-cutting pitfalls.
- `references/mobile-webview.md`: embedding VisioOne in a native app (Android, iOS, Flutter, React Native): how to package the web bundle, the native↔JS bridge contract, a minimal skeleton per platform and platform-specific pitfalls.

## Steps

1. **Understand the target project**
   - Detect the package manager (`package.json`: npm, pnpm or yarn) and the framework (vanilla, React, Vue…).
   - VisioOne is a browser SDK. For a native mobile app (Android, iOS, Flutter, React Native), the supported approach is to embed VisioOne in a WebView with a native↔JS bridge: follow `references/mobile-webview.md`. For any other kind of project, ask for confirmation before going further.
   - If the project is empty, ask which framework to use.

2. **Confirm before installing**
   - State the exact command (`npm install @visioglobe/visioone` or its pnpm/yarn equivalent) and wait for approval.

3. **Install the SDK**

4. **Generate a minimal integration module** (e.g. `src/lib/visioone.ts`) that follows the project's existing conventions:

   ```ts
   import { createVisioOne } from '@visioglobe/visioone';

   const visioOne = createVisioOne();
   // Read the hash the way the project reads its other settings (Vite shown here).
   const venue = await visioOne.loadVenue({ vg_maphash: import.meta.env.VITE_VISIOONE_MAP_HASH }, container);
   const view = await visioOne.createView(container, venue);
   ```

   The container needs an explicit height, otherwise nothing is visible.

   - Read the map hash from an environment variable, never hard-code it. Add the variable to `.env.example` if that file exists.
   - Only add `baseURL` (custom map server) or an authorization token if the user says their map needs them.
   - Keep the module thin: expose what the user needs (load, view, POIs, routing). No extra abstraction layer.

5. **Add a minimal usage example** (a page or component that displays the map), based on the official samples or the demo app.

6. **Summarize**: what was installed and generated, what the user still has to provide (map hash, etc.), and any limitation you hit.

## Known pitfalls (VisioOne 1.0.6 → 1.1.0)

- **The map identifier is `vg_maphash`** since 1.0.6, both as a `loadVenue()` option and as a URL parameter (`?vg_maphash=...`). There is no alias: `loadVenue({ hash })` fails with `Cannot load the venue`. Older code samples still use `hash`.
- **`createView()` can fail on some maps** (since 1.0.6; the code involved is unchanged in 1.1.0) with `TypeError: Cannot read properties of undefined (reading 'labelSizePolicy')` even though `loadVenue()` succeeded. Always test `createView()` against the user's real map. If this error occurs, tell the user to contact Visioglobe. Do not try to work around it in code.
- **TypeScript typing**: the package root types are incomplete (1.0.9 and 1.1.0) (`createVisioOne()` resolves to `any`, other types are not exported from the root). Use type-only deep imports as shown in `references/api-recipes.md` section 0. The declarations also type a second `loadVenue` parameter (`loaderContainer: HTMLElement`) as non-optional, even though a single argument works at runtime: pass the map container.
- **Error classes are not exported**: `instanceof` checks are impossible, compare `error.constructor.name` instead.
- **`view.goToFloor(...)` is optional** since 1.0.6 but still the way to choose the starting floor.
- **Custom data is not loaded by `loadVenue()`**: call `await venue.refreshCustomData()` once before `venue.getPOICustomData(poi)`, otherwise it returns `{}`. `refreshCustomData()` rejects if the map has no published custom data, so wrap it in `try/catch`. Custom data is read-only and its values are always strings.
- **Upgrading from 1.0.9 to 1.1.0**: the built-in UI string key `go` is now `go-there`, and custom navigation locales need five new keys (`maneuvers.enterBuilding`, `maneuvers.exitBuilding`, `detailedInstructions.goUp`, `goDown`, `changeFloor`). Navigations through several floors now have one more instruction per floor transition: never hard-code instruction indexes.
- **New in 1.1.0**: `allNavigationAccessible` (load option and View property, or the `accessibleNavigation` URL parameter) forces accessible routes everywhere; `venue.navigationMarkerRenderer` customizes navigation markers. See `references/api-recipes.md` sections 4.2 and 4.6.
- **Positions are always geographic** (`{ latitude, longitude, altitude? }`, WGS84), never local `{x, y}` map coordinates.

## Guardrails

- Never commit a map hash or a token in clear text.
- Never install any package other than `@visioglobe/visioone` for this SDK.
- If the documentation is incomplete or unreachable, say so explicitly rather than improvising an API.
