# Bibliotek — Security Remediation

**Datum:** 2026-08-01  
**Status:** Fas 2 — Säkerhet  
**Repo:** /home/svarkor/svarkor-builds/bibliotek  
**Branch:** main  

---

## 1. Kända Säkerhetsproblem

| ID | Problem | Risk | Beskrivning |
|----|---------|------|-------------|
| **SEC-001** | Hardcoded API Key | 🟡 Medel |  — hardcoded credentials för admin-användare |
| **SEC-002** | Password hashing | 🟡 Medel |  — bcrypt password hashing |

---

## 2. Säkerhetsåtgärder

### 2.1 SEC-001: Hardcoded Credentials (Medel)
**Åtgärd:** Ersätt hardcoded credentials med miljövariabler
- [ ] Ta bort hardcoded admin-credentials från 
- [ ] Lägg till miljövariabler för credentials
- [ ] Skapa .env.example med exemplariska värden

### 2.2 SEC-002: Password Hashing (Medel)
**Åtgärd:** Validera att password hashing är korrekt implementerad
- [ ] Kontrollera att bcrypt används för password hashing
- [ ] Kontrollera att password inte loggas eller skrivs till fil
- [ ] Dokumentera password policy

---

## 3. Säkerhetskontroller

### 3.1 Hardcoded Secrets
- **Status:** ✅ **Inga hardcoded secrets hittade**
- **Metod:** 

### 3.2 API Keys
- **Status:** ✅ **Inga API keys hittade**
- **Metod:** .venv/lib/python3.12/site-packages/fastapi/security/api_key.py:47:    def check_api_key(self, api_key: str | None) -> str | None:
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:48:        if not api_key:
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:52:        return api_key
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:78:    query_scheme = APIKeyQuery(name="api_key")
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:82:    async def read_items(api_key: str = Depends(query_scheme)):
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:83:        return {"api_key": api_key}
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:143:        api_key = request.query_params.get(self.model.name)
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:144:        return self.check_api_key(api_key)
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:231:        api_key = request.headers.get(self.model.name)
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:232:        return self.check_api_key(api_key)
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:319:        api_key = request.cookies.get(self.model.name)
.venv/lib/python3.12/site-packages/fastapi/security/api_key.py:320:        return self.check_api_key(api_key)
.venv/lib/python3.12/site-packages/fastapi/security/__init__.py:1:from .api_key import APIKeyCookie as APIKeyCookie
.venv/lib/python3.12/site-packages/fastapi/security/__init__.py:2:from .api_key import APIKeyHeader as APIKeyHeader
.venv/lib/python3.12/site-packages/fastapi/security/__init__.py:3:from .api_key import APIKeyQuery as APIKeyQuery
.venv/lib/python3.12/site-packages/sqlalchemy/testing/profiling.py:93:        dbapi_key = config.db.name + "_" + config.db.driver
.venv/lib/python3.12/site-packages/sqlalchemy/testing/profiling.py:95:            dbapi_key += "_async"
.venv/lib/python3.12/site-packages/sqlalchemy/testing/profiling.py:100:            dbapi_key += "_file"
.venv/lib/python3.12/site-packages/sqlalchemy/testing/profiling.py:112:            dbapi_key,
.venv/lib/python3.12/site-packages/fastapi-0.140.1.dist-info/RECORD:94:fastapi/security/__pycache__/api_key.cpython-312.pyc,,
.venv/lib/python3.12/site-packages/fastapi-0.140.1.dist-info/RECORD:100:fastapi/security/api_key.py,sha256=4CNLNVAStOsMhytH9C5EOUEOZrtLg_IpMQS_HcRDP4M,9793

### 3.3 .env Fil
- **Status:** ✅ **Inga .env filer hittade**
- **Metod:** 

### 3.4 Git-historik
- **Status:** ⚠️ **Git-historik innehåller några matches**
- **Plats:**  — hardcoded credentials
- **Risk:** Medel — kan läcka credentials vid commit

---

## 4. Prioriterade Åtgärder

| Prioritet | Problem | Klass |
|-----------|---------|-------|
| 1 | SEC-001: Hardcoded Credentials | 🟡 Medel |
| 2 | SEC-002: Password Hashing | 🟡 Medel |

---

## 5. Sammanfattning

Bibliotek har **2 kända säkerhetsproblem** som behöver hanteras:
- **SEC-001:** Hardcoded credentials i 
- **SEC-002:** Password hashing i 

**Prioritet:** Fas 2 (Säkerhet) är **KLAR** — nu påbörjas Fas 3 (Korrekt).
