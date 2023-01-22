FROM python:3.10

COPY ./templates ./templates
COPY ./static/css ./static/css
COPY ./best.onnx .
COPY ./yolo_api.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD python yolo_api.py

EXPOSE 5000