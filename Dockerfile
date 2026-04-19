FROM python:3.14-alpine3.22

WORKDIR /app

# copy hanya requirements dulu
COPY app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# baru copy semua source
COPY app/ /app/

CMD ["python", "app.py"]