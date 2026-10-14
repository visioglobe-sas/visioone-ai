# VisioOne web SDK — API recipes (`@visioglobe/visioone` 1.0.9)

Task-oriented recipes. Every symbol below was checked against the 1.0.9 type declarations
(`node_modules/@visioglobe/visioone/dist/src/VisioOne/**.d.ts`). Snippets assume `visioOne`,
`venue` and `view` from recipe 1.1 are in scope. All positions are WGS84 `{ latitude, longitude, altitude? }`.

## 0. Setup and typing

```bash
npm install @visioglobe/visioone
```

```ts
import { createVisioOne } from '@visioglobe/visioone';
// Type-only deep imports (see gotcha below)
import type { VisioOne, Venue, POI, Floor, Building } from '@visioglobe/visioone/dist/src/VisioOne/Venue';
import type { View, POIEvent, VenueEvent } from '@visioglobe/visioone/dist/src/VisioOne/View';
import type { Position, Color } from '@visioglobe/visioone/dist/src/VisioOne/Core';
import type { NavigationTrace } from '@visioglobe/visioone/dist/src/VisioOne/Navigation';
```

Gotchas:
- **The package root types are incomplete in 1.0.9.** `dist/src/visioOne.d.ts` imports `VisioOne` from
  `./VisioOneImplementation/...`, which is not shipped. As a result `createVisioOne()` resolves to `any`
  (or a "cannot find module" error without `skipLibCheck`), and no other type is exported from the root.
  Annotate explicitly (`const visioOne: VisioOne = createVisioOne()`) using **type-only** deep imports
  from `dist/src/VisioOne/{Venue,View,Core,Navigation,Content}`. Never import runtime values from those paths.
- At runtime the package exports only `createVisioOne`, `VisioOne` and a default export. **Error classes
  are not exported**, so `instanceof RouteNotFoundError` is impossible (see 1.5).
- With npm, the SDK CSS is injected by the JS bundle; no stylesheet import is needed.
- The map container **must have an explicit height** (e.g. `height: 80vh`), otherwise nothing is visible.
- WebGL is required (browser or WebView).

---

## 1. Loading & view

### 1.1 Load a venue and display it
Load map data by hash, then render it in a container.

```ts
const visioOne: VisioOne = createVisioOne();
const container = document.querySelector<HTMLElement>('#map')!;

const venue: Venue = await visioOne.loadVenue({ vg_maphash: 'YOUR_MAP_HASH' }, container);
const view: View = await visioOne.createView(container, venue);
console.log(visioOne.version); // '1.0.9'
```

Gotchas:
- The option is **`vg_maphash`** (renamed from `hash` in 1.0.6, no alias). Older docs/snippets showing
  `loadVenue({ hash })` fail with `Error('Cannot load the venue')`.
- The hash (41 characters, found on my.visioglobe.com) only works once the map has been **built** in VisioMapEditor.
- `loadVenue(options, loaderContainer)`: `loaderContainer` is not optional in the types (JS callers often omit
  it). The loader is removed automatically once `createView` resolves.
- `createView` **wipes the container's existing content**. Add your own overlays after it resolves.
- **URL query parameters override code options**: a host page served with `?vg_maphash=<other>` loads that
  other map. Do not serve the host page with query params you do not control (see section 11).
- **Known 1.0.6–1.0.9 issue**: on some maps `createView()` rejects with
  `TypeError: Cannot read properties of undefined (reading 'labelSizePolicy')` even though `loadVenue()`
  succeeded. Test `createView` on your real map early.
- Since 1.0.6 the map renders without an initial `goToFloor` (it was required up to 1.0.5).
- Several `View`s can share one `Venue`.

### 1.2 View creation options
Configure camera and rendering at creation time (`ViewCreateOptions`).

```ts
const view2 = await visioOne.createView(container, venue, {
  cameraProjection: 'orthographic', // 'perspective' (default) | 'orthographic'
  zenithalMode: false,              // true = top-down view, pitch locked
  lockPitch: 45,                    // 1..75 degrees; ignored when zenithalMode is true
  zoomSpeed: 1,
  focusOnPOI: 'SOME-POI-ID',        // camera animates to this POI once the view is created
  disableCameraOnClick: false,      // true = default UI does not move the camera on POI click
  enableShadows: false,             // costly
  quality: 'auto',                  // 'auto' | 'low' | 'medium' | 'high'
});
```

Gotchas:
- Older docs show `{ useOrthographicCamera: true }`: **not in 1.0.9**, use `cameraProjection: 'orthographic'`.
- `view.cameraProjection` is read-only after creation; recreate the view to change it.
- Most options also exist as URL parameters (section 11), and URL parameters win.

### 1.3 Rendering quality
React to the device-capability recommendation.

```ts
console.log(view.quality); // { tier, recommendedTier, mismatch }
view.addEventListener('qualityrecommendation', (e: any) => {
  // e.applied / e.recommended : 'low' | 'medium' | 'high'
  // The SDK only signals. To switch: destroyView + createView({ quality: e.recommended }).
});
```

Gotcha: fired at most once, at startup, and only when the applied tier differs from the recommended one.
`QualityRecommendationEvent` is exported from `dist/src/VisioOne/View/Events`, not from `.../View`.

### 1.4 Tear down
Free GPU and DOM resources (SPA route change, component unmount, map switch).

```ts
await visioOne.destroyView(view);
await visioOne.unloadVenue(venue); // also destroys any remaining views on this venue
```

Gotcha: in 1.0.5 `unloadVenue()` always rejected after unloading (fixed in 1.0.9). A `try/catch` around
teardown is still a sensible default in components that remount.

### 1.5 Handle SDK errors
Catch typed errors without importable classes.

```ts
try {
  await visioOne.loadVenue({ vg_maphash: 'YOUR_MAP_HASH' }, container);
} catch (error) {
  const name = (error as Error).constructor.name; // 'VenueNotFoundError', 'UnauthorizedError', ...
  if (name === 'UnauthorizedError') { /* refresh the token, retry */ }
  visioOne.showError(error as Error, container); // optional built-in error UI
}
```

Gotchas:
- `error.name` is always the generic `"Error"`; compare `error.constructor.name`.
- An unreachable `baseURL` (DNS/network) rejects with a generic `Error('Cannot load the venue')`, not a
  typed error. A wrong hash rejects with `VenueNotFoundError`.
- `showError` renders a full overlay with a very high z-index that covers your own UI. Skip it if your app
  offers its own "retry" flow. Without a container it logs to the console.
- `visioOne.showLoader(container)` displays the loader manually. It is removed when `createView` resolves.

### 1.6 Move the camera (reset, building, floor, POI, viewpoint)
Animate the camera to a target. Every `goTo*` returns an awaitable, cancelable `AnimationPromise`.

```ts
await view.goToGlobal();                                   // reset: whole venue, explore mode -> 'global'
const building = venue.venueLayout.buildings[0];
await view.goToBuilding(building, { orientation: { heading: 42, pitch: 51 } });
await view.goToFloor(building.floors[0]);
await view.goToViewpoint(
  { positions: [{ latitude: 45.2146, longitude: 5.8086 }, { latitude: 45.2148, longitude: 5.8103 }],
    targetAltitude: 0 },
  { duration: 800, easing: 'easeInOutSine', padding: { top: 80, right: 80, bottom: 80, left: 80 } },
);
const anim = view.goToGlobal({ duration: 3000 });
anim.cancel(); // jumps to the final state; anim.isCanceled === true
view.setCameraDefaultAnimationOptions({ duration: 500, easing: 'easeOutQuad' });
```

