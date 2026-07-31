# Bibliotek Build LEDGER

**Goal:** Bibliotekssystem med utlåning/inlämning (28 dagar), ISBN-streckkod via mobilkamera, HCF-integration för svensk bokidentifiering, roller (användare, bibliotekarie, admin).

**Acceptance:** Webapp kör på localhost:8140. Kameran skannar streckkod → söker bok → bibliotekarie kan låna ut → inlämning räknar tillbaka 28 dagar.

## Modules

|| Module | Concern | Status |
||---|---|---|
|| PLAN.md | Modular plan from Planner | ✅ done (job 15) |
|| DESIGN.md | Data model, interface contracts | ✅ done |
|| src/database.py | SQLAlchemy models + session | ✅ done + verified (job 17) |
|| src/models.py | Pydantic schemas (requests/responses) | ✅ done + verified |
|| src/auth.py | JWT auth, password hashing, role middleware | ✅ done + verified (job 18) |
|| src/books.py | Book CRUD + ISBN/EAN lookup + HCF API | ✅ done + verified (job 19) |
|| src/circulation.py | Checkout/return, 28-day due date, overdue | ✅ done + verified (job 20) |
|| src/users.py | User management (librarian CRUD) | ✅ done + verified (job 21) |
|| src/app.py | FastAPI app, routers, static files | ✅ done + verified (job 21) |
|| templates/ | HTML templates (Jinja2) | ✅ done + verified (job 22) |
|| static/ | CSS/JS (camera scanner) | ✅ done + verified (job 22) |
|| tests/ | Unit + E2E tests | ✅ done + verified (job 23) |
| **Server** | **Live on port 8140** | **✅ deployed (job 24)** |
