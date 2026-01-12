import cv2
import numpy as np
import datetime
from deepface import DeepFace
import pygame
import time
from twilio.rest import Client
from tkinter import messagebox, simpledialog, filedialog

# ==== LOGIN CONFIG ====
MAX_ATTEMPTS = 2
PASSWORD = "admin123"  # Change this to your secure password
login_failures = 0

# Initialize sound for alerts
pygame.mixer.init()
alarm_sound = pygame.mixer.Sound("alarm.mp3") 

def log_to_blockchain(event):
    print(f"[Blockchain] Event Logged: {event}")

# Simulate failed login and time condition
def get_failed_login_attempts():
    global login_failures
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        input_pw = simpledialog.askstring("Login", "Enter admin password:", show='*')
        if input_pw is None:
            exit()
        if input_pw == PASSWORD:
            login_failures = attempts
            return True
        else:
            attempts += 1
            messagebox.showerror("Error", f"Incorrect password. {MAX_ATTEMPTS - attempts} attempt(s) left.")
    pygame.mixer.Sound.play(alarm_sound)
    messagebox.showwarning("Locked", "Too many incorrect attempts. Access denied.")
    return attempts
    exit()

def is_after_6_pm():
    return datetime.datetime.now().hour >= 18

# Twilio Configuration
account_sid = 'Your Account SID'
auth_token = 'Your Account Authentication Token'
twilio_number = 'Your Twillo Number'  
recipient_number = 'Personal Mobile Number'  

client = Client(account_sid, auth_token)

def send_sms_alert(message):
    try:
        sms = client.messages.create(
            body=message,
            from_=twilio_number,
            to=recipient_number
        )
        print(f"[SMS Sent] SID: {sms.sid}")
    except Exception as e:
        print(f"[SMS Error] {e}")


# Alert function
def alert_user(anomaly_type):
    pygame.mixer.Sound.play(alarm_sound)
    message = f"[ALERT] {anomaly_type} detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!"
    print(message)
    send_sms_alert(message)
    log_to_blockchain(anomaly_type)

# Load face detector
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Start video
cap = cv2.VideoCapture(0) 

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    result = DeepFace.analyze(frame , actions = ['emotion'])

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(gray, 1.1, 5)

    for (x, y, w, h) in faces:
        # Draw green circle on face
        center_coordinates = (x + w // 2, y + h // 2)
        radius = max(w // 2, h // 2)
        cv2.circle(frame, center_coordinates, radius, (0, 255, 0), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX

        cv2.putText(frame,
                    result[0]['dominant_emotion'],
                    (50, 50),
                    font, 3,
                    (0, 0, 255),
                    2,
                    cv2.LINE_4)
        # Apply intrusion detection logic
        failed_logins = get_failed_login_attempts()
        time_check = is_after_6_pm()
        emotion = result[0]['dominant_emotion']

        if emotion == 'Fear' and failed_logins > 2 and time_check:
            alert_user("Intruder")
        elif emotion == 'Fear' or failed_logins > 2 or time_check:
            alert_user("Suspicious")

    cv2.imshow('IoT Security - Emotion Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
