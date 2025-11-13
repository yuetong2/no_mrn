# Use official Render Python image
FROM python:3.12-slim

# Install Tesseract and dependencies
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev && rm -rf /var/lib/apt/lists/*

# Copy code and install Python deps
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Start Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]
