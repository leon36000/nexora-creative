# Brief — OPSYS-AI

## Common rules (all three films)
fr-CA, 40–50 s, 16:9 (9:16 version only for the winners later); **spectacular, cinematic, rhythmic, emotional; sell the product and make the viewer want it**; the product must be **unmistakable within 5 seconds** (not a generic corporate/café ad); hook in the first 3 s, payoff by 15 s, strong last line + neutral end card (brand in `marque.json`; the name will change); no claims we cannot prove (no stats, no "meilleur"), unreleased things labelled "En préparation"/"Vision"; no brand/NVIDIA names, no known-franchise lookalikes (H3 imitates them unprompted: reject), no text inside generated media (all text set in code), no close-up faces unless they hold up; narration vs text: stated per brief.

## Brief
**OPSYS-AI** — Product truth (see `films/opsys/FAITS.md`): a team of AI agents for construction and field-service companies in Québec, organised in 10 departments M1–M10 (Réception, CRM, Estimation, Terrain, Finance, Matériel, Marketing, Analytique, Stratégie, Mémoire) with human approval levels; real today as drafts validated by a human: accepted quote → intervention → material needs → draft invoice → proposed content → morning briefing. It is a **vision film, labelled "Vision · en développement"**. Audience: roofing/plumbing/renovation contractors. Dream: "Votre entreprise tourne pendant que vous travaillez." Setting that makes the product obvious: a contractor on a roof/job site at 6 a.m. (trucks, ladders, blueprints, tablet in gloved hands), his company running in parallel (departments shown as a living board where each M lights up and does its job: quote sent, crew booked, materials ordered, invoice drafted, post published), the morning briefing, his thumb approving, the house rising in time-lapse. **Narrator (Québécois) + powerful short titles; an assistant/avatar voice may answer a question once** (do not claim NVIDIA ACE). Never a café ad: tools, roofs, trucks, plans, Québec winter light.

Mode: **narrated** (narrator + short titles; one optional assistant reply line).

## Appendix — product facts (from `films/opsys/FAITS.md` §2; status: real = drafts validated by a human)
| M | Department | Real today | In preparation | Vision |
|---|---|---|---|---|
| M1 | Réception | request qualification, transfers, complaints, missed calls logged, reception summary | transcribed voicemail, real sending to client, SMS | live omnichannel voice receptionist |
| M2 | CRM | lead ingestion, suggested next action, readiness for estimation | client 360, follow-ups | — |
| M3 | Estimation | deterministic estimate that refuses to price without information, draft PDF quote, 11-criteria review + approval before sending | estimated/actual calibration | measuring from photos |
| M4 | Terrain | intervention born from the accepted quote, job completion | route scheduling, time punching, photo proof, weather | live GPS, dispatch |
| M5 | Finance | **draft invoice after work is done**, receivables and payables | cash forecast, tax calendar | full accounting, payroll, bank connectors |
| M6 | Matériel | needs from the accepted quote, reservations, quantity variance | purchase orders (approval), receptions | catalogue, supplier APIs |
| M7 | Marketing | job done → proposed content, consent checked, manual export; review inbox | review requests | publishing to social networks |
| M8 | Analytique | collection on the bus, executive view | alerts | — |
| M9 | Stratégie | **morning briefing**, strategic reading | decision tracking | council of agents, scenarios |
| M10 | Mémoire | chained registers, context pack, case search | hybrid memory | semantic recall and graph |

Strongest real chain: accepted quote (M3) → intervention (M4) → material needs (M6) → job done → draft invoice (M5) → proposed content (M7) → executive view (M8) → morning briefing (M9) → memory (M10), server side, as drafts, with human validation. Real sending to clients does not exist yet. No hours-saved figure exists: show time given back through the hour of the day and the person's life, never a number.
