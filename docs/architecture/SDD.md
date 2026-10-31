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
- **Hosting:** Vercel (frontend) via Vercel's own git integration (§2). A future backend will be
  hosted on Railway (ADR 001, issue #8); nothing runs there yet. GitHub Pages was dropped
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
| `#/accept-invite?token=` | `accept-invite` → renders `<AcceptInvitePage/>` (link from a staff invite email) |
| `#/forgot-password` (+ optional `?token=`) | `forgot-password` → renders `<ForgotPasswordPage/>` (request view if no token, reset view if a token is present) |
| `#/vision-home` | `vision-home` → renders `<VisionHomePage/>` (redirects to `#/login` if the API says there's no session — see §14) |
| anything else (incl. plain `#section-id` anchors) | `home` → renders the full home-page section stack |

All eight non-`home` route names are collected in the `SATELLITE_ROUTES` array (top of `App.jsx`, right
above `useRoute()`) so the scroll-to-top effect below and any future "is this a satellite page" check
stay in sync with one list instead of a repeated `route === 'x' || route === 'y' || ...` chain.

`<Header/>` and `<Footer/>` always render regardless of route.

On route change, `Site()`'s `useEffect`:
- scrolls to top (`window.scrollTo(0,0)`) for any route in `SATELLITE_ROUTES`,
- otherwise (route `home`), if the current hash is a plain anchor (doesn't start with `#/`), scrolls
  that element into view via `document.getElementById(hash.slice(1))?.scrollIntoView()`.

**Query strings on hash routes:** `#/accept-invite?token=...` and `#/forgot-password?token=...` carry a
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

- **Contact form and calculator "send me these results" are real (spec `specs/001-backend`, Story 1).**
  `Contact()` posts to `/api/contact` and `CalculatorPage` to `/api/calculator-results` (`src/api.js`);
  the backend (`server/`) stores each request and emails staff and the visitor. Both forms carry an
  off-screen honeypot field (`.hp-field`).
- **Meeting booking is live (Story 2).** Schedule mode loads `/api/availability` (VeritX Google
  Calendar free/busy minus existing bookings, same CDMX grid, 24 h–60 days ahead) and books with
  `/api/bookings`, which creates a Meet event and invites the visitor; a slot taken in the
  meantime shows `slotTaken` and refreshes. If the calendar is down the form offers to send a
  normal message instead. This supersedes the "fixed illustrative slot list" in §10.17.
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
- **The customer portal is real (§14, Stories 3–4)**: invite-only sign-in, password reset, sessions,
  Vision Home data and support tickets come from the backend. Still out of scope: an admin web UI
  (staff use the CLI), online payments, and staff replies inside the portal (they reply by email).

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

## 14. Customer Portal (Login / Invite / Recovery / Vision Home)

### 14.1 What this is
A real, invite-only customer portal (spec `specs/001-backend`, Story 3) backed by the FastAPI
service in `server/` (`server/app/routes/auth.py`, `server/app/security.py`). There is **no
self-registration**: staff create companies and invite people with the CLI
(`python -m app.cli invite --company … --email … --name … --lang es|en|fr`). Several users can
belong to one company; all of them see the same company data. The email is the username.

### 14.2 `auth.js` — the client side
`src/auth.js` holds no credentials and no data store. The session is an **HttpOnly, Secure,
SameSite=Lax cookie (`vx_session`, `Path=/api`)** that the browser sends to `/api` by itself;
JavaScript can't read it. `auth.js` keeps the last `GET /api/me` answer in memory and exposes:
- `useAuthSession()` → `{ status, me }` with `status` = `unknown` (checking) · `in` · `out` · `error`
  (API unreachable). It checks the session once on first use; `Header` uses `me` to pick
  "Log in" vs "My Account".
- `login(email, password)` → `{ ok }` or `{ ok:false, error:'invalid_credentials'|'locked', minutes }`
- `logout()`, `getInvite(token)`, `acceptInvite(token, password)`,
  `requestPasswordReset(email, lang)`, `resetPassword(token, password)`
- `passwordProblem(password, confirm)` — same rules as the server (≥12 chars, not on the common
  list, confirmation matches), only for instant feedback; the server is authoritative.

### 14.3 Pages
- **Login (`LoginPage.jsx`)** — email + password. Unknown email and wrong password show the same
  message. After 5 failures in 15 min the account is locked for 15 min (message shows minutes).
  Says accounts are by invitation; no "create account" or "forgot username" links.
- **Accept invite (`AcceptInvitePage.jsx`, `#/accept-invite?token=`)** — shows company and email from
  `GET /api/auth/invite/{token}`, sets the password, signs in, goes to Vision Home. Invite links last
  7 days and work once; a used/expired one shows "ask for a new invitation".
- **Forgot / reset password (`ForgotPasswordPage.jsx`)** — the request view always shows the same
  confirmation (no account enumeration). The emailed link (`#/forgot-password?token=`, 30 min, single
  use) opens the reset view; a successful reset signs the user out everywhere.
- **Vision Home (`VisionHomePage.jsx`)** — loads `GET /api/me`: company name, subscriptions with status
  (active/paused/cancelled), payment history newest first (entered by staff with
  `python -m app.cli payment-add`; display only, no online payment). Empty and error states included.

### 14.4 Staff administration
No admin web UI. Everything is the CLI (`server/app/cli.py`, contract in
`specs/001-backend/contracts/cli.md`): `company-add`, `invite`, `user-disable` / `user-enable`
(disable ends the user's sessions immediately), `subscription-add` / `subscription-set`,
`payment-add`, `list companies|users|pending`, `cleanup`. Run it against production with
`railway run python -m app.cli …`. With `GOOGLE_FAKE=1` (local dev) emails, including invite and
reset links, are printed to the log instead of sent.

### 14.5 Security summary
Argon2id password hashes; link secrets and session ids stored only as SHA-256; server-side sessions
(7 days absolute, 24 h idle); every query scoped to the user's company (other companies' records
answer 404); Origin check on state-changing requests; audit rows (`audit_log`) for sign-in success/
failure, sign-out, invite sent/accepted, reset requested/done and disable/enable.

### 14.6 Support tickets
Signed-in users open tickets from Vision Home (subject, description, priority low/medium/high, up to
3 PNG/JPEG/PDF files of ≤2 MB). Files upload one per request to `/api/attachments` (type judged by
content on the server; `src/tickets.js` only pre-checks), then `/api/tickets` links them. Staff get an
email with the files and the user as reply-to, answer from Gmail, and change the status with
`python -m app.cli ticket-status --id N --status in_progress|resolved|closed`. Every user of the
company sees the company's tickets and can download their files; other companies get 404.

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

### 14.8 Removed in Story 3
`RegisterPage.jsx`, `VerifyEmailPage.jsx`, `RecoverUsernamePage.jsx`, the localStorage "auth
service", the SHA-256-in-JS hashing and the development demo login (`test` / `vision`) were deleted,
with their routes and copy in all three languages.

### 14.9 Recipe: add a new customer-portal screen
Use the `demo-hero` + `demo-section` + `.auth-shell`/`.auth-card` shell of the existing pages; add
the endpoint to `server/` first (with tests, and company scoping if it returns data), then a function
in `src/auth.js` or a call through `src/api.js`; add a route branch in `useRoute()`/`Site()` and to
`SATELLITE_ROUTES` (§4); add copy under `t.auth.whatever` in es/en/fr.
