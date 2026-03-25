import cv2

def draw_profiles(frame, profiles, selected_idx):

    h, w, _ = frame.shape

    cv2.putText(frame, "Profiles",
                (50, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255),
                2)

    y_start = 100

    for i, p in enumerate(profiles):

        y = y_start + i * 120

        color = (0,255,0) if i == selected_idx else (255,255,255)

        # Name
        cv2.putText(frame,
                    f"{p['name']}",
                    (50, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2)

        # Face image
        if p["image"] is not None:
            img = cv2.resize(p["image"], (80, 80))

            frame[y-60:y+20, 200:280] = img

    # Instructions
    cv2.putText(frame,
                "UP/DOWN: Navigate | D: Delete | E: Edit | ESC: Back",
                (50, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,255),
                1)