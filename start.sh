export PYTHONPATH=$PYTHONPATH://Users/davidgarcia/Documents/chatbot/app
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.api:app