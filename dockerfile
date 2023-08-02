# Use the official Python image as a base
FROM python:3.9-slim-buster

# Set work directory
WORKDIR /app

# Copy the project (taking into account the dockerigonre)
COPY . /app

# Install dependencies
#   * libpq-dev - required when you install Python packages that need to interact with a PostgreSQL database
#   * gcc - includes the C compiler. Some Python packages have C extensions that need to be compiled during installation
#   * rm -rf /var/lib/apt/lists/* - caches the downloaded package files. Removes those cached files to reduce the size of the Docker image
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && python -m pip install -r requirement.txt

# Set python modules path & flask main app path
ENV FLASK_APP="flaskApp.backservice"
ENV FLASK_ENV="docker"

# Expose the port the Flask app will be running on
EXPOSE 5000
