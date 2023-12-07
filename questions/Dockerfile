FROM python:3.10-slim-buster
LABEL authors="plux"

WORKDIR /app
VOLUME /app/data
EXPOSE 3000

#COPY requirements.txt requirements.txt

COPY . .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]