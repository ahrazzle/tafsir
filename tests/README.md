Run the real browser navigation regression journeys with optional Playwright tooling:

```sh
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node tests/browser.mjs
```

The script starts an ephemeral local HTTP server and checks delayed tajweed/navigation races, failed data load and successful retry, and keyboard behavior in settings. External requests are blocked. No Quranic text or annotations are synthesized. `PLAYWRIGHT_MODULE` can point to an existing Playwright module.
