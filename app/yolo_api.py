import io
import os
from flask import Flask, render_template, request, redirect, send_file, Response
from PIL import Image
import numpy as np
import cv2
import time
from cvu.detector.yolov5 import Yolov5 as Yolov5Onnx
import threading
import glob
from pathlib import Path
from multiprocessing import Value
import psutil

app = Flask(__name__)

last_request_time = time.time()
request_count = Value('i', 0)
process_start_time = str(time.time())

# load model
model = Yolov5Onnx(classes=['eye_open', 'eye_closed'],
                    backend="onnx",
                    weight='best.onnx',
                    device='cpu')

def clear_stored_images(interval_s=15, older_than_s=60):
    older_than_ns = older_than_s * 1000000000
    while True:
        current_time_ns = time.time_ns()
        cut_off_time_ns = current_time_ns - older_than_ns

        jpg_paths = glob.glob('static\\\[0-9]*.jpg')
        for jpg_path in jpg_paths:
            file_timestamp = int(Path(jpg_path).stem)
            if(cut_off_time_ns > file_timestamp):
                os.remove(jpg_path)

        time.sleep(interval_s)


clear_stored_images_thread = threading.Thread(target=clear_stored_images, daemon=True)
clear_stored_images_thread.start()

def detect_image(image, filename='static/0.jpg'):
    # inference
    preds = model(image)
    print(preds)

    # draw image
    preds.draw(image)

    # write image
    cv2.imwrite(filename, image)

@app.before_request
def increment_request_counter():
    with request_count.get_lock():
        request_count.value = request_count.value + 1

@app.route('/', methods=['GET', 'POST'])
def process_request():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return

        current_time_ns = time.time_ns()
        filename = 'static/' + str(current_time_ns) + '.jpg'

        img_bytes = file.read()
        opencvImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(img_bytes))), cv2.COLOR_RGB2BGR) # dont know if necessary
        detect_image(opencvImage, filename=filename)
        #result.save(save_dir='static', exist_ok=True)

        return send_file(filename, mimetype='image/jpg')
    return render_template('index.html')


@app.route('/metrics')
def get_request_count():
    global last_request_time
    global process_start_time

    current_time = time.time()
    request_time_difference = time.time() - last_request_time
    last_request_time = current_time

    with request_count.get_lock():
        return_value = request_count.value / request_time_difference
        request_count.value = 0
    
    metrics_string = '# TYPE requests_per_s gauge\nrequests_per_s ' + str(return_value) + '\n\n'

    cpu_load_1m, cpu_load_5m, cpu_load_15m = psutil.getloadavg()
    cpu_load_1m = cpu_load_1m * 100
    cpu_load_5m = cpu_load_5m * 100
    cpu_load_15m = cpu_load_15m * 100

    metrics_string = metrics_string + '# TYPE cpu_avg_load_1m gauge\ncpu_avg_load_1m ' + str(cpu_load_1m) + '\n'
    metrics_string = metrics_string + '# TYPE cpu_avg_load_5m gauge\ncpu_avg_load_5m ' + str(cpu_load_5m) + '\n'
    metrics_string = metrics_string + '# TYPE cpu_avg_load_15m gauge\ncpu_avg_load_15m ' + str(cpu_load_15m) + '\n\n'

    ram_usage = psutil.virtual_memory()
    metrics_string = metrics_string + '# TYPE ram_usage_percent gauge\nram_usage_percent ' + str(ram_usage[2]) + '\n'
    metrics_string = metrics_string + '# TYPE ram_usage_gb gauge\nram_usage_gb ' + str(ram_usage[3] / 1000000000) + '\n\n'

    # get current unix timestamp
    metrics_string = metrics_string + '# TYPE process_start_time_seconds gauge\nprocess_start_time_seconds ' + process_start_time + '\n'
    
    return Response(metrics_string, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)