Gotchas:
- `AnimationOptions`: `duration` (ms, default 1000), `easing` (animejs Penner names), `padding`
  (pixels, all four sides required), `orientation: { heading?, pitch? }` (degrees or `'initial'` to keep the current value).
- `goToGlobal()` accepts optional `AnimationOptions` and returns a promise (some docs say "no arguments,
  nothing to await"). It switches `currentExploreMode` to `'global'` **when the animation completes**.
- `goToBuilding` also changes the floor (to `building.defaultFloorID`). Do not chain a `goToFloor` in the
  same gesture, or two animations overlap.
- `goToFloor`/`goToBuilding`/`goToPOI` take objects, not IDs.
- Pitch convention: 0 = looking straight down, 90 = horizon. Heading: 0 = North, clockwise.

### 1.7 Constrain the camera
Lock movements and bounds (kiosk, embedded widget).

```ts
const cam = view.camera;
cam.rotationEnabled = false;  // also: panEnabled, zoomEnabled, pitchEnabled
cam.minimumAltitude = 20;     // also: maximumAltitude, minimumRadius, maximumRadius
cam.minimumPitch = 10;        // also: maximumPitch (default 75)
cam.heading = 90;             // writable; also pitch
console.log(cam.position, cam.target); // read-only Positions
view.setZenithalMode(true);   // or view.zenithalModeEnabled = true
view.lockPitch(true, 30);     // view.lockPitch(false) to unlock
view.disableCameraOnClick = true; // default UI only
```

---

## 2. POIs & interaction

### 2.1 Find a POI and get its name and position
There is no `getPOIById`. A POI has no `name` and no lat/lng of its own.

```ts
const poi = venue.pois.find((p) => p.id === 'SOME-POI-ID'); // undefined if absent (no throw)

function poiName(p: POI): string {
  return venue.translator.translatePOI(p, venue.currentLocale).name || p.labels[0]?.text || p.id;
}
function poiPosition(p: POI): Position | undefined {
  return p.markers[0]?.position ?? p.labels[0]?.position ?? p.images[0]?.position
      ?? p.surfaces[0]?.positions[0];
}
```

Gotchas:
- A POI is a **container** (`images`, `labels`, `lines`, `markers`, `surfaces`, `categories`, `floor?`).
- `venue.pois` also contains non-business entries: a floor-anchor POI whose id equals a floor id, and
  decorative icon/3D-model POIs. Filter them out of search lists and route pickers.
- `poi.floor` is optional; `poi.categories` may be empty.
- `translatePOI` falls back to the default locale, then to empty strings. It also returns `categories`,
  `description` (may contain HTML) and `url`.

### 2.2 Search POIs
No search API. Filter `venue.pois` in app code.

```ts
const q = 'café'.toLowerCase();
const results = venue.pois.filter((p) => poiName(p).toLowerCase().includes(q));
```

### 2.3 React to a POI click / hover / selection
Listen to pointer events on the view (standard `EventTarget` semantics).

```ts
const onClick = (e: POIEvent) => {
  const hits = e.pois;          // array: one tap can hit several overlapping POIs (marker + surface)
  console.log(hits.map((p) => p.id), e.coordinate, e.originalEvent);
};
view.addEventListener('poiclick', onClick as any);
view.removeEventListener('poiclick', onClick as any);
// Others: 'poidblclick' | 'poimousedown' | 'poimouseup' | 'poimouseover' | 'poimouseout' | 'selectedpoischange'
view.addEventListener('poimouseover', ((e: POIEvent) => console.log(e.pois)) as any, { passive: true });
```

Gotchas:
- The payload is the event object itself (no `.detail`).
- `e.pois` is always an array; never assume length 1, and it can be empty.
- `addEventListener` takes a union of callback types. In strict TS, cast or type the parameter
  explicitly as shown.
- `view.selectedPOIs` (read/write `POI[]`) holds the selection; assigning it highlights those POIs' surfaces
  with `selectionColor`.

### 2.4 Focus / highlight a POI
Bring a POI into view reliably, including across buildings.

```ts
async function focusPOI(p: POI) {
  if (p.floor) await view.goToFloor(p.floor); // recommended before goToPOI
  view.selectedPOIs = [p];
  await view.goToPOI(p, { orientation: { pitch: 20 },
                          padding: { top: 100, right: 100, bottom: 100, left: 100 } });
}
```

Gotchas:
- The SDK docs state the **caller is responsible for calling `goToFloor` before `goToPOI`**. Without it,
  in `'floor'` explore mode the screen shows the POI's floor but `currentFloor`/`currentBuilding` stay on
  the old floor, and no `currentfloorchanged` is fired (desync). An outdoor POI requested in
  `'building'`/`'floor'` mode is ignored (console warning) while the promise still resolves.
- Alternative highlight: `venue.updateSurface(s, { selectionColor: '#057DBC' })` per surface. Revert with
  `selectionColor: 'default'`, not `undefined`.

### 2.5 Highlight every POI of a category
Resolve the POIs of a category, then recolor their surfaces.

```ts
const label = (c: { id: string }) =>
  venue.translator.translateCategory(c, venue.currentLocale).name || c.id;
const options = venue.categories.map((c) => ({ id: c.id, label: label(c) }));

function highlightCategory(categoryId: string, color: Color) {
  const pois = venue.pois.filter((p) => p.categories.some((c) => c.id === categoryId));
  pois.forEach((p) => p.surfaces.forEach((s) => venue.updateSurface(s, { color })));
  return pois;
}
const clear = (pois: POI[]) =>
  pois.forEach((p) => p.surfaces.forEach((s) => venue.updateSurface(s, { color: 'initial' })));
```

Gotchas:
- `Category` is only `{ id }`. The id is opaque (often numeric). Display `translateCategory(...).name`.
- A POI can have several categories: use `.some`.
- Marker-only POIs have no surfaces. Add an Image or Marker to highlight them instead (section 5).
- Categories are flat (no parent/child). Build hierarchies in app code.

### 2.6 Clickable / interactive surface
Let the SDK handle the hover and selection colors of a surface.

```ts
function setInteractive(p: POI, on: boolean) {
  p.surfaces.forEach((s) => venue.updateSurface(s, on
    ? { isInteractive: true, color: '#2ECC71', hoverColor: '#F1C40F', selectionColor: '#E74C3C' }
    : { isInteractive: false, color: 'initial', hoverColor: 'default', selectionColor: 'default' }));
}
```

Gotchas:
- Color swapping is SDK-managed. Use `poiclick` only to *react* (book a room, open a card).
- `isInteractive: false` does not clear colors: reset `color: 'initial'` explicitly.
- Without per-surface colors, the view-wide `view.surfaceHoverColor` (default `'highlight'`) and
  `view.surfaceSelectionColor` apply. `view.hoverEnabled` / `view.selectionEnabled` toggle the behavior globally.
- Hover only exists with a pointer device. On touch, the surface goes straight to `selectionColor`.

### 2.7 Create, update and remove POIs at runtime
Add your own POIs without republishing the map.

```ts
const floor = venue.venueLayout.buildings[0].floors[0];  // omit floor => always displayed
const cat = venue.createCategory('my-category');
let myPoi: POI | undefined;
try {
  myPoi = venue.createPOI({ id: 'my-poi-1', floor, categories: [cat] });
} catch (e) {
  if ((e as Error).constructor.name === 'POIAlreadyExistsError') { /* pick another id */ }
}
if (myPoi) {
  const lbl = venue.createLabel({ poi: myPoi, position: { latitude: 45.2147, longitude: 5.8087 },
                                  width: 10, height: 2, text: 'Pop-up store' });
  venue.updatePOI(myPoi, { categories: [...myPoi.categories, venue.categories[0]] });
  venue.updateLabel(lbl, { text: 'Pop-up store (open)' });
  venue.removePOI(myPoi); // cascades: removes its labels/images/markers/lines too
}
venue.removeCategory(cat); // also removes it from every POI
```

Gotchas:
- A bare POI is **invisible**. Attach at least one Image/Label/Marker/Line.
- `createPOI` throws `POIAlreadyExistsError` for any existing id, including ids from the map bundle.
- `updatePOI` can only change `categories`, and it **replaces** the list. Spread the existing ones.
  Any visual edit goes through `update{Label,Image,Marker,Line,Surface}`.
- After `removePOI`, calling `removeLabel` etc. on its elements throws (already gone).
- A runtime category has no translated name: the default UI does not display it and its search does not find it.
  Older docs mention `createCategoryLocaleEntry`: **not in 1.0.9**.
- Runtime POIs cannot carry CustomData (no setter, no `customData` option).
- `position` must be real WGS84. Malformed positions throw (`"Provided position has a missing latitude"`).

---

## 3. Floors, buildings & explore mode

### 3.1 Custom floor / building selector
Drive floors from your own UI and stay in sync with the SDK.

```ts
const { outside, buildings } = venue.venueLayout;
const allFloors: Floor[] = [...(outside ? [outside] : []), ...buildings.flatMap((b) => b.floors)];
const sorted = [...buildings[0].floors].sort((a, b) => a.levelIndex - b.levelIndex);
const floorLabel = (f: Floor) => venue.translator.translateFloor(f, venue.currentLocale).name || f.id;
const buildingLabel = (b: Building) => venue.translator.translateBuilding(b, venue.currentLocale).name || b.id;

view.addEventListener('currentfloorchanged', ((e: VenueEvent) => {
  render(e.newBuilding?.id, e.newFloor?.id); // read newFloor/newBuilding only
}) as any);
view.goToFloor(sorted[1]);
console.log(view.currentFloor, view.currentBuilding); // read-only
declare function render(buildingId?: string, floorId?: string): void;
```

Gotchas:
- `Floor` has only `id`, `altitude`, `levelIndex`. Sort by `levelIndex` (array order is not guaranteed).
  Get display names with `translateFloor` / `translateBuilding` (`name`, `shortName?`, `description?`).
- The floor also changes through the SDK's own widget, search, navigation and tracking: always sync on
  `currentfloorchanged`, never on your own calls.
- In `'building'` mode, `oldFloor`/`oldBuilding` of the event can equal the new ones. Do not rely on them.
- `view.currentBuilding` is `undefined` outdoors. `view.currentFloor` is then the outside floor.
- To hide the built-in selector: `view.setUIPartVisible('floorSelector', false)` (section 6).

### 3.2 Explore mode (global / exploded building / single floor)
Switch how buildings are presented.

```ts
if (!view.currentBuilding) await view.goToBuilding(venue.venueLayout.buildings[0]);
view.currentExploreMode = 'building'; // 'global' | 'building' | 'floor'
view.addEventListener('exploremodechanged', ((e: { currentExploreMode: string }) =>
  console.log(e.currentExploreMode)) as any);
```

Gotchas:
- `'building'` = outside hidden, floors of the open building shown as a "carousel" (wheel/swipe to change
  the active floor, click to switch to `'floor'`). It shows nothing unless a building is open.
- `'building'` → `'floor'` on click is automatic. Keep UI in sync via `exploremodechanged`.
- Assigning `'global'` is immediate and does not animate out. Use `goToGlobal()` for an animated return.
  Assigning `'global'` from `'floor'` may log an internal console error. It is harmless.
- URL parameter: `exploreMode`.

---

## 4. Navigation / routing

### 4.1 Compute and display a route
Compute (Venue), build the visual (Venue), then display it (View).

```ts
let trace: NavigationTrace | undefined;
function showRoute(origin: POI | string | Position, destination: POI | string | Position) {
  try {
    const navigation = venue.computeNavigation({ origin, destination, type: 'fastest' });
    trace = venue.createNavigationTrace(navigation);
    view.setCurrentNavigationTrace(trace); // shows the route + the instructions UI, camera to start
  } catch (e) {
    const name = (e as Error).constructor.name;
    // 'RouteNotFoundError' | 'SourceOutOfLimitError' | 'DestinationOutOfLimitError'
    // | 'InvalidNavigationRequestError' (e.g. origin === destination) | generic Error (non-navigable POI)
  }
}
function clearRoute() {
  view.removeCurrentNavigationTrace();
  if (trace) venue.removeNavigationTrace(trace); // destroys the object; skip it and it leaks
  trace = undefined;
}
```

Gotchas:
- `origin`/`destination` accept a `POI`, a POI id, or a `Position` (snapped to the nearest routing edge).
  Pass resolved POIs to tell "unknown id" apart from "no route".
- Only one *current* navigation at a time. `createNavigationTrace` alone renders a **preview**. Remove
  previews you no longer need with `removeNavigationTrace(trace)` (some docs wrongly pass the request).
- Non-navigable POIs (floor anchors, decorative icon/model POIs) throw an untyped
  `"Cannot get node as RoutingSolver returned undefined."`. Filter pickers.
- Request options: `type` (`'fastest'` default | `'shortest'`), `isAccessible`, `firstNodeAsIntersection`
  (default false), `mergeFloorChangeInstructions` (default true), `excludedModalities`, `excludedAttributes`.
- Older docs pass `displayMode` in the request: **not in 1.0.9** (the request has no rendering options,
  and `createNavigationTrace` takes none).
- Route events: `navigationstarted`, `navigationstopped`, `navigationinstructionreached`,
  `navigationtoofarfromtrackedposition` (payload `NavigationEvent`: `navigation?`, `navigationTrace?`, `venue`, `view`).

### 4.2 Accessible route / avoid lifts, stairs, modalities
Constrain the routing graph.

```ts
const accessible = venue.computeNavigation({ origin: 'A', destination: 'B', isAccessible: true });
const noLift = venue.computeNavigation({ origin: 'A', destination: 'B', excludedAttributes: ['lift'] });
console.log(venue.modalities, venue.attributes); // what this venue actually defines
```

Gotchas:
- `isAccessible` uses the venue's own accessible-route rules authored in VisioMapEditor (not inspectable).
  It is additive with manual exclusions. Default is `false`.
- Attribute and modality strings are venue-defined. The elevator attribute is typically `'lift'` (not
  `'elevator'`, as the JSDoc example suggests). An attribute passed in `excludedModalities` does nothing.
  Unknown strings are silently ignored. Check `venue.attributes` / `venue.modalities`.
- When exclusions remove every path, you get the same errors as an unreachable pair.
- Options are read once per call: recompute after toggling.

### 4.3 Multiple destinations / waypoints
Route through several stops.

```ts
const multi = venue.computeNavigationMultiDestination({
  origin: 'A',
  destinations: ['CHECKPOINT', 'GATE-12'], // in order when optimize is false
  optimize: false,
});
view.setCurrentNavigationTrace(venue.createNavigationTrace(multi));
```

Gotchas:
- `optimize: true` reorders the intermediate stops but **keeps the last destination fixed** (cost grows
  factorially). There is no "closest"/"free last stop" strategy. For "closest", compute one route per
  candidate (or pre-sort with `venue.computeDistance`) and keep the shortest.
- Instructions carry `waypointIndex`. The `'waypoint'` maneuver marks a stop.
- URL parameters `origin`, `waypoint`, `destination` pre-fill a route at load.

### 4.4 Step-by-step instructions (custom navigation UI)
Read and drive instructions yourself.

```ts
const nav = venue.computeNavigation({ origin: 'A', destination: 'B' });
for (const i of nav.instructions) {
  console.log(i.maneuverType, i.detailedInstruction, i.length, i.duration, i.floor.id, i.modality);
}
view.addEventListener('navigationinstructionreached', () => {
  console.log(view.currentNavigationInstruction?.detailedInstruction); // undefined outside navigation
});
view.navigateToNextInstruction();     // animates dot + camera, switches floor if needed
view.navigateToPreviousInstruction();
view.setCurrentNavigationInstruction(nav.instructions[2]);
```

Gotchas:
- `detailedInstruction` is localized with the venue's current locale. `maneuverType` is a stable code
  (`goStraight`, `turnLeft`, `goUp`, `changeFloor`, `waypoint`, `end`, …) to map to your own icons.
- `view.currentNavigationInstruction` exists since 1.0.8. Before that, use
  `view.currentNavigationTrace.navigation.instructions[trace.index]`.
- To replace the built-in panel: `view.setUIPartVisible('navigation', false)`.

### 4.5 Restyle the route
Match brand colors.

```ts
const t = venue.createNavigationTrace(nav);
view.setCurrentNavigationTrace(t);
try {
  venue.updateNavigationTrace(t, {
    progressColor: '#E53935', progressOutlineColor: '#FFFFFF', progressFutureColor: '#F8C9C7',
    previewColor: '#F8C9C7', previewOutlineColor: '#FFFFFF',
    // also: progressOverlayColor, progressDisabledColor, progressDisabledOverlayColor,
    //       previewOverlayColor, textureRepeat, animationSpeed
  });
} catch { /* see gotcha */ }
// Per-segment fine-tuning:
t.sceneElements.forEach((se) => venue.updateLine(se.lineProgress, { thickness: 0.8 }));
```

Gotchas:
- No reset call: re-apply SDK defaults yourself (active `#0094F0`, inactive `#C5C5C5`). Re-apply your
  options after every new trace.
- `updateNavigationTrace` has been observed to throw an internal
  `TypeError (reading 'material')` *after* applying the colors. Wrap it in `try/catch`.
- `displayMode`/`thickness` are readable on the trace but not in `NavigationTraceUpdateOptions`. Older docs
  list `color`, `overlayColor`, `inactiveColor`, `inactiveOverlayColor` on the trace: **not in 1.0.9**.
- `sceneElements[i]` contains `lineProgress`, `lineProgressOverlay`, `lineProgressOutline`,
  `lineProgressDisabled`, `lineProgressDisabledOverlay`, `linePreview`, `linePreviewOutline`,
  `linePreviewOverlay`, `dot` (Image), `startMarker?`, `endMarker` (Markers).

### 4.6 Default origin ("You are here" kiosk)
Pre-fill the origin whenever the user starts a navigation from the UI.

```ts
view.setDefaultOrigin('KIOSK-POI-ID'); // POI, id or Position; unknown POI => console error, unchanged
```

Gotchas:
- `view.navigationStartPoint` (string) and the `navigationStartPoint` URL parameter still exist but are
  deprecated. Use `setDefaultOrigin` / the `defaultOrigin` URL parameter. Unlike `origin`, `defaultOrigin`
  does not open the navigation view on load.
- When no default origin is set and `allowTracking` is true, the latest tracked position is used.

### 4.7 Reroute when the user drifts off the route
The SDK warns but never recomputes by itself.

```ts
let destination: POI | string = 'B';
view.addEventListener('navigationtoofarfromtrackedposition', () => {
  const from = view.latestTrackedPosition;
  if (!from) return;
  const old = view.currentNavigationTrace;
  const t2 = venue.createNavigationTrace(venue.computeNavigation({ origin: from, destination }));
  view.setCurrentNavigationTrace(t2);
  if (old) venue.removeNavigationTrace(old);
});
```

Requires tracking (section 9). Test on real paths, especially multi-building sites.

---

## 5. Visual elements: images, labels, markers, lines, surfaces

All of them belong to a POI (`poi` option). They render only while the POI's floor is displayed (a POI
without a floor is always displayed). They are appended to `poi.images/labels/...`, so the map's own items
stay. Each `create*` call adds a new element: keep the reference to update or remove it. Sizes are in
**meters** (they scale with zoom). Colors: hex, `rgb()`, `hsl()` (alpha ignored, invalid → `InvalidColorError`).
URLs: absolute, data URL, or relative to `venue.baseURL`.

