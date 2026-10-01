// Layout check under real mobile emulation (Chrome DevTools Protocol).
//
//   python3 -m http.server 8765 --bind 127.0.0.1 --directory docs   (from the site folder)
//   node tools/check_layout.mjs [outDir]
//
// For each page at 360, 390, 768 and 1280 px it reports horizontal overflow
// (scrollWidth vs the device width, never innerWidth), the h1 count, console
// errors and failed requests, and saves a full-page screenshot to outDir.
// Below 900 px it also opens the mobile menu and checks that again (the open
// panel must not overflow, and its links must sit inside the side gutter),
// saving <page>-<width>-menu.jpg for the home page. On the home page it
// reports where the hero photo starts, so her face stays in the first screen.
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const ORIGIN = process.env.SITE_ORIGIN || "http://127.0.0.1:8765/";
// 404.html links its assets at the live BASE (it must work at any depth).
// Requests to BASE are answered from ORIGIN, so the 404 page checks locally.
const LIVE_BASE = process.env.LIVE_BASE || "https://ogeddiesmith.github.io/trish-leto/";
const OUT = process.argv[2] || join(tmpdir(), "trish-shots");
const PAGES = (process.env.PAGES || ",work-with-me/,portfolio/,about/,speaking/,contact/,404.html").split(",");
const WIDTHS = [360, 390, 768, 1280];
const PORT = 9333;

mkdirSync(OUT, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "trish-chrome-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Shared page-side check: scrollWidth plus every visible element that pokes
// past the device width (ignoring clipped and fixed ones). Needs W in scope.
const OVERFLOW_JS = `
      const sw = document.documentElement.scrollWidth;
      const over = [];
      document.querySelectorAll("body *").forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width && (r.right > W + 0.5 || r.left < -0.5)) {
          let hidden = false;
          for (let p = el.parentElement; p; p = p.parentElement) { const s = getComputedStyle(p); if (s.overflowX === "hidden" || s.overflow === "hidden" || s.display === "none") { hidden = true; break; } }
          if (!hidden && getComputedStyle(el).position !== "fixed") over.push(el.tagName.toLowerCase() + "." + [...el.classList].join(".") + " [" + Math.round(r.left) + "," + Math.round(r.right) + "]");
        }
      });`;
let version;
for (let i = 0; i < 50 && !version; i++) {
  try { version = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); } catch { await sleep(200); }
}
const target = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));

let seq = 0;
const pending = new Map();
const listeners = [];
ws.addEventListener("message", (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  else listeners.forEach((fn) => fn(msg));
});
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++seq;
  pending.set(id, (m) => (m.error ? reject(new Error(method + ": " + m.error.message)) : resolve(m.result)));
  ws.send(JSON.stringify({ id, method, params }));
});

let problems = [];
const urls = new Map();
listeners.push((m) => {
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") problems.push("console: " + JSON.stringify(m.params.args.map((a) => a.value)));
  if (m.method === "Runtime.exceptionThrown") problems.push("exception: " + m.params.exceptionDetails.text);
  if (m.method === "Network.requestWillBeSent") urls.set(m.params.requestId, m.params.request.url);
  if (m.method === "Network.loadingFailed" && !m.params.canceled) problems.push("request failed: " + m.params.errorText + " " + (urls.get(m.params.requestId) || ""));
  if (m.method === "Network.responseReceived" && m.params.response.status >= 400 && !m.params.response.url.endsWith("404.html")) problems.push(`HTTP ${m.params.response.status}: ${m.params.response.url}`);
});

listeners.push((m) => {
  if (m.method !== "Fetch.requestPaused") return;
  const { requestId, request } = m.params;
  fetch(ORIGIN + request.url.slice(LIVE_BASE.length)).then(async (r) => {
    const body = Buffer.from(await r.arrayBuffer()).toString("base64");
    const responseHeaders = [...r.headers].map(([name, value]) => ({ name, value }))
      .concat([{ name: "Access-Control-Allow-Origin", value: "*" }]); // manifest fetches are CORS
    await send("Fetch.fulfillRequest", { requestId, responseCode: r.status, responseHeaders, body });
  }).catch(() => send("Fetch.failRequest", { requestId, errorReason: "Failed" }).catch(() => {}));
});
await send("Fetch.enable", { patterns: [{ urlPattern: LIVE_BASE + "*" }] });
await send("Page.enable");
await send("Runtime.enable");
await send("Network.enable");

