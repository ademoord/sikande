# Sikande

Personal finance app (Flask) — expenses, debts, plans, investments, and historical archive reporting.

## Local development

Requires Python 3 and no `~/config.txt` (that file switches the app to production MySQL).

```bash
cd /path/to/sikande
make install    # or: pip install -r requirements.txt
make run        # http://127.0.0.1:5000
```

**Local login** (from `data/users.csv`):

| Username | Password |
|----------|----------|
| admin    | admin    |
| demo     | demo123  |

### Progressive Web App (PWA)

Sikande ships with a web app manifest, install icons, and a root-scoped service worker that caches static assets only (CSS, JS, logos). HTML pages and authenticated routes always use the network.

After deploy, verify in Chrome DevTools → **Application** → **Manifest** and **Service Workers**. On mobile, use **Settings → Install Sikande** or **Add to Home Screen**.

| URL | Purpose |
| --- | --- |
| `/manifest.webmanifest` | Install metadata (Flask route, correct MIME type) |
| `/sw.js` | Service worker (must be at site root for full scope) |

If you change cached static files, bump `CACHE_VERSION` in `static/sw.js`.

| Database | Path |
|----------|------|
| Live (Purchases/Input) | `data/local.sqlite3` |
| Historical archive   | `data/archive.sqlite3` |
| SQL dump samples     | `data/sql_samples/` |

Production uses `~/config.txt` → MySQL, and reads SQL backups from `../Data/`.

---

## Testing the Historical Archive

The archive merges monthly `sikande*.sql` mysqldump files into a searchable SQLite database (search, filter, group, aliases, dashboard charts).

### One-command test

```bash
make test-archive
```

This will:

1. Read all `sikande*.sql` files from `data/sql_samples/` (local) or `../Data/` (production)
2. Rebuild `data/archive.sqlite3` (aliases preserved)
3. Print ingest stats and a few sanity checks (e.g. canonical grouping for “nas”)

### Manual UI test

```bash
make run
```

Then visit:

| URL | What to try |
|-----|-------------|
| [/archive](http://127.0.0.1:5000/archive) | Search `nas`, group by **Canonical name**, filter **Legacy** category |
| [/archive/aliases](http://127.0.0.1:5000/archive/aliases) | Add alias, fuzzy suggestions |
| [/dashboard](http://127.0.0.1:5000/dashboard) | **Historical Archive** charts and YoY |
| [/settings](http://127.0.0.1:5000/settings) | **Sync** / **Full Rebuild** |

### Add real dumps locally

Copy production backups into the samples folder, then rebuild:

```bash
cp ~/path/to/sikandeAug24.sql data/sql_samples/
make test-archive
```

Or use **Settings → Full Rebuild** in the UI.

### Reset archive

```bash
rm data/archive.sqlite3
make test-archive
```

### Production

1. Deploy code to `~/mysite/`
2. Ensure SQL dumps exist in `~/Data/`
3. **Settings → Full Rebuild** (creates `~/Data/archive.sqlite3`)
4. After each new monthly backup: **Sync New Dumps**