### 5.1 Images (icons in the 3D scene)
```ts
const anchor = venue.pois.find((p) => p.id === 'SOME-POI-ID')!;
const img = venue.createImage({
  poi: anchor, position: poiPosition(anchor)!, width: 6, height: 6,
  url: 'data:image/png;base64,iVBORw0KGgo...', orientationType: 'facing', // 'fixed' | 'flat' | 'facing'
});
venue.updateImage(img, { orientationType: 'fixed', rotation: 42 }); // rotation only for 'fixed'
venue.updateImage(img, { isVisible: false });
venue.removeImage(img);
```
Gotchas: `height` defaults to `width`. On update, `width` alone sets both, and `height` alone has no effect.
`'flat'`/`'facing'` on runtime images were broken before 1.0.9. An older doc says `url` is relative to an
`/images` directory without extension: the 1.0.9 types say relative to `baseURL`, so prefer full or data URLs.

### 5.2 Labels (text in the 3D scene)
```ts
const lbl = venue.createLabel({ poi: anchor, position: poiPosition(anchor)!,
  width: 16, height: 3, text: 'Lunch 12:00–14:00', color: '#E53935', rotation: 0 });
venue.updateLabel(lbl, { color: '#43A047', text: 'Closed today' });
venue.updateLabel(lbl, { width: 22, height: 4 }); // always both
venue.removeLabel(lbl);
```
Gotchas:
- **Always pass `height`**: it defaults to `width` (square box, huge wrapped text).
- `rotation` is create-only (not in `LabelUpdateOptions`). Remove and recreate to rotate.
- Empty `text` throws. Reusing a removed label throws `Provided label is not registered`.
- Labels re-render with the POI's locale entry after `setCurrentLocale` (empty if none).

