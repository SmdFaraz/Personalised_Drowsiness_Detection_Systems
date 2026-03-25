import cv2

def draw_panel(frame, x, y, w, h, color=(0,0,0), alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x,y), (x+w, y+h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)


def draw_progress_bar(frame, x, y, w, h, progress):
    cv2.rectangle(frame, (x,y), (x+w, y+h), (255,255,255), 2)
    cv2.rectangle(frame, (x,y), (x+int(w*progress), y+h), (0,200,0), -1)


def draw_text(frame, text, x, y, scale=0.7, color=(255,255,255), thickness=2):
    cv2.putText(frame, text, (x,y),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness)