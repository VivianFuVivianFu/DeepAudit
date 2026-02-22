FROM python:3.11-slim as build
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . /app
ENV PYTHONUNBUFFERED=1
ENV STORE_RAW=false
EXPOSE 8080
ENTRYPOINT ["python", "main.py"]
