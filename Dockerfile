# Start from the lightest image for Python3
FROM python:3.9-alpine3.15

RUN mkdir /data

# Set the working directory to container's root /
WORKDIR /app

# Install the requirements for the Python app
COPY requirements.txt ./
COPY desecurity.py ./
RUN pip install --no-cache-dir -r requirements.txt

# SEE ENVIRONMENT VARIABLES IN docker-compose.yml

# Run the script
CMD ["python", "./desecurity.py"]
