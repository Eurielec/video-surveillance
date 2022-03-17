# Start from the lightest image for Python3
FROM python:slim-bullseye

RUN mkdir /data

# Set the working directory to container's root /
WORKDIR /app

# Requirements for opencv
RUN apt-get update && apt-get install -y python3-opencv

# Install the requirements for the Python app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the program
COPY desecurity.py ./

# SEE ENVIRONMENT VARIABLES IN docker-compose.yml

# Run the script
CMD ["python", "./desecurity.py"]
