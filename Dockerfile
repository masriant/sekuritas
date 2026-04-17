FROM python:3.10

WORKDIR /app

# copy hanya requirements dulu
COPY app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# baru copy semua source
COPY app/ /app/

CMD ["python", "app.py"]