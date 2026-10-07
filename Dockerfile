FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5050
EXPOSE 5050
CMD ["hypercorn", "src.user:app", "--bind", "0.0.0.0:5050"]