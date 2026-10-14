# References

`migration-map.json` is the machine-readable table of the public API of the legacy SDKs (VisioWeb, VisioWeb Essential, VisioMove Essential V2) and of their VisioOne equivalents.

- It is **generated** from the API correspondence appendix of the public VisioOne migration guide by `scripts/build_migration_map.py`. Never edit it by hand: fix the guide, then regenerate.
- The generator checks every VisioOne symbol written as code against the TypeScript declarations of the targeted `@visioglobe/visioone` version, and fails if one is missing.
- `note` fields are in French, the guide's current language. They will switch to English when the English guide is published.

Entry shape:

```json
{
  "sdk": "visioweb | visioweb-essential | visiomove-essential-v2",
  "section": "Legacy API area (appendix heading)",
  "legacy": "Mapviewer.initialize(mapDiv, parameters)",
  "visioone": "visioOne.loadVenue(options) puis visioOne.createView(container, venue, options?)",
  "status": "direct | different | workaround | none | not-applicable",
  "note": "Explanation of the mapping",
  "guide": ["Migration Web §2.2"]
}
```
