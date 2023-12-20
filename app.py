import os
from flask import Flask, render_template, Response, request
import cv2
import requests
from line_notify import LineNotify

app = Flask(__name__)


# ESP32_API_URL = "http://esp32-ip-address/api"
# LINE_NOTIFY_TOKEN = "your-line-notify-token"
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
                trigger_face_recognition_actions()

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    object_camera.release_camera()


@app.route('/re_recognize_faces', methods=['POST'])
def re_recognize_faces():
    # Logic for re-recognizing faces (triggered by the "Re-Recognize Faces" button)
    # You can implement face recognition with your known faces database
    # ...

    return "Re-recognized faces"


@app.route('/store_face', methods=['POST'])
def store_face():
    # Get the user-inputted face name
    face_name = request.form.get('face_name')

    if not face_name:
        return "Error: Face name is required"

    # Logic for storing a face image in the "pictures" folder
    # You may need to customize this based on your face capture and storage process
    frame = object_camera.capture_frame()

    if frame is not None:
        save_path = os.path.join('pictures', f'{face_name}.jpg')
        print(save_path)
        cv2.imwrite(save_path, frame)
        return f"Face '{face_name}' stored successfully"
    else:
        return "Error capturing face"


def trigger_face_recognition_actions():
    # You can customize this function based on your requirements
    # For example, turn on lights and send Line Notify
    # requests.post(f"{ESP32_API_URL}/turn_on_light")
    # line_notify.send(message="Face recognized! Opened the door.")
    print("Face recognized! Opened the door.")


# Face recognition route
@app.route('/face_recognition', methods=['POST'])
def face_recognition():
    # You can add more logic here, such as storing recognized faces or triggering specific actions
    trigger_face_recognition_actions()
    return "Face recognition completed"


# Line Notify integration route
@app.route('/send_line_notify', methods=['POST'])
def send_line_notify():
    message = request.form.get('message')
    # line_notify.send(message=message)
    return "Line Notify message sent"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)
