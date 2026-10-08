# diwaanka-ajaanibka

Nidaam loogu talagalay diiwaangelinta ajaanibta, maamulka, xafiisyada, iyo ogaanshaha wejiyada.

## Local development

For local development and tests, install `backend-api/requirements-dev.txt` with `pip install -r backend-api/requirements-dev.txt`, then run `python app.py` from the repository root. This includes the backend runtime dependencies plus test-only packages (`httpx` and `pytest`). For deployment/runtime-only installs, use `pip install -r backend-api/requirements.txt`. Local development uses SQLite and the demo accounts `admin` / `admin123` and `officer` / `officer123`; do not use these credentials in production.

The backend requirements allow NumPy 2.x, letting pip select a release with a wheel for your Python version. NumPy 1.26.4 does not provide a wheel for Python 3.14, so pip may try to build it from source and require the MSVC C/C++ toolchain. Use the repository requirements rather than pinning NumPy to 1.26.4.

## Render deployment

Set `APP_ENV` to `production` and configure `SECRET_KEY`, `DATABASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `OFFICER_USERNAME`, and `OFFICER_PASSWORD` as private Render environment variables. Use a long, randomly generated JWT secret and strong, unique passwords. The service intentionally refuses to start in production if its secret, login credentials, or database URL are missing. `DATABASE_URL` must be a valid PostgreSQL URL without a Python-version prefix.
