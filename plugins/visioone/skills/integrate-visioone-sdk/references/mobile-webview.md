# Embedding VisioOne in a mobile app (WebView + native↔JS bridge)

VisioOne (`@visioglobe/visioone`, 1.1.0) is a JS/WebGL SDK. There is **no native iOS/Android/Flutter/RN SDK**:
every mobile integration hosts a small HTML page that runs the SDK inside a WebView, and the app talks
to it through a bridge. The SDK API inside the page is exactly the web API
(`createVisioOne()` → `loadVenue()` → `createView()`); there is no "mobile variant".

Reference implementations (public example repos, one complete app per platform; read the one matching
the project for anything this file only sketches):

| Platform | Repo | SDK in the page |
|---|---|---|
| Android (Kotlin, Compose) | https://github.com/visioglobe-sas/VisioOneMeetAndroid | web bundle built with Vite |
| iOS (Swift, SwiftUI) | https://github.com/visioglobe-sas/VisioOneMeetIos | vendored SDK (UMD) |
| Flutter (`webview_flutter`) | https://github.com/visioglobe-sas/VisioOneMeetFlutter | vendored SDK (UMD) |
| React Native (`react-native-webview`) | https://github.com/visioglobe-sas/VisioOneMeetReactNative | SDK from the CDN (ESM) |

The same features without a WebView (SDK running directly in the DOM): https://github.com/visioglobe-sas/VisioOneMeetVueJS.
Each repo documents its features one by one in `docs/features/*.md`. Check the SDK version a repo pins
before reusing its code: if it differs from the targeted one, the TypeScript declarations win on API.

---

## 1. Architecture

### 1.1 Two layers

A native shell (hosts the WebView, loading/ready/error UI, native controls) and a web page (loads the
SDK, exposes commands, forwards SDK events).
Rule shared by all four repos: **native never touches `venue`/`view` directly.** The page exposes a
small, stable command surface (`window.MapBridge.<method>(...)` or a message `switch`), resolves ids to
SDK objects (`venue.pois.find(...)`) on the JS side, and sends back only plain JSON
(`{ id, name }`, never a live `POI` object: SDK objects have circular refs and methods and cannot
cross the bridge).

### 1.2 Which SDK build, and how the page is served

| Platform | SDK build | How it gets into the app | How the page is loaded |
|---|---|---|---|
| Android (native) | ESM, bundled with **Vite** (`base: './'`, `outDir` = `app/src/main/assets/www`) | Build output committed in `assets/www/`; rebuild manually with `npm run build` (Gradle does not run it) | `WebViewAssetLoader` → `https://appassets.androidx.local/assets/www/index.html?vg_maphash=…` |
| iOS (native) | **UMD** `dist/visioone.umd.cjs` (~8 MB, CSS/assets inlined), vendored as-is, no bundler | `WebContent/` **folder reference** (not a group) next to `map.html` | `webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())` |
| Flutter | **UMD** `visioone.umd.cjs`, vendored | `assets/www/` declared in `pubspec.yaml` | `WebViewController.loadFlutterAsset('assets/www/map.html')` |
| React Native | ESM, `import()`-ed at runtime from the public CDN (`https://cdn.visioglobe.com/visioone/1.1.0/dist/visioone.js`) | HTML shipped as a TS template-literal string | `<WebView source={{ html, baseUrl: 'https://cdn.visioglobe.com/' }} />` |

Why: the ESM build (`dist/visioone.js`) is a tiny entry that dynamically `import()`s large chunks.
Under `file://`, WebKit (and Chromium) block ES-module loading for CORS reasons, so the map silently
never loads. Two working answers:

