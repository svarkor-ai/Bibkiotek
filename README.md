# Bibliotek — Bibliotek med utlåning via streckkod

Webapplikation för bibliotek med:
- **Utlåning/inlämning** av böcker (28 dagar lånetid)
- **ISBN/EAN-streckkod** via mobilkamera
- **Användare, bibliotekarier och admin**
- **HCF-integration** för svensk bokidentifiering

## Kör lokal

```bash
cd ~/svarkor/builds/bibliotek
uv venv .venv && . .venv/bin/activate
uv pip install -r requirements.txt
python src/app.py
```

Öppna `http://localhost:8140` i webbläsaren.

## Test

```bash
python -m pytest tests/ -v
```
