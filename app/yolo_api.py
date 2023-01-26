import io
from flask import Flask, render_template, request, redirect, send_file, Response
from PIL import Image
import torch

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


@app.route('/metrics')
def get_request_count():
    global request_count
    return_value = request_count / METRIC_POLL_FREQUENCY
    request_count = 0
    return Response('# TYPE requests_per_s gauge\nrequests_per_s ' + str(return_value), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)