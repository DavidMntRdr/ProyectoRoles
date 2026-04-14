FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc-dev \
    g++ \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 10000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:10000"]