- serve the page from a real/synthetic **https origin** (Android `WebViewAssetLoader`, RN `baseUrl`), or
- use the **UMD** build via a classic `<script src="visioone.umd.cjs">` (not `type="module"`), which
  works whatever the origin (`file://`, `https://`, Flutter's internal origin). This is the safest
  default for a new integration, especially cross-platform (Flutter, one page for both OSes).

To refresh the vendored UMD bundle:

```bash
npm pack @visioglobe/visioone@1.1.0
tar xzf visioglobe-visioone-*.tgz
cp package/dist/visioone.umd.cjs <web-assets-dir>/visioone.umd.cjs
```

### 1.3 JS entry point (host page)

UMD variant (iOS / Flutter; the UMD global is `VisioOne`):

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <style>html, body, #container { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #000; }</style>
</head>
<body>
  <div id="container"></div>
  <script src="visioone.umd.cjs"></script>
  <script>
    var visioOne = VisioOne.createVisioOne();
    var container = document.getElementById('container');
    var venue = null, view = null;
    var hash = new URLSearchParams(window.location.search).get('vg_maphash') || 'YOUR_MAP_HASH';

    visioOne.loadVenue({ vg_maphash: hash }, container)
      .then(function (v) { venue = v; return visioOne.createView(container, venue); })
      .then(function (v) {
        view = v;
        view.addEventListener('poiclick', onPoiClick);
        postToNative('ready');
      })
      .catch(function (error) {
        visioOne.showError(error, container);           // SDK's own error rendering
        postToNative('error', String(error && error.message || error));
      });
  </script>
</body>
</html>
```

ESM variant (Android/Vite, `web/src/main.js`):

```js
import { createVisioOne } from '@visioglobe/visioone';

const params = new URLSearchParams(window.location.search);
const hash = params.get('vg_maphash') || 'YOUR_MAP_HASH';
const container = document.querySelector('#content');
const bridge = window.AndroidBridge;   // injected by addJavascriptInterface; undefined in a desktop browser
let venue = null, view = null;

async function main() {
  try {
    const visioOne = createVisioOne();
    venue = await visioOne.loadVenue({ vg_maphash: hash });
    view = await visioOne.createView(container, venue);
    view.addEventListener('poiclick', onPoiClick);
    bridge?.onMapReady();
  } catch (error) {
    bridge?.onMapError(String(error?.message ?? error));
  }
}
main();
```

Notes:
- `vg_maphash` replaced `hash` in 1.0.6, both as a `loadVenue` option and as a URL parameter. There is
  no alias: an old `hash` key is ignored and loading fails ("Cannot load the venue").
- The SDK **merges page-URL query params into `loadVenue` options, and the URL wins**
  (`?vg_maphash=`, `?baseURL=`, exact case). Android/iOS pass the hash (and base URL) in the page URL,
  read them in the page and forward them explicitly to `loadVenue`; Android's `?baseUrl=` key is read
  only by its page, not by the SDK. Corollary:
  never serve the host page with query params you don't control.
- `baseURL` defaults to `https://mapserver.visioglobe.com/`; map data is fetched at runtime, so the
  device needs network access. First cold load can take 20–30 s on an emulator (large JS chunk + map
  assets + WebGL init): a long spinner is not a hang.
- `baseURL`/hash are `loadVenue` options, not live properties: changing them means reloading the venue
  (`destroyView` + `unloadVenue` + new `loadVenue`, as Flutter's `setup()` does) or recreating the WebView.

---

## 2. Bridge contract

### 2.1 Mechanisms per platform

| | Native → JS | JS → Native | Native receives on |
|---|---|---|---|
| Android | `webView.evaluateJavascript("window.MapBridge.x(<json>)", null)` | `webView.addJavascriptInterface(obj, "AndroidBridge")` + `@JavascriptInterface` methods; JS calls `window.AndroidBridge.onX(jsonString)` | **a background (JavaBridge) thread** |
| iOS | `webView.evaluateJavaScript(...)`, or `callAsyncJavaScript(_:arguments:in:in:)` (iOS 14+) for awaited Promises / real JS arguments | `WKUserContentController.add(handler, name: "mapBridge")`; JS calls `window.webkit.messageHandlers.mapBridge.postMessage({...})` | main thread |
| Flutter | `WebViewController.runJavaScript("window.MapBridge.x(<json>)")` | `addJavaScriptChannel('VisioOneBridge', onMessageReceived: ...)`; JS calls `VisioOneBridge.postMessage(JSON.stringify({...}))` | root Dart isolate (safe to `setState`) |
| React Native | `webRef.current.postMessage(JSON.stringify({type, data}))` (alternative: `injectJavaScript("...; true;")`) | `window.ReactNativeWebView.postMessage(JSON.stringify({...}))` → `<WebView onMessage>` | JS thread (`event.nativeEvent.data`, a string) |

### 2.2 Message format

- **Native → JS, Android/iOS/Flutter:** one JS function per command on `window.MapBridge`. Arguments are
  **JSON-encoded on the native side and interpolated as JS literals**: Kotlin `JSONObject.quote(id)` /
  `JSONArray` / `JSONObject`, Swift `JSONSerialization.data(withJSONObject:options:[.fragmentsAllowed])`,
  Dart `jsonEncode`. The JS function therefore receives real JS values: **never `JSON.parse` them
  again** (Flutter hit this: `JSON.parse("k5f…")` threw, nothing caught it, the app sat on the loading
  screen forever without `ready` or `error`). Never build the script with raw string concatenation
  (`'goToPOI(\'' + id + '\')'`): that's a JS-injection vector.
- **Native → JS, React Native:** a single `{type, data}` JSON envelope, dispatched by a `switch(evt.type)`
  in the page (`setup`, `select_place`, `clear_place`, ...).
- **JS → Native:**
  - Android: one `@JavascriptInterface` method per event, primitives/Strings only; structured payloads
    are passed as a JSON string (`onPoiClick(JSON.stringify(pois))`).
  - iOS: `{ type, message }` object posted as-is (body arrives as `[String: Any]`; only
    property-list types: always `as?`, never force-cast).
  - Flutter / RN: `JSON.stringify({ type, data })`. Flutter parses defensively and ignores malformed
    input; the RN repo calls `JSON.parse` unguarded: wrap it (see React Native gotchas).
  - The public guide recommends a single `{type, data}` envelope as the default JS→native pattern.

### 2.3 Readiness handshake

The SDK is "ready" only after `createView()` resolves. Native must not send map commands before that:
bridge commands check that `venue` (and `view` when they need it) exist before doing anything, so they
are silent no-ops until loading is done, and native UI
only enables controls after the `ready` event.

| Platform | Who starts the load | Ready signal |
|---|---|---|
| Android | Page itself, on load, reading `?vg_maphash=` from its URL | `AndroidBridge.onMapReady()` / `onMapError(msg)` |
| iOS | Page itself, on load (hash from `?vg_maphash=` or a default) | `postMessage({type:'ready'})` / `{type:'error', message}` |
| Flutter | Native: `onPageFinished` → `runJavaScript("window.MapBridge.setup(<hash>, <baseURL>)")` | `{type:'loading'}` then `{type:'ready'}` / `{type:'error', data:{message}}` (+ a `pageReady` on `DOMContentLoaded`) |
| RN | Native: `onLoadEnd` → `setTimeout(500)` → `postMessage({type:'setup', data:{hash, baseURL}})` | `{type:'ready', data:{buildings, currentFloorId, ...}}` / `{type:'error', data:'Name: message'}` |

Pitfalls:
- A native→JS message sent **before the JS listener exists is lost silently**. RN mitigates by
  registering `window.addEventListener('message', ...)` synchronously, *before* the async SDK `import()`
  resolves, and making `setup` `await` that import; the 500 ms delay is a heuristic, not a guarantee.
  A more robust handshake, used in the React Native skeleton below (not in the repo): the page posts `page_loaded` once its
  listeners exist → native then sends `setup`.
- Push initial state with `ready` (floors, current floor, explore mode) rather than making native
  query for it; then keep it in sync with SDK events (`currentfloorchanged`, `exploremodechanged`),
  which also fire when the SDK's own UI or camera interaction changes state.
- Prefer **one native→JS message per user intent** and chain multi-step SDK calls in JS
  (e.g. `goToFloor(poi.floor).then(() => goToPOI(poi))`) instead of 2–3 bridge round-trips.

### 2.4 Request/response

`evaluateJavascript`/`runJavaScript` don't await Promises. Patterns used:
- **requestId + event**: native calls `MapBridge.loadCustomData(requestId, poiId)`; JS answers with
  `onCustomDataLoaded(requestId, json)` / `{type:'customDataLoaded', data:{requestId, ...}}`.
- **result event keyed by the object id** (RN): `{type:'poi_custom_data_result', data:{placeId, ...}}`;
  simpler, but concurrent requests for the same id cannot be told apart.
- **synchronous return value** (iOS): for non-Promise results, read the value passed to the
  `evaluateJavaScript` completion handler (`getCategories`, position/polygon lookups).
- **iOS only**: `callAsyncJavaScript("return await window.MapBridge.loadCustomData(poiId);", arguments: ["poiId": id], in: nil, in: .page)` awaits the Promise, with real JS arguments.
- Return explicit statuses (`{status:'created'|'duplicate'|'notFound'|'error', message}`) instead of
  letting a JS exception escape.

### 2.5 Error handling

- Wrap the whole bootstrap in `try/catch` (or `.catch`) and **always** emit `error` with the real
  message, otherwise native shows an infinite spinner. RN additionally captures the SDK's
  `console.warn('VisioOne error:', err)` during load because the thrown error is a generic
  "Cannot load the venue"; Flutter adds `window.onerror` → `error`.
- SDK calls that can throw (`computeNavigation`, `createPOI`, `setCurrentLocale`, `createLabel`, ...):
  `try/catch` in JS and report `{status:'error', message}` / `onNavigationError(msg)`.
- Native side: log `evaluateJavaScript` completion errors (iOS); wrap `runJavaScript` in `try/catch`
  (Flutter `_run`); parse incoming JSON defensively.
- Unknown ids: navigation-style commands (`goTo…`, highlight) silently no-op in all repos; create/resolve
  commands report a status (`notFound`, `anchor-not-found`, an `…_error` event). Add a channel back
  wherever your UI needs to know.

### 2.6 Threading

- **Android:** `@JavascriptInterface` methods run on a background thread. Re-post every UI/state
  update: `Handler(Looper.getMainLooper()).post { ... }`. Forgetting it gives intermittent
  `CalledFromWrongThreadException`. `evaluateJavascript` must be called from the UI thread.
- **iOS:** `WKScriptMessageHandler` callbacks arrive on the main thread; call `evaluateJavaScript`
  on the main thread.
- **Flutter:** channel callbacks are delivered on the root isolate; `setState` directly. `runJavaScript`
  is async, `await` it before assuming it ran.
- **RN:** `onMessage` runs on the JS thread; call parent callbacks from the event handler, not during render.

---

## 3. Minimal skeletons (load page, send `goToPOI`, receive `poiclick`)

### 3.1 Android (Kotlin, Compose)

`web/vite.config.js`:

```js
import { defineConfig } from 'vite';
export default defineConfig({
  base: './', // served under https://appassets.androidx.local/assets/www/: keep paths relative
  build: { outDir: '../app/src/main/assets/www', emptyOutDir: true },
});
```

`web/src/main.js` (add to the ESM entry of §1.3):

```js
let selectedPoi = null;

window.MapBridge = {
  goToPOI(poiId) {                       // already a JS string: no JSON.parse
    if (!venue || !view) return;
    const poi = venue.pois.find((p) => p.id === poiId);
    if (!poi) return;
    selectedPoi = poi;
    view.goToFloor(poi.floor).then(() =>
      view.goToPOI(poi, { orientation: { pitch: 20 }, padding: { top: 100, right: 100, bottom: 100, left: 100 } }));
    poi.surfaces.forEach((s) => venue.updateSurface(s, { selectionColor: view.surfaceSelectionColor }));
  },
};

function onPoiClick(event) {
  const locale = venue.currentLocale;
  const pois = event.pois.map((poi) => ({
    id: poi.id,
    name: venue.translator.translatePOI(poi, locale).name || poi.id,
  }));
  bridge?.onPoiClick(JSON.stringify(pois));     // event.pois is an array
}
```

Kotlin:

```kotlin
// build.gradle: implementation("androidx.webkit:webkit:<version>")
// AndroidManifest: <uses-permission android:name="android.permission.INTERNET" />
private const val ASSET_DOMAIN = "appassets.androidx.local"

private class MapBridge(
    private val onReady: () -> Unit,
    private val onError: (String) -> Unit,
    private val notifyPoiClick: (String) -> Unit,   // don't name it like the method (Kotlin recursion error)
) {
    @JavascriptInterface fun onMapReady() = onReady()
    @JavascriptInterface fun onMapError(message: String) = onError(message)
    @JavascriptInterface fun onPoiClick(payload: String) = notifyPoiClick(payload)
}

@Composable
fun VisioOneMap(mapHash: String, onWebView: (WebView) -> Unit, onPoiClick: (String) -> Unit) {
    val mainHandler = remember { Handler(Looper.getMainLooper()) }
    var ready by remember { mutableStateOf(false) }
    AndroidView(modifier = Modifier.fillMaxSize(), factory = { context ->
        val assetLoader = WebViewAssetLoader.Builder()
            .setDomain(ASSET_DOMAIN)
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(context))
            .build()
        WebView(context).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            if (BuildConfig.DEBUG) WebView.setWebContentsDebuggingEnabled(true)
            // Must be registered BEFORE loadUrl
            addJavascriptInterface(MapBridge(
                onReady = { mainHandler.post { ready = true } },
                onError = { msg -> mainHandler.post { /* show error */ } },
                notifyPoiClick = { json -> mainHandler.post { onPoiClick(json) } },
            ), "AndroidBridge")
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
                    assetLoader.shouldInterceptRequest(request.url)
            }
            loadUrl("https://$ASSET_DOMAIN/assets/www/index.html?vg_maphash=" +
                URLEncoder.encode(mapHash, "UTF-8"))
        }.also(onWebView)
    })
}

// Native -> JS (UI thread, only after onMapReady)
fun WebView.goToPOI(poiId: String) =
    evaluateJavascript("window.MapBridge.goToPOI(${JSONObject.quote(poiId)})", null)
```

### 3.2 iOS (Swift, SwiftUI, WKWebView)

`map.html` = §1.3 UMD page, plus:

```js
function postToNative(type, message) {
  var h = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.mapBridge;
  if (!h) { console.log('[VisioOne:web]', type, message); return; }
  h.postMessage({ type: type, message: message });
}
function onPoiClick(event) {
  var poi = event.pois && event.pois[0];
  if (!poi) return;
  postToNative('poiSelected', { id: poi.id, name: venue.translator.translatePOI(poi, venue.currentLocale).name || null });
}
window.MapBridge = {
  goToPOI: function (poiId) {
    if (!venue || !view) return;
    var poi = venue.pois.find(function (p) { return p.id === poiId; });
    if (!poi) return;
    (poi.floor ? view.goToFloor(poi.floor) : Promise.resolve()).then(function () { view.goToPOI(poi); });
  },
};
```

Swift:

```swift
import SwiftUI
import WebKit

final class MapBridge: NSObject, WKScriptMessageHandler, ObservableObject {
    static let handlerName = "mapBridge"
    @Published private(set) var isReady = false
    @Published private(set) var tappedPOI: (id: String, name: String?)?
    weak var webView: WKWebView?

    func userContentController(_ ucc: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == Self.handlerName,
              let body = message.body as? [String: Any],
              let type = body["type"] as? String else { return }
        switch type {
        case "ready": isReady = true
        case "error": print("VisioOne error: \(body["message"] ?? "")")
        case "poiSelected":
            guard let p = body["message"] as? [String: Any], let id = p["id"] as? String else { return }
            tappedPOI = (id, p["name"] as? String)
        default: break
        }
    }

    func goToPOI(_ poiId: String) {
        guard let webView,
              let data = try? JSONSerialization.data(withJSONObject: poiId, options: [.fragmentsAllowed]),
              let json = String(data: data, encoding: .utf8) else { return }
        webView.evaluateJavaScript("window.MapBridge.goToPOI(\(json))") { _, error in
            if let error { print("goToPOI failed: \(error)") }
        }
    }
}

/// add(_:name:) retains its handler strongly: go through a weak proxy to avoid leaking the web view.
final class WeakScriptMessageHandler: NSObject, WKScriptMessageHandler {
    private weak var target: WKScriptMessageHandler?
    init(target: WKScriptMessageHandler) { self.target = target }
    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        target?.userContentController(c, didReceive: m)
    }
}

struct MapWebView: UIViewRepresentable {
    let bridge: MapBridge

    func makeUIView(context: Context) -> WKWebView {
        let ucc = WKUserContentController()
        ucc.add(WeakScriptMessageHandler(target: bridge), name: MapBridge.handlerName) // before creating the web view
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.userContentController = ucc

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = .black
        webView.scrollView.bounces = false
        #if DEBUG
        if #available(iOS 16.4, *) { webView.isInspectable = true }
        #endif
        if let url = Bundle.main.url(forResource: "map", withExtension: "html", subdirectory: "WebContent") {
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        bridge.webView = webView
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: ()) {
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: MapBridge.handlerName)
    }
}
```

To pass the hash at runtime, append `?vg_maphash=` with `URLComponents` to the `file://` URL; keep
`allowingReadAccessTo:` pointing at the original file's directory.

### 3.3 Flutter (`webview_flutter`)

`pubspec.yaml`: `webview_flutter`, `webview_flutter_android`, `webview_flutter_wkwebview`;
`flutter: assets: [assets/www/]` containing `map.html` + `visioone.umd.cjs` (same folder).

`assets/www/map.html` (UMD, the SDK is started by native via `setup`):

```js
var visioOne = null, venue = null, view = null;
var container = document.getElementById('container');

function sendToNative(type, data) {
  var ch = window.VisioOneBridge;
  if (!ch) { console.log('[VisioOne:web]', type, data); return; }
  ch.postMessage(JSON.stringify({ type: type, data: data }));
}
window.onerror = function (message) { sendToNative('error', { message: 'Uncaught JS error: ' + message }); };

window.MapBridge = {
  setup: function (hash, baseURL) {
    if (view) { visioOne.destroyView(view); view = null; }
    if (venue) { visioOne.unloadVenue(venue); venue = null; }
    visioOne = VisioOne.createVisioOne();
    visioOne.loadVenue(baseURL ? { vg_maphash: hash, baseURL: baseURL } : { vg_maphash: hash }, container)
      .then(function (v) { venue = v; return visioOne.createView(container, venue); })
      .then(function (v) {
        view = v;
        view.addEventListener('poiclick', function (e) {
          var poi = e.pois && e.pois[0];
          if (poi) sendToNative('poiSelected', { id: poi.id, name: venue.translator.translatePOI(poi, venue.currentLocale).name || null });
        });
        sendToNative('ready', null);
      })
      .catch(function (err) {
        visioOne.showError(err, container);
        sendToNative('error', { message: err && err.message ? err.message : String(err) });
      });
  },
  goToPOI: function (poiId) {
    if (!venue || !view) return;
    var poi = venue.pois.find(function (p) { return p.id === poiId; });
    if (poi) view.goToFloor(poi.floor).then(function () { view.goToPOI(poi); });
  },
};
```

Dart:

```dart
class VisioOneController {
  VisioOneController._(this.web);
  final WebViewController web;
  final _messages = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get messages => _messages.stream;

  static Future<VisioOneController> create() async {
    if (kDebugMode && WebViewPlatform.instance is AndroidWebViewPlatform) {
      await AndroidWebViewController.enableDebugging(true); // before creating the controller
    }
    final c = VisioOneController._(WebViewController());
    await c.web.setJavaScriptMode(JavaScriptMode.unrestricted);
    await c.web.setBackgroundColor(const Color(0xFF000000));
    await c.web.addJavaScriptChannel('VisioOneBridge', onMessageReceived: (m) {
      try {
        final decoded = jsonDecode(m.message);
        if (decoded is Map<String, dynamic> && decoded['type'] is String) c._messages.add(decoded);
      } catch (_) {/* ignore malformed */}
    });
    if (kDebugMode && c.web.platform is WebKitWebViewController) {
      await (c.web.platform as WebKitWebViewController).setInspectable(true);
    }
    return c;
  }

  Future<void> load(String hash) async {
    await web.setNavigationDelegate(NavigationDelegate(onPageFinished: (_) => setup(hash)));
    await web.loadFlutterAsset('assets/www/map.html');
  }

  Future<void> setup(String hash, {String? baseURL}) => _call('setup', [hash, baseURL]);
  Future<void> goToPOI(String poiId) => _call('goToPOI', [poiId]);

  Future<void> _call(String method, List<Object?> args) async {
    final script = 'window.MapBridge.$method(${args.map(jsonEncode).join(', ')})';
    try { await web.runJavaScript(script); } catch (e) { debugPrint('JS failed: $script ($e)'); }
  }

  void dispose() => _messages.close();
}

// Widget: WebViewWidget(controller: controller.web), listen to controller.messages:
// 'ready' -> hide spinner; 'error' -> show data['message'] + retry (call setup again);
// 'poiSelected' -> data['id'], data['name'].
```

### 3.4 React Native (`react-native-webview`)

Page (inline string, ESM from CDN):

```html
<div id="content" style="height:100vh"></div>
<script type="module">
  // Register the listener BEFORE the async import resolves, or the first 'setup' can be lost.
  const visioOneReady = import('https://cdn.visioglobe.com/visioone/1.1.0/dist/visioone.js')
    .then(({ createVisioOne }) => createVisioOne());
  let venue = null, view = null;
  const sendToNative = (evt) => window.ReactNativeWebView?.postMessage(JSON.stringify(evt));

  const setup = async (hash) => {
    try {
      const visioOne = await visioOneReady;
      const container = document.querySelector('#content');
      venue = await visioOne.loadVenue({ vg_maphash: hash }, container);
      view = await visioOne.createView(container, venue);
      view.addEventListener('poiclick', (e) => sendToNative({
        type: 'poi_click',
        data: { pois: (e.pois || []).map((p) => ({ id: p.id, name: p.labels?.[0]?.text || p.id, floorId: p.floor?.id })) },
      }));
      sendToNative({ type: 'ready' });
    } catch (error) {
      sendToNative({ type: 'error', data: error instanceof Error ? `${error.name}: ${error.message}` : String(error) });
    }
  };
  const goToPOI = async (poiId) => {
    if (!venue || !view) return;
    const poi = venue.pois.find((p) => p.id === poiId);
    if (!poi) return;
    await view.goToFloor(poi.floor);
    view.goToPOI(poi);
  };
  const onMessage = (event) => {
    try {
      const evt = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
      switch (evt.type) {
        case 'setup': setup(evt.data.hash); break;
        case 'select_place': goToPOI(evt.data.placeId); break;
        default: console.error('Unknown message type:', evt.type);
      }
    } catch (e) { console.error('Bad message from React Native', e); }
  };
  window.addEventListener('message', onMessage);   // iOS dispatches on window
  document.addEventListener('message', onMessage); // Android dispatches on document
  // Handshake: tell native the listeners are in place, so it can send 'setup' without guessing a delay.
  sendToNative({ type: 'page_loaded' });
</script>
```

TSX:

```tsx
import { useRef } from 'react';
import { WebView, WebViewMessageEvent } from 'react-native-webview';
import { visioOneHtml } from './visioOneHtml'; // the page above as a template literal

export function VisioMap({ hash, onPoiClick }: { hash: string; onPoiClick: (pois: any[]) => void }) {
  const webRef = useRef<WebView>(null);
  const send = (msg: object) => webRef.current?.postMessage(JSON.stringify(msg));
  const goToPlace = (placeId: string) => send({ type: 'select_place', data: { placeId } });

  const onMessage = (e: WebViewMessageEvent) => {
    let evt: any;
    try { evt = JSON.parse(e.nativeEvent.data); } catch { return; }
    if (evt.type === 'page_loaded') send({ type: 'setup', data: { hash } });
    else if (evt.type === 'ready') { /* enable controls; e.g. goToPlace('SOME_POI_ID') */ }
    else if (evt.type === 'error') { /* show evt.data */ }
    else if (evt.type === 'poi_click') onPoiClick(evt.data.pois);
  };

  return (
    <WebView
      ref={webRef}
      originWhitelist={['*']}
      source={{ html: visioOneHtml, baseUrl: 'https://cdn.visioglobe.com/' }} // see gotchas: baseUrl is required
      onMessage={onMessage}
      javaScriptEnabled
      domStorageEnabled
    />
  );
}
```

`injectJavaScript` alternative: `webRef.current?.injectJavaScript(\`window.MapBridge.goToPOI(${JSON.stringify(id)}); true;\`)`
(the trailing `true;` avoids silent failures on iOS).

---

## 4. Platform-specific gotchas

### Cross-platform
- **ESM under `file://` fails** (dynamic `import()` + CORS): UMD via classic `<script>`, or an https origin.
- **URL params override `loadVenue` options** (`?vg_maphash=`, `?baseURL=`). Before the 1.0.6 rename,
  a dev-server's cache-busting `?hash=` (React Native Metro, debug builds with `require('./page.html')`)
  silently replaced the map hash → `descriptor.json` 404 → "Hash not found".
- **Opaque origin breaks the SDK**: a page with origin `null` (RN `source={{ html }}` without
  `baseUrl`) throws `SecurityError: The operation is insecure` from the SDK's `localStorage`-based
  stats logger. Give the page a real origin. Keep `domStorageEnabled` on (Android/RN).
- **POI click payload**: `event.pois` is an array (stacked POIs); name via
  `venue.translator.translatePOI(poi, venue.currentLocale).name` can be empty, so fall back to `poi.id`.
- **`goToPOI` takes a `POI` object, not an id**, and does not change floor by itself: call
  `view.goToFloor(poi.floor)` first (SDK docs). Unknown ids → silent no-op.
- To clear a highlight use `venue.updateSurface(surface, { selectionColor: 'default' })` (documented value).
- The SDK has no pause/resume API: relay the **WebView's own lifecycle** (pause rendering when
  backgrounded). None of the example repos implement this, nor hardware back handling inside the
  WebView: design it yourself.
- Debug: Android `chrome://inspect`, iOS Safari → Develop (needs `isInspectable` on iOS 16.4+), Flutter
  `setOnConsoleMessage` relays `console.*` to `flutter run` output.
- Security: bridge objects are callable by **any** JS in the WebView: only load content you control,
  expose the minimum surface, JSON-encode every argument.
- Keep the `poiDetails` UI part hidden (`view.setUIPartVisible('poiDetails', false)`) if native handles
  POI taps: native cannot synchronously intercept/cancel SDK default behavior across the bridge.

### Android (native)
- Never `loadUrl("file:///android_asset/www/index.html")` with the Vite/ESM bundle: module imports fail
  silently. Use `WebViewAssetLoader` (`https://appassets.androidx.local/assets/...`) + `shouldInterceptRequest`.
- Vite `base: './'` so asset paths stay relative under `/assets/www/`.
- `addJavascriptInterface` **before** `loadUrl`. Only `@JavascriptInterface` methods are visible;
  parameters must be primitives/Strings. Callbacks are off the UI thread.
- Use optional chaining (`window.AndroidBridge?.x()`) so the page still runs in a desktop browser (`npm run dev`).
- Manifest: `INTERNET` permission, `android:hardwareAccelerated="true"` (WebGL), and
  `configChanges="orientation|screenSize|screenLayout|keyboardHidden"` so rotation/keyboard don't
  recreate the Activity (and reload the map).
- Settings used: `javaScriptEnabled`, `domStorageEnabled`, `mediaPlaybackRequiresUserGesture = false`.
- Recreating the WebView (e.g. Compose `key(hash, baseUrl)`) is the simple way to switch map/server.
- Keep `minSdk` ≥ 17 (`@JavascriptInterface` reflection vulnerability below that; the repo uses 26).
- Kotlin: don't give a constructor callback the same name as its `@JavascriptInterface` method.

### iOS (native)
- Use `loadFileURL(_:allowingReadAccessTo:)`, not `load(URLRequest)`, so WebKit can read the sibling
  `visioone.umd.cjs`.
- Add `WebContent` as a **folder reference** (blue folder / XcodeGen `type: folder`,
  `buildPhase: resources`), else files are flattened. **Never name the folder `Resources`**: install
  fails with a misleading "Info.plist does not contain a valid CFBundleVersion".
- With `GENERATE_INFOPLIST_FILE`, set `CURRENT_PROJECT_VERSION` and `MARKETING_VERSION`.
- `WKUserContentController.add` retains the handler strongly → weak proxy + remove it in `dismantleUIView`.
- Register the handler on the configuration **before** creating the `WKWebView`.
- `message.body` is property-list only (dictionaries, arrays, strings, numbers, `NSNull`).
- `evaluateJavaScript` does not await Promises: use `callAsyncJavaScript` (iOS 14+) when you need a result.
- No Info.plist entries/ATS exceptions needed for the map: data is HTTPS from `mapserver.visioglobe.com`.
- Config used: `allowsInlineMediaPlayback = true`, `isOpaque = false` + black background (avoids white
  flash), `scrollView.bounces = false`.

### Flutter
- `map.html` and `visioone.umd.cjs` must sit in the same asset folder (relative `<script src>`).
- `AndroidWebViewController.enableDebugging(true)` must run **before** creating the `WebViewController`.
- Start the SDK from `onPageFinished` (calling `setup` earlier hits an undefined `MapBridge`).
- Don't `JSON.parse` arguments in `MapBridge.*`: `jsonEncode` already produced JS literals.
- Re-calling `setup()` must `destroyView` + `unloadVenue` first.
- A malformed channel message must never crash the app: `tryParse` and drop it.

### React Native
- Load the page as `source={{ html, baseUrl }}` (not `require('./page.html')`): avoids Metro's URL and
  the opaque-origin `localStorage` error. Keep an inline copy (TS template literal) in sync by hand.
- Props used: `originWhitelist={['*']}`, `javaScriptEnabled`, `domStorageEnabled`,
  `mixedContentMode="compatibility"`, `allowUniversalAccessFromFileURLs`.
- `react-native-webview` dispatches `postMessage` events on **`window` on iOS but `document` on
  Android** (with `bubbles: false`), so listen on both. The RN example repo only listens on `window`:
  do not copy that part.
- Wrap the native-side `JSON.parse(event.nativeEvent.data)` in `try/catch`.
- Map loading needs network at runtime (SDK from the CDN + map data from the map server).