### 5.3 Markers (HTML overlays, always on top, screen-facing)
```ts
const el = document.createElement('div');
el.className = 'you-are-here';
el.textContent = 'You are here';
const marker = venue.createMarker({ poi: anchor, position: poiPosition(anchor)!, element: el });
venue.updateMarker(marker, { position: { latitude: 45.2147, longitude: 5.8087 } });
venue.updateMarker(marker, { isVisible: false });
el.textContent = 'Updated';   // content: mutate your own element (no 'element' in MarkerUpdateOptions)
venue.removeMarker(marker);
```
Gotchas:
- Markers are not occluded by the 3D scene. Use them for pins, badges, "You are here", asset trackers, and
  geofencing pop-ups. Style them with your own CSS.
- Clicks on your element are plain DOM events: attach your own listeners.
- **Foreign markers** (native WebView overlays): `isForeignMarker: true`. The SDK does not position them.
  Listen to `'foreignmarkerupdated'` and read `e.screenPosition` (`left`, `top`, `z`, `isVisible`) on every
  camera move.

### 5.4 Lines
```ts
const line = venue.createLine({
  poi: anchor, thickness: 1, color: '#0094F0', zOffset: 0.2,
  positions: [{ latitude: 45.21463, longitude: 5.80653 }, { latitude: 45.21463, longitude: 5.80843 }],
  displayMode: 'textured', texture: 'https://example.com/arrow.png', animationSpeed: 1, textureRepeat: 1,
});
venue.updateLine(line, { color: '#00FF00', displayMode: 'progressOutline' });
venue.removeLine(line);
```
Gotchas: `displayMode` is `'textured' | 'halo' | 'progress' | 'progressOutline'`. `texture` /
`animationSpeed` / `textureRepeat` only apply to `'textured'`. The special texture `'#halo'` produces a halo
line. Older docs list `inactiveColor`: **not in 1.0.9**.

