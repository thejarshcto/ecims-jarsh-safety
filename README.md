# Jarsh Safety — ECIMS Setup Guide

## What You Have
```
ecims/
├── backend/           ← Flask Python API
│   ├── app.py         ← Entry point
│   ├── config.py      ← DB credentials go here
│   ├── models.py      ← Database models
│   ├── helpers.py     ← UID generation, logging
│   ├── extensions.py
│   ├── requirements.txt
│   └── routes/
│       ├── auth.py
│       ├── skus.py
│       ├── stock.py
│       ├── allocations.py
│       ├── employees.py
│       ├── projects.py
│       ├── suppliers.py
│       ├── reports.py
│       └── logs.py
├── frontend/          ← Browser UI (no build needed)
│   ├── index.html     ← Open this in browser
│   └── static/
│       ├── css/style.css
│       └── js/
│           ├── api.js
│           └── app.js
└── database/
    └── schema.sql     ← Run this in MySQL first
```

---

## Step 1 — MySQL Setup

1. Install MySQL Server + MySQL Workbench
2. Open MySQL Workbench, connect to localhost
3. Open `database/schema.sql` and run it (Ctrl+Shift+Enter)
4. This creates the `ecims` database, all tables, and an admin user

---

## Step 2 — Configure DB Credentials

Edit `backend/config.py`:
```python
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_actual_mysql_password"
MYSQL_HOST = "localhost"
MYSQL_DB = "ecims"
```

---

## Step 3 — Install Python Packages

```bash
cd backend
pip install -r requirements.txt
```

If you get errors, try:
```bash
pip install flask flask-cors flask-sqlalchemy flask-jwt-extended mysql-connector-python bcrypt
```

---

## Step 4 — Run the Backend

```bash
cd backend
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

---

## Step 5 — Open the Frontend

1. Open `frontend/index.html` in Chrome
   - Either double-click the file, or
   - Use VS Code Live Server (right-click → Open with Live Server)

2. Login with:
   - **Username:** admin
   - **Password:** admin123

3. **Change your password** after first login via Admin → your account

---

## Default Login
| Username | Password  | Role  |
|----------|-----------|-------|
| admin    | admin123  | Admin |

---

## API Base URL
All API calls go to: `http://localhost:5000/api`

If your backend runs on a different port, edit the first line of `frontend/static/js/api.js`:
```javascript
const BASE = "http://localhost:5000/api";
```

---

## UID Format
Auto-generated when you add stock:
```
R0603-10K-2026-0001     ← Resistor, 0603 package, 10K value, year, sequence
C0805-100nF-2026-0001   ← Capacitor
IC-ESP32-2026-0001      ← IC
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Access denied for MySQL` | Check username/password in `config.py` |
| `CORS error` in browser | Make sure backend is running on port 5000 |
| Login fails | Make sure `schema.sql` was run successfully |
| `Unknown column` error | Re-run `schema.sql` to reset the DB |

---

## Future Enhancements (from your spec)
- [ ] Barcode / QR label printing per UID
- [ ] CSV bulk import for SKUs
- [ ] Email alerts for low stock
- [ ] Mobile-responsive improvements
- [ ] Docker deployment config
