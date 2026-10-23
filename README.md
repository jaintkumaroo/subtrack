# SubTrack

**Know exactly where your subscription money goes.**

SubTrack is a full-stack web app that tracks every recurring payment (Netflix, Spotify, ChatGPT, gym, domain
names, and so on), converts them all into one currency with live exchange rates, warns you about upcoming
renewals, and shows where your money goes with charts and plain-language insights.

Built with **Python, FastAPI, Streamlit, SQLAlchemy and Microsoft SQL Server**.

## Features

- Add, edit, pause, resume and delete subscriptions
- Billing cycles: weekly, monthly, quarterly, yearly (everything is normalised to a monthly and yearly cost)
- 20 currencies, converted with live rates from a free public API (falls back to built-in rates when offline)
- Dashboard: monthly spend, yearly projection, money due in the next 7 days, spending by category,
  5-week charge timeline, billing-cycle split, top subscriptions and generated insights
- Quick-add templates for popular services and a live cost preview while you type
- Custom categories with colours, search, filters and sorting
- CSV report (opens in Excel) and a full data table
- One-click sample data for demos
- Interactive REST API documentation at `/docs`

## Quick start (Windows)

1. Install **Python 3.10 or newer** (tick *Add Python to PATH*).
2. Double-click **`setup.bat`**. It creates the virtual environment, installs the packages and creates `.env`.
3. Open **`.env`** in Notepad and set `MSSQL_SERVER` (see below).
4. Double-click **`check_database.bat`**. It should say `OK: connected.`
5. Double-click **`start.bat`**. Two windows open and the app appears at <http://localhost:8501>.

Click **Load sample data** on the dashboard to see it with data.

### Setting up SQL Server

Open `.env` and change `MSSQL_SERVER` to the same **Server name** you type when you open SSMS:

| SSMS shows | Put in `.env` |
|---|---|
| `DESKTOP-ABC123\SQLEXPRESS` | `MSSQL_SERVER=DESKTOP-ABC123\SQLEXPRESS` |
| `localhost` | `MSSQL_SERVER=localhost` |
| `.\SQLEXPRESS` | `MSSQL_SERVER=.\SQLEXPRESS` |

- Windows Authentication (the default): keep `MSSQL_TRUSTED_CONNECTION=yes`.
- SQL login: set `MSSQL_TRUSTED_CONNECTION=no` and fill in `MSSQL_USER` and `MSSQL_PASSWORD`.
- `MSSQL_DRIVER` must match an installed ODBC driver. `check_database.bat` lists the installed ones.
- The `SubTrack` database and its tables are created automatically the first time the backend starts.
  Afterwards refresh **Databases** in SSMS and look at the `categories` and `subscriptions` tables.

No SQL Server at all? Set `DB_MODE=sqlite` in `.env` and the app uses a local file database instead.

## Run it manually (any operating system)

```bash
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # Mac/Linux: cp .env.example .env

# terminal 1: the API
uvicorn app.main:app --reload

# terminal 2: the web interface
streamlit run frontend/app.py
```

## Project structure

```
subtrack/
├── app/                      Backend (FastAPI)
│   ├── main.py               Creates the app, connects the routers, prepares the database
│   ├── config.py             Reads settings from .env
│   ├── database/
│   │   ├── connection.py     SQLAlchemy engine for SQL Server (or SQLite)
│   │   ├── session.py        Per-request database session
│   │   ├── models.py         Tables: categories, subscriptions
│   │   ├── init_db.py        Creates the database, tables and default categories
│   │   └── diagnose.py       Connection checker
│   ├── schemas/              Pydantic models: validation of everything that enters the API
│   ├── services/             The real logic
│   │   ├── billing.py        Billing-cycle and renewal-date maths
│   │   ├── currency_service.py  Live exchange rates + conversion
│   │   ├── subscription_service.py  Create / read / update / delete
│   │   ├── dashboard_service.py     Totals, timeline, insights
│   │   └── demo_service.py   Sample data
│   └── routers/              HTTP endpoints
├── frontend/                 Web interface (Streamlit)
│   ├── app.py                Sidebar, navigation, page routing
│   ├── api.py                Every call the UI makes to the backend
│   ├── ui.py                 Theme, CSS and reusable components
│   └── views/                Dashboard, Subscriptions, Add, Reports pages
├── tests/                    Automated tests (pytest)
├── .env.example              Settings template
└── requirements.txt
```

The code follows the layered design **services (logic) → schemas (validation) → routers (HTTP) → main**,
with the database in its own package and the interface talking to the backend only through the API.

## API overview

| Method | Path | Purpose |
|---|---|---|
| GET | `/subscriptions` | List (filters: `status`, `category_id`, `search`, `sort`, `base`) |
| POST | `/subscriptions` | Create |
| GET / PUT / DELETE | `/subscriptions/{id}` | Read / update / delete |
| PATCH | `/subscriptions/{id}/toggle` | Pause or resume |
| GET / POST | `/categories` | List / create categories |
| GET | `/dashboard` | All dashboard numbers |
| GET | `/reports/export.csv` | CSV download |
| GET | `/rates`, `/meta`, `/health` | Exchange rates, app info, health check |
| POST / DELETE | `/demo/seed`, `/demo/clear` | Load / remove sample data |

Add `?base=USD` (or any supported currency) to show amounts in that currency. Full interactive docs:
<http://127.0.0.1:8000/docs>.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests use a temporary SQLite database and never touch SQL Server or the internet.

## Troubleshooting

| Problem | Fix |
|---|---|
| App says "Backend not running" | Start it with `start.bat`, and keep the *SubTrack Backend* window open |
| `Login timeout expired` / `server not found` | `MSSQL_SERVER` is wrong. Copy it exactly from the SSMS login window |
| `Data source name not found` | `MSSQL_DRIVER` is not installed. Run `check_database.bat` and copy a listed name |
| `Login failed for user` | Use Windows Authentication, or switch to a SQL login in `.env` |
| `Cannot open database` | Your login cannot create databases. Create an empty `SubTrack` database in SSMS manually |
| "Offline rates" badge | No internet. Values are approximate. They switch to live rates when online |
| Port already in use | Close the old windows, or restart the computer |

## Possible next steps

User accounts and login, email reminders before renewals, importing a bank statement, a spending
history chart, and deployment to a cloud host.