### 5.5 Surfaces (update only)
```ts
const s = venue.pois.find((p) => p.id === 'ROOM-1')!.surfaces[0];
venue.updateSurface(s, { color: '#00FF00', opacity: 0.6, extrusionHeight: 3 });
venue.updateSurface(s, { color: 'initial', hoverColor: 'default', selectionColor: 'default' });
console.log(s.positions, s.isFromBundle, s.isInteractive);
```
Gotchas:
- **No `createSurface` / `removeSurface` in 1.0.9.** Surfaces are drawn in VisioMapEditor (a
  `SurfaceCreateOptions` file exists in the typings but no method uses it). Draw zones in the editor.
- Reset sentinels: `color: 'initial'` (bundle color), and `hoverColor`/`selectionColor: 'default'`
  (view-wide color). `undefined` is not a documented reset. An older doc uses `hoverColor: 'initial'`:
  it compiles (`Color` is a plain `string`) but is not the documented sentinel for hover/selection.
  `Color` being `string` also means typos in colors are only caught at runtime (`InvalidColorError`).
- `opacity` and `isVisible` are only effective on non-bundle surfaces (per the typings).

### 5.6 Distances
```ts
const d = venue.computeDistance({ latitude: 45.2147, longitude: 5.8087 }, s); // meters
```
Accepts a `Position`, `Image`, `Label`, `Line` or `Surface` (center for images/labels, nearest edge for
lines/surfaces). Straight-line distance, not route length (`instruction.length` sums give the route length).

---

## 6. UI customization & theming

### 6.1 Colors, theme and global UI toggles
```ts
view.accentColor = '#FF0000';        // buttons/accent (default '#0094f0')
view.textAccentColor = '#FFFFFF';    // text on accent
view.surfaceHoverColor = '#20B2AA';  // or 'highlight' (default)
view.surfaceSelectionColor = '#20B2AA';
console.log(view.themes);            // available theme names
view.setTheme(view.themes[0]);
view.showUI = false;                 // hide the whole built-in UI
```
Gotchas: theming beyond 2 accent colors and named themes means hiding UI parts and rebuilding them.
URL parameters: `accentColor`, `textAccentColor`, `dark`, `bright`, `mirrorUI`.

### 6.2 Show / hide built-in UI parts
```ts
const parts = ['floorSelector', 'navigation', 'poiDetails', 'search', 'userTracking'] as const;
view.setUIPartVisible('floorSelector', false);
console.log(view.isUIPartVisible('search'));
```
Gotchas: the values are exact and case-sensitive (a typo fails silently in JS). Hidden widgets keep their
internal state (re-showing them is in sync). Hiding `search`/`navigation`/`userTracking` removes the only
built-in entry point to that flow: provide your own (2.2, 4.x, 9.1).

### 6.3 Replace a built-in widget with your own
```ts
view.setUIPartVisible('floorSelector', false);
const panel = document.createElement('div');
panel.style.cssText = 'position:absolute;top:100px;right:8px;z-index:1';
for (const b of venue.venueLayout.buildings) {
  const btn = document.createElement('button');
  btn.textContent = buildingLabel(b);
  btn.onclick = () => view.goToBuilding(b);
  panel.append(btn);
}
container.append(panel); // after createView resolved (it clears the container)
```
Same pattern for search (2.2), POI card (`poiclick` + `translatePOI`), and navigation panel (4.4).

---

## 7. Localization

### 7.1 Switch language at runtime
```ts
console.log(venue.translator.allLocales, venue.currentLocale);
await venue.setCurrentLocale('fr'); // labels, UI and current navigation re-render
```
Gotchas: it is async, so await it before reading `currentLocale`. There is no "locale changed" event.
`allLocales` excludes the `'default'` key, which is still a valid argument. Two codes may hold identical
content. Items without an entry for the target locale silently fall back to the default locale (some text
does not change). URL parameter: `locale` (ISO 639-1). The built-in UI ships `en`, `fr`, `ar`.

### 7.2 Translate venue content for your own UI
```ts
const e = venue.translator.translatePOI(anchor, venue.currentLocale);   // { name, categories, description?, url? }
venue.translator.translateCategory(venue.categories[0], 'en').name;
venue.translator.translateFloor(view.currentFloor, 'en').shortName;
if (view.currentBuilding) venue.translator.translateBuilding(view.currentBuilding, 'en').name;
```

### 7.3 Add a locale / override UI and navigation strings
```ts
venue.translator.addLocale('es', {
  'search-for-anything': 'Buscar cualquier cosa', // built-in UI key (LocaleUIStrings)
  'until': 'hasta {{ time }}',                     // keep required placeholders
  'turnRight': 'Gire a la derecha',                // navigation maneuver key
  'welcome': 'Bienvenido',                         // your own app key
});
venue.translator.translate('welcome', 'es');       // 'Bienvenido'
venue.translator.translate('key', 'es', { context: 'male' }); // i18next context/plurals
venue.translator.getLocale('es');
await venue.setCurrentLocale('es');
venue.translator.removeLocale('es');
```
Gotchas:
- In memory only (lost on reload). Re-add it after each `loadVenue`.
- It never translates POI/floor/building/category names: those come from the map authored in VisioMapEditor.
- Placeholders are mandatory in some keys: `poi-info-placeholder-1` (`{{ distance }} {{ duration }}`),
  `until` (`{{ time }}`), `itinerary-from-to` (`{{ from }}`, `{{ to }}`), `around-in-*` (`{{ count }}`),
  `no-result-for` (`{{ search }}`). Navigation sentences use `{{ duration }}`, `{{ floor }}`, `{{ modality }}`,
  `{{ poiName }}`.
