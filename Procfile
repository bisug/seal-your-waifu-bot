# Buildpack deploy (heroku/python): app code lives in backend/,
# so the web process starts from there (config.py + backend package are
# relative to that directory). Container deploys (heroku.yml) ignore this.
web: cd backend && uvicorn backend.webapp.main:app --host 0.0.0.0 --port $PORT --workers 1