GOAL:      Bibliotekssystem för utlåning och inlämning av böcker via streckkod.
ACCEPTANCE: Webapp på localhost:8140 med kamera-streckkodsläsare, bokidentifiering, utlåning (28 dagar), inlämning, roller (användare/bibliotekarie/admin).

SYSTEM:
- Backend: FastAPI + SQLAlchemy (SQLite) + JWT-auth
- Frontend: Jinja2 templates + vanilla JS + quagga2/jsqr för kamera-streckkod
- Bok-ID: EAN-13 streckkod → ISBN → HCF API (svenskt bibliotekssystem) för metadata
- Roller: admin (all access), bibliotekarie (utlåning/inlämning), användare (egen historik)
- Lånetid: 28 dagar från utlåning. Överlånat = varning. Inlämning frigör boken.

TECHNICAL DECISIONS TO MAKE:
1. HCF API — Vilket svenskt biblioteks-API ska användas? Kungliga bibliotekets API? Libris?
   Rekommendation med länk till dokumentation.
2. Kamera — quagga2 (EAN-13) vs native HTML5 camera API + barcode-scanner library.
3. Auth — JWT med cookie vs bearer token för mobilvänlighet.
4. Template engine — Jinja2 med vanilla JS (enkel, ingen build step) vs React/Vue.

PRODUCÉ A MODULAR, REUSE-FIRST, FILE-LEVEL PLAN:
- Every module: one concern, one file, exact path, explicit interface (function signatures/route shapes)
- Name what already exists on the fleet we should extend
- Give 2-3 options for each TECHNICAL DECISION with trade-offs and recommendation
- No code, only architecture
- End with the RESULT block.

--- RESULT ---
STATUS: | BLOCKED
FILES: paths created, one per line
DID: what you did, <=4 lines
VERIFY: the check you ran + its outcome
BLOCKERS: concrete blocker, or "none"
--- END ---