- Typed key lists: `LocaleUIStrings` and `NavigationInstructionsStrings` (`maneuvers`, `modalities`,
  `duration`, `detailedInstructions`) in `dist/src/VisioOne/Content`. Older docs show combined sentence
  keys such as `goUpThenGoStraight` or `turnLeftThenChangeModality`: **these are not in the 1.0.9
  `DetailedInstructionsSentences` interface**, which only has `goStraightWithDuration*`, `endAtPOI` and
  `endAtDefinedPosition`.
- `translate` reads straight from the resource store: the reliable way to verify `addLocale`.

---

## 8. Custom data

### 8.1 Read business key/values authored on a POI
```ts
try { await venue.refreshCustomData(); } catch { /* nothing published for this map: not an error */ }
const data = venue.getPOICustomData(anchor); // { [key: string]: string }, synchronous
if (Object.keys(data).length) console.log(data['price']);
```
Gotchas:
- **Never auto-loaded**: until `refreshCustomData()` resolves, every POI returns `{}`. A single call fetches
  the whole venue. Call it again for fresh data.
- It **rejects** when the map has no CustomData published: catch and ignore.
- Always returns an object (never null). "No data" and "not refreshed" look identical.
- Read-only: no setter, nothing for runtime-created POIs. Values are always strings (parse numbers and dates yourself).

---

## 9. Position tracking & geofencing

### 9.1 Show a tracked position (blue dot) and device heading
```ts
view.allowTracking = true; // mandatory BEFORE injecting
view.updatePositionTrackerGraphicOptions({ color: '#0094F0', opacity: 0.8 });

function onPosition(lat: number, lng: number, accuracyMeters?: number) {
  view.injectTrackedPosition(
    { position: { latitude: lat, longitude: lng }, precisionCircleRadius: accuracyMeters },
    { duration: 1000, easing: 'linear' }, // optional: animate the dot
  );
}
window.addEventListener('deviceorientation', (e) => {
  view.injectDeviceOrientation({ alpha: e.alpha ?? 0, beta: e.beta ?? 0, gamma: e.gamma ?? 0 });
}, true);

view.lockCameraPositionOnTracking = true;     // follow the dot
view.lockCameraOrientationOnTracking = true;  // rotate with the device
view.addEventListener('trackingon', () => {});
view.addEventListener('trackingoff', () => {});
view.addEventListener('trackingchanged', () => {});  // lock flags changed (user moved the camera, etc.)
console.log(view.latestTrackedPosition);

view.allowTracking = false; // removes dot and circle
view.lockCameraPositionOnTracking = false; // not reset automatically
```
Gotchas:
- `injectTrackedPosition` **throws** (`InvalidTrackingStateError`) when `allowTracking` is false. The lock flags
  are a silent no-op in that case.
- The SDK provides no positioning: you feed WGS84 positions (indoor positioning system, GPS, simulation).
  No precision circle is shown without `precisionCircleRadius`.
- No "position changed" event: run your own logic (geofencing, reroute) in your feed callback.
- While navigating, the dot snaps to the route and progress updates (see 4.7 for drifting).
- The built-in compass button (`userTracking` UI part) cycles through off, follow position, and follow
  position + orientation. Any manual camera gesture unlocks it. Other tracking events: `positiontrackingstate`
  (`TrackingEvent.positionTrackingEnabled`).
- iOS requires a user gesture plus `DeviceOrientationEvent.requestPermission()` for orientation (browser API).

### 9.2 Geofencing (enter/leave a zone)
No geofence API. Test the tracked position against `surface.positions` in app code.

```ts
function inside(pt: Position, poly: Position[]): boolean {
  let r = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi, xj, yj] = [poly[i].longitude, poly[i].latitude, poly[j].longitude, poly[j].latitude];
    if ((yi > pt.latitude) !== (yj > pt.latitude) &&
        pt.longitude < ((xj - xi) * (pt.latitude - yi)) / (yj - yi) + xi) r = !r;
  }
  return r;
}
const zone = venue.pois.find((p) => p.id === 'ZONE-1')!;
let wasInside = false;
function onTick(pt: Position) {
  const now = zone.surfaces.some((s) => inside(pt, s.positions));
  if (now !== wasInside) {
    zone.surfaces.forEach((s) => venue.updateSurface(s, { color: now ? '#E74C3C' : 'initial' }));
    wasInside = now;
  }
}
```
Gotchas: 2D test that ignores altitude, so also compare the floor for multi-floor footprints. Proximity
variant: `venue.computeDistance(pt, surface) < 5`. Show a Marker (5.3) for promos or alerts.

---

## 10. Occupancy (real-time status)

### 10.1 Color rooms, desks or parking spots from a live feed
```ts
const STATUS: Record<string, Color> = { free: '#2ECC71', soon: '#F39C12', busy: '#E74C3C' };
function applyOccupancy(poiId: string, status: keyof typeof STATUS | null) {
  const p = venue.pois.find((x) => x.id === poiId);
  if (!p) return;
  p.surfaces.forEach((s) => venue.updateSurface(s, { color: status ? STATUS[status] : 'initial' }));
}
// e.g. socket.onmessage = (m) => { const { id, status } = JSON.parse(m.data); applyOccupancy(id, status); };
```
Gotchas: only POIs with surfaces can be colored (no single "set POI color" call). Build a `Map<id, POI>`
once if you update many POIs often. Revert with `'initial'` (not `undefined`). Combine with 2.6 (interactive)
and `poiclick` for booking. Keep the source of truth in your backend: the SDK holds no occupancy state.

---

## 11. Map server, auth token & URL parameters

### 11.1 Custom / self-hosted map server and authorization
```ts
const securedVenue = await visioOne.loadVenue({
  vg_maphash: 'YOUR_MAP_HASH',
  baseURL: 'https://maps.example.com/',  // default: https://mapserver.visioglobe.com/ (no auth support)
  authorizationToken: jwt,               // sent as "Authorization: Bearer <token>"
  disableCache: false,                   // true = bypass HTTP cache (map + icons + models)
}, container);
securedVenue.setAuthorizationToken(freshJwt); // before expiry; the integrator must refresh it in time
console.log(securedVenue.baseURL);           // e.g. icons at baseURL + 'icons/'
declare const jwt: string, freshJwt: string;
```
Gotchas:
- `baseURL` is read once. To switch servers: `destroyView` + `unloadVenue`, then `loadVenue` + `createView` again.
- Errors: `UnauthorizedError` (missing/invalid token), `VenueNotFoundError` (bad hash/baseURL),
  `MapHasExpiredError`, `InvalidLoadOptionsError`, and a generic `Error` for network failures.
- `disableCache` is cache-busting only. The SDK has **no offline cache** of map data (the code can be bundled
  but data needs the network).
- Never ship long-lived tokens in public pages. Mint short-lived tokens server-side.

### 11.2 URL parameters (read from the host page URL at load)
Type `URLParameters` lists them. URL values override code options.

