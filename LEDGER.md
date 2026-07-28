# Bibliotek Build LEDGER

**Goal:** Bibliotekssystem med utlåning/inlämning (28 dagar), ISBN-streckkod via mobilkamera, HCF-integration för svensk bokidentifiering, roller (användare, bibliotekarie, admin).

**Acceptance:** Webapp kör på localhost:8140. Kameran skannar streckkod → söker bok → bibliotekarie kan låna ut → inlämning räknar tillbaka 28 dagar.

## Modules

| Module | Concern | Status |
|---|---|---|
| PLAN.md | Modular plan from Planner | planned |
| DESIGN.md | Data model, interface contracts | planned |
| src/database.py | SQLAlchemy models + session | planned |
| src/models.py | Pydantic schemas (requests/responses) | planned |
| src/auth.py | JWT auth, password hashing, role middleware | planned |
| src/books.py | Book CRUD + ISBN/EAN lookup + HCF API | planned |
| src/circulation.py | Checkout/return, 28-day due date, overdue | planned |
| src/users.py | User management (librarian CRUD) | planned |
| src/app.py | FastAPI app, routers, static files | planned |
| templates/ | HTML templates (Jinja2) | planned |
| static/ | CSS/JS (camera scanner) | planned |
| tests/ | Unit + E2E tests | planned |
