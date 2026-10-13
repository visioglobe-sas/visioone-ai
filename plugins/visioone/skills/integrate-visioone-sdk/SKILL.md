---
name: integrate-visioone-sdk
description: Integrates the VisioOne SDK (Visioglobe) into the current web project — 3D indoor/outdoor maps, POIs, multimodal routing. Use when the user asks to add, integrate or set up VisioOne, the Visioglobe SDK or a Visioglobe map in their project. For migrating an existing VisioWeb, VisioWeb Essential or VisioMove Essential app, use migrate-to-visioone instead.
---

# Integrating the VisioOne SDK

VisioOne is Visioglobe's web SDK (JavaScript/TypeScript) for loading and exploring 3D maps built with VisioMapEditor: POI management, multimodal routing, customizable markers and a fully overridable UI.

This skill targets **`@visioglobe/visioone` 1.0.9**. If the project already uses another version, read that version's changelog before applying the notes below.

## Official sources (use only these, never guess others)

- **npm package**: https://www.npmjs.com/package/@visioglobe/visioone
- **Documentation** (getting started, samples): https://my.visioglobe.com/docs/VisioOne/docs/index.html
- **API reference**: https://my.visioglobe.com/docs/VisioOne/APIdocs/index.html
- **Demo app**: https://cdn.visioglobe.com/visioone/latest/apps/demo/

Once the package is installed, its TypeScript declarations (`node_modules/@visioglobe/visioone`) are the authoritative API surface. Check every method, option and event you use against them. If something is not declared there, do not use it.

If information you need (map hash, custom map server URL, authorization token) is not in these sources, ask the user instead of making it up.

## Steps

1. **Understand the target project**
   - Detect the package manager (`package.json`: npm, pnpm or yarn) and the framework (vanilla, React, Vue…).
   - VisioOne is a browser SDK. If the project is not a web JS/TS project, ask for confirmation before going further. For a native mobile app, the supported approach is to embed VisioOne in a WebView with a native↔JS bridge — say so and ask how to proceed.
   - If the project is empty, ask which framework to use.

2. **Confirm before installing**
   - State the exact command (`npm install @visioglobe/visioone` or its pnpm/yarn equivalent) and wait for approval.

3. **Install the SDK**

4. **Generate a minimal integration module** (e.g. `src/lib/visioone.ts`) that follows the project's existing conventions:

   ```ts
   import { createVisioOne } from '@visioglobe/visioone';

   const visioOne = createVisioOne();
   const venue = await visioOne.loadVenue({ vg_maphash: import.meta.env.VITE_VISIOONE_MAP_HASH });
   const view = await visioOne.createView(container, venue);
   ```

   - Read the map hash from an environment variable, never hard-code it. Add the variable to `.env.example` if that file exists.
   - Only add `baseURL` (custom map server) or an authorization token if the user says their map needs them.
   - Keep the module thin: expose what the user needs (load, view, POIs, routing). No extra abstraction layer.

5. **Add a minimal usage example** (a page or component that displays the map), based on the official samples or the demo app.

6. **Summarize**: what was installed and generated, what the user still has to provide (map hash, etc.), and any limitation you hit.

## Known pitfalls (VisioOne 1.0.6 → 1.0.9)

- **The map identifier is `vg_maphash`** since 1.0.6, both as a `loadVenue()` option and as a URL parameter (`?vg_maphash=...`). There is no alias: `loadVenue({ hash })` fails with `Cannot load the venue`. Older code samples still use `hash`.
- **`createView()` can fail on some maps** with `TypeError: Cannot read properties of undefined (reading 'labelSizePolicy')` even though `loadVenue()` succeeded. Always test `createView()` against the user's real map. If this error occurs, tell the user to contact Visioglobe. Do not try to work around it in code.
- **TypeScript strict mode**: the declarations type a second `loadVenue` parameter (`loaderContainer: HTMLElement`) as non-optional, even though a single argument works at runtime. In a strict TS project, pass it explicitly.
- **`view.goToFloor(...)` is optional** since 1.0.6 but still the way to choose the starting floor.
- **Custom data is not loaded by `loadVenue()`**: call `await venue.refreshCustomData()` once before `venue.getPOICustomData(poi)`, otherwise it returns `{}`. `refreshCustomData()` rejects if the map has no published custom data, so wrap it in `try/catch`. Custom data is read-only and its values are always strings.
- **Positions are always geographic** (`{ latitude, longitude, altitude? }`, WGS84), never local `{x, y}` map coordinates.

## Guardrails

- Never commit a map hash or a token in clear text.
- Never install any package other than `@visioglobe/visioone` for this SDK.
- If the documentation is incomplete or unreachable, say so explicitly rather than improvising an API.
