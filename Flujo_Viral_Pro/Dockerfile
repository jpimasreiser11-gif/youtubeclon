FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy for MoviePy
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install playwright browsers
RUN playwright install chromium
RUN playwright install-deps

CMD ["python", "main.py"]
