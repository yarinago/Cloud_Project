FROM python:3.8-slim-buster

# Set work directory
WORKDIR /app

# Set python modules path & flask main app path
ENV PYTHONPATH="${PYTHONPATH}:./flaskr"
ENV FLASK_APP="flaskr/backservice.py"
ENV FLASK_ENV="docker"

# Copy the project (taking into account the dockerigonre)
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && \
    python -m pip install -r requirement.txt

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "-h", "0.0.0.0"]