# Dockerfile — builds the container that runs our Gradio app

FROM python:3.11-slim

# Hugging Face Spaces requires a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install dependencies first (better caching)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app (app.py, model.pkl, labels.pkl)
COPY --chown=user . .

# Spaces routes traffic to port 7860
EXPOSE 7860

CMD ["python", "chatbot.py"]