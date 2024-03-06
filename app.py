import os
from flask import Flask, render_template, Response, request, jsonify
import cv2
import face_recognition as face_rec
import requests
import threading
import numpy as np

app = Flask(__name__)


ESP32_API_URL = "http://192.168.1.22/api/"
# Line Notify token
line_token = "FbCTBCptFxcETZ06dwRKpJ9G3I9Ymh5UgIUtvEt32yt"
# line_notify = LineNotify(LINE_NOTIFY_TOKEN)


class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

    def capture_frame(self):
        # Read a frame from the camera
        success, frame = self.cap.read()

        if not success:
            print("Error capturing frame from the camera")
            return None

        # Optionally, you can perform additional processing on the frame here
        # For example, resizing, converting to grayscale, etc.

        return frame

    def release_camera(self):
        # Release the camera when done
        self.cap.release()

    def restart_camera(self):
        # Reopen the camera
        self.cap = cv2.VideoCapture(0)


# Create a global Camera object
object_camera = Camera()


# Function to load and encode reference images in a folder
def load_reference_images(folder_path):
    reference_encodings = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.png')):
            image_path = os.path.join(folder_path, filename)
            reference_image = face_rec.load_image_file(image_path)
            reference_encoding = face_rec.face_encodings(reference_image)[0]
            name = os.path.splitext(filename)[0]
            reference_encodings[name] = reference_encoding
    return reference_encodings


# Specify the folder containing reference images
reference_folder_path = 'pictures'

# Load reference images and encodings
reference_encodings = load_reference_images(reference_folder_path)

# Variable to track frames
is_recognize = False


def send_to_line_notify_async(jpeg_image, line_token, message):
    try:
        send_to_line_notify(jpeg_image, line_token, message)
    except Exception as e:
        print("An error occurred while sending to Line Notify:", e)


def post_to_esp32_api_async(name):
    try:
        print(requests.post(f"{ESP32_API_URL}face_recognized", data={'message': f"{name} has opened the door."}))
    except Exception as e:
        print("An error occurred while posting to ESP32 API:", e)


def generate_frames():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while True:
        success, frame = object_camera.cap.read()
        if not success:
            break
        else:
            # Perform face detection (you may need to customize this part)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Trigger action on face recognition (e.g., turn on lights and send Line Notify)
                if not is_recognize:
                    trigger_face_recognition_actions(frame)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    object_camera.release_camera()


# Function to convert frame to JPEG format
def convert_to_jpeg(frame):
    # Convert frame to JPEG format
    _, jpeg_image = cv2.imencode('.jpg', frame)

    return jpeg_image.tobytes()


# Function to send image to Line Notify with a message
def send_to_line_notify(image_bytes, token, message):
    # Line Notify API endpoint
    url = "https://notify-api.line.me/api/notify"

    # Set request headers with Authorization token
    headers = {"Authorization": "Bearer " + token}

    # Set request payload with image data and message
    files = {"imageFile": image_bytes}
    payload = {"message": message}

    # Send HTTP POST request to Line Notify
    response = requests.post(url, headers=headers, files=files, data=payload)

    # Print response status code and message
    print("Response:", response.status_code, response.text)


def process_face_recognition(frame, face_locations, reference_encodings):
    global is_recognize
    for face_encoding in face_rec.face_encodings(frame, face_locations):
        distances = face_rec.face_distance(list(reference_encodings.values()), face_encoding)
        best_match_index = np.argmin(distances)
        if distances[best_match_index] < 0.38:  # Adjust this threshold as needed
            is_recognize = True
            name = list(reference_encodings.keys())[best_match_index]
            # Add drawing and labeling logic here as needed
            print("threshold", distances[best_match_index], "Name:", name)
            # Draw rectangles and display name as before
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            # Convert frame to JPEG format
            jpeg_image = convert_to_jpeg(frame)
            # Message to accompany the image
            message = "Frame captured from camera"
            # Create and start threads for Line Notify and ESP32 API
            line_notify_thread = threading.Thread(target=send_to_line_notify_async, args=(jpeg_image, line_token, message))
            esp32_api_thread = threading.Thread(target=post_to_esp32_api_async, args=(name,))
            line_notify_thread.start()
            esp32_api_thread.start()

            # Wait for threads to finish
            line_notify_thread.join()
            esp32_api_thread.join()
            print("Face recognized! Opened the door.", name)


def trigger_face_recognition_actions(frame=None):
    global is_recognize
    if not is_recognize:
        face_locations = face_rec.face_locations(frame)
        # Start the face recognition in a new thread to avoid blocking the main thread
        threading.Thread(target=process_face_recognition, args=(frame, face_locations, reference_encodings)).start()


@app.route('/delete_recognize_faces', methods=['POST'])
def delete_recognize_faces():
    global reference_encodings
    # Get the user-inputted face name
    face_name = request.form.get('face_name')

    if face_name is not None:
        delete_path = os.path.join('pictures', f'{face_name}.jpg')
        print(delete_path)
        os.remove(delete_path)
        message = f"Face '{face_name}' delete successfully"
        reference_encodings = load_reference_images(reference_folder_path)
    else:
        message = "Error: Face name is required"

    return jsonify(message=message), 200


@app.route('/restart_recognize_process', methods=['GET'])
def restart_recognize_process():
    # Logic for re-recognizing faces (triggered by the "Re-Recognize Faces" button)
    # You can implement face recognition with your known faces database
    # ...
    global is_recognize
    is_recognize = False

    return jsonify(message="Recognition process restarted"), 200


@app.route('/store_face', methods=['POST'])
def store_face():
    global reference_encodings
    # Get the user-inputted face name
    face_name = request.form.get('face_name')

    if not face_name:
        message = "Error: Face name is required"

    # Logic for storing a face image in the "pictures" folder
    # You may need to customize this based on your face capture and storage process
    frame = object_camera.capture_frame()

    if frame is not None:
        save_path = os.path.join('pictures', f'{face_name}.jpg')
        print(save_path)
        cv2.imwrite(save_path, frame)
        message = f"Face '{face_name}' stored successfully"
        reference_encodings = load_reference_images(reference_folder_path)
    else:
        message = "Error capturing face"

    return jsonify(message=message), 200


# # Face recognition route
# @app.route('/face_recognition', methods=['POST'])
# def face_recognition():
#     # You can add more logic here, such as storing recognized faces or triggering specific actions
#     trigger_face_recognition_actions()
#     return "Face recognition completed"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # --host 0.0.0.0 --port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
