import io
from flask import Flask, render_template, request, redirect, send_file, Response
from PIL import Image
import numpy as np
import cv2
from cvu.detector.yolov5 import Yolov5 as Yolov5Onnx

METRIC_POLL_FREQUENCY = 15

app = Flask(__name__)

request_count = 0

def detect_image(device, weight, image):
    # load model
    model = Yolov5Onnx(classes=['eye_open', 'eye_closed'],
                       backend="onnx",
                       weight=weight,
                       device=device)

    # inference
    preds = model(image)
    print(preds)

    # draw image
    preds.draw(image)

    # write image
    cv2.imwrite('static/image0.jpg', image)

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
        opencvImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(img_bytes))), cv2.COLOR_RGB2BGR) # dont know if necessary
        detect_image('cpu', 'best.onnx', opencvImage)
        #result.save(save_dir='static', exist_ok=True)

        return send_file('static/image0.jpg', mimetype='image/jpg')
    return render_template('index.html')


@app.route('/metrics')
def get_request_count():
    global request_count
    return_value = request_count / METRIC_POLL_FREQUENCY
    request_count = 0
    return Response('# TYPE requests_per_s gauge\nrequests_per_s ' + str(return_value) + '\n', mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)