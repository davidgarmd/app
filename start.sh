gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app chmod +x start.sh}