const report = [];
for (const width of WIDTHS) {
  const mobile = width < 768;
  await send("Emulation.setDeviceMetricsOverride", { width, height: mobile ? 800 : 900, deviceScaleFactor: mobile ? 2 : 1, mobile });
  await send("Emulation.setTouchEmulationEnabled", { enabled: mobile });
  for (const page of PAGES) {
    problems = [];
    const loaded = new Promise((r) => { const fn = (m) => { if (m.method === "Page.loadEventFired") { listeners.splice(listeners.indexOf(fn), 1); r(); } }; listeners.push(fn); });
    await send("Page.navigate", { url: ORIGIN + page });
    await loaded;
    await send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => true)", awaitPromise: true });
    // Full-page captures do not scroll, so load lazy images first.
    await send("Runtime.evaluate", { awaitPromise: true, expression: `Promise.all([...document.images].map((i) => { i.loading = "eager"; return i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 4000); }); }))` });
    await sleep(250);
    const { result } = await send("Runtime.evaluate", { returnByValue: true, expression: `(() => {
      const W = ${width};
      ${OVERFLOW_JS}
      const smallTargets = [...document.querySelectorAll("a, button")].filter((el) => { const r = el.getBoundingClientRect(); return r.width && r.height && r.height < 24 && !el.closest("p, li, dd, .footer-list") ; }).map((el) => el.textContent.trim().slice(0, 30));
      const hero = document.querySelector(".hero-photo img");
      return { sw, h1: document.querySelectorAll("h1").length, height: document.documentElement.scrollHeight, over: over.slice(0, 8), smallTargets: smallTargets.slice(0, 6), font: document.fonts.check("800 20px 'Bricolage Grotesque'"), heroTop: hero ? Math.round(hero.getBoundingClientRect().top + scrollY) : null, vh: innerHeight };
    })()` });
    const v = result.value;
    const name = (page.replace(/\/$/, "").replace(".html", "") || "home") + "-" + width;
    const shot = await send("Page.captureScreenshot", { format: "jpeg", quality: 70, captureBeyondViewport: true,
      clip: { x: 0, y: 0, width, height: Math.min(v.height, 16000), scale: mobile ? 0.5 : 1 } });
    writeFileSync(join(OUT, name + ".jpg"), Buffer.from(shot.data, "base64"));
    // Open the mobile menu and check the open panel too.
    let menu = null;
    if (width < 900) {
      await send("Runtime.evaluate", { expression: `window.scrollTo(0, 0); document.querySelector(".nav-toggle").click()` });
      await sleep(150);
      menu = (await send("Runtime.evaluate", { returnByValue: true, expression: `(() => {
        const W = ${width};
        ${OVERFLOW_JS}
        const nav = document.getElementById("site-nav");
        const links = [...nav.querySelectorAll("a")].map((a) => a.getBoundingClientRect());
        const open = nav.classList.contains("is-open") && getComputedStyle(nav).display !== "none";
        return { open, sw, over: over.slice(0, 6), minLeft: Math.round(Math.min(...links.map((r) => r.left))), maxRight: Math.round(Math.max(...links.map((r) => r.right))) };
      })()` })).result.value;
      if (page === "") {
        const m = await send("Page.captureScreenshot", { format: "jpeg", quality: 70, clip: { x: 0, y: 0, width, height: mobile ? 800 : 900, scale: mobile ? 0.5 : 1 } });
        writeFileSync(join(OUT, name + "-menu.jpg"), Buffer.from(m.data, "base64"));
      }
      await send("Runtime.evaluate", { expression: `document.querySelector(".nav-toggle").click()` });
    }
    const menuOk = !menu || (menu.open && menu.sw <= width && !menu.over.length && menu.minLeft >= 8 && menu.maxRight <= width - 8);
    const ok = v.sw <= width && v.h1 === 1 && !v.over.length && !problems.length && menuOk;
    report.push(`${ok ? "OK  " : "FAIL"} ${name.padEnd(22)} scrollWidth=${v.sw}/${width} h1=${v.h1} font=${v.font} h=${v.height}` +
      (v.heroTop !== null ? ` heroPhotoTop=${v.heroTop}/${v.vh}` : "") +
      (menu ? `\n      menu open=${menu.open} scrollWidth=${menu.sw}/${width} links ${menu.minLeft}..${menu.maxRight}` : "") +
      (menu && menu.over.length ? `\n      menu overflow: ${menu.over.join(" | ")}` : "") +
      (v.over.length ? `\n      overflow: ${v.over.join(" | ")}` : "") +
      (v.smallTargets.length ? `\n      small targets: ${v.smallTargets.join(" | ")}` : "") +
      (problems.length ? `\n      ${problems.join("\n      ")}` : ""));
  }
}
console.log(report.join("\n"));
console.log("screenshots:", OUT);
ws.close();
chrome.kill();
