import io
from flask import Flask, render_template, request, redirect, send_file
from PIL import Image
import torch
import pandas as pd

METRIC_POLL_FREQUENCY = 15

app = Flask(__name__)

model = torch.hub.load('ultralytics/yolov5', 'custom', 'best.onnx')
request_count = 0

@app.route('/', methods=['GET', 'POST'])
def process_request():
    global request_count
    request_count = request_count + 1
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return

        img_bytes = file.read()
        result = model(Image.open(io.BytesIO(img_bytes)))
        result.save(save_dir='static', exist_ok=True)

        return send_file('static/image0.jpg', mimetype='image/jpg')
    return render_template('index.html')


@app.route('/metrics', methods=['GET'])
def get_request_count():
    global request_count
    return_value = request_count / METRIC_POLL_FREQUENCY
    request_count = 0
    return str(return_value)

if __name__ == '__main__':
    app.run(debug=True)