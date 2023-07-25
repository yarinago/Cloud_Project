# Use the official Python image as a base
FROM python:3.9-slim-buster

# Set work directory
WORKDIR /app

# Copy the project (taking into account the dockerigonre)
COPY . /app

# Install PostgreSQL development files + dependencies
RUN apt-get update \
    && pip install --upgrade pip \
    && python -m pip install -r requirement.txt

# Set python modules path & flask main app path
ENV FLASK_APP="flaskr.backservice"
ENV FLASK_ENV="docker"

# Expose the port the Flask app will be running on
EXPOSE 5000
