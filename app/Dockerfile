FROM python:3.10

COPY ./templates ./templates
COPY ./static/css ./static/css
COPY ./best.onnx .
COPY ./yolo_api.py .
COPY requirements.txt .

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install -r requirements.txt

CMD python yolo_api.py

EXPOSE 5000