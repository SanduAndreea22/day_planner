# Imaginea de bază cu Python
FROM python:3.10-slim

# Setează folderul de lucru în container
WORKDIR /app

# Copiază și instalează cerințele
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiază restul codului (manage.py, folderele de app etc.)
COPY . .

# Expune portul 8000
EXPOSE 8000

# Pornește serverul
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]