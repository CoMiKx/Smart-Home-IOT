import face_recognition
import cv2
import os


# Function to load and encode reference images in a folder
def load_reference_images(folder_path):
    reference_encodings = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.png')):
            image_path = os.path.join(folder_path, filename)
            reference_image = face_recognition.load_image_file(image_path)
            reference_encoding = face_recognition.face_encodings(reference_image)[0]
            name = os.path.splitext(filename)[0]
            reference_encodings[name] = reference_encoding
    return reference_encodings


# Specify the folder containing reference images
reference_folder_path = 'pictures'

# Load reference images and encodings
reference_encodings = load_reference_images(reference_folder_path)

# Open a connection to the camera (0 is the default camera)
video_capture = cv2.VideoCapture(0)

# Variable to track frames
frame_count = 0

while True:
    # Capture each frame from the camera
    ret, frame = video_capture.read()

    # Skip every other frame
    if frame_count % 2 == 0:
        # Find all face locations in the current frame
        face_locations = face_recognition.face_locations(frame)

        if len(face_locations) > 0:
            # Encode faces in the current frame
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            # Check each reference face against faces in the frame
            for face_encoding in face_encodings:
                for name, reference_encoding in reference_encodings.items():
                    results = face_recognition.compare_faces([reference_encoding], face_encoding)
                    if results[0]:
                        # Draw rectangles around the faces and display the name
                        for (top, right, bottom, left) in face_locations:
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            font = cv2.FONT_HERSHEY_DUPLEX
                            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        # Display the resulting frame
        cv2.imshow('Face Verification', frame)

    # Increment frame count
    frame_count += 1

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close the window
video_capture.release()
cv2.destroyAllWindows()