| Parameter | Effect |
|---|---|
| `locale=fr` | initial locale |
| `dark` / `bright` | force UI color scheme (otherwise auto-detected since 1.0.3) |
| `orthographic`, `zenithal`, `lockPitch=45`, `zoomSpeed=2` | camera setup |
| `exploreMode=building` | initial explore mode |
| `focusOnPOI=<id>` | camera on a POI at start |
| `disableCameraOnClick` | no camera move on POI click |
| `origin=<id>`, `waypoint=<id>`, `destination=<id>` | open a route at load (share links / QR codes) |
| `defaultOrigin=<id or JSON Position>` | default origin without opening navigation (`navigationStartPoint` is deprecated) |
| `accentColor=rgb(252,3,15)`, `textAccentColor=...` | UI colors |
| `mirrorUI` | POI card on the right, floor/tracking selector on the left |
| `quality=low` | overrides `ViewCreateOptions.quality` |

Gotchas: `vg_maphash` also works as a URL parameter (not part of the `URLParameters` type) and **overrides
the hash in code**. Through 1.0.5 the generic name `hash` could be hijacked by third-party query params
(cache-busting dev servers). Control the host page URL, especially in WebViews.

---

## 12. Cross-cutting pitfalls (checklist)

1. `vg_maphash`, not `hash`. Pass a `loaderContainer` in strict TS.
2. Root typings broken in 1.0.9: use type-only deep imports. Error classes cannot be imported: use `constructor.name`.
3. Test `createView` on your real map (`labelSizePolicy` issue, 1.0.6–1.0.9).
4. `goToFloor(poi.floor)` before `goToPOI`. Sync floor UI only from `currentfloorchanged.newFloor`.
5. POI = container. No name/position fields. Filter non-navigable POIs from route pickers.
6. Reset sentinels: `color: 'initial'`, `hoverColor/selectionColor: 'default'`.
7. Labels: always set `height`, and update `width` + `height` together. Rotation is create-only.
8. Remove navigation with **both** `view.removeCurrentNavigationTrace()` and `venue.removeNavigationTrace(trace)`.
9. `refreshCustomData()` before `getPOICustomData`, and catch its rejection.
10. `allowTracking = true` before `injectTrackedPosition`. There is no automatic reroute: handle `navigationtoofarfromtrackedposition`.
11. Runtime locales are not persisted and never translate map content.
12. No runtime surface creation, no POI clustering, no offline data cache, no "closest" multi-destination strategy.
13. In mobile WebViews loading from `file://`, ES module imports can fail on CORS: prefer the UMD build
    (`dist/visioone.umd.cjs`) or serve from an HTTP(S) origin.

