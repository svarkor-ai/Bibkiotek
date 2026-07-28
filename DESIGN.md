# Bibliotek — System Design

## Arkitektur

```
┌─────────────────────────────────────────────┐
│                  Browser                     │
│  (mobil + desktop, kamera-streckkod)         │
└──────────────┬──────────────────────────────┘
               │ HTTPS
┌──────────────▼──────────────────────────────┐
│              FastAPI (port 8140)             │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ auth.py  │ │ books.py │ │ circulation.py│ │
│  │ /api/*   │ │ /api/*   │ │ /api/*        │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │ Jinja2 Templates + vanilla JS        │    │
│  │ /login, /scanner, /dashboard, /books  │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  ┌──────────┐ ┌──────────┐                  │
│  │ database │ │ auth     │                  │
│  │ session  │ │ JWT+BC   │                  │
│  └──────────┘ └──────────┘                  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────┐   ┌──────────────────────┐
│    SQLite (bibliotek.db)    │   │ Libris API (KB)      │
│                             │   │ libris.kb.se/api/    │
└─────────────────────────────┘   └──────────────────────┘
```

## Moduler (fil-nivå, en concern per fil)

### 1. `src/database.py` — SQLAlchemy session + base
- `get_engine()` → SQLite engine med SQLAlchemy 2.0 async eller sync
- `get_session()` → context manager för DB session
- `Base.metadata.create_all()` → skapar alla tabeller vid startup

### 2. `src/models.py` — SQLAlchemy ORM models
- `User(id, username, password_hash, role, email, created_at)` — role ∈ {'admin', 'librarian', 'user'}
- `Book(id, isbn, title, author, publisher, year, cover_url, hcf_category, created_at, created_by)` — hcf_category ∈ {'hcf', 'hcg', 'hcb', 'adult', None}
- `Loan(id, book_id, user_id, librarian_id, checkout_date, due_date, return_date, created_at)` — due_date = checkout_date + 28 dagar
- `HcfCategory(id, code, name, description, min_age, max_age)` — pre-seeded med HCF/HCG/HCB

### 3. `src/config.py` — Miljövariabler (redan skapad)

### 4. `src/auth.py` — JWT-auth, roller
- `create_access_token(user_id, role)` → JWT
- `verify_token(token)` → (user_id, role) eller None
- `hash_password(password)` → bcrypt hash
- `check_password(password, hash)` → bool
- `require_role(allowed_roles)` → FastAPI dependency
- Rutt: `POST /api/auth/login` → (username, password) → {access_token, user}

### 5. `src/books.py` — Bokhantering + Libris-integration
- CRUD: `POST /api/books`, `GET /api/books`, `GET /api/books/{id}`, `PUT /api/books/{id}`, `DELETE /api/books/{id}`
- `POST /api/books/scan` → (barcode=ean13) → söker Libris → returnerar bokinfo
- `GET /api/books/search?q=<query>` → söker i lokal DB + Libris
- `libris_lookup(isbn)` → {title, author, publisher, year, cover_url} från Libris API
- `classify_hcf(title, author, year)` → HCF-kategori baserat på Libris metadata + heuristik

### 6. `src/circulation.py` — Utlåning/inlämning
- `POST /api/loans/checkout` → (book_id, user_id, librarian_id) → skapar Loan med due_date = today + 28 dagar
- `POST /api/loans/return` → (loan_id) → sätter return_date, frigör bok
- `GET /api/loans/active` → alla pågående lån med overdue-flagga
- `GET /api/loans/user/<user_id>` → användarens historik
- `GET /api/loans/overdue` → alla överlåna lån
- `is_overdue(loan)` → bool (return_date är None och today > due_date)

### 7. `src/users.py` — Användarhantering (admin/bibliotekarie)
- `GET /api/users` → alla användare (admin+librarian)
- `POST /api/users` → skapa användare (admin)
- `PUT /api/users/{id}` → uppdatera roll (admin)
- `GET /api/users/me` → aktuell användares profil

### 8. `src/app.py` — FastAPI entry point, router-wiring
- Mount routers: `/api/auth`, `/api/books`, `/api/loans`, `/api/users`
- Mount static files: `/static/`
- Mount templates: Jinja2Templates(directory="templates/")
- Startup event: create tables, seed admin, seed HCF categories
- Root: serve `/templates/index.html`

### 9. `templates/index.html` — Haupt-sida med navigation
### 10. `templates/login.html` — Inloggning
### 11. `templates/dashboard.html` — Dashboard med aktivt utflöde
### 12. `templates/scanner.html` — Kamera/streckkod-skanner
### 13. `templates/books.html` — Boköversikt + sök + lägga till bok
### 14. `templates/loans.html` — Lån-hantering (utlåning/inlämning)
### 15. `templates/users.html` — Användarhantering (admin)
### 16. `static/css/style.css` — Responsive design, mobil-optimerad
### 17. `static/js/scanner.js` — html5-qrcode integration
### 18. `static/js/app.js` — Frontend logik (navigation, API-anrop)

## Data Model (mer detaljerad)

### User
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| username | VARCHAR(50) UNIQUE | Login-identifierare |
| password_hash | VARCHAR(128) | bcrypt hash |
| role | VARCHAR(20) | 'admin', 'librarian', 'user' |
| email | VARCHAR(255) | |
| created_at | DATETIME | AUTO NOW |

