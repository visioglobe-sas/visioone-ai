# References

This folder will contain `migration-map.json`: the machine-readable table of legacy API symbols (VisioWeb, VisioWeb Essential, VisioMove Essential V2) and their VisioOne equivalents.

Rules for its content:

- It is generated from the public VisioOne migration guide (API correspondence appendix). It is never edited by hand and never contains a mapping that the public guide does not document.
- Every entry links to the guide section that justifies it.
- Every VisioOne symbol it cites is checked against the TypeScript declarations of the targeted `@visioglobe/visioone` version.

Expected entry shape (draft):

```json
{
  "sdk": "visioweb | visioweb-essential | visiomove-essential-v2",
  "legacy": "Mapviewer.initialize",
  "visioone": "VisioOne.loadVenue + VisioOne.createView",
  "status": "direct | partial | absent | integrator",
  "since": "1.0.0",
  "guide": "https://my.visioglobe.com/docs/VisioOne/docs/..."
}
```
