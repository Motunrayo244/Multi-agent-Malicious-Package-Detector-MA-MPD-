# Use an official Python runtime as a base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 

# Add Poetry's bin directory to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy the Poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies inside the virtual environment created by Poetry
RUN poetry install --no-root


# Copy the rest of the application code
COPY . /app/

# Expose the port the FastAPI app will run on
EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["poetry", "run", "uvicorn", "api.classify:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
