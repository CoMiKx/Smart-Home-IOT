import cv2
import requests


# Function to capture frame from camera video
def capture_frame():
    # Initialize camera capture
    cap = cv2.VideoCapture(0)

    # Capture frame-by-frame
    ret, frame = cap.read()

    # Release the capture
    cap.release()

    return frame


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


# Main function
def main():
    # Line Notify token
    line_token = "FbCTBCptFxcETZ06dwRKpJ9G3I9Ymh5UgIUtvEt32yt"

    # Capture frame from camera
    frame = capture_frame()

    # Convert frame to JPEG format
    jpeg_image = convert_to_jpeg(frame)

    # Message to accompany the image
    message = "Frame captured from camera"

    # Send image to Line Notify with message
    send_to_line_notify(jpeg_image, line_token, message)


if __name__ == "__main__":
    main()
