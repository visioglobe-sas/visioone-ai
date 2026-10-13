# VisioOne AI plugins

Official Visioglobe plugins for AI coding assistants. They help you integrate the [VisioOne](https://www.npmjs.com/package/@visioglobe/visioone) indoor mapping SDK into your project, and migrate existing apps from legacy Visioglobe SDKs.

> **Status: draft, not published yet.** `migrate-to-visioone` only produces an inventory and a migration plan until its mapping table ships.

## Skills

| Skill | What it does |
|---|---|
| `integrate-visioone-sdk` | Adds VisioOne to a web project: installation, minimal integration module, usage example. |
| `migrate-to-visioone` | Migrates a VisioWeb, VisioWeb Essential or VisioMove Essential V2 app to VisioOne, following the official migration guide. |

Both target `@visioglobe/visioone` **1.0.9**.

## Install (Claude Code)

```
/plugin marketplace add visioglobe-sas/visioone-ai
/plugin install visioone@visioone-ai
```

Then ask Claude, for example: *"Integrate VisioOne in this project"* or *"Migrate this VisioWeb app to VisioOne"*.

## Documentation

- VisioOne documentation: https://my.visioglobe.com/docs/VisioOne/docs/index.html
- API reference: https://my.visioglobe.com/docs/VisioOne/APIdocs/index.html
- Support: https://my.visioglobe.com/support

## License

This plugin and its skills are licensed under the [Apache License 2.0](LICENSE).

This license covers the plugin and its skills only. The VisioOne SDK (`@visioglobe/visioone`) is proprietary software distributed under its own terms. As stated in section 6 of the license, it grants no right to use the Visioglobe or VisioOne names.
