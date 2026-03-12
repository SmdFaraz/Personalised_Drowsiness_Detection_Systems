import cv2
import mediapipe as mp
from eye_utils import eye_aspect_ratio
from mouth_utils import mouth_aspect_ratio

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True
)

# Eye landmarks
LEFT_EYE = [33,160,158,133,153,144]
RIGHT_EYE = [362,385,387,263,373,380]

# Mouth landmarks
MOUTH = [78,81,13,311,308,402,14,178]

# Thresholds
EAR_THRESHOLD = 0.25
CONSEC_FRAMES = 3
DROWSY_FRAMES = 20

YAWN_THRESHOLD = 0.50
YAWN_FRAMES = 15

blink_counter = 0
total_blinks = 0

yawn_counter = 0
total_yawns = 0

cap = cv2.VideoCapture(0)

try:
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        status = "ALERT"

        if results.multi_face_landmarks:

            for face_landmarks in results.multi_face_landmarks:

                h, w, _ = frame.shape

                left_eye = []
                right_eye = []
                mouth = []

                # LEFT EYE
                for idx in LEFT_EYE:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    left_eye.append((x,y))
                    cv2.circle(frame,(x,y),2,(0,255,0),-1)

                # RIGHT EYE
                for idx in RIGHT_EYE:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    right_eye.append((x,y))
                    cv2.circle(frame,(x,y),2,(0,255,0),-1)

                # MOUTH
                for idx in MOUTH:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    mouth.append((x,y))
                    cv2.circle(frame,(x,y),2,(255,0,0),-1)

                # Calculate EAR
                leftEAR = eye_aspect_ratio(left_eye)
                rightEAR = eye_aspect_ratio(right_eye)
                ear = (leftEAR + rightEAR) / 2.0

                # Calculate MAR
                mar = mouth_aspect_ratio(mouth)

                # ----- BLINK & DROWSY DETECTION -----
                if ear < EAR_THRESHOLD:

                    blink_counter += 1

                    if blink_counter >= DROWSY_FRAMES:
                        status = "DROWSY"

                else:

                    if blink_counter >= CONSEC_FRAMES:
                        total_blinks += 1

                    blink_counter = 0

                # ----- YAWN DETECTION -----
                if mar > YAWN_THRESHOLD:

                    yawn_counter += 1

                    if yawn_counter >= YAWN_FRAMES:
                        total_yawns += 1
                        status = "DROWSY"
                        yawn_counter = 0

                else:
                    yawn_counter = 0

                # Display EAR
                cv2.putText(frame,
                            f"EAR: {ear:.2f}",
                            (30,50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0,255,0),
                            2)

                # Display MAR
                cv2.putText(frame,
                            f"MAR: {mar:.2f}",
                            (30,100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255,0,0),
                            2)

                # Display blink count
                cv2.putText(frame,
                            f"Blinks: {total_blinks}",
                            (30,150),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0,255,0),
                            2)

                # Display yawn count
                cv2.putText(frame,
                            f"Yawns: {total_yawns}",
                            (30,200),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255,0,0),
                            2)

                # Status display
                color = (0,0,255) if status=="DROWSY" else (0,255,0)

                cv2.putText(frame,
                            f"Status: {status}",
                            (30,250),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            color,
                            3)

        cv2.imshow("Driver Monitoring System", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    cap.release()
    cv2.destroyAllWindows()