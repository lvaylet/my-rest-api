# Gunicorn logs to stderr by default since 19.2, so no need for "--log-file -" or "--error-logfile -"
web: gunicorn rest_api:app --access-logfile -
