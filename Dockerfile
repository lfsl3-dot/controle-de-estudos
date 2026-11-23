# Usado no Hugging Face Spaces (SDK Docker). As chaves NAO ficam aqui:
# cadastre SUPABASE_URL e SUPABASE_KEY em Settings -> Variables and secrets.
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O Hugging Face espera a porta 7860 (o main.py le a variavel PORT)
ENV PORT=7860
EXPOSE 7860

RUN useradd -m appuser
USER appuser

CMD ["python", "main.py"]
