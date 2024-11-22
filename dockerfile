FROM python:3.12-slim
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app ./

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]