# Site and identity redesign (02/11/2026)

Founder's mandate (02/11/2026): rebuild the **public site** (not the user panel or the admin panel) with an exceptional, "triple A" structure and visuals. Forge an identity of our own that radiates technological advance: **the current visuals look too much like Mistral** (orange pixel mosaic). Put forward Creative and the videos, add the new services, use our own image and video tools. The company name and logo **will change** (rebrand to come): everything must be swappable in a single place.

## 1. Rules that do not change
- Repository rules for the site: `/home/pc6/Desktop/NexoraSite/AGENTS.md` (no secrets, content truth, fr-CA first then en-CA, WCAG 2.2 AA, `prefers-reduced-motion`, tests, bun, never `pkill -f`).
- **Content truth**: no fake client, testimonial, figure, price, certification or claim we cannot prove. We describe what we install and how it works.
- No text inside AI-generated images: text and logo are always set in code.
- **Québec**: mention it once or twice where it means something (hosting on our servers, data sovereignty), **not everywhere**.
- No legal caveats or licence notes in the pages (the founder and a lawyer handle that).

## 2. The new identity: "Signal" (replaces "la braise" on the site)
Idea: **precise light in the dark**, the world of a measuring instrument and of a data center. What the AI sees, hears and computes, shown as fine lines of light, point clouds, waveforms, heat maps, glass and metal hardware lit at a grazing angle. Cinematic, silent, at scale.
- **Forbidden on the site**: the pixel mosaic, cascades of orange squares, the "braise" ramp as an image texture (all of that reads as Mistral). Robots, glowing brains, "AI" sparkles, purple startup gradients, stock photos.
- **Palette (tokens, swappable)**: background `abyss` #05070B, surfaces #0B0F16 / #111723, hairlines #1C2433, text #EEF3FA, secondary text #8C97AA. Main accent **"ion" #3EC8FF** (light, interactions, links on dark). Rare warm counterpoint **"flare" #FF6A2B**: a single point of heat per screen, such as a highlighted call to action or an alert. It echoes the warm light of the existing films. Status colours: alert #FF4D5E, OK #3FE0A5. Light mode is optional for the public site: dark-first.
- **Type**: keep Geist (display, very large, tight) + Inter (body) + JetBrains Mono (technical labels, capitals). Display headings can go to 7–9 rem on desktop.
- **Signature materials** (code, SVG/canvas/WebGL kept light): 1) the **scan line**, a fine horizontal line of light that sweeps across a block when it appears; 2) the **light field**, a point cloud / lidar mesh in perspective; 3) the **waveform** (voice, reception); 4) **detection boxes** (thin brackets in the corners, monospaced labels, surveillance); 5) **precision grids** at 1 px. Radii of 2 to 10 px, glass surfaces with a 1 px border, no decorative drop shadows; restrained glow only on the ion accent.
- **Motion**: scroll reveals (opacity + 8–16 px), scan line, number counters only where the figure is true, silent looping background videos. All disabled or static under `prefers-reduced-motion`. Performance: LCP < 2.5 s, videos lazy-loaded with a poster image, AVIF/WebP.
- **Brand swappable in one place**: name, signature, logo (component plus SVG files), colours and fonts in tokens; no product name hard-coded in a component (dictionaries / Directus / a single brand config). The logo component must accept a temporary **typographic logo** (the name set in Geist + a "signal" mark that is not the pixel N) until the new logo arrives.

## 3. Structure of the public site (fr-CA routes, en-CA mirror)
Main navigation: **Solutions** ▾ · **Infrastructure** ▾ · **Tools** ▾ · Pricing · Resources · [Plan a consultation] (main CTA).

1. **Home** `/` : full-screen video hero (silent loop, poster), promise in one sentence; three pillars **Automate** (virtual reception, AI surveillance, agents) · **Equip** (AI infrastructure installed at your site or hosted with us) · **Create and build** (Creative, WorkStudio, Code, RAG, WebPilot); showcase of the brand film (60 s) and of Creative; method (consultation → installation → operation and support); sovereignty and security (one mention: your data stays with you or on our servers in Québec); final CTA.
2. **Virtual reception** `/solutions/reception-virtuelle` : answers calls and places them, replies to and sends emails, replies to text messages; takes appointments, qualifies, transfers to the right person, summarises each exchange; 24/7, in French and English; connected to your systems (calendar, CRM, phone line). A complete virtual reception service. Visual: waveform, dashboard of conversations.
3. **AI surveillance** `/solutions/surveillance-ia` : **key message to put up front**: "Even with the best cameras and huge storage, nobody watches hundreds or thousands of hours of video. Our AIs do, in real time." Connects to existing cameras and security systems; detects suspicious behaviour as it happens; alerts by email, text, dashboard or mobile app; can notify your security officers, your monitoring centre or the police according to your instructions; produces reports for every suspicious activity (events, clips, timeline). Visual: detection boxes, timeline, heat maps.
4. **AI infrastructure** `/infrastructure` : we sell and install complete AI infrastructure: **three cards with photos**: **NVIDIA DGX Spark** (compact, on a desk), **NVIDIA DGX Station** (workstation), **server racks** (data center); turnkey installation at your site (models, applications, security, monitoring) **or** hosted on our servers (here the Québec mention makes sense). Link to VPS.
5. **Creative** `/creative` (or the existing Creative sheet, made prominent) : studio for image, video and sound, with the promo video, a gallery of renders, "the AI does the heavy lifting"; easy mode and pro mode.
6. Existing pages kept and restyled: agents/WorkStudio, Code, Apps, models, VPS, pricing, contact, docs, legal pages.

## 4. Media to produce (files and manifest: `~/nexora-creative-data/site-medias/` + `manifest.json`)
Images (Qwen-Image, no text, "Signal" palette: dark, ion light, rare warm point; 16:9 2560 px + 4:5/9:16 crops when useful):
- `hero-*` : 2–3 candidates for the home page (data center at night in grazing light, light field, line of light over a city at night).
- `infra-dgx-spark`, `infra-dgx-station`, `infra-racks` : product shots (studio on a dark background, grazing light). DGX Spark = very compact golden metal-foam box; DGX Station = tower workstation with a golden metal-foam front; racks = data-center aisle with servers.
- `reception-*` (sober reception area at night, phone/headset, waveform), `surveillance-*` (a store or warehouse seen by a camera, empty parking lot at night, monitoring room), `creative-*`, `workstudio-*`, `code-*`, `methode-*`, `souverainete-*`.
Videos (MiniMax H3 text → video on the 5090; music MiniMax Music 3; editing with `marketing/nexora/video/outils/film.py`; text set in code; fr/en; 16:9 + 9:16):
- `hero-boucle` : silent loop of 10–15 s for the home hero (+ poster).
- One film per solution or tool: **reception**, **surveillance**, **infrastructure**, **Creative** (reuse and improve the existing promo), **WorkStudio**, **Code**; 30–45 s each, spectacular and high quality.
- The 60 s brand film already exists (`marketing/nexora/video/final/film-marque-*`), so reuse it.
- Look at **every** shot before publishing (H3 imitates known franchises; no character, robot or logo that resembles an existing brand).
