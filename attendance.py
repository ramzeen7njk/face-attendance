import cv2
import numpy as np
import face_recognition
import pandas as pd
from datetime import datetime
import os
import urllib.request
import time

class AttendanceSystem:
    def __init__(self):
        # Replace this IP address with your IP Webcam address
        self.ip_address = "192.168.1.6:8080"  # Example IP address
        self.known_faces = []
        self.known_names = []
        self.attendance_df = self.initialize_attendance()
        
    def initialize_attendance(self):
        if os.path.exists('attendance.xlsx'):
            return pd.read_excel('attendance.xlsx')
        return pd.DataFrame(columns=['Name', 'Date', 'Time', 'Status'])
    
    def get_frame(self):
        try:
            url = f"http://{self.ip_address}/shot.jpg"
            img_resp = urllib.request.urlopen(url)
            img_arr = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_arr, -1)
            if frame is None:
                raise Exception("Failed to decode frame")
            return frame
        except Exception as e:
            print(f"Error capturing frame: {str(e)}")
            print("Please check if:")
            print("1. IP Webcam app is running on your phone")
            print(f"2. The IP address {self.ip_address} is correct")
            print("3. Your phone and computer are on the same network")
            return None
    
    def register_face(self):
        print("Registration mode activated. Press 'o' to capture face or 'q' to quit.")
        while True:
            frame = self.get_frame()
            if frame is None:
                time.sleep(1)
                continue
                
            cv2.imshow('Registration', frame)
            key = cv2.waitKey(1)
            
            if key == ord('o'):  # Capture face
                face_locations = face_recognition.face_locations(frame)
                if face_locations:
                    name = input("Enter student name: ")
                    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
                    self.known_faces.append(face_encoding)
                    self.known_names.append(name)
                    print(f"Successfully registered {name}")
                    break
                else:
                    print("No face detected. Please try again.")
            
            elif key == ord('q'):
                break
        
        cv2.destroyWindow('Registration')
    
    def mark_attendance(self, name):
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        
        # Check if attendance already marked for today
        today_attendance = self.attendance_df[
            (self.attendance_df['Name'] == name) & 
            (self.attendance_df['Date'] == date)
        ]
        
        if today_attendance.empty:
            new_attendance = pd.DataFrame({
                'Name': [name],
                'Date': [date],
                'Time': [time],
                'Status': ['Present']
            })
            self.attendance_df = pd.concat([self.attendance_df, new_attendance], ignore_index=True)
            self.attendance_df.to_excel('attendance.xlsx', index=False)
            print(f"Marked attendance for {name}")
    
    def run(self):
        print("Starting Attendance System...")
        print("Press 'r' to register new face")
        print("Press 'q' to quit")
        
        while True:
            frame = self.get_frame()
            if frame is None:
                time.sleep(1)
                continue
            
            # Find faces in current frame
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(self.known_faces, face_encoding)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_names[first_match_index]
                    self.mark_attendance(name)
                
                # Draw rectangle and name
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            
            cv2.imshow('Attendance System', frame)
            key = cv2.waitKey(1)
            
            if key == ord('r'):  # Register new face
                self.register_face()
            elif key == ord('q'):  # Quit
                break
        
        cv2.destroyAllWindows()

if __name__ == "__main__":
    attendance_system = AttendanceSystem()
    attendance_system.run()
