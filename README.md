# diwaanka-ajaanibka

Nidaam loogu talagalay diiwaangelinta ajaanibta, maamulka, xafiisyada, iyo ogaanshaha wejiyada.

## Local development

Install the backend dependencies with `pip install -r backend-api/requirements.txt`, then run `python app.py` from the repository root. Local development uses SQLite and the demo accounts `admin` / `admin123` and `officer` / `officer123`; do not use these credentials in production.

Important: on Windows with Python 3.12+, use the repository's NumPy 2.x requirement. Avoid installing `numpy==1.26.4` in this project unless you also have the full MSVC C/C++ build toolchain installed; otherwise pip will try to compile from source and fail.

## Render deployment

Set `APP_ENV` to `production` and configure `SECRET_KEY`, `DATABASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `OFFICER_USERNAME`, and `OFFICER_PASSWORD` as private Render environment variables. Use a long, randomly generated JWT secret and strong, unique passwords. The service intentionally refuses to start in production if its secret, login credentials, or database URL are missing. `DATABASE_URL` must be a valid PostgreSQL URL without a Python-version prefix.
