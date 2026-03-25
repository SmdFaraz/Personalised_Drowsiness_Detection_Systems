from ui.components import draw_panel, draw_progress_bar, draw_text


def draw_header(frame):
    draw_text(frame, "Driver Monitoring System", 20, 40, 1, (255,255,255), 2)


def draw_status_panel(frame, ear, mar, status):
    draw_panel(frame, 10, 60, 250, 160)

    draw_text(frame, f"EAR: {ear:.2f}", 20, 100, 0.7, (0,255,0))
    draw_text(frame, f"MAR: {mar:.2f}", 20, 140, 0.7, (255,0,0))

    color = (0,0,255) if status == "DROWSY" else (0,255,0)
    draw_text(frame, f"Status: {status}", 20, 180, 0.8, color, 3)


def draw_waiting(frame, w, h):
    draw_panel(frame, w//2-200, h//2-80, 400, 160)
    draw_text(frame, "Press 'C' to Start Calibration",
              w//2-180, h//2, 0.7, (0,255,255), 2)


def draw_calibration(frame, w, h, remaining, progress):
    draw_panel(frame, w//2-200, h//2-100, 400, 200)

    draw_text(frame, "Calibrating...",
              w//2-80, h//2-40, 1, (0,255,255), 2)

    draw_text(frame, f"Keep steady: {remaining}s",
              w//2-100, h//2, 0.7, (255,255,255), 2)

    draw_progress_bar(frame,
                      w//2-150, h//2+40,
                      300, 20, progress)