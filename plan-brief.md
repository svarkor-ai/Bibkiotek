GOAL:      Bibliotekssystem för utlåning/inlämning av böcker via mobilkamera-streckkod.
ACCEPTANCE: Webapp på localhost:8140. Kameran scannar EAN-13 → identifierar bok via Libris API (ISBN) → bibliotekarie låner ut (28 dagar) → inlämning frigör boken. Roller: admin, bibliotekarie, användare.

SYSTEM:
- Backend: FastAPI + SQLAlchemy (SQLite) + JWT-auth (python-jose + bcrypt)
- Frontend: Jinja2 templates + vanilla JS + html5-qrcode för kamera/streckkod på mobil
- Bok-ID: EAN-13-streckkod → ISBN → Libris API (libris.kb.se) för metadata (titel, författare, HCF-kategori)
- HCF: Svenskt boktypsystem (Hcf=6-9 år, Hcg=10-12 år, Hcb=13+ år etc). Systemet matchar Libris metadata mot HCF-kategori och lagrar detta.
- Roller: admin (all access), bibliotekarie (utlåning/inlämning/bokhantering), användare (egen historik, egna lån)
- Lånetid: exakt 28 dagar. Överlånat = flagga + varning.
- Databas: SQLite med SQLAlchemy ORM. Tabeller: users, books, loans, hcf_categories.

API-REFERENS:
- Libris API: https://libris.kb.se/api/docs/ (BIBFRAME/RDF, sökning via ISBN, titel, författare)
  Exempel: GET https://libris.kb.se/api/record/{libris-id}
  Sök via ISBN: GET https://libris.kb.se/api/search?q=isbn:{isbn}
  CORS-enabled, public API, inget API-nyckel krävs för läsning.

TECHNICAL DECISIONS TO ADDRESS:
1. Auth: JWT med httpOnly cookie (mobilvänligt) vs bearer token. Rekommendation: cookie.
2. Template engine: Jinja2 + vanilla JS (ingen build step, enkel deployment).
3. Kamera: html5-qrcode (både kamera + bild från galleri, EAN-13 stöd).
4. HCF-klassificering: Antingen (a) hämta från Libris metadata eller (b) manuell kategorisering av bibliotekarien. Rekommendation: kombinera — försök auto-matcher mot Libris "genre/form", fallback till manuell.

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
