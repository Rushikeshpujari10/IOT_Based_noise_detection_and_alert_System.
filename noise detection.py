import time
import smtplib
import sounddevice as sd
import numpy as np
import RPi.GPIO as GPIO
import sqlite3

# Adjust these values as per your setup and requirements
HIGH_NOISE_THRESHOLD = 0.05  # Adjust this threshold value for high noise levels
SECONDS_TO_MONITOR = 10  # Number of seconds to monitor audio for noise
RECIPIENT_EMAIL = "hodjjmcoe.com"  # The email address to send alerts to

# Set up GPIO for the speaker and noise sensor
GPIO.setmode(GPIO.BCM)
SPEAKER_PIN = 18
NOISE_SENSOR_PIN = 23
GPIO.setup(SPEAKER_PIN, GPIO.OUT)
GPIO.setup(NOISE_SENSOR_PIN, GPIO.IN)

# Create a database and table to store noise data and lecture schedule
db_conn = sqlite3.connect("lecture_data.db")
db_cursor = db_conn.cursor()
db_cursor.execute('''CREATE TABLE IF NOT EXISTS noise_data
                    (timestamp TEXT, noise_level REAL)''')
db_cursor.execute('''CREATE TABLE IF NOT EXISTS lecture_schedule
                    (lecture_time TEXT, teacher_email TEXT)''')
db_conn.commit()

def send_email(recipient, subject, body):
    sender_email = "your_email@gmail.com"  # Your email address
    sender_password = "your_email_password"  # Your email password

    message = f"From: {sender_email}\nTo: {recipient}\nSubject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, message)
    except Exception as e:
        print("Error sending email:", str(e))

def store_data(timestamp, noise_level):
    db_cursor.execute("INSERT INTO noise_data (timestamp, noise_level) VALUES (?, ?)",
                      (timestamp, noise_level))
    db_conn.commit()

def check_lecture_schedule():
    current_time = time.strftime('%H:%M')
    db_cursor.execute("SELECT teacher_email FROM lecture_schedule WHERE lecture_time=?", (current_time,))
    result = db_cursor.fetchone()
    if result:
        teacher_email = result[0]
        return teacher_email
    else:
        return None

def display_instructions():
    # Add code here to display instructions on the screen using the speaker and display
    # For example, you can play an audio file using the speaker and show messages on the screen.
    # You'll need to use the appropriate libraries for your speaker and display setup.
    pass

def audio_callback(indata, frames, time, status):
    # Calculate the RMS (Root Mean Square) value of the audio data
    rms = np.sqrt(np.mean(np.square(indata)))
    
    # Check if the RMS value exceeds the high noise threshold
    if rms > HIGH_NOISE_THRESHOLD:
        # Check the database for scheduled lecture
        teacher_email = check_lecture_schedule()
        if teacher_email:
            # Send an email alert to the teacher of the scheduled lecture
            subject = "High Noise Alert in Your Lecture!"
            body = f"High noise detected during your lecture at {time.strftime('%Y-%m-%d %H:%M:%S')}. Noise level: {rms:.4f}"
            send_email(teacher_email, subject, body)

            # Display instructions on the screen using the speaker and display
            display_instructions()

    # Store the data in the database
    store_data(time.strftime('%Y-%m-%d %H:%M:%S'), rms)

def main():
    print("Starting Noise Detection...")
    print(f"Monitoring for {SECONDS_TO_MONITOR} seconds. Press Ctrl+C to stop.")

    with sd.InputStream(callback=audio_callback):
        time.sleep(SECONDS_TO_MONITOR)

if _name_ == "_main_":
    try:
        main()
    except KeyboardInterrupt:
        print("Noise Detection Stopped.")
    finally:
        GPIO.cleanup()
        db_conn.close()