<!-- VERIFICATION
Checked against @visioglobe/visioone 1.0.9, dist/src/ (paths relative to dist/src/VisioOne/ unless noted).
All ```ts snippets were extracted and compiled with tsc (strict, skipLibCheck) against these .d.ts: 0 errors.
Negative test confirmed tsc rejects: hash, useOrthographicCamera, inactiveColor, LabelUpdateOptions.rotation,
NavigationRequest.displayMode, getPOIById. Root import: createVisioOne() is `any` with skipLibCheck, TS2307 without.

Entry / runtime exports:
- createVisioOne, VisioOne (default) ............ ../visioOne.d.ts (imports missing ./VisioOneImplementation/Venue/VisioOne), VisioOne/index.d.ts
- runtime exports verified in dist/visioone.js: VisioOne, createVisioOne, default (no error classes)

Venue/VisioOne.d.ts: loadVenue, unloadVenue, showError, showLoader, createView, destroyView, version
Venue/LoadOptions.d.ts: vg_maphash, baseURL, disableCache, authorizationToken
Venue/ViewCreateOptions.d.ts: zoomSpeed, cameraProjection, zenithalMode, lockPitch, focusOnPOI, disableCameraOnClick, enableShadows, quality
Venue/Venue.d.ts: baseURL, venueLayout, currentLocale, setCurrentLocale, createPOI, removePOI, createImage, createLabel, createLine, createMarker, createCategory, removeImage, removeLabel, removeLine, removeMarker, removeCategory, updatePOI, updateImage, updateLabel, updateLine, updateSurface, updateMarker, modalities, attributes, computeNavigation, computeNavigationMultiDestination, updateNavigationTrace, createNavigationTrace, removeNavigationTrace, pois, categories, translator, getPOICustomData, refreshCustomData, setAuthorizationToken, computeDistance
Venue/VenueLayout.d.ts: outside, buildings
Venue/Building.d.ts: id, floors, defaultFloorID
Venue/Floor.d.ts: id, altitude, levelIndex
Venue/Category.d.ts: id
Venue/POI.d.ts: id, floor, images, labels, lines, surfaces, markers, categories
Venue/POICreateOptions.d.ts: id, floor, categories ; Venue/POIUpdateOptions.d.ts: categories
Venue/Image.d.ts, ImageCreateOptions.d.ts, ImageUpdateOptions.d.ts: poi, position, width, height, rotation, url, orientationType, isVisible
Venue/OrientationType.d.ts: 'fixed' | 'flat' | 'facing'
Venue/Label.d.ts, LabelCreateOptions.d.ts, LabelUpdateOptions.d.ts: poi, position, width, height, text, color, rotation (create only), isVisible (update)
Venue/Marker.d.ts, MarkerCreateOptions.d.ts, MarkerUpdateOptions.d.ts: poi, position, element, isForeignMarker, isVisible (update: position, isVisible only)
Venue/Line.d.ts, LineCreateOptions.d.ts, LineUpdateOptions.d.ts: poi, positions, thickness, color, displayMode, texture ('#halo'), animationSpeed, textureRepeat, zOffset, isVisible (update)
Venue/LineDisplayMode.d.ts: 'textured' | 'halo' | 'progress' | 'progressOutline'
Venue/Surface.d.ts: poi, positions, isInteractive, color ('initial'), hoverColor, selectionColor, extrusionHeight, isFromBundle, isVisible
Venue/SurfaceUpdateOptions.d.ts: color | 'initial', isInteractive, hoverColor | 'default', selectionColor | 'default', extrusionHeight, isVisible, opacity
Venue/URLParameters.d.ts: dark, bright, locale, orthographic, zoomSpeed, zenithal, origin, waypoint, destination, accentColor, textAccentColor, exploreMode, lockPitch, focusOnPOI, disableCameraOnClick, mirrorUI, navigationStartPoint (deprecated), defaultOrigin, quality
Venue/Errors/*.d.ts: VenueNotFoundError, UnauthorizedError, MapHasExpiredError, InvalidLoadOptionsError, POIAlreadyExistsError, POINotFoundError, InvalidColorError (CategoryNotFoundError, ImageNotFoundError, InvalidItemError, InvalidLoadOptionsError, LabelNotFoundError, SurfaceNotFoundError are not re-exported by Venue/index.d.ts)
Navigation/Errors/*.d.ts: RouteNotFoundError, SourceOutOfLimitError, DestinationOutOfLimitError, InvalidNavigationRequestError
View/Errors/*.d.ts: InvalidTrackingStateError

Core/Position.d.ts: latitude, longitude, altitude ; Core/Color.d.ts: Color ; Core/ForeignMarkerScreenPosition.d.ts: left, top, z, isVisible

Navigation/NavigationRequest.d.ts: origin, destination, type, isAccessible, firstNodeAsIntersection, mergeFloorChangeInstructions, excludedModalities, excludedAttributes, POIOrIDOrPosition
Navigation/NavigationRequestMultiDestination.d.ts: origin, destinations, optimize (+ same options)
Navigation/NavigationRequestType.d.ts: 'shortest' | 'fastest'
Navigation/Navigation.d.ts: request, instructions
Navigation/NavigationInstruction.d.ts: segmentPositions, iconPosition, modality, floor, length, duration, maneuverType, detailedInstruction, attributes, waypointIndex
Navigation/ManeuverType.d.ts: changeModality, changeFloor, goDown, goUp, waypoint, goStraight, turnGentleLeft, turnGentleRight, turnRight, turnLeft, turnSharpRight, turnSharpLeft, end
Navigation/NavigationTrace.d.ts: navigation, index, percentageOfDistanceCovered, textureRepeat, displayMode, animationSpeed, thickness, sceneElements; NavigationSceneElements: lineProgress, lineProgressOverlay, lineProgressOutline, lineProgressDisabled, lineProgressDisabledOverlay, linePreview, linePreviewOutline, linePreviewOverlay, dot, startMarker, endMarker
Navigation/NavigationTraceUpdateOptions.d.ts: progressColor, progressOutlineColor, progressFutureColor, progressOverlayColor, progressDisabledOverlayColor, progressDisabledColor, previewColor, previewOutlineColor, previewOverlayColor, textureRepeat, animationSpeed

View/View.d.ts: UIPart ('floorSelector'|'navigation'|'poiDetails'|'search'|'userTracking'), showUI, isUIPartVisible, setUIPartVisible, quality {tier, recommendedTier, mismatch}, hoverEnabled, surfaceHoverColor ('highlight'), selectionEnabled, surfaceSelectionColor, accentColor, textAccentColor, themes, setTheme, addEventListener, removeEventListener, currentExploreMode, currentBuilding, currentFloor, selectedPOIs, currentNavigationTrace, cameraProjection, camera, zenithalModeEnabled, disableCameraOnClick, setZenithalMode, lockPitch, setCameraDefaultAnimationOptions, goToGlobal, goToBuilding, goToFloor, goToPOI, goToViewpoint, currentNavigationInstruction, navigationStartPoint, setDefaultOrigin, setCurrentNavigationTrace, removeCurrentNavigationTrace, setCurrentNavigationInstruction, navigateToNextInstruction, navigateToPreviousInstruction, allowTracking, lockCameraOrientationOnTracking, lockCameraPositionOnTracking, injectTrackedPosition, updatePositionTrackerGraphicOptions, injectDeviceOrientation, latestTrackedPosition
View/Camera.d.ts: position, target, pitch, heading, minimumAltitude, maximumAltitude, minimumRadius, maximumRadius, minimumPitch, maximumPitch, panEnabled, zoomEnabled, rotationEnabled, pitchEnabled
View/CameraProjection.d.ts: 'perspective' | 'orthographic'
View/ExploreMode.d.ts: 'global' | 'building' | 'floor'
View/EventType.d.ts: poiclick, poidblclick, poimousedown, poimouseup, poimouseover, poimouseout, selectedpoischange, currentfloorchanged, navigationstarted, navigationstopped, navigationtoofarfromtrackedposition, navigationinstructionreached, positiontrackingstate, trackingon, trackingoff, trackingchanged, foreignmarkerupdated, exploremodechanged, qualityrecommendation
View/AnimationOptions.d.ts: duration, easing, padding, orientation ; View/OrientationOptions.d.ts: heading, pitch ('initial') ; View/Padding.d.ts: top, right, bottom, left
View/AnimationPromise.d.ts: isCanceled, cancel
View/ViewpointParameters.d.ts: positions, targetAltitude
View/DeviceAngles.d.ts: alpha, beta, gamma
View/PositionTrackerOptions.d.ts: position, precisionCircleRadius ; View/PositionTrackerGraphicOptions.d.ts: color, opacity
View/Events/POIEvent.d.ts: eventType, originalEvent, venue, view, pois, coordinate
View/Events/VenueEvent.d.ts: newBuilding, oldBuilding, newFloor, oldFloor
View/Events/ExploreModeEvent.d.ts: currentExploreMode
View/Events/NavigationEvent.d.ts: navigation, navigationTrace
View/Events/TrackingEvent.d.ts: positionTrackingEnabled, view
View/Events/ForeignMarkerEvent.d.ts: poi, marker, screenPosition (exported only via View/Events/index.d.ts)
View/Events/QualityRecommendationEvent.d.ts: applied, recommended (exported only via View/Events/index.d.ts)

Content/Translator.d.ts: allLocales, translatePOI, translateFloor, translateBuilding, translateCategory, translate, addLocale, removeLocale, getLocale, Context, Resources
Content/POILocaleEntry.d.ts: name, categories, description, url ; Content/VenueLocaleEntry.d.ts: name, shortName, description ; Content/CategoryLocaleEntry.d.ts: name, icon
Content/CustomData.d.ts: CustomData
Content/LocaleUIStrings.d.ts: 'search-for-anything', 'until', 'poi-info-placeholder-1', 'itinerary-from-to', 'around-in-*', 'no-result-for', ...
Content/NavigationInstructionsStrings.d.ts: maneuvers, modalities, duration, detailedInstructions (DetailedInstructionsSentences: goStraightWithDuration*, endAtPOI, endAtDefinedPosition)

DROPPED / CORRECTED (used in docs, absent from or different in 1.0.9):
- LoadOptions.hash -> vg_maphash (renamed 1.0.6; NPM.md, Venue.md, View/UI.md still use `hash`)
- ViewCreateOptions.useOrthographicCamera (View/Camera.md) -> cameraProjection: 'orthographic'
- NavigationRequest.displayMode / NavigationRequestMultiDestination.displayMode (Navigation.md) -> absent
- NavigationTrace.color / overlayColor / inactiveColor / inactiveOverlayColor (Navigation.md) -> absent; use NavigationTraceUpdateOptions
- venue.removeNavigationTrace(navigationRequest) (Navigation.md) -> takes a NavigationTrace
- LineCreateOptions.inactiveColor (Venue/POIs/Line.md) -> absent (commented out in .d.ts)
- Translator.createCategoryLocaleEntry (Conventions.md) -> absent
- hoverColor: 'initial' (Conventions.md) -> documented sentinel is 'default' for hoverColor/selectionColor; 'initial' only for color (compiles anyway since Color = string)
- Image url "relative to /images, no extension" (Venue/POIs/Image.md) -> .d.ts: relative to baseURL
- DetailedInstructionsSentences combined keys (goUpThenGoStraight, turnLeftThenChangeModality, changeModalityThenChangeModality, changeFloorThenGoUp) (Venue/TranslateSdkKeys.md) -> absent from interface
- view.navigationStartPoint / ?navigationStartPoint (Samples/Demo/Kiosk.md) -> still present but deprecated; use setDefaultOrigin / defaultOrigin
- Venue.createSurface / removeSurface -> absent (SurfaceCreateOptions.d.ts exists but is unused and not exported)
- Venue.getPOIById, POI.name, trackedpositionchanged event -> never existed
-->
