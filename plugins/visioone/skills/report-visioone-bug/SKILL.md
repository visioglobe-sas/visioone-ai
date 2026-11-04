---
name: report-visioone-bug
description: Prepares a bug report for the Visioglobe team about the VisioOne SDK, a Visioglobe map or this plugin, ready to submit through Visioglobe support (my.visioglobe.com/support). Use when the user wants to report a bug, an issue or unexpected behavior to Visioglobe, or contact Visioglobe support, or when another VisioOne skill hits a problem it says to report to Visioglobe.
---

# Reporting a bug to Visioglobe

Bug reports go to the Visioglobe team through **Visioglobe support: https://my.visioglobe.com/support**. This skill prepares the report; the user submits it. Never send it anywhere yourself: no GitHub issue, no e-mail, no web form.

This skill targets **`@visioglobe/visioone` 1.1.0**, the version the "Known pitfalls" of `../integrate-visioone-sdk/SKILL.md` are written for. If the project uses another version, say so in the report and read that version's changelog before ruling out a known issue.

## Steps

1. **Rule out a misuse first**
   - Check every VisioOne call involved against the TypeScript declarations of the installed `@visioglobe/visioone` package, and against the "Known pitfalls" of `../integrate-visioone-sdk/SKILL.md`.
   - If the problem comes from the project's own code, explain it and propose the fix, but do not change any file without the user's approval. During a migration, the migration plan's approval rule still applies.

2. **Classify the bug**
   - **SDK**: the VisioOne library itself misbehaves (error thrown from `@visioglobe/visioone`, wrong rendering, a declared API that does not do what its documentation says).
   - **Map**: the map data looks wrong (missing or misplaced POI, wrong route, a valid map hash that does not load).
   - **Plugin**: one of this plugin's skills gave wrong guidance (an API that does not exist, a wrong migration mapping, a wrong step).

3. **Collect the facts.** Read what you can from the project before asking the user:
   - VisioOne version: the installed one (`node_modules/@visioglobe/visioone/package.json`), not the range in `package.json`.
   - Framework and bundler; browser and OS, or the WebView platform for a native app.
   - How the map is loaded: whether it uses a custom `baseURL` and an authorization token (yes/no only, never their values).
   - The exact error message and stack trace, from the console or the logs.
   - Steps to reproduce, expected result, actual result.
   - A minimal reproduction: the smallest code that triggers the bug, without business logic.
   - Ask the user whether the bug also happens in the demo app (https://cdn.visioglobe.com/visioone/latest/apps/demo/) with the same map. The demo runs the latest VisioOne release, which can differ from the installed version: record the demo's version if the user can see it, otherwise write that it was the `latest` demo.
   - For a plugin bug: the skill, what it said and what is correct, and the plugin version. That version is the `version` field of the plugin's own `.claude-plugin/plugin.json`, two folders above this skill's base directory (in the Claude Code plugin cache, not in the user's project). If you cannot read it, ask the user to check it in `/plugin`. For a migration, add the legacy symbol and its `migration-map.json` entry.

4. **Remove sensitive data** from every part of the report, error messages, stack traces, URLs and code included:
   - Replace authorization tokens, JWTs, API keys, passwords, cookies and credentials in URLs with `<redacted>`.
   - Replace the host of a custom map server (`baseURL`) with `<map-server>`.
   - Replace local paths that reveal a user name or a private folder (e.g. `/Users/<name>/…`, `C:\Users\<name>\…`) with a path relative to the project.
   - The map hash helps Visioglobe reproduce the bug: ask the user before including it. If they refuse, replace it with `<map-hash>` everywhere, including `vg_maphash=` URL parameters and `loadVenue()` options in the reproduction.
   - Leave out personal data and project code unrelated to the bug.

5. **Write the report** in the language the user is writing in, following this template. One bug per report; write "unknown" rather than guessing a value.

   ```markdown
   ## Summary
   <one sentence: what fails, where>

   ## Category
   SDK | Map | Plugin

   ## Environment
   - VisioOne version:
   - Framework / bundler:
   - Browser and OS, or native platform (WebView):
   - Custom map server: yes/no — Authorization token: yes/no
   - Map hash: <only if the user agreed, otherwise <map-hash>>
   - Plugin version and skill: <plugin bugs only>

   ## Steps to reproduce
   1.

   ## Expected result

   ## Actual result
   <exact error message and stack trace>

   ## Minimal reproduction
   <code>

   ## Reproduces in the demo app
   yes / no / not tested — demo version: <version or "latest">
   ```

6. **Hand it over**
   - Show the report in the conversation. If the user wants a file, write it outside the project's repository (e.g. in their temporary or downloads folder), never in the working tree, so that it cannot be committed.
   - Tell the user to open https://my.visioglobe.com/support, submit the report there and attach screenshots or full logs if they have any, after checking them for the same sensitive data. If they cannot access it, they should send it to their Visioglobe contact.

## Guardrails

- Never submit the report yourself, and never post it on a public site.
- Never include a token, a key or a password, even partially.
- Never change project files while preparing a report without the user's approval.
- Never invent a version, an error message or a reproduction step: ask the user or write "unknown".
