# rasa/Dockerfile
FROM python:3.8.19-slim

# Install build-essential and curl for compiling dependencies and fetching scripts
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the Portuguese spaCy model
RUN pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.7.0/pt_core_news_sm-3.7.0.tar.gz

# Copy the rest of the application code
COPY . /app

# Train the Rasa model
# Expose Rasa's port
EXPOSE 5005

# Define the entrypoint and command
ENTRYPOINT ["rasa"]
CMD ["run", "--enable-api", "--cors", "*", "--port", "5005"]
