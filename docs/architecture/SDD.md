# VeritX Vision — Website SDD (Software Design Document)

**Purpose of this file:** a self-contained snapshot of the site's current state — structure, content,
design decisions, and constraints — so a future session can make changes without re-reading every
source file or re-deriving decisions that were already made and settled. If this file and the actual
code ever disagree, **the code is the source of truth**; update this file to match it.

Last verified against the live source on: 2026-08-14.

---

## 1. What this is

A bilingual (Spanish/English) marketing website for **VeritX Vision**, a fictional/prototype product
by a company headquartered in Tlaxcala, Mexico, building an AI-powered fabric-defect-inspection system
("Vision A") for textile manufacturers. It is a single-page marketing site plus several satellite pages
(Demo, Calculator, About) **and a client-only-simulated customer portal** (Login, Register, email
verification, password/username recovery, and a "Vision Home" account dashboard — see §14), all
client-side routed.

- **Live site (Vercel):** the repo is also connected to Vercel directly — URL not recorded here yet
  (fill in once known; it'll be a `*.vercel.app` subdomain unless a custom domain is attached).
- **GitHub repo:** https://github.com/ismael-galaviz/defect-detection-website (branch `main`)
- **Hosting:** Vercel only, via Vercel's own git integration (§2). GitHub Pages was dropped
  (ADR `docs/decisions/001-stack.md`).

---

## 2. Tech stack

- **React 18** + **Vite 5** (`@vitejs/plugin-react`). No TypeScript, no CSS framework, no component
  library, no router library (routing is a ~10-line custom hash hook — see §4).
- Styling: one hand-written global stylesheet, `src/index.css` (~1035 lines), using CSS custom
  properties for the palette and plain class selectors. No CSS Modules, no styled-components.
- Icons: hand-drawn inline SVG paths (no icon library dependency) — see §6.
- State: local `useState`/`useEffect` only. No Redux/Zustand/Context beyond the language provider.
- Tests: Vitest (`npm test`), minimal scope — ROI formulas and `auth.js` only (ADR 001). No linter.
- `package.json` deps: `react`, `react-dom` (runtime); `vite`, `@vitejs/plugin-react`, `vitest` (dev).

### Build & dev

```bash
npm install        # if node_modules is missing/stale
npm run dev         # Vite dev server
npm run build        # production build to dist/
npm run preview      # preview the production build locally
npm test             # Vitest, run once
```

**Known local-env quirk:** npm's optional-dependency resolution sometimes omits the native Rollup
binary (`@rollup/rollup-<platform>`), causing `npm run build` to fail with a `MODULE_NOT_FOUND` on a
native `.node` file. Fix: re-run `npm install`.

**Dev server port:** the repo's own Vite config has no fixed port, but in this environment port 5173
was already taken by another app, so the harness's dev-server launcher
(`02_Website_Code/.claude/launch.json`, **one level above this repo, not git-tracked by it**) pins the
dev server to port 5199 via `--port 5199 --strictPort` and runs it with `--prefix frontend/veritx-web`
from the `02_Website_Code` directory. This file is a local tooling convenience, not part of the
deployed app.

### Vite config (`vite.config.js`)

```js
export default defineConfig({
  plugins: [react()],
})
```

Vite's default `base` (`'/'`) is correct because the only deploy target, Vercel, serves the site at
the domain root. (Until 2026-10 a `VERCEL`-conditional `base` also served a GitHub Pages build under
`/defect-detection/`; Pages was dropped and that branch removed.)

### CI (`.github/workflows/ci.yml`)

Runs on every PR and on push to `main`: secret scan (gitleaks), repo hygiene (no tracked `.env`,
`docs/README.md` exists, `GOTCHA.md` entries valid), and `npm ci` → `npm test` → `npm run build`.
It does not deploy.

### Deploy — Vercel

The repo is connected to Vercel through its own git integration (not a GitHub Actions step): every
push to `main` deploys production, and every PR gets a preview deployment. **No `vercel.json` exists
and none is needed**: Vercel auto-detects Vite and defaults to `npm run build` + `dist`. No rewrite
rules are needed either, since every route is a `#/...` hash fragment (§4). The "Root Directory"
setting stays blank — `package.json` is at the git root.

### `.gitignore`

Covers `node_modules`, `dist`, logs, Vite timestamp files, `.env*` (except `.env.example`) and
Claude Code local files.

---

## 3. File map

```
defect-detection-website/
├── CLAUDE.md / GOTCHA.md       # Claude rules; dated operational surprises
├── index.html                 # HTML shell; <html lang="es"> static default, overwritten at runtime
├── package.json / package-lock.json
├── vite.config.js
├── .github/                    # ci.yml, PR + issue templates
├── .claude/ .specify/ specs/   # Claude settings/skills, Spec Kit, feature specs (see §13)
├── public/
│   └── favicon.svg
├── docs/                       # index in docs/README.md
│   └── architecture/SDD.md     # this file
└── src/
    ├── main.jsx                # ReactDOM root (wrapped in React.StrictMode), imports index.css, mounts <App/>
    ├── App.jsx                 # routing hook, ALL page-1 components (Header..Footer), <Site/>, <App/>
    ├── icons.jsx                # shared <Icon name size/> component + ICON_PATHS map (SVG paths)
    ├── i18n.jsx                 # LanguageProvider/useLanguage — language state, not the copy itself
    ├── translations.js          # ALL user-facing copy, both languages, one big object (see §5, §9)
    ├── auth.js                   # client-only simulated auth "backend" — see §14
    ├── DemoPage.jsx              # route #/demo — interactive defect-map demo
    ├── *.test.js                  # Vitest tests (calculator formulas, auth.js)
    ├── CalculatorPage.jsx         # route #/calculator — interactive ROI/savings calculator (see §10.16)
    ├── AboutPage.jsx              # route #/about — "Who We Are" page (incl. the Mexico locator map)
    ├── PrivacyPolicyPage.jsx       # route #/privacy — Privacy Policy page, content in translations.js → privacyPage
    ├── MexicoMap.jsx               # <MexicoMap/> component used by AboutPage — see §14.7
    ├── mexicoMapData.js            # generated SVG path data consumed by MexicoMap.jsx — see §14.7
    ├── LoginPage.jsx                # route #/login — see §14
    ├── RegisterPage.jsx              # route #/register — see §14
    ├── VerifyEmailPage.jsx            # route #/verify-email — see §14
    ├── ForgotPasswordPage.jsx          # routes #/forgot-password (+ ?token=) — see §14
    ├── RecoverUsernamePage.jsx          # route #/recover-username — see §14
    ├── VisionHomePage.jsx                # route #/vision-home — protected account dashboard, see §14
    └── index.css                 # the only stylesheet, global, ~1450+ lines
```

There is no `components/` subfolder — every home-page section component (`Header`, `Hero`, `VisionA`,
`HowItWorks`, `UseCases`, `Comparison`, `Specs`, `Contact`, `Footer`, plus small helpers `LangSwitch`,
`NavDropdown`, `MobileAccordion`, `MadeInMexicoBadge`) lives directly in `App.jsx` as sibling function
components, in the order they render. `Site()` is the component that assembles them per route; `App()`
just wraps `Site` in `LanguageProvider`. The customer-portal pages (§14) each get their own file,
following the same one-file-per-satellite-page convention as `DemoPage.jsx`/`CalculatorPage.jsx`/`AboutPage.jsx`.

---

## 4. Routing

No router library. `useRoute()` (top of `App.jsx`) reads `window.location.hash`, listens for
`hashchange`, and maps it to one of these route names:

| hash prefix | route |
|---|---|
| `#/demo` | `demo` → renders `<DemoPage/>` |
| `#/calculator` | `calculator` → renders `<CalculatorPage/>` |
| `#/about` | `about` → renders `<AboutPage/>` |
| `#/privacy` | `privacy` → renders `<PrivacyPolicyPage/>` |
| `#/login` | `login` → renders `<LoginPage/>` |
| `#/register` | `register` → renders `<RegisterPage/>` |
| `#/verify-email` (+ `?token=`) | `verify-email` → renders `<VerifyEmailPage/>` |
| `#/forgot-password` (+ optional `?token=`) | `forgot-password` → renders `<ForgotPasswordPage/>` (request view if no token, reset view if a token is present) |
| `#/recover-username` | `recover-username` → renders `<RecoverUsernamePage/>` |
| `#/vision-home` | `vision-home` → renders `<VisionHomePage/>` (redirects to `#/login` client-side if there's no session — see §14) |
| anything else (incl. plain `#section-id` anchors) | `home` → renders the full home-page section stack |

All ten non-`home` route names are collected in the `SATELLITE_ROUTES` array (top of `App.jsx`, right
above `useRoute()`) so the scroll-to-top effect below and any future "is this a satellite page" check
stay in sync with one list instead of a repeated `route === 'x' || route === 'y' || ...` chain.

`<Header/>` and `<Footer/>` always render regardless of route.

On route change, `Site()`'s `useEffect`:
- scrolls to top (`window.scrollTo(0,0)`) for any route in `SATELLITE_ROUTES`,
- otherwise (route `home`), if the current hash is a plain anchor (doesn't start with `#/`), scrolls
  that element into view via `document.getElementById(hash.slice(1))?.scrollIntoView()`.

**Query strings on hash routes:** `#/verify-email?token=...` and `#/forgot-password?token=...` carry a
token as a query string appended directly to the hash fragment (not a "real" URL query string, since
everything after `#` is opaque to the browser/server — this is a static site with no server-side
routing anyway). Each page reads it with a small `getTokenFromHash()` helper:
`new URLSearchParams(window.location.hash.split('?')[1] || '').get('token')`. `useRoute()`'s
`hash.startsWith('#/forgot-password')` check matches both the bare and `?token=`-suffixed forms since
the query string comes right after the route segment.

This means an in-page anchor like `#contact` works both when already on `home` (native browser anchor
scroll, assisted by `html { scroll-behavior: smooth }` in CSS) **and** when clicked from a satellite
page (e.g. Calculator's CTA linking to `#contact` — the hash change flips the route back to `home`,
which mounts the Contact section, and the effect above scrolls to it).

**To add a new page/route:** add a `hash.startsWith('#/whatever')` branch in `useRoute()`, add
`{route === 'whatever' && <WhateverPage/>}` in `Site()`, import the new page component, and add it to
`route === 'home' || route === 'demo' || ...` in the top-scroll `useEffect` condition if it should
scroll-to-top on entry (satellite pages do; anchor-style routes don't).

---

## 5. i18n system

`src/i18n.jsx` exports `LanguageProvider` and `useLanguage()`.

- `detectLanguage()`: reads `localStorage['veritx-lang']`; if it's `'en'` or `'es'`, use it; **otherwise
  defaults to `'es'`** (Spanish-first is intentional — the target audience is Mexico/LatAm-first, per
  explicit product decision, not a browser-language auto-detect).
- On every language change: persists to `localStorage['veritx-lang']` and sets
  `document.documentElement.lang` to match (so `index.html`'s static `lang="es"` is just the pre-JS
  default; the real value is runtime-managed).
- `useLanguage()` returns `{ lang, setLang, t }` where `t` is `translations[lang]` — the whole
  per-language object from `translations.js`. Components read copy as `t.section.field`.

**Language switcher UI** (`LangSwitch` in `App.jsx`): a native `<select>` styled to look custom
(class `lang-switch`), not a pair of buttons — two `<option>`s, each prefixed with a flag emoji:
`🇲🇽 ES` and `🇺🇸 EN`. This is the one place emoji are intentionally used (see §6 — everywhere else
emoji were replaced with SVG icons; flags here represent language/country identity, not decoration,
and were explicitly kept). Lives in the header, opens as a real native dropdown (per explicit
instruction: "que sea un dropbox", after an earlier iteration used two flag buttons).

**To add a language:** add a new top-level key to `translations.js` (e.g. `pt: {...}` mirroring the
full shape of `en`/`es`), add an `<option>` in `LangSwitch`, and extend `detectLanguage`'s validity
check.

---

## 6. Icon system (`src/icons.jsx`)

A single exported component:

```jsx
export function Icon({ name, size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICON_PATHS[name]}
    </svg>
  )
}
```

All icons are **hand-drawn stroke-only SVG paths** (no icon library/font), colored via CSS
`color` on the parent element (they use `stroke="currentColor"`). This was a deliberate replacement of
an earlier emoji-based icon set ("cambia los emojis por iconos más serios y que el color sea el mismo
del tema de la página") — icons are consistently tinted with the brand cyan (`var(--cyan)` on dark
backgrounds, `var(--cyan-dark)` on light backgrounds), never left at default/emoji color, **except** the
language-switcher flags (see §5).

**Current icon names** (`ICON_PATHS` keys) and what they're used for:

| name | used in | meaning |
|---|---|---|
| `bolt` | Vision A feature 1 | Plug & play |
| `link` | Vision A feature 2 | Easy integration |
| `sliders` | Vision A feature 3 | Flexible to your process |
| `weave` | Use Cases card 1 | Fabric Production |
| `droplet` | Use Cases card 2 | Finishing |
| `eyeCheck` | Use Cases card 3 | Final Inspection (compound eye + checkmark-badge icon, explicitly requested) |
| `pause` | How It Works integration example 1 | "stop the line" |
| `tag` | How It Works integration example 2 | "trigger the labeling unit" |
| `mail` | Contact info row | Email us |
| `pin` | Contact info row, About facts | Location/HQ |
| `gear` | How It Works integration card | Machine-integration/automation |
| `target` | Why VeritX Vision card 1 | Industrial-grade accuracy |
| `activity` | Why VeritX Vision card 2 | Real-time inline inspection |
| `percent` | Why VeritX Vision card 3 | Accessible pricing |
| `cloud` | Why VeritX Vision card 4 | Cloud or on-premises |
| `globe` | About facts | "Where we serve" |
| `chevronDown` | Nav dropdown / mobile accordion triggers | Expand/collapse indicator (rotates 180° via `.chev.open`) |
| `clock` | Calculator, section 2 (labor hours); also reused for Vision Home's "next payment" and "schedule a meeting" cards | Time/hours |
| `gauge` | Calculator, section 3 (line speed) | Speed |
| `shield` | Calculator, soft savings | Customer trust/reputation |
| `clipboard` | Calculator, soft savings; also reused for Vision Home's "active subscriptions" card | Audits/certifications |
| `spark` | Calculator, soft savings | Employee experience |
| `whatsapp` | Contact info row | WhatsApp chat link (`wa.me/526462416056`) |
| `eye` / `eyeOff` | Login/Register/Reset-password forms | Show/hide password toggle (swapped by `showPassword` state) |
| `user` | Header account link/dropdown trigger | Login/My Account entry point |
| `flask` | Every auth page's "demo mode" panel (dummy-login banner, verification/reset dev-links, recover-username dev-panel) | Signals "this is simulated, not a real backend action" |
| `linkedin` | Footer, brand column | Social link icon (placeholder — see §11) |

`user`, `flask`, `eye`/`eyeOff`, and `linkedin` were added for the customer-portal work (§14); `whatsapp`
was added when a WhatsApp contact row was requested alongside the existing email row in `Contact()`.

**To add an icon:** add a `name: <path .../>` (or `<>...</>` fragment for multi-element icons) entry to
`ICON_PATHS` in `icons.jsx`, keeping the `viewBox="0 0 24 24"` coordinate space consistent with the
existing set so sizing behaves predictably.

---

## 7. Design tokens & layout conventions

CSS custom properties, defined on `:root` in `index.css`:

```css
--navy: #0B1F3A;
--navy-light: #12315c;
--cyan: #00D4FF;
--cyan-dark: #00a8cc;
--ink: #0d1b2a;
--gray-50: #f7f9fc;
--gray-100: #eef1f6;
--gray-300: #cbd5e1;
--gray-500: #64748b;
--gray-700: #334155;
--white: #ffffff;
--radius: 14px;
--max-width: 1180px;
```

Font: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`
(no font is actually loaded/imported — this falls back to system fonts since Inter isn't linked
anywhere; cosmetic gap, not a bug per se).

**Section vertical padding** — base rule `section { padding: 77px 0; }`. This value (and the hero's
`80px 0 96px`, the demo/calculator/about hero's `58px 0`, and their content section's `51px 0 77px`)
are **already a 20%-reduced** version of the original design (96px / 100+120px / 72px / 64+96px) per
an explicit "reduce spacing 20%" request. If asked to adjust spacing again, these current numbers are
the baseline to scale from, not the original ones.

**Responsive breakpoints:** two, both `max-width` media queries — `900px` (the main one: collapses
grids to 1–2 columns, hides desktop nav, shows the hamburger) and `600px` (a couple of demo-page-only
tweaks). No `min-width` breakpoints are used.

**Container:** `.container { max-width: 1180px; margin: 0 auto; padding: 0 24px; }` — used inside every
section.

**Buttons:** `.btn` base + `.btn-primary` (cyan, dark navy text), `.btn-ghost` (transparent, white
border, for dark backgrounds), `.btn-dark` (navy bg, white text, used for the contact form submit).

**Card/section pattern reused across the site:** an icon in a small rounded square with a tinted cyan
background (`rgba(0,212,255, .1–.15)`), a heading, a paragraph. This exact visual pattern is shared by
Vision A features (`.vf-icon`), Use Cases cards (`.usecase-icon`), and the "Why VeritX Vision" cards
(`.usecase-icon` reused via the `why-grid` class — see §9.7) — reuse this pattern rather than inventing
a new card style when adding similar content.

**Pages that aren't the home page** (`DemoPage`, `CalculatorPage`, `AboutPage`) all share the same
two-part layout: a `<section className="demo-hero">` navy gradient banner with just an eyebrow + `<h1>`
(and optionally a lead paragraph / toolbar, as Demo does), followed by a `<section className="demo-section">`
light-gray content area. Reuse this `demo-hero` + `demo-section` pair for any new satellite page instead
of inventing new classes.

---

## 8. Component inventory (`App.jsx`)

In file order:

- **`useRoute()`** — hash-based router hook, see §4.
- **`LangSwitch()`** — native `<select>` language switcher, see §5.
- **`NavDropdown({ label, items, isOpen, onToggle, onNavigate })`** — a header nav item that's a button
  + absolutely-positioned panel of links. Controlled from outside (open/close state lives in `Header`).
- **`MobileAccordion({ label, items, onNavigate })`** — the mobile-hamburger-menu equivalent of
  `NavDropdown`; manages its own `open` state locally (each mobile menu section is independent, unlike
  desktop where only one dropdown can be open at a time).
- **`Header()`** — sticky header. Desktop nav, left to right: **Home** (plain link, `href="#"`) →
  **Product** (`NavDropdown`, `t.nav.productItems`) → **Calculate Savings** (plain link,
  `href="#/calculator"`, `t.nav.calculator` — renamed from "Calculator"/"Calculadora" to "Calculate
  Savings"/"Calcular ahorros") → **About Us** (`NavDropdown`, `t.nav.aboutItems`). Only one dropdown can
  be open at a time (`openDropdown` state: `null | 'product' | 'about' | 'account'` — see the account
  dropdown below). Dropdowns open **on click, not hover** (explicit choice — more accessible, consistent
  with mobile). Closed by: clicking its own trigger again, clicking any item inside it, clicking
  anywhere outside the dropdown's own container, or pressing `Escape`. Outside-click detection uses
  **two refs**, not one: `navRef` (wraps `nav.nav-links`, for `product`/`about`) and `accountRef` (wraps
  the account-menu `<div>`, for `account`) — the shared `mousedown` handler picks
  `openDropdown === 'account' ? accountRef : navRef` so each dropdown only reacts to clicks outside its
  own DOM subtree (a single shared ref would either fail to close the account menu when clicking a nav
  link, or vice versa). The mobile hamburger (`mobile-toggle` button, ☰/✕) toggles a separate
  `<nav className="mobile-menu">` that mirrors the same structure — Home link, Product
  `MobileAccordion`, Calculate Savings link, About Us `MobileAccordion`, plus the account link/logout
  row (see below). **There is no CTA button in the header** — deliberately removed once the header got
  crowded; the primary CTA lives in the hero, the contact section, and page-specific CTAs. **There used
  to be a third "Tools" dropdown** grouping Demo + Calculator together — Demo was explicitly removed
  from the nav (the `#/demo` route/page itself still exists and works, it's just unlinked — see §11),
  leaving Tools with only one item, so it was collapsed into the plain Calculate-Savings link described
  above rather than keeping a single-item dropdown. `DemoPage` is still imported and routed in `Site()`;
  only the nav link was removed. **Account link** (`nav-cta`, after `LangSwitch`): see the icon-only
  dropdown described in §6's icon table and §14.2 — this replaced an earlier icon+text-label version.
- **`Hero()`** — headline, lead paragraph, two CTAs (`#contact`, `#how-it-works`), three stat chips
  (`t.hero.stats`), and a decorative "scan frame" visual with two floating defect-tag labels
  (`t.hero.defectTags`) and an animated scan line (`@keyframes scan`, pure CSS). **The middle stat was
  changed from an abstract `'Flexible'` / "Install adapts to your machine" to a concrete number**:
  `'100%'` / "Of rolls inspected — not sampled" — requested as a "more tangible fact a business owner
  would find attractive" than a non-numeric value; the wording reuses the existing "inspects 100% of
  pieces consistently" claim already established in the ROI calculator copy (§10.16), not a new,
  unvalidated claim.
- **`VisionA()`** (`id="vision-a"`) — product intro section, right after Hero. Left: eyebrow/title/sub +
  3 feature rows (icon + title + body, from `t.visionA.features`). Right: **the visual column now holds
  only the 16:9 YouTube embed** (`.video-embed`, privacy-enhanced `youtube-nocookie.com` domain, video
  id `djK5l04jRoM`, accessible `title` from `t.visionA.videoTitle`) — no other content below it.
  **Superseded:** this column used to show a decorative CSS-only "device" mockup (`.device-frame`, pure
  CSS, no real image/animation asset) with a row of small pill tags (`t.visionA.tags`) *underneath* a
  separate full-width video embed. Both were explicitly removed in two steps — first the device mockup
  was replaced by moving the video into that spot, then the pill tags below it were removed outright —
  leaving just the single video. `t.visionA.tags` and the `.device-frame`/`.device-name`/`.device-bar`/
  `.device-beam`/`.device-fabric`/`.visiona-tags` CSS were deleted along with them; don't resurrect
  either without a fresh request. **The product video lives here (product description section), not on
  the About page** — it was initially added to About and explicitly moved to Vision A; if a second video
  is ever needed for About, that'd be a new addition, not "restoring" anything.
- **`HowItWorks()`** (`id="how-it-works"`) — 4-step numbered pipeline grid (`t.howItWorks.steps`,
  `.step-card`), plus one extra full-width dark **"integration card"** below the grid
  (`t.howItWorks.integration`) explaining that Vision A can trigger **client-defined actions** on
  severe defects (e.g. stop the line, trigger a labeling unit) — this card was explicitly requested as
  an "extra box", not a numbered step, and is visually distinct (navy gradient vs. the light step
  cards) for that reason.
- **`UseCases()`** (`id="use-cases"`) — 3-card grid, `t.useCases.cards` (Fabric Production, Finishing,
  Final Inspection).
- **`Comparison()`** (`id="comparison"`) — despite the id/name (kept for URL/nav-anchor stability), this
  is **not** a competitor-comparison table. It renders `t.comparison.cards` as a 4-card grid (class
  `usecases-grid why-grid` — reuses the use-cases card styling, `why-grid` just changes the grid to 4
  columns). **This was deliberately reworked from an earlier "VeritX vs. Legacy Systems" two-column
  table into standalone value-prop cards, per an explicit "don't compare to the competition" request.**
  Do not reintroduce a competitor/legacy-systems comparison here.
- **`Specs()`** (`id="specs"`) — dark navy section, 4 stat cards (`t.specs.cards`).
- **`Contact()`** (`id="contact"`) — two-column: left is contact info (`.contact-info`); right is the
  lead-gen form. **Left column layout:** an `.info-row-pair` puts "Email us" (`mail` icon) and "Chat on
  WhatsApp" (`whatsapp` icon, `href="https://wa.me/526462416056"`, opens in a new tab) side by side,
  with "Based in" (`pin` icon) as a full-width row below — the WhatsApp row was requested to sit next to
  the email row specifically, not stacked under it. `.info-row` (and its `a.info-row` link variant) is
  shared with `AboutPage`'s facts list. The form opens with a `.mode-toggle` (segmented control, `mode`
  state: `'message' | 'schedule'`). In `'schedule'` mode, an `<AppointmentPicker/>` renders between the
  stage select and the message textarea, and — schedule mode or not — a video-tool `<select>`
  (`a.videoTool`/`videoToolOptions`: Zoom, Google Meet, Microsoft Teams, WhatsApp Video, Other) renders
  right after the picker so the visitor can say how they'd like to take the call — see §10.17 for its
  behavior. **On submit, the success message is scrolled into view** (`successRef` +
  `scrollIntoView({behavior:'smooth', block:'center'})` in a `useEffect` keyed on `submitted`) — before
  this fix, submitting collapsed the tall schedule-mode form (with the date/time picker) down to a short
  success banner while the scroll position stayed put, leaving the visitor looking at the footer instead
  of the confirmation. See §9.6 and §10 for the form's exact fields, ordering, and behavior — it's the
  most complex component in the file.
- **`AppointmentPicker`** (defined just above `Contact()`) — a hand-built month-view calendar (no date
  library) plus a fixed set of business-hour time slots, all declared and labeled in **Mexico City time
  (CDMX)** regardless of the visitor's own timezone. See §10.17.
- **`MadeInMexicoBadge()`** — small decorative footer badge, pure CSS Mexican-flag color bar, no
  translated text (the "HECHO EN MÉXICO" label is hardcoded, not through `t`, since it's a fixed
  Spanish-language brand mark regardless of site language — this was an explicit request, not an
  oversight).
- **`Footer()`** — brand block (logo, tagline, a `.footer-social` row, the Mexico badge) + 3 link
  columns (`Product`, `Company`, `Legal`) + bottom bar (copyright only — see below). `.footer-social`
  currently holds one icon-only entry, LinkedIn (`Icon name="linkedin"`), rendered as a non-interactive
  `<span>` (no `href`) rather than a real `<a>` link — **there is no real company LinkedIn URL yet**;
  wire it up as a proper link once one exists (don't guess/fabricate a URL — see §11). The `Company`
  column is `About` (→ `#/about`) and `Contact` (→ `#contact`) — both real links; there is no `Careers`
  entry. **The `Legal` column is still not real links** — see §11. **Superseded:** the bottom bar used
  to include a second line, "Prototype product — specifications subject to change." — removed by
  request; `t.footer.prototype` no longer exists in either language, don't re-add it without being asked.
- **`Site()`** — route-to-component mapping, see §4.
- **`App()`** — default export, wraps `<Site/>` in `<LanguageProvider>`.

---

## 9. Content — full copy (both languages)

⚠️ **This section is now known-stale for parts of the file and is kept for the original marketing
copy only.** It was originally a full verbatim reproduction of `translations.js`, but the file has
since grown a large `auth` namespace (login/register/recovery/Vision Home copy — see §14.1) that is
**deliberately not reproduced here** (it would roughly double this document's length for content that's
easy to read directly in the source file), plus a number of smaller edits to the marketing copy below
that were **not** re-synced into this quoted block afterward: the hero's middle stat (§10.23), the
footer's removed "prototype" line (§8's `Footer()` entry), Vision A's removed device-mockup tags
(§8's `VisionA()` entry), the About page's added Vision/Mission section and WhatsApp contact row
(§10.25, §8's `Contact()` entry), the nav's "Calculator" → "Calculate Savings" rename (§10.22), and the
calculator's currency selector / send-results panel / relocated methodology note (§10.19–21). **For any
of those areas, or anything under `auth`, read `src/translations.js` directly — it is unambiguously the
source of truth.** The reproduction below is otherwise accurate for the rest of the site's copy as of
2026-08-13 (before this round of changes); trust the real file over this block for literally anything
that seems to disagree with it, per the standing rule at the top of this document.

```js
export const translations = {
  en: {
    nav: {
      home: 'Home',
      product: 'Product',
      productItems: [
        { href: '#vision-a', label: 'Vision A' },
        { href: '#how-it-works', label: 'How It Works' },
        { href: '#use-cases', label: 'Use Cases' },
        { href: '#comparison', label: 'Why VeritX' },
        { href: '#specs', label: 'Specifications' },
      ],
      calculator: 'Calculator',
      aboutLabel: 'About Us',
      aboutItems: [
        { href: '#/about', label: 'Who We Are' },
        { href: '#contact', label: 'Contact' },
      ],
    },
    calculatorPage: {
      eyebrow: 'ROI Tool',
      title: 'Savings calculator',
      intro: 'See how much VeritX Vision could save on your line. These are the three sources of measurable savings quality engineers use to justify the investment — adjust the numbers below for your own line; the defaults are illustrative examples.',
      resultLabel: 'Annual savings',
      formulaLabel: 'View formula',
      sections: [
        {
          id: 'defects',
          icon: 'eyeCheck',
          title: '1. Reducing undetected defects',
          body: 'The biggest savings, and the easiest to defend to finance. Today some defects pass manual or sampled inspection and reach the customer, or trigger downstream rework. A vision system inspects 100% of pieces consistently, without fatigue or shift-to-shift variability.',
          formula: 'Annual savings =\n  (Defect rate BEFORE − Defect rate AFTER)\n  × Annual production volume\n  × Cost per defect\n\nCost per defect =\n  Rework/scrap cost + Warranty/return cost\n  + (optional) Reputational cost / customer penalties',
          fields: [
            { key: 'rateBefore', label: 'Current defect rate (%)' },
            { key: 'rateAfter', label: 'Expected defect rate with the system (%)' },
            { key: 'volume', label: 'Annual production volume (m² produced)' },
            { key: 'costPerDefect', label: 'Cost per defect (MXN)' },
          ],
          hint: 'For an accurate estimate, use your current defect rate (from your quality reports), the expected rate with the system (pilot data or vendor reference), and the real cost of each defect — not just material, but rework labor, return logistics, and contractual penalties if any.',
        },
        {
          id: 'laborHours',
          icon: 'clock',
          title: '2. Reducing manual-inspection labor hours',
          body: 'If inspection today depends on people visually reviewing parts, the system can free that time for higher-value tasks, reduce shifts dedicated only to inspection, or remove bottlenecks caused by inspector fatigue.',
          formula: 'Annual savings =\n  (Inspection labor hours BEFORE − Labor hours AFTER)\n  × Cost per hour\n  × Operating shifts per year',
          fields: [
            { key: 'hoursBefore', label: 'Inspection hours before (per shift, all inspectors)' },
            { key: 'hoursAfter', label: 'Inspection hours after (per shift, all inspectors)' },
            { key: 'hourlyCost', label: 'Cost per hour (MXN)' },
            { key: 'shiftsPerYear', label: 'Operating shifts/days per year' },
          ],
          hint: 'Important: this savings rarely means layoffs. It usually means reassigning your staff to higher-value tasks (maintenance, continuous improvement) or avoiding new inspector hires as your production grows.',
        },
        {
          id: 'lineSpeed',
          icon: 'gauge',
          title: '3. Increasing line speed',
          body: 'Manual inspection is often the bottleneck limiting how fast the line can run. A vision system inspects in real time at process speed, allowing you to increase line speed without sacrificing quality.',
          formula: 'Annual savings =\n  (New line speed − Current speed) [m/min]\n  × 60 min/hour\n  × Operating hours per year\n  × Contribution margin per meter produced',
          fields: [
            { key: 'speedBefore', label: 'Current line speed (m/min)' },
            { key: 'speedAfter', label: 'New line speed (m/min)' },
            { key: 'hoursPerYear', label: 'Operating hours per year' },
            { key: 'marginPerMeter', label: 'Contribution margin per meter produced (MXN)' },
          ],
          hint: "This savings only applies if your business can sell the extra capacity (enough demand) or if it avoids investing in a second line — worth confirming with your own team before treating it as guaranteed. The speed difference is per minute, so the calculator converts it to a yearly total (×60 minutes/hour × your operating hours) before applying your margin per meter.",
        },
      ],
      totalTitle: 'Total estimated savings',
      totalAnnual: 'Total annual savings (sum of the three)',
      methodologyNote: "How to read this: add the three annual savings for your total estimate. The defect-reduction savings (point 1) is usually the easiest to calculate with data you already have from your quality reports; points 2 and 3 strengthen the case but depend on your own line's operational decisions.",
      softSavings: {
        title: 'Beyond the numbers: soft savings',
        intro: "These benefits are harder to put a dollar figure on, but they matter just as much when building your case.",
        items: [
          {
            icon: 'shield',
            title: 'Stronger customer trust',
            body: 'Fewer defective shipments reaching customers protects your reputation and reduces the risk of losing accounts over quality issues.',
          },
          {
            icon: 'clipboard',
            title: 'Easier audits & certifications',
            body: 'Consistent, documented inspection data makes ISO audits and customer quality certifications faster to pass.',
          },
          {
            icon: 'spark',
            title: 'Better employee experience',
            body: 'Frees inspectors from repetitive, fatiguing visual checks so they can focus on higher-value work.',
          },
          {
            icon: 'activity',
            title: 'Data-driven decisions',
            body: 'Real-time defect data replaces guesswork, helping you spot trends and act before small issues become big ones.',
          },
        ],
      },
      ctaSub: 'Want a version customized with your own numbers, backed by our team?',
      cta: 'Request Contact',
    },
    demo: {
      eyebrow: 'Live Demo',
      title: 'Roll defect map',
      sub: 'Every detected defect is logged with its position along the roll and across the fabric width. This simulation shows the map an operator sees once a roll has been inspected.',
      simulate: 'Simulate new roll',
      defectsDetected: 'defects detected',
      rollInfo: '120 m roll · 160 cm fabric width',
      xAxis: 'Meters produced (m)',
      yAxis: 'Fabric width (cm)',
      sizeNote: 'Square size indicates severity',
      types: { hole: 'Hole', stain: 'Stain', weave: 'Weaving error', other: 'Other' },
      severities: { low: 'Low', medium: 'Medium', high: 'High' },
      tooltip: { position: 'Position', width: 'Width', severity: 'Severity', confidence: 'Confidence' },
      table: {
        title: 'Defect log',
        cols: ['#', 'Position (m)', 'Width (cm)', 'Type', 'Severity', 'Confidence'],
      },
    },
    hero: {
      eyebrow: 'AI-Powered Fabric Inspection',
      titleStart: 'Catch every textile defect. ',
      titleAccent: 'Cut inspection costs by half.',
      lead: 'VeritX Vision uses real-time computer vision and machine learning to detect fabric defects on the production line — delivering enterprise-grade quality control at a fraction of the cost of legacy inspection systems.',
      ctaPrimary: 'Request Contact',
      ctaSecondary: 'See How It Works',
      stats: [
        { num: '99.2%', label: 'Detection accuracy' },
        { num: 'Flexible', label: 'Install adapts to your machine' },
        { num: '~50%', label: 'Lower cost vs. legacy systems' },
      ],
      defectTags: [
        { label: 'Hole 98%', style: { top: '22%', left: '30%', width: '60px', height: '40px' } },
        { label: 'Stain 94%', style: { top: '58%', left: '62%', width: '70px', height: '46px' } },
      ],
      liveFeed: 'Live detection feed',
      feedDetail: '2 defects flagged · 12 ft roll',
    },
    visionA: {
      eyebrow: 'Meet the Product',
      title: 'Vision A: inspection that plugs into your line',
      sub: 'Vision A is our first inspection unit — engineered to be plug and play, so any mill can go from unboxing to automated quality control without re-engineering its production line.',
      features: [
        {
          icon: 'bolt',
          title: 'Plug & play by design',
          body: 'Vision A ships pre-calibrated with mounting hardware included. Mount it over your line, connect power and network, and start detecting — no specialized technicians, no production stops.',
        },
        {
          icon: 'link',
          title: 'Easy integration',
          body: 'Designed to retrofit onto your existing looms, finishing lines, or inspection frames without modifying them. Open APIs and standard industrial protocols connect it to your MES, ERP, or dashboards.',
        },
        {
          icon: 'sliders',
          title: 'Flexible to your process',
          body: 'Works across fabric types, widths, and line speeds. Start with a single unit at final inspection or scale to full-line coverage — in the cloud or on-premises.',
        },
      ],
      tags: ['Pre-calibrated', 'Flexible installation', 'Open API', 'No line modifications'],
      videoTitle: 'VeritX Vision video',
    },
    howItWorks: {
      eyebrow: 'How It Works',
      title: 'From raw fabric to actionable quality data',
      sub: 'A simple, four-step pipeline that plugs into your existing production line.',
      steps: [
        {
          n: '01',
          title: 'Camera & Sensor Capture',
          body: 'High-resolution line-scan cameras mount directly onto existing looms, finishing lines, or final inspection frames — no need to replace your current equipment.',
        },
        {
          n: '02',
          title: 'Real-Time AI Analysis',
          body: 'Our machine learning model analyzes fabric imagery frame by frame, classifying defects such as holes, stains, weaving errors, and shade variation in real time.',
        },
        {
          n: '03',
          title: 'Instant Defect Mapping',
          body: 'Detected defects are logged with position, type, and severity, and mapped onto the roll so operators know exactly where to inspect or cut.',
        },
        {
          n: '04',
          title: 'Reporting & Yield Optimization',
          body: 'Quality data feeds into a dashboard for trend analysis and integrates with your existing MES and production ecosystem, helping you optimize cut positions, reduce waste, and make data-driven decisions.',
        },
      ],
      integration: {
        title: 'Client-defined actions on severe defects',
        body: "Vision A can talk directly to your line's control system to react automatically when a defect crosses a severity threshold you set. You define the rules and the actions — VeritX Vision executes them in real time.",
        examples: [
          { icon: 'pause', rule: 'Severe defect detected 5+ times within 100 m', action: 'stop the line' },
          { icon: 'tag', rule: 'Severe defect detected', action: 'trigger the labeling unit to mark the defect' },
        ],
      },
    },
    useCases: {
      eyebrow: 'Where VeritX Fits',
      title: 'Coverage across your entire fabric line',
      sub: 'Deploy at one stage or across the full production flow — the system adapts to your setup.',
      cards: [
        {
          icon: 'weave',
          title: 'Fabric Production',
          body: 'Inline inspection during weaving and knitting catches defects at the source — before hours of production compound a single flaw.',
        },
        {
          icon: 'droplet',
          title: 'Finishing',
          body: 'Monitor dyeing, coating, and finishing stages for shade variation, streaks, and contamination before fabric moves downstream.',
        },
        {
          icon: 'eyeCheck',
          title: 'Final Inspection',
          body: 'Full-roll automated inspection before packaging and shipment, with a complete defect map for cutting and grading decisions.',
        },
      ],
    },
    comparison: {
      eyebrow: 'Why VeritX Vision',
      title: 'Precision, flexibility, and value — built into every unit',
      sub: 'VeritX Vision combines industrial-grade AI detection with a pricing and deployment model designed to fit mills of any size.',
      cards: [
        {
          icon: 'target',
          title: 'Industrial-grade accuracy',
          body: 'AI-based classification identifies holes, stains, weaving errors, and shade variation with industrial-grade precision, in real time.',
        },
        {
          icon: 'activity',
          title: 'Real-time inline inspection',
          body: 'Defects are flagged the moment they happen on the line, not discovered downstream after hours of production.',
        },
        {
          icon: 'percent',
          title: 'Accessible pricing',
          body: 'Designed from the ground up to be cost-efficient, so AI-powered quality control fits mills of any size — not just large enterprise budgets.',
        },
        {
          icon: 'cloud',
          title: 'Cloud or on-premises',
          body: 'Deploy VeritX Vision in the cloud, on-premises, or a hybrid setup — your infrastructure, your rules.',
        },
      ],
    },
    specs: {
      eyebrow: 'Technical Specifications',
      title: 'Precision built for production floors',
      sub: 'Prototype performance based on internal testing. Full technical datasheet available on request.',
      cards: [
        { val: '99.2%', label: 'Defect detection accuracy' },
        { val: '≤5mm', label: 'Minimum detectable defect size' },
        { val: 'Up to 120m/min', label: 'Inspection line speed' },
        { val: 'Custom-trained', label: 'Defect classes learned per material, not fixed' },
      ],
    },
    about: {
      eyebrow: 'About Us',
      title: 'Mexican engineering, built for textile manufacturers everywhere',
      body: 'VeritX Vision started in Tlaxcala, Mexico, built by a team with years of hands-on experience in the textile industry, with a simple goal: bring AI-powered quality control within reach of textile mills of any size — not just the largest manufacturers. We combine computer vision, machine learning, and hardware designed to fit into real production lines, so quality control stops being a luxury only a few can afford.',
      facts: [
        { icon: 'pin', label: 'Headquarters', value: 'Tlaxcala, Mexico' },
        { icon: 'globe', label: 'Where we serve', value: 'Mexico, Latin America, and beyond' },
      ],
    },
    contact: {
      eyebrow: 'Get In Touch',
      title: 'Ready to see VeritX Vision on your line?',
      body: "Tell us about your production setup and we'll schedule a personalized demo — in person or over video — to show how VeritX Vision fits into your process.",
      emailLabel: 'Email us',
      email: 'hello@veritxvision.com',
      locationLabel: 'Based in',
      location: 'Tlaxcala, Mexico — serving textile manufacturers across Mexico, Latin America, and the world',
      success: "Thanks for reaching out! We'll get back to you within one business day to schedule your demo.",
      successSchedule: "Your appointment request has been received! We'll confirm by email shortly.",
      appointment: {
        modeMessage: 'Send a message',
        modeSchedule: 'Schedule a meeting',
        timezoneNote: 'All times shown are Mexico City time (CDMX).',
        currentTime: 'Current time in Mexico City',
        selectDate: 'Select a date',
        selectTime: 'Select a time',
        summaryLabel: 'Selected appointment',
        required: 'Please pick a date and time for your appointment.',
      },
      privacy: {
        title: 'How we use your information',
        summary: 'VeritX Vision collects the information you submit here only to respond to your request and schedule a demo.',
        points: [
          'We use your data solely to contact you about VeritX Vision and follow up on your request.',
          'We never sell or share your information with third parties for marketing purposes.',
          'Your data is stored securely and kept only as long as needed to support your inquiry.',
          'You can request access, correction, or deletion of your data at any time by emailing hello@veritxvision.com.',
        ],
        consentLabel: 'I have read and agree to the processing of my personal data as described in this Privacy Policy.',
        consentRequired: 'Please accept the Privacy Policy to continue.',
      },
      form: {
        name: 'Full name',
        namePlaceholder: 'Jane Smith',
        company: 'Company',
        companyPlaceholder: 'Your mill or company',
        email: 'Work email',
        emailPlaceholder: 'jane@company.com',
        stage: 'Where would you use VeritX Vision?',
        stagePlaceholder: 'Select a stage',
        stageOptions: [
          {
            label: 'Fabric production',
            hint: 'Catches defects at the source — during weaving or knitting, before hours of production compound a single flaw.',
          },
          {
            label: 'Finishing',
            hint: 'Flags shade variation, streaks, and contamination during dyeing and coating, before fabric moves downstream.',
          },
          {
            label: 'Final inspection',
            hint: 'Gives you a complete defect map on the full roll before packaging, so cutting and grading decisions are based on real data.',
          },
          {
            label: 'Multiple stages',
            hint: 'Correlates defects across stages to trace recurring issues back to their source on the line.',
          },
        ],
        country: 'Country',
        countryPlaceholder: 'Select a country',
        countries: [
          { group: null, options: ['Mexico'] },
          {
            group: 'Latin America',
            options: [
              'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Costa Rica', 'Cuba',
              'Dominican Republic', 'Ecuador', 'El Salvador', 'Guatemala', 'Honduras',
              'Nicaragua', 'Panama', 'Paraguay', 'Peru', 'Puerto Rico', 'Uruguay', 'Venezuela',
            ],
          },
          {
            group: 'Other countries',
            options: [
              'Australia', 'Bangladesh', 'Belgium', 'Canada', 'China', 'Denmark', 'Egypt',
              'France', 'Germany', 'India', 'Indonesia', 'Israel', 'Italy', 'Japan', 'Kenya',
              'Morocco', 'Netherlands', 'New Zealand', 'Nigeria', 'Norway', 'Pakistan',
              'Philippines', 'Poland', 'Portugal', 'Russia', 'Saudi Arabia', 'South Africa',
              'South Korea', 'Spain', 'Sweden', 'Switzerland', 'Thailand', 'Turkey',
              'United Arab Emirates', 'United Kingdom', 'United States', 'Vietnam', 'Other',
            ],
          },
        ],
        message: 'Tell us about your line',
        messagePlaceholder: 'Fabric type, line speed, current inspection process...',
        submit: 'Request Contact',
      },
    },
    footer: {
      tagline: 'AI-powered fabric inspection for modern textile manufacturers. Enterprise-grade quality control, without the enterprise price.',
      product: 'Product',
      productLinks: [
        { href: '#vision-a', label: 'Vision A' },
        { href: '#how-it-works', label: 'How It Works' },
        { href: '#use-cases', label: 'Use Cases' },
        { href: '#specs', label: 'Specifications' },
      ],
      company: 'Company',
      about: 'About',
      contact: 'Contact',
      legal: 'Legal',
      privacy: 'Privacy Policy',
      terms: 'Terms of Service',
      rights: 'All rights reserved.',
      prototype: 'Prototype product — specifications subject to change.',
    },
  },

  es: {
    nav: {
      home: 'Inicio',
      product: 'Producto',
      productItems: [
        { href: '#vision-a', label: 'Vision A' },
        { href: '#how-it-works', label: 'Cómo funciona' },
        { href: '#use-cases', label: 'Casos de uso' },
        { href: '#comparison', label: 'Por qué VeritX' },
        { href: '#specs', label: 'Especificaciones' },
      ],
      calculator: 'Calculadora',
      aboutLabel: 'Nosotros',
      aboutItems: [
        { href: '#/about', label: 'Quiénes somos' },
        { href: '#contact', label: 'Contacto' },
      ],
    },
    calculatorPage: {
      eyebrow: 'Herramienta ROI',
      title: 'Calculadora de ahorro',
      intro: 'Descubre cuánto podría ahorrar VeritX Vision en tu línea. Estas son las tres fuentes de ahorro medible que los ingenieros de calidad usan para justificar la inversión — ajusta los números con los datos de tu línea; los valores por defecto son ejemplos ilustrativos.',
      resultLabel: 'Ahorro anual',
      formulaLabel: 'Ver fórmula',
      sections: [
        {
          id: 'defects',
          icon: 'eyeCheck',
          title: '1. Reducción de defectos no detectados',
          body: 'Es el ahorro más grande y el más fácil de defender ante finanzas. Hoy, algunos defectos pasan la inspección (manual o por muestreo) y llegan al cliente o generan retrabajo aguas abajo. Un sistema de visión inspecciona el 100% de las piezas de forma consistente, sin fatiga ni variabilidad entre turnos.',
          formula: 'Ahorro anual =\n  (Tasa de defectos ANTES − Tasa de defectos DESPUÉS)\n  × Volumen de producción anual\n  × Costo unitario por defecto\n\nCosto unitario por defecto =\n  Costo de retrabajo/scrap + Costo de garantías/devoluciones\n  + (opcional) Costo reputacional / penalizaciones del cliente',
          fields: [
            { key: 'rateBefore', label: 'Tasa de defectos actual (%)' },
            { key: 'rateAfter', label: 'Tasa de defectos esperada con el sistema (%)' },
            { key: 'volume', label: 'Volumen de producción anual (m² producidos)' },
            { key: 'costPerDefect', label: 'Costo por defecto (MXN)' },
          ],
          hint: 'Para un estimado preciso, usa tu tasa de defectos actual (de tus reportes de calidad), la tasa esperada con el sistema (con base en una prueba piloto o referencia del proveedor), y el costo real de cada defecto — no solo el material, también la mano de obra de retrabajo, la logística de devoluciones y, si aplica, penalizaciones contractuales.',
        },
        {
          id: 'laborHours',
          icon: 'clock',
          title: '2. Reducción de horas-hombre en inspección manual',
          body: 'Si hoy la inspección depende de personas revisando piezas visualmente, el sistema puede liberar ese tiempo para tareas de mayor valor, reducir turnos dedicados solo a inspección, o eliminar cuellos de botella causados por fatiga del inspector.',
          formula: 'Ahorro anual =\n  (Horas-hombre de inspección ANTES − Horas-hombre DESPUÉS)\n  × Costo por hora\n  × Turnos operativos al año',
          fields: [
            { key: 'hoursBefore', label: 'Horas-persona de inspección antes (por turno, todos los inspectores)' },
            { key: 'hoursAfter', label: 'Horas-persona de inspección después (por turno, todos los inspectores)' },
            { key: 'hourlyCost', label: 'Costo por hora (MXN)' },
            { key: 'shiftsPerYear', label: 'Turnos/días operativos al año' },
          ],
          hint: 'Nota importante: este ahorro rara vez significa despidos. Generalmente se traduce en reasignar a tu personal a tareas de mayor valor (mantenimiento, mejora continua) o evitar contratar inspectores adicionales conforme crece tu producción.',
        },
        {
          id: 'lineSpeed',
          icon: 'gauge',
          title: '3. Aumento de velocidad de línea',
          body: 'La inspección manual suele ser el cuello de botella que limita qué tan rápido puede correr la línea. Un sistema de visión inspecciona en tiempo real a la velocidad del proceso, lo que permite subir la velocidad de línea sin sacrificar calidad.',
          formula: 'Ahorro anual =\n  (Nueva velocidad de línea − Velocidad actual) [m/min]\n  × 60 min/hora\n  × Horas de operación al año\n  × Margen de contribución por metro producido',
          fields: [
            { key: 'speedBefore', label: 'Velocidad actual de línea (m/min)' },
            { key: 'speedAfter', label: 'Nueva velocidad de línea (m/min)' },
            { key: 'hoursPerYear', label: 'Horas de operación al año' },
            { key: 'marginPerMeter', label: 'Margen de contribución por metro producido (MXN)' },
          ],
          hint: 'Este ahorro solo aplica si tu negocio puede vender esa capacidad extra (demanda suficiente) o si evita invertir en una segunda línea — vale la pena confirmarlo con tu propio equipo antes de darlo por hecho. La diferencia de velocidad está en metros por minuto, así que la calculadora la convierte a un total anual (×60 minutos/hora × tus horas de operación) antes de aplicar tu margen por metro.',
        },
      ],
      totalTitle: 'Ahorro total estimado',
      totalAnnual: 'Ahorro total anual (suma de los tres)',
      methodologyNote: 'Cómo interpretarlo: suma los tres ahorros anuales para obtener tu total estimado. El ahorro por reducción de defectos (punto 1) suele ser el más fácil de calcular con datos que ya tienes de tus reportes de calidad; los puntos 2 y 3 refuerzan el caso pero dependen de decisiones operativas de tu línea.',
      softSavings: {
        title: 'Más allá de los números: beneficios adicionales',
        intro: 'Estos beneficios son más difíciles de traducir en un número, pero pesan igual de fuerte al armar tu caso de negocio.',
        items: [
          {
            icon: 'shield',
            title: 'Mayor confianza del cliente',
            body: 'Menos envíos defectuosos que llegan al cliente protege tu reputación y reduce el riesgo de perder cuentas por temas de calidad.',
          },
          {
            icon: 'clipboard',
            title: 'Auditorías y certificaciones más simples',
            body: 'Datos de inspección consistentes y documentados agilizan las auditorías ISO y las certificaciones de calidad con tus clientes.',
          },
          {
            icon: 'spark',
            title: 'Mejor experiencia para tu equipo',
            body: 'Libera a los inspectores de revisiones visuales repetitivas y agotadoras para que se enfoquen en tareas de mayor valor.',
          },
          {
            icon: 'activity',
            title: 'Decisiones basadas en datos',
            body: 'Los datos de defectos en tiempo real reemplazan las conjeturas, ayudándote a detectar tendencias y actuar antes de que un problema pequeño crezca.',
          },
        ],
      },
      ctaSub: '¿Quieres una versión personalizada con tus propios números, respaldada por nuestro equipo?',
      cta: 'Solicitar contacto',
    },
    demo: {
      eyebrow: 'Demo en vivo',
      title: 'Mapa de defectos del rollo',
      sub: 'Cada defecto detectado se registra con su posición a lo largo del rollo y a lo ancho de la tela. Esta simulación muestra el mapa que ve un operador al terminar la inspección de un rollo.',
      simulate: 'Simular nuevo rollo',
      defectsDetected: 'defectos detectados',
      rollInfo: 'Rollo de 120 m · 160 cm de ancho de tela',
      xAxis: 'Metros producidos (m)',
      yAxis: 'Ancho de tela (cm)',
      sizeNote: 'El tamaño del cuadro indica la severidad',
      types: { hole: 'Agujero', stain: 'Mancha', weave: 'Error de tejido', other: 'Otro' },
      severities: { low: 'Baja', medium: 'Media', high: 'Alta' },
      tooltip: { position: 'Posición', width: 'Ancho', severity: 'Severidad', confidence: 'Confianza' },
      table: {
        title: 'Registro de defectos',
        cols: ['#', 'Posición (m)', 'Ancho (cm)', 'Tipo', 'Severidad', 'Confianza'],
      },
    },
    hero: {
      eyebrow: 'Inspección de telas con IA',
      titleStart: 'Detecta cada defecto textil. ',
      titleAccent: 'Reduce los costos de inspección a la mitad.',
      lead: 'VeritX Vision utiliza visión por computadora y aprendizaje automático en tiempo real para detectar defectos en la tela sobre la línea de producción — control de calidad de nivel empresarial a una fracción del costo de los sistemas de inspección tradicionales.',
      ctaPrimary: 'Solicitar contacto',
      ctaSecondary: 'Ver cómo funciona',
      stats: [
        { num: '99.2%', label: 'Precisión de detección' },
        { num: 'Flexible', label: 'La instalación se adapta a tu máquina' },
        { num: '~50%', label: 'Menor costo vs. sistemas tradicionales' },
      ],
      defectTags: [
        { label: 'Agujero 98%', style: { top: '22%', left: '30%', width: '60px', height: '40px' } },
        { label: 'Mancha 94%', style: { top: '58%', left: '62%', width: '70px', height: '46px' } },
      ],
      liveFeed: 'Detección en vivo',
      feedDetail: '2 defectos marcados · rollo de 12 ft',
    },
    visionA: {
      eyebrow: 'Conoce el producto',
      title: 'Vision A: inspección que se conecta a tu línea',
      sub: 'Vision A es nuestra primera unidad de inspección — diseñada para ser plug and play, para que cualquier fábrica pase de abrir la caja al control de calidad automatizado sin reingeniería de su línea de producción.',
      features: [
        {
          icon: 'bolt',
          title: 'Plug & play desde el diseño',
          body: 'Vision A llega precalibrada y con el hardware de montaje incluido. Móntala sobre tu línea, conecta corriente y red, y empieza a detectar — sin técnicos especializados ni paros de producción.',
        },
        {
          icon: 'link',
          title: 'Fácil integración',
          body: 'Diseñada para adaptarse a tus telares, líneas de acabado o marcos de inspección existentes sin modificarlos. APIs abiertas y protocolos industriales estándar la conectan a tu MES, ERP o tableros.',
        },
        {
          icon: 'sliders',
          title: 'Flexible a tu proceso',
          body: 'Funciona con distintos tipos de tela, anchos y velocidades de línea. Empieza con una unidad en inspección final o escala a cobertura total — en la nube o en sitio.',
        },
      ],
      tags: ['Precalibrada', 'Instalación flexible', 'API abierta', 'Sin modificar tu línea'],
      videoTitle: 'Video de VeritX Vision',
    },
    howItWorks: {
      eyebrow: 'Cómo funciona',
      title: 'De la tela cruda a datos de calidad accionables',
      sub: 'Un flujo simple de cuatro pasos que se integra a tu línea de producción existente.',
      steps: [
        {
          n: '01',
          title: 'Captura con cámaras y sensores',
          body: 'Cámaras de barrido lineal de alta resolución se montan directamente sobre telares, líneas de acabado o marcos de inspección final existentes — sin necesidad de reemplazar tu equipo actual.',
        },
        {
          n: '02',
          title: 'Análisis con IA en tiempo real',
          body: 'Nuestro modelo de aprendizaje automático analiza las imágenes de la tela cuadro por cuadro, clasificando defectos como agujeros, manchas, errores de tejido y variación de tono en tiempo real.',
        },
        {
          n: '03',
          title: 'Mapeo instantáneo de defectos',
          body: 'Los defectos detectados se registran con posición, tipo y severidad, y se mapean sobre el rollo para que los operadores sepan exactamente dónde inspeccionar o cortar.',
        },
        {
          n: '04',
          title: 'Reportes y optimización de rendimiento',
          body: 'Los datos de calidad alimentan un panel de análisis de tendencias y se integran con tu MES y ecosistema de producción existente, ayudándote a optimizar posiciones de corte, reducir desperdicio y tomar decisiones basadas en datos.',
        },
      ],
      integration: {
        title: 'Acciones definidas por el cliente ante defectos severos',
        body: 'Vision A puede comunicarse directamente con el sistema de control de tu línea para reaccionar automáticamente cuando un defecto supera un umbral de severidad que tú definas. Tú defines las reglas y las acciones — VeritX Vision las ejecuta en tiempo real.',
        examples: [
          { icon: 'pause', rule: 'Defecto severo detectado 5+ veces en 100 m', action: 'detener la línea' },
          { icon: 'tag', rule: 'Defecto severo detectado', action: 'activar la etiquetadora para marcar el defecto' },
        ],
      },
    },
    useCases: {
      eyebrow: 'Dónde encaja VeritX',
      title: 'Cobertura en toda tu línea de tela',
      sub: 'Instálalo en una etapa o a lo largo de todo el flujo de producción — el sistema se adapta a tu configuración.',
      cards: [
        {
          icon: 'weave',
          title: 'Producción de tela',
          body: 'La inspección en línea durante el tejido detecta defectos en el origen — antes de que horas de producción multipliquen una sola falla.',
        },
        {
          icon: 'droplet',
          title: 'Acabado',
          body: 'Monitorea las etapas de teñido, recubrimiento y acabado para detectar variación de tono, rayas y contaminación antes de que la tela avance en el proceso.',
        },
        {
          icon: 'eyeCheck',
          title: 'Inspección final',
          body: 'Inspección automatizada del rollo completo antes de empaque y envío, con un mapa completo de defectos para decisiones de corte y clasificación.',
        },
      ],
    },
    comparison: {
      eyebrow: 'Por qué VeritX Vision',
      title: 'Precisión, flexibilidad y valor — en cada unidad',
      sub: 'VeritX Vision combina detección con IA de nivel industrial con un modelo de precio y despliegue diseñado para fábricas de cualquier tamaño.',
      cards: [
        {
          icon: 'target',
          title: 'Precisión de nivel industrial',
          body: 'La clasificación con IA identifica agujeros, manchas, errores de tejido y variación de tono con precisión de nivel industrial, en tiempo real.',
        },
        {
          icon: 'activity',
          title: 'Inspección en línea en tiempo real',
          body: 'Los defectos se marcan en el momento en que ocurren en la línea, no se descubren después de horas de producción.',
        },
        {
          icon: 'percent',
          title: 'Precio accesible',
          body: 'Diseñado desde cero para ser eficiente en costo, para que el control de calidad con IA quepa en fábricas de cualquier tamaño — no solo en grandes presupuestos empresariales.',
        },
        {
          icon: 'cloud',
          title: 'En la nube o en sitio',
          body: 'Despliega VeritX Vision en la nube, en sitio, o en un esquema híbrido — tu infraestructura, tus reglas.',
        },
      ],
    },
    specs: {
      eyebrow: 'Especificaciones técnicas',
      title: 'Precisión diseñada para pisos de producción',
      sub: 'Rendimiento del prototipo basado en pruebas internas. Ficha técnica completa disponible a solicitud.',
      cards: [
        { val: '99.2%', label: 'Precisión de detección de defectos' },
        { val: '≤5mm', label: 'Tamaño mínimo de defecto detectable' },
        { val: 'Hasta 120m/min', label: 'Velocidad de línea de inspección' },
        { val: 'Entrenamiento a medida', label: 'Clases de defectos aprendidas por material, no fijas' },
      ],
    },
    about: {
      eyebrow: 'Quiénes somos',
      title: 'Ingeniería mexicana, hecha para fabricantes textiles de todo el mundo',
      body: 'VeritX Vision nació en Tlaxcala, México, de la mano de un equipo con años de experiencia en el sector textil, con un objetivo simple: poner el control de calidad con IA al alcance de fábricas textiles de cualquier tamaño — no solo de los fabricantes más grandes. Combinamos visión por computadora, aprendizaje automático y hardware diseñado para integrarse a líneas de producción reales, para que el control de calidad deje de ser un lujo al alcance de unos pocos.',
      facts: [
        { icon: 'pin', label: 'Sede', value: 'Tlaxcala, México' },
        { icon: 'globe', label: 'A quién atendemos', value: 'México, Latinoamérica y el mundo' },
      ],
    },
    contact: {
      eyebrow: 'Contáctanos',
      title: '¿Listo para ver VeritX Vision en tu línea?',
      body: 'Cuéntanos sobre tu configuración de producción y agendaremos una demo personalizada — presencial o por video — para mostrarte cómo VeritX Vision encaja en tu proceso.',
      emailLabel: 'Escríbenos',
      email: 'hello@veritxvision.com',
      locationLabel: 'Ubicados en',
      location: 'Tlaxcala, México — atendiendo a fabricantes textiles de México, Latinoamérica y el mundo',
      success: '¡Gracias por contactarnos! Te responderemos en un día hábil para agendar tu demo.',
      successSchedule: '¡Tu solicitud de cita fue recibida! Te confirmaremos por correo en breve.',
      appointment: {
        modeMessage: 'Enviar un mensaje',
        modeSchedule: 'Agendar una cita',
        timezoneNote: 'Todos los horarios se muestran en hora de Ciudad de México (CDMX).',
        currentTime: 'Hora actual en Ciudad de México',
        selectDate: 'Selecciona una fecha',
        selectTime: 'Selecciona un horario',
        summaryLabel: 'Cita seleccionada',
        required: 'Elige una fecha y un horario para tu cita.',
      },
      privacy: {
        title: 'Cómo usamos tu información',
        summary: 'VeritX Vision recopila la información que nos envíes en este formulario únicamente para responder tu solicitud y agendar una demo.',
        points: [
          'Usamos tus datos únicamente para contactarte sobre VeritX Vision y dar seguimiento a tu solicitud.',
          'Nunca vendemos ni compartimos tu información con terceros con fines de marketing.',
          'Tus datos se almacenan de forma segura y se conservan solo el tiempo necesario para atender tu solicitud.',
          'Puedes solicitar acceso, corrección o eliminación de tus datos en cualquier momento escribiendo a hello@veritxvision.com.',
        ],
        consentLabel: 'He leído y acepto el tratamiento de mis datos personales conforme a este aviso de privacidad.',
        consentRequired: 'Debes aceptar el aviso de privacidad para continuar.',
      },
      form: {
        name: 'Nombre completo',
        namePlaceholder: 'María López',
        company: 'Empresa',
        companyPlaceholder: 'Tu fábrica o empresa',
        email: 'Correo de trabajo',
        emailPlaceholder: 'maria@empresa.com',
        stage: '¿Dónde usarías VeritX Vision?',
        stagePlaceholder: 'Selecciona una etapa',
        stageOptions: [
          {
            label: 'Producción de tela',
            hint: 'Detecta defectos en el origen — durante el tejido, antes de que horas de producción multipliquen una sola falla.',
          },
          {
            label: 'Acabado',
            hint: 'Marca variación de tono, rayas y contaminación durante el teñido y recubrimiento, antes de que la tela avance en el proceso.',
          },
          {
            label: 'Inspección final',
            hint: 'Te da un mapa completo de defectos del rollo antes de empacar, para decidir corte y clasificación con datos reales.',
          },
          {
            label: 'Varias etapas',
            hint: 'Cruza los defectos entre etapas para rastrear problemas recurrentes hasta su origen en la línea.',
          },
        ],
        country: 'País',
        countryPlaceholder: 'Selecciona un país',
        countries: [
          { group: null, options: ['México'] },
          {
            group: 'Latinoamérica',
            options: [
              'Argentina', 'Bolivia', 'Brasil', 'Chile', 'Colombia', 'Costa Rica', 'Cuba',
              'Ecuador', 'El Salvador', 'Guatemala', 'Honduras', 'Nicaragua', 'Panamá',
              'Paraguay', 'Perú', 'Puerto Rico', 'República Dominicana', 'Uruguay', 'Venezuela',
            ],
          },
          {
            group: 'Otros países',
            options: [
              'Alemania', 'Arabia Saudita', 'Australia', 'Bangladés', 'Bélgica', 'Canadá',
              'China', 'Corea del Sur', 'Dinamarca', 'Egipto', 'Emiratos Árabes Unidos',
              'España', 'Estados Unidos', 'Filipinas', 'Francia', 'India', 'Indonesia',
              'Israel', 'Italia', 'Japón', 'Kenia', 'Marruecos', 'Nigeria', 'Noruega',
              'Nueva Zelanda', 'Países Bajos', 'Pakistán', 'Polonia', 'Portugal',
              'Reino Unido', 'Rusia', 'Sudáfrica', 'Suecia', 'Suiza', 'Tailandia',
              'Turquía', 'Vietnam', 'Otro país',
            ],
          },
        ],
        message: 'Cuéntanos sobre tu línea',
        messagePlaceholder: 'Tipo de tela, velocidad de línea, proceso de inspección actual...',
        submit: 'Solicitar contacto',
      },
    },
    footer: {
      tagline: 'Inspección de telas con IA para fabricantes textiles modernos. Control de calidad de nivel empresarial, sin el precio empresarial.',
      product: 'Producto',
      productLinks: [
        { href: '#vision-a', label: 'Vision A' },
        { href: '#how-it-works', label: 'Cómo funciona' },
        { href: '#use-cases', label: 'Casos de uso' },
        { href: '#specs', label: 'Especificaciones' },
      ],
      company: 'Empresa',
      about: 'Nosotros',
      contact: 'Contacto',
      legal: 'Legal',
      privacy: 'Aviso de privacidad',
      terms: 'Términos de servicio',
      rights: 'Todos los derechos reservados.',
      prototype: 'Producto prototipo — especificaciones sujetas a cambio.',
    },
  },
}
```

---

## 10. Established decisions & constraints (read before changing content)

These are product/brand decisions that were **explicitly requested** during development. Don't
casually reverse them without the user re-confirming — re-litigating them wastes a round-trip.

1. **Default language is Spanish**, not browser-detected. English is opt-in via the header switcher.
2. **No competitor comparisons anywhere on the site.** The "Why VeritX Vision" section was rewritten
   from a "VeritX vs. Legacy Systems" table into standalone value-prop cards for exactly this reason.
   Don't reintroduce head-to-head competitor framing (explicit or implied) in that section or elsewhere.
3. **No specific installation-time promises** (e.g. "installs in < 48h"). Physical installation time
   varies by machine, so every mention of install time was changed to communicate **flexibility**
   instead of a fixed duration — see the hero stat, Vision A tags, and the "Why VeritX Vision" cards.
4. **CTA copy is "Request Contact" / "Solicitar contacto"** everywhere (hero, contact form submit,
   calculator placeholder) — not "Request a Demo"/"Solicitar demo" (an earlier version used that
   wording; it was explicitly renamed).
5. **No CTA button in the header** — removed once the header got crowded with the language switcher
   and 3 nav dropdowns. The primary CTA lives in content (hero, contact section, calculator page).
6. **Company facts, baked into copy:** HQ in **Tlaxcala, Mexico**; serves **Mexico, Latin America, and
   the world**; contact email **hello@veritxvision.com**. A "Hecho en México" footer badge with a small
   Mexican-flag-colored bar is present regardless of site language (hardcoded Spanish text — this is a
   fixed brand mark, not meant to translate to "Made in Mexico" in the English version).
7. **Superseded:** Demo and Calculator were briefly grouped under one "Tools"/"Herramientas" nav
   dropdown. **Demo was later explicitly removed from the nav entirely** (the page/route still exists,
   just unlinked), which left Tools with a single item, so it was collapsed into a direct "Calculator"
   top-level link instead of a single-item dropdown. Current nav: Home (link) → Product (dropdown) →
   Calculator (link) → About Us (dropdown). See §8's `Header()` entry.
8. **Contact form field order:** Name + Company (2-col row) → Work email + Country (2-col row) → Stage
   select (full width, with a dynamic hint) → Message (textarea) → Privacy policy `<details>` →
   required consent checkbox → Submit button.
9. **Country select ordering is fixed:** Mexico first (standalone, no group label), then a "Latin
   America"/"Latinoamérica" `<optgroup>`, then an "Other countries"/"Otros países" `<optgroup>` — in
   that order, always. This was an explicit ordering requirement, not alphabetical-everything.
10. **The "stage" select shows a contextual hint** below it in light gray (`.field-hint`, `var(--gray-500)`)
    explaining, per selected stage, why deploying there matters — updates live as the visitor picks a
    different option. This was an explicit request ("agrega ... una descripción corta del por qué...").
11. **Contact form requires explicit consent** — a required checkbox (blocks native form submission via
    HTML5 validation + a `setCustomValidity` localized message) paired with a collapsible `<details>`
    block summarizing what data is collected and why. This exists because of an explicit "add a data
    policy and request consent" instruction.
12. **Icons are hand-drawn SVG, not emoji**, tinted with the brand cyan — an explicit reversal of an
    earlier emoji-based version ("cambia los emojis por iconos más serios..."). The one deliberate
    exception is the language-switcher's flag emoji (🇲🇽/🇺🇸), which represent language/country identity
    rather than being decorative.
13. **Section vertical spacing was reduced 20%** from the original design values — see §7. If asked to
    adjust spacing again, treat the current CSS values as the baseline.
14. **The demo-page defect-map color palette is validated**, not arbitrary — see the comment at the top
    of `DemoPage.jsx`: colors were checked for CVD-safety and contrast against the navy map surface
    (`#10294a`) using the project's internal data-viz accessibility method (all-pairs CVD ΔE ≥ 9.4,
    normal-vision ΔE ≥ 20.9, contrast ≥ 3:1). If defect-type colors are ever changed, re-validate rather
    than picking colors by eye.
15. **The product video belongs on the Vision A / product-description section**, not the About page —
    explicitly corrected after an initial placement in About. See §8's `VisionA()` entry.
16. **The `#/calculator` page is a real, interactive ROI calculator**, sourced from a client-provided
    document (`Guia_Ingeniero_Calidad_ROI.docx`, a "Quality Engineer's ROI Guide") — not a placeholder.
    Three savings sections (defect reduction, manual-inspection labor hours, line-speed increase), each
    with editable inputs (defaults = the guide's own worked examples), a live-computed annual-savings
    result, a collapsible formula box, and a hint; a total card sums the three. **Deliberately simplified
    after the first version**: an initial-investment/payback-period feature and a recurring-annual-cost
    input existed briefly and were removed by request — the total card is now just the sum of the three
    annual savings, nothing else. The "annual production volume" field reads in **square meters produced
    (m²)**, not generic "pieces", to match the textile/fabric context. All labels/formulas/hints are
    bilingual (`translations.js` → `calculatorPage`); the numeric defaults and the calculation functions
    themselves live in `CalculatorPage.jsx` (`DEFAULTS`, `CALC`), not in translations, since they aren't
    language-dependent. Numeric inputs (`CalcNumberInput`) show thousand separators at rest and switch to
    raw digits while focused, so live comma-insertion doesn't disrupt typing/cursor position. **The
    section hints and the methodology note were rewritten once already** — the source guide phrases them
    for an internal salesperson ("qué datos pedirle al cliente", "cómo presentarlo ante el cliente"), but
    the actual reader is the website visitor filling out the calculator themselves, who *is* that client.
    All four were reframed to speak directly to the visitor ("usa tu tasa de defectos...", "con tu propio
    equipo..."). If more copy is ported from the source document later, apply the same reframing — don't
    carry over salesperson-perspective phrasing verbatim. **Line-speed formula was corrected and
    simplified (resolves the earlier flagged discrepancy):** the original formula, ported from the
    source guide, multiplied a speed difference in m/min directly by hours/year with no min→hour
    conversion — a genuine unit-consistency bug (this is what produced the guide-vs-calculator mismatch
    flagged previously, not just a copy-over error). Fixed to `(speedAfter − speedBefore) × 60 ×
    hoursPerYear × marginPerMeter`. Also dropped the `unitsPerMeter` × `marginPerUnit` two-step in favor
    of a single `marginPerMeter` field (contribution margin per linear meter of fabric produced) —
    removes an extra error-prone hop and matches the m²-based framing already used in the
    defect-reduction section instead of introducing an unrelated "unit" concept. New default
    (`marginPerMeter: 0.5`) gives $3,600,000 MXN for that section with the same speed/hours defaults as
    before, and $4,550,000 MXN total. Formula/fields/hint copy updated in all three languages.
17. **Contact form has a "Schedule a meeting" mode** (`mode-toggle`, `mode` state), alongside the default
    "Send a message" mode. In schedule mode, `AppointmentPicker` (a hand-built month calendar, no date
    library) shows a fixed set of business-hour time slots — `09:00, 10:00, 11:00, 12:00, 13:00, 16:00,
    17:00` — explicitly declared and labeled as **Mexico City time (CDMX)**, per an explicit "debe estar
    en horario méxico" requirement. These are illustrative fixed slots, not pulled from a real calendar
    or availability system — there is no backend, same limitation as the rest of the contact form (§11).
    Weekends and past dates are disabled in the calendar; the "previous month" nav button is disabled
    once viewing the current month (can't book in the past). Submission in schedule mode is blocked
    client-side (`field-error`, translated) until both a date and a time are picked; on success it shows
    `t.contact.successSchedule` instead of the generic `t.contact.success`. The current Mexico City clock
    time is shown for context via `Intl.DateTimeFormat(..., { timeZone: 'America/Mexico_City' })` — the
    one place real timezone conversion is used; the slot list itself is just fixed local-time strings,
    not converted from/to the visitor's own timezone.
18. **The calculator has a "soft savings" section** (`t.calculatorPage.softSavings`), below the total
    card, before the closing CTA — four qualitative benefit cards (customer trust, easier audits/
    certifications, employee experience, data-driven decisions) with no dollar figure, unlike the three
    formula-driven sections above them. **Not sourced from the ROI guide docx** (that document only
    covered the three quantifiable savings) — authored to round out the business case with the kind of
    benefits that are hard to put a number on but still matter. Reuses the existing `.usecases-grid
    why-grid` / `.usecase-card` / `.usecase-icon` visual pattern (§7) rather than inventing new card
    styling — icons: `shield`, `clipboard`, `spark`, `activity` (the last one reused from the "Why VeritX
    Vision" section).
19. **The calculator has a currency selector** (`.calc-currency`, above the three formula sections) —
    `t.calculatorPage.currencyOptions` follows the **same grouping convention as the contact form's
    country select** (§10.9): Mexico standalone first, then a "Latin America" `<optgroup>` (ARS, BOB,
    BRL, CLP, COP, CRC, DOP, GTQ, HNL, NIO, PYG, PEN, UYU, VES), then an "Other currencies" `<optgroup>`
    (USD, EUR) — keep new currencies in that same three-tier order, don't just alphabetize or append.
    **The calculator does not convert between currencies** — selecting a currency only changes the label
    suffix on the three monetary fields (`MONEY_FIELD_KEYS` in `CalculatorPage.jsx`: `costPerDefect`,
    `hourlyCost`, `marginPerMeter`) and the `Intl.NumberFormat` currency code used to render every result;
    the numbers the visitor types are trusted to already be in the selected currency. `formatCurrency(n,
    lang, currency)` replaced the old currency-hardcoded `formatMXN`.
20. **The calculator has a "send me these results" panel** (`.calc-send`, directly below the total
    card), collecting name + email and, on submit, just flips local `sent` state to show a thank-you
    message — **same no-backend pattern as the contact form** (§11), not a real email dispatch. An
    earlier version tried to route around the missing backend with a `mailto:` link (opening the
    visitor's own mail client with a pre-filled draft) — **explicitly replaced** after feedback that the
    flow should read as "you ask us, we handle sending it" (matching the Contact form's own framing),
    not "here's a drafted email, you send it yourself." Don't reintroduce the `mailto:` approach without
    a fresh request.
21. **The "How to read this" methodology note** (`t.calculatorPage.methodologyNote`) **lives inside the
    total-savings card** (`.calc-total`), directly under the total row — not as a standalone paragraph
    between the total card and the "send results" panel, which is where it originally sat. Styled via
    `.calc-total .calc-methodology` (translucent white text, no `max-width` cap) since it now sits on the
    total card's dark navy background instead of the page's light background.
22. **The nav/page label changed from "Calculator"/"Calculadora" to "Calculate Savings"/"Calcular
    ahorros"** (`t.nav.calculator`) — the page's own `<h1>` (`t.calculatorPage.title`, "Savings
    calculator"/"Calculadora de ahorro") was left as-is; only the short nav-entry name changed.
23. **The hero's middle stat chip is `'100%'` / "Of rolls inspected — not sampled"**, not the earlier
    `'Flexible'` / "Install adapts to your machine" — see §8's `Hero()` entry. Don't revert to a
    non-numeric stat there without a fresh request; the other two stats (`99.2%`, `~50%`) are unchanged.
24. **The About page includes a Mexico locator map** (`<MexicoMap/>`, inside `.about-facts`, below the
    HQ/coverage facts) highlighting Tlaxcala with its three true bordering states labeled (Puebla,
    Hidalgo, México/State of Mexico — verified by nearest-point distance against real boundary data, not
    guessed) and every other state rendered unlabeled for context. **Deliberately only the three
    neighbors are labeled, and Tlaxcala itself is not** — it's identified instead by fill color (solid
    cyan) plus a pulsing marker dot, with a small caption ("● Tlaxcala") below the map, per an explicit
    "highlight Tlaxcala, only label the neighboring states" request. See §14.7 for the data/build
    pipeline (this isn't hand-drawn — regenerate, don't hand-edit the path data if it ever needs to
    change).
25. **The About page has a "Vision" and "Mission" section** (`.vm-section`, its own `<section>` right
    after the intro/facts grid) — two cards (`vm-grid`/`vm-card`, reusing the `vf-icon` circular-icon
    pattern) under `t.about.vision` / `t.about.mission` (`icon`, `title`, `body`). Background is
    `var(--white)` via `.demo-section.vm-section` (needs both classes for specificity — see the CSS
    comment) so it visually separates from the gray-50 intro section above it.
26. **The Contact section's WhatsApp number and the footer's target LinkedIn URL are both currently
    unverified/placeholder-status from the codebase's point of view** — WhatsApp (`+52 246 241 6056`) was
    given directly by the user and is wired as a real `wa.me` link; LinkedIn has **no URL at all** yet
    (rendered as a non-linked icon — see §8's `Footer()` entry and §11). If asked to "add more social
    links" or "fix the WhatsApp number," check with the user for the real destination first — don't
    invent one.

---

## 11. Known gaps / intentionally unfinished

> This is a point-in-time snapshot. **GitHub issues are the live list** — check them for the current
> state, and update this section when you close an item out (see §13).

- **The contact form does not submit anywhere — including appointment requests.** `Contact()`'s
  `handleSubmit` just calls `e.preventDefault()` and flips local `submitted` state to show a static
  success message (`t.contact.success` or, in schedule mode, `t.contact.successSchedule`). There is no
  backend, no email service (e.g. Formspree), no API call, and **no real calendar/availability system**
  behind the appointment picker — its time slots are a fixed illustrative list (§10.17), not checked
  against anyone's actual schedule, so double-booking isn't prevented. If the user asks "why didn't I
  get an email" or "why did it let two people pick the same slot", this is why — it's
  cosmetic/prototype-only, flagged previously, not yet wired up.
- **Footer "Company" column** now has exactly two real links: "About"/"Nosotros" (`href="#/about"`,
  wired to the real About page) and "Contact"/"Contacto" (`href="#contact"`). "Careers"/"Vacantes" was
  removed entirely (was a non-functional placeholder with no page behind it) — do not re-add a Careers
  link without a real destination for it.
- **Footer "Legal" column:** "Privacy Policy"/"Aviso de privacidad" is now a real link
  (`href="#/privacy"`) to `PrivacyPolicyPage.jsx` — content in `translations.js` → `privacyPage`
  (all three languages), covering what data the site actually collects (contact form, account
  registration, support tickets, the language preference kept in `localStorage`), that there's no
  tracking/analytics, the `youtube-nocookie.com` embed, and the WhatsApp link being governed by its
  own policy. **"Terms of Service"/"Términos de servicio" is still a plain `<span>`** — no
  terms-of-service page exists yet (separate TODO item, not done in this pass).
- **No web font is actually loaded** — `index.css` requests `'Inter'` first in the font stack, but
  nothing imports/links Inter, so every browser silently falls back to its next system font.
- **Minimal automated tests only** (calculator formulas, `auth.js`); no UI tests, no linter/formatter.
- **The footer's LinkedIn icon has no real URL** — rendered as a non-interactive `<span>`, not an
  `<a>`, specifically because no company LinkedIn page was provided (see §10.26). Wire it up as a real
  link (and probably add `target="_blank" rel="noopener noreferrer"`, matching the WhatsApp link
  pattern) as soon as the user gives you the actual URL — don't fabricate one.
- **The entire customer portal (§14) is a client-only simulation, not a real backend.** This is the
  single biggest gap added this round — see §14.8 for the full breakdown (no real server, no real email
  delivery, SHA-256-in-JS instead of bcrypt/Argon2, client-side-only and trivially bypassable rate
  limiting, no audit log, no HttpOnly/Secure/SameSite session cookies since there's no server to set
  them). Read §14.8 before telling a user any part of the auth flow is "production-ready."

---

## 12. Recipes for common changes

- **Change copy in an existing section:** edit the matching keys in `translations.js`, in **both**
  `en` and `es` blocks. There's no fallback language — a missing key renders `undefined`.
- **Add a new home-page section:** write a new function component in `App.jsx` (steal the shape of an
  existing one, e.g. `UseCases()`), add a matching content object to `translations.js` (both
  languages), add its `<Whatever/>` to the `route === 'home'` block in `Site()`, and — if it should be
  reachable from the nav — add an entry to `nav.productItems` (marketing content) or `nav.aboutItems`
  (company-facing pages) in both languages, or add a new plain top-level link in `Header()` (see the
  `nav.calculator` link for the pattern) if it doesn't belong in either dropdown.
- **Add a brand-new page (own hash route):** create `src/WhateverPage.jsx` following the
  `AboutPage.jsx`/`CalculatorPage.jsx` pattern (`demo-hero` + `demo-section`), add a route branch in
  `useRoute()` and `Site()` (see §4), and add its translations under a new top-level key in both
  language blocks.
- **Add/replace an icon:** add an entry to `ICON_PATHS` in `icons.jsx` (see §6), reference it by name
  from wherever needs it.
- **Add a language:** see the end of §5.
- **Add a new customer-portal screen:** see §14.9.
- **Regenerate the Mexico map:** see §14.7.
- **Deploy:** merge the PR into `main`; Vercel deploys production on its own. Each PR gets a Vercel
  preview first (§2).

---

## 13. Pending work — GitHub issues

Pending items live in **GitHub issues** (the old root `TODO.md` was migrated there in 2026-10).
Features go through Spec Kit (`specs/NNN-name/`, see `CLAUDE.md`); small fixes go straight to a PR.

- When a PR closes an item, reference the issue (`Closes #N`).
- New gaps or "track this for later" requests become new issues, not chat notes.
- If closing or adding an issue makes §11 stale, update §11 in the same PR.

---

## 14. Customer Portal (Login / Register / Recovery / Vision Home)

### 14.1 What this is and why it's built the way it is

A full login → register → verify-email → forgot-password/recover-username → account-dashboard flow,
added from a detailed client-supplied spec (security-conscious: generic non-enumerating error messages,
rate limiting, token expiry, hashed passwords, HttpOnly/Secure session cookies, audit logs — the kind of
spec you'd hand a team with a real backend). **This site has no backend and never has** (§2: static
Vite build, deployed to Vercel, no server runtime at all) — so rather than silently
dropping the request or blocking on "you need a backend first," the whole thing was built as a
**client-only simulation**: a `localStorage`-backed "auth service" (`auth.js`) standing in for a real
API, following the exact same precedent already established by the contact form and appointment picker
(§11) — fully clickable, end-to-end testable, honest in the UI and in this document about what's real
and what isn't. **Read §14.8 before presenting any part of this as production-ready to a user** — it is
not, by design, and several of the spec's actual security requirements (bcrypt/Argon2, server-side rate
limiting, audit logs, HttpOnly cookies) are architecturally impossible without a real backend.

Routes: see the table in §4. Files: see §3 (`auth.js`, `LoginPage.jsx`, `RegisterPage.jsx`,
`VerifyEmailPage.jsx`, `ForgotPasswordPage.jsx`, `RecoverUsernamePage.jsx`, `VisionHomePage.jsx`,
`MexicoMap.jsx`, `mexicoMapData.js`). Translations: one top-level `auth` key in `translations.js` (both
languages) — `navLogin`, `navAccount`, `dummy`, `login`, `register`, `verifyEmail`, `forgotPassword`,
`resetPassword`, `recoverUsername`, `visionHome`. **Not reproduced verbatim in §9** (unlike the rest of
the site's copy) — it's large and would bloat this document without much benefit; read `translations.js`
directly for exact strings, and treat this section as the shape/behavior reference instead.

Shared visual pattern: every portal page uses the same `demo-hero` + `demo-section` shell as the other
satellite pages (§7), with form content centered in a new `.auth-shell`/`.auth-card` wrapper
(`.auth-card` just adds the `.lead-form` white-card look to a narrower, centered column). Password
fields use a shared `.password-field`/`.password-toggle` pattern (`eye`/`eyeOff` icons, §6). Demo-mode
disclosures use a shared `.dummy-panel` component style (amber, `flask` icon) across the dummy-login
banner, the register/forgot-password "here's your verification/reset link" boxes, and the
recover-username "here's your username" box.

### 14.2 `auth.js` — the simulated backend

Everything is `localStorage`-backed, under `veritx-auth-*` keys:

| key | shape | purpose |
|---|---|---|
| `veritx-auth-users` | `[{ firstName, lastName, email, username, passwordHash, verified, createdAt, account }]` | the "user table". `account` is `null` for every freshly registered user (§14.6's empty state) or a `{status, subscriptions, payments}` object. |
| `veritx-auth-session` | `{ username, isDummy, loginAt } \| null` | the "session" — just a localStorage value, not a cookie (see §14.8). |
| `veritx-auth-verify-tokens` | `[{ token, username, expiresAt }]` | 24h TTL. **Not deleted on successful verification** (see the StrictMode note below) — only pruned by expiry. |
| `veritx-auth-reset-tokens` | `[{ token, username, expiresAt }]` | 30min TTL. Deleted on successful use (one-shot, unlike verify tokens — see below for why the two behave differently). |
| `veritx-auth-attempts` | `{ [identifier]: { count, lockedUntil } }` | per-identifier failed-login counter for the rate-limit simulation. |

Passwords are hashed with `crypto.subtle.digest('SHA-256', ...)` before being stored — **not a
substitute for server-side bcrypt/Argon2** (no salt rounds, no memory-hardness; this is purely "don't
keep raw plaintext sitting in localStorage," not real credential security) — see §14.8.

**Dummy test login** (`test` / `vision`, per the original spec's "modo de prueba"): checked directly
inside `login()`, gated behind `export const IS_DUMMY_LOGIN_ENABLED = import.meta.env.DEV`. This is a
**real, load-bearing gate, not just a UI banner** — Vite replaces `import.meta.env.DEV` with the literal
`false` at build time for a production build (`npm run build`, which is what
Vercel runs — §2), so the entire dummy-login code path is dead code and unreachable on the live site,
satisfying the spec's "must be fully disabled in production" requirement for real, not just cosmetically
via a banner. It only actually works under `npm run dev`. A logged-in dummy session resolves (in
`getCurrentUser()`) to a fixed in-memory `DEMO_ACCOUNT` (2 active subscriptions, 2 upcoming payments) so
the "account assigned" state of Vision Home (§14.6) has something to render in dev without needing to
register a real user first.

**Rate limiting** (`login()`): after `MAX_ATTEMPTS = 5` failed attempts for the same identifier
(email/username, lowercased), a 60s lockout is recorded in `veritx-auth-attempts` and further attempts
return `{ok:false, error:'locked'}` until it expires. **This is client-side only and trivially
bypassable** (clear `localStorage`, or just call `auth.js`'s exports directly from the console) — it
exists to make the UI demonstrate the *behavior* the spec asked for, not to actually rate-limit anyone.
Real rate limiting needs a backend. Flagged again in §14.8/§11.

**Cross-component reactivity — `useAuthSession()`:** components (`Header()`, `VisionHomePage`) need to
re-render when login/logout happens *in the same tab*, which a plain `localStorage` read on mount can't
do (the browser's own `storage` event only fires in *other* tabs). `auth.js` keeps a small in-module
`Set` of listener callbacks; `login()`/`logout()` call an internal `notifyAuthChange()` after writing to
`veritx-auth-session`, and `useAuthSession()` (a hook, also exported from `auth.js`) subscribes to that
set plus the cross-tab `storage` event, returning the current session and forcing a re-render on either
signal. If you add a new place that needs to know "is someone logged in," use this hook — don't read
`getSession()` once and cache it in local state, it'll go stale the moment the user logs in/out
elsewhere on the page.

**A real bug found and fixed during this build, worth knowing about if you touch `verifyEmailToken` or
`ResetPasswordView` again:** `src/main.jsx` wraps the app in `React.StrictMode`, which **double-invokes
effects in development** as a side-effect-detection aid (not present in production builds). Two spots
in this codebase are/were sensitive to that:
- `verifyEmailToken(token)` used to delete the token from `veritx-auth-verify-tokens` on success. Under
  StrictMode, `VerifyEmailPage`'s mount effect ran twice: the first call verified and deleted the token;
  the second call, immediately after, found no token and returned `'invalid'` — overwriting the
  already-correct "success" UI state with an error, in dev only. **Fixed by making the function
  idempotent instead of one-shot**: it now checks `if (!user.verified)` before flipping the flag and
  never deletes the token (only expiry prunes it) — verifying an already-verified account is a no-op
  success, not an error. This is also just more *correct* behavior on its own merits (a user re-clicking
  an old confirmation email link, or a mail client prefetching the link, shouldn't see "invalid link"
  for a token that already worked), not only a StrictMode workaround.
- `ForgotPasswordPage`'s `ResetPasswordView` computed `const check = validateResetToken(token)` directly
  in the render body. `resetPassword()` *does* delete the reset token on success (intentionally — unlike
  verify tokens, a password-reset link should be genuinely one-shot). After a successful submit,
  `setDone(true)` triggers a re-render, which re-ran `validateResetToken` against the now-deleted token
  and got `invalid` — and since the component checked `!check.ok` before checking `done`, it showed
  "this link is invalid or expired" instead of "password updated," even though the password change had
  already succeeded. **Fixed by freezing `check` at mount** via `useState(() => validateResetToken(token))`
  instead of recomputing it every render. General lesson for this codebase: **never call a
  token-consuming `auth.js` function directly in a render body or in an effect without a stable
  freeze/guard** — validity checks that have side effects (or that check state a submit handler is about
  to mutate) need to be computed once, not on every re-render.

### 14.3 Login (`LoginPage.jsx`)

Fields: identifier (email or username) + password (with show/hide toggle). `IS_DUMMY_LOGIN_ENABLED`
gates a `.dummy-panel` above the form with a "fill in test credentials" button (sets the fields to
`test`/`vision` — doesn't auto-submit). Errors are looked up from `t.auth.login.errors` by the error
code `login()` returns (`invalid_credentials`, `unverified`, `locked`) — generic on purpose, per the
non-enumeration requirement in the original spec (never says which of email/username/password was
wrong). Success navigates to `#/vision-home` via `window.location.hash = ...`.

### 14.4 Register (`RegisterPage.jsx`) + email verification (`VerifyEmailPage.jsx`)

Fields: first name, last name, email, username, password, confirm password. Client-side validation
(`isValidEmail`, `isValidUsername`, `isPasswordCommon`, password length ≥ 12, confirm-match) runs
before calling `registerUser()`. **Email uniqueness is enumeration-safe** (a duplicate email still
returns `{ok:true}` with no verification token, so the UI can't distinguish "sent" from "already
registered" — matching the spec's "don't reveal if an email exists" requirement); **username
uniqueness is not** (`{ok:false, error:'username_taken'}`, shown inline) — this asymmetry is
intentional and mirrors the source spec, which treats username availability as normal expected UX (like
any signup form) but treats email existence as sensitive.

On success, the page shows a "check your email" screen with `t.auth.register.successBody`, and —
**because there is no real email service** — a `.dummy-panel` showing the actual
`#/verify-email?token=...` link directly in the page (always shown when a token exists, not gated to
`IS_DUMMY_LOGIN_ENABLED`, since without it there's no way to complete the flow in this demo at all — the
gate only controls the fixed `test`/`vision` shortcut credentials, not the general "no backend" reality
of the rest of the portal). `VerifyEmailPage` reads the token from the hash query string, calls
`verifyEmailToken()` (idempotent — §14.2), and shows success/error accordingly.

### 14.5 Forgot password / recover username (`ForgotPasswordPage.jsx`, `RecoverUsernamePage.jsx`)

`ForgotPasswordPage` is **one component covering two views**, switched on whether `?token=` is present
in the hash: no token → `RequestView` (identifier input, generic "if registered..." message + dev-panel
reset link on submit); token present → `ResetPasswordView` (new password + confirm, blocked client-side
below 12 chars / a common password / mismatch, then `resetPassword()` — which also calls `logout()`
internally so any existing session is invalidated after a password change, and clears that identifier's
rate-limit counter). `RecoverUsernamePage` is the simpler one-view equivalent for "I forgot my
username" — email in, generic message + dev-panel showing the actual username out. Both request views
return the same generic copy regardless of whether the identifier actually matched a user, per the
non-enumeration requirement (§14.2/§14.4).

**Scroll-into-view on every state transition:** all four success/result screens across these two files
(register's "check your email," the two forgot-password result states, recover-username's result) use
the same `resultRef`/`doneRef` + `useEffect(() => ref.current?.scrollIntoView({behavior:'smooth',
block:'center'}), [state])` pattern already established for the contact form (§8's `Contact()` entry).
Reason: these pages are short, but submitting can still shrink the visible content (a filled form
collapsing to a couple of lines of success text) enough that, on a scrolled-down viewport, the result
would otherwise render below the fold with the footer covering it — flagged explicitly during testing
("cada vez que un formulario se completa, el footer le quita el espacio... haz scroll automático").
Apply the same pattern to any new form/result transition added to these pages.

### 14.6 Vision Home (`VisionHomePage.jsx`) — the account dashboard

**Route guard:** not a real protected route (there's no server to enforce that) — a `useEffect` checks
`useAuthSession()` on render and redirects to `#/login` if there's no session; the component returns
`null` until a session exists, so there's no flash of dashboard content before the redirect fires.

**Breadcrumb, not an eyebrow pill:** unlike every other satellite page (which use the `.eyebrow` pill in
the dark `demo-hero` banner — §7), Vision Home uses a `.breadcrumb` ("Home / Vision Home") **inside the
light `demo-section` content area**, above the dummy-panel/cards — not in the dark hero. This was an
explicit two-step change: first the eyebrow pill was replaced with a breadcrumb, then the breadcrumb
was moved out of the hero into the content section. If Vision Home ever needs breadcrumbs again
elsewhere, follow this placement (content section, not hero) rather than the eyebrow-pill convention
used everywhere else.

**Two account states**, driven by `getCurrentUser().account`:
- **No account** (`account === null` — the state every freshly registered real user starts in):
  `.vh-empty-state` card, "You don't have an account assigned yet," with two CTAs that both link to
  `#contact` (the *marketing* Contact section, on the `home` route) rather than opening any dashboard-
  local form — reuses the site's one real lead-capture surface instead of duplicating it.
- **Account assigned** (dummy test login always has one — `DEMO_ACCOUNT`, §14.2): a `.vh-grid` of three
  cards — Active Subscriptions (list + count), Next Payment Date (soonest of `account.payments`, with a
  "view all" toggle), Amount to Pay (next payment's amount, with a "view billing detail" toggle listing
  subscription names). All dates/currency formatted via `Intl.DateTimeFormat`/`Intl.NumberFormat` for
  the current `lang`.

**Support + appointment cards** (below the state-dependent block above, shown regardless of account
state): "Technical support" opens an inline `SupportTicketForm` (subject, description, priority select —
**no file-attachment field**, since there's nowhere for an upload to go without a backend; flagged in
§11/TODO) that on submit just flips local `sent` state, same no-backend pattern as everything else here.
"Schedule a meeting" is a **plain link to `#contact`**, not a duplicated appointment widget — the
marketing Contact section already has a full working `AppointmentPicker` (§10.17); this CTA deliberately
reuses it instead of re-implementing a second calendar component inline. Don't build a second
`AppointmentPicker` for Vision Home without a specific reason to diverge from the existing one.

**Logout lives in the header's account dropdown, not on this page.** An earlier version had a standalone
"Log out" button in Vision Home's own header row — **explicitly moved** into the `Header()` account
dropdown (§8's `Header()` entry) after feedback that it belonged in a menu behind the account icon, not
as a page-level button. The status badge ("Active"/"Trial"/"Pending assignment," `t.auth.visionHome.status`)
that used to sit next to that button was also removed outright (not relocated) in the same pass — the
`status`/`status-active`/`status-trial`/`status-pending` CSS and the badge markup are gone; the
translation keys under `t.auth.visionHome.status` are still defined (reused by the subscription-list
pills, `.vh-pill`) but nothing currently renders a page-level account-status badge. Don't re-add one
without checking whether that omission was intentional (it was) or just re-add it as a
`.vh-pill`-style badge if asked.

### 14.7 Mexico locator map (`MexicoMap.jsx` / `mexicoMapData.js`)

Used by `AboutPage.jsx` (§10.24), not part of the auth system itself, but built in the same session and
documented here since it's a generated-data component like nothing else in this codebase.

**Data provenance:** `mexicoMapData.js` was generated once from a public-domain Mexico state-boundary
GeoJSON (`angelnmara/geojson`, file `mexicoHigh.json` — a small, precise, MIT-ish-licensed dataset
commonly used in D3 Mexico-choropleth tutorials; fetched directly, not eyeballed/hand-drawn) via a
one-off Node script (not checked into the repo — this was a scratch/throwaway build step, not a
reusable tool). The script: (1) projects lon/lat to a 760×481 SVG viewbox using a simple
equirectangular projection with longitude scaled by `cos(meanLatitude)` to reduce east-west distortion
at Mexico's latitude; (2) simplifies every ring with a from-scratch Douglas-Peucker implementation
(ε≈0.7px in projected space) to cut a ~185KB raw GeoJSON down to ~30KB of SVG path data — still enough
detail to read as "Mexico," light enough to inline; (3) computes each state's area-weighted centroid
(shoelace formula) on its largest ring, for icon/label placement; (4) **verifies Tlaxcala's true
neighbors by nearest-point distance** between polygons rather than guessing from memory — confirmed
Puebla, Hidalgo, and México (State of Mexico) all touch Tlaxcala (distance 0) and Veracruz/CDMX/Morelos
don't (0.24–0.34° away), which is what's reflected in the "only label the neighbors" behavior (§10.24).

**Label placement:** neighbor labels use **manually nudged offsets** (`LABEL_OFFSET` in
`MexicoMap.jsx`), not the raw computed centroids — Puebla's area-weighted centroid lands almost on top
of Tlaxcala's tiny shape (Puebla wraps around most of it), so the raw centroid would put "Puebla" text
directly over the highlighted state. The nudges push each label into open space inside that state's own
territory instead. If the map is ever regenerated from source data, **re-check these offsets** — a
different simplification epsilon or projection could shift centroids enough to need new nudge values.

**To regenerate:** re-fetch `mexicoHigh.json` (or an updated equivalent), re-run the same
projection/simplification/centroid steps described above (rewrite the one-off script — it wasn't
retained), re-verify neighbor adjacency by distance rather than assuming it hasn't changed, and
re-tune `LABEL_OFFSET`. **Never hand-edit coordinates in `mexicoMapData.js` directly** — the `d` path
strings are generated, not authored; treat the file as a build artifact.

### 14.8 What's real vs. simulated — read before calling any of this "done"

| Spec requirement | Status here |
|---|---|
| Dummy/test login disabled in production | ✅ Real — `import.meta.env.DEV` gate, dead-code-eliminated in prod builds (§14.2) |
| Generic, non-enumerating error messages | ✅ Real UX behavior (client-side), though there's no server to enforce it against a determined attacker |
| Password length / common-password checks | ✅ Real client-side checks (`isPasswordCommon` is a small hardcoded list, not a real breach-database lookup like HaveIBeenPwned) |
| Passwords hashed, not stored in plaintext | ⚠️ Partial — SHA-256 via Web Crypto, client-side. **Not** bcrypt/Argon2 with per-user salt and tunable work factor; a real backend is required for that |
| Email verification / password reset via token | ⚠️ Partial — real token generation (`crypto.getRandomValues`), real expiry, real one-shot consumption for reset tokens. **No real email is ever sent** — the token/link is shown directly in the UI in a labeled "demo mode" panel |
| Rate limiting on failed logins | ⚠️ Partial — real UI/UX behavior, but enforced in `localStorage`, so trivially bypassed by clearing storage or calling `auth.js` directly. Real rate limiting needs a backend |
| Session cookies with `Secure`/`HttpOnly`/`SameSite`, session-ID regeneration on login | ❌ Not applicable/implemented — there is no server to set cookies. "Session" is a `localStorage` value read by client JS, which is a fundamentally weaker model (readable/writable by any script on the page) than an HttpOnly cookie |
| Audit logs (registration, login attempts, password/recovery events) | ❌ Not implemented — nothing is logged anywhere durable; `localStorage` state changes aren't an audit trail |
| HTTPS everywhere | ✅ Real, but incidental — Vercel serves over HTTPS by default, not something this app configures itself |

If a user asks to "make the login real" or "add a real backend," that's a substantially different,
much larger project (an actual API + database + email service + hosting for that service) — not a
tweak to the existing files. Flag that scope difference explicitly rather than trying to bolt real
security onto the `localStorage` simulation.

### 14.9 Recipe: add a new customer-portal screen

Follow the existing five pages as the template. Create `src/WhateverPortalPage.jsx` using the
`demo-hero` + `demo-section` + `.auth-shell`/`.auth-card` shell (§14.1); add any new `auth.js` functions
needed (keep the "generic message regardless of whether the identifier matched" pattern for anything
recovery-related, and remember the StrictMode-idempotency lesson in §14.2 if the new screen consumes a
token on mount); add a route branch in `useRoute()`/`Site()` and to the `SATELLITE_ROUTES` array (§4);
add translations under `t.auth.whatever` in both languages (don't reproduce them in §9 — see §14.1); and
if the new screen has a "did this action succeed" transition that can shrink the page's content, add the
`resultRef`/`scrollIntoView` pattern from §14.5.