### Book
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| isbn | VARCHAR(13) UNIQUE | ISBN-13 / EAN-13 |
| title | VARCHAR(500) | |
| author | VARCHAR(255) | |
| publisher | VARCHAR(255) | |
| year | INTEGER | |
| cover_url | VARCHAR(500) | |
| hcf_category | VARCHAR(20) | 'hcf', 'hcg', 'hcb', 'adult', NULL |
| created_at | DATETIME | AUTO NOW |
| created_by | INTEGER FK → User | Skapad av bibliotekarie |

### Loan
| Field | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| book_id | INTEGER FK → Book | |
| user_id | INTEGER FK → User | Låntagare |
| librarian_id | INTEGER FK → User | Utlåningspersonal |
| checkout_date | DATETIME | AUTO NOW |
| due_date | DATETIME | checkout_date + 28 dagar |
| return_date | DATETIME | NULL = pågående |
| created_at | DATETIME | AUTO NOW |

## API Contract (sammanfattning)

```
POST   /api/auth/login        (username, password) → {token, user}
POST   /api/users             (username, role, email) → {user}        [admin]
GET    /api/users             → [users]                           [admin+librarian]
GET    /api/users/me          → {user}                            [any authenticated]

POST   /api/books             (isbn, title, author, ...) → {book}  [admin+librarian]
GET    /api/books             → [books]                           [any authenticated]
GET    /api/books/{id}        → {book}                            [any authenticated]
GET    /api/books/search?q=   → [books]                           [any authenticated]
POST   /api/books/scan        (barcode=ean13) → {book from Libris}[any authenticated]

POST   /api/loans/checkout    (book_id, user_id, librarian_id) → {loan}  [admin+librarian]
POST   /api/loans/return      (loan_id) → {loan}                      [admin+librarian]
GET    /api/loans/active      → [loans]                             [any authenticated]
GET    /api/loans/overdue     → [loans]                             [admin+librarian]
GET    /api/loans/user/{id}   → [loans]                             [user (their own), librarian (all)]

GET    /api/hcf/categories    → [hcf_categories]                    [any authenticated]
```

## HCF-klassificering

HCF (Huvudkategoriför barn) är ett svenskt boktypssystem:
- **hcf** = 6-9 år (Huvudkategoriför 6-9)
- **hcg** = 10-12 år
- **hcb** = 13+ år
- **adult** = vuxen
- **NULL** = okänd

Klassificeringsheuristik (från Libris metadata):
1. Titta på Libris "genre/form"-fält för åldersangivelser
2. Om författarens andra böcker är kända för barn → hcf/hcg
3. Annars → manual classification via admin UI (bibliotekarien avgör)

## Libris API Integration — VERIFIERAD 2026-07-28

Base URL: `https://libris.kb.se/api`

### XSearch API (VERIFIERAD — fungerar live)
- **Sök:** `GET /api/xsearch?q={query}&format=json&limit={n}`
- **Exempel:** `GET /api/xsearch?q=isbn:9780140033366&format=json` → returns `{"xsearch":{"list":[{"identifier":"...","title":"...","creator":"...","isbn":["..."],"publisher":"...","date":"...","language":"...","type":"book"}]}}`
- **Exempel:** `GET /api/xsearch?q=title:snow+crane&format=json` → sök via titel
- Inget API-nyckel krävs för läsning
- Rate limiting: KB:s policy (10 req/s rekommenderat)
- Returnerar: JSON med `identifier` (bib ID), `title`, `creator`, `isbn`, `publisher`, `date`, `language`, `type`
- Sökmed `isbn:{isbn}` fungerar INTE (XSearch stödjer inte isbn-prefix), sök med ren ISBN-siffra: `q={isbn}`

### Hämta full rekord via Libris identifier
- `GET https://libris.kb.se/api/record/{libris-id}` → BIBFRAME/RDF
- Eller via OAI-PMH: `GET /oai-pmh?verb=GetRecord&metadataPrefix=marcxml&identifier={oai-id}`

### Implementation
```python
def libris_search(query: str, limit: int = 5) -> list[dict]:
    """Sök Libris via XSearch API."""
    url = "https://libris.kb.se/api/xsearch"
    params = {"q": query, "format": "json", "limit": limit}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("xsearch", {}).get("list", [])

def libris_lookup_by_isbn(isbn: str) -> dict | None:
    """Hitta bok via ISBN (ren siffra, ingen prefix)."""
    results = libris_search(isbn, limit=1)
    if results:
        return _parse_libris_record(results[0])
    return None
```

## Tekniska beslut

### A. Auth: JWT med httpOnly cookie ✓ REKOMMENDERAT
- Fördel: mobilvänligt, XSS-skydd, ingen token-manual hantering
- Nackdel: CSRF-skydd krävs (SameSite cookie + CSRF token)
- Alternativ: Bearer token (mindre mobilvänligt)

### B. Kamera: html5-qrcode ✓ REKOMMENDERAT
- Stödjer: kamera LIVE + bild från galleri
- Format: EAN-13 (ISBN), QR, Code 128
- Native Web API: `<input type="file" capture="environment">` (fallback)
- Nackdel: Chrome kräver HTTPS för kamera (undantag: localhost)

### C. Template engine: Jinja2 + vanilla JS ✓ REKOMMENDERAT
- Ingen build step, enkel deployment
- Responsive via CSS media queries
- Alternativ: React/Vue (kräver build step, onödigt komplexitet)

## Deployment

- Port: 8140
- Server: uvicorn src.app:app --host 0.0.0.0 --port 8140
- Database: SQLite (bibliotek.db) — filbaserad, ingen extra tjänst
- HTTPS: nginx reverse proxy eller development med --reload
- Backup: `sqlite3 bibliotek.db ".backup 'backup.db'"`
