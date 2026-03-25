import cv2

CARD_W = 200
CARD_H = 150
PADDING = 20

def draw_profile_cards(frame, profiles, scroll_offset, selected_idx):

    h, w, _ = frame.shape
    cards = []

    cols = max(1, w // (CARD_W + PADDING))

    for i, p in enumerate(profiles):

        row = i // cols
        col = i % cols

        x = PADDING + col * (CARD_W + PADDING)
        y = 80 + row * (CARD_H + PADDING) - scroll_offset

        if y < -CARD_H or y > h:
            continue

        # Card box
        cv2.rectangle(frame, (x, y), (x+CARD_W, y+CARD_H), (255,255,255), 2)

        # Image
        if p["image"] is not None:
            img = cv2.resize(p["image"], (80,80))
            frame[y+10:y+90, x+10:x+90] = img

        # Name
        cv2.putText(frame, p["name"],
                    (x+10, y+120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255,255,255),
                    2)

        # DELETE button
        cv2.rectangle(frame, (x+110, y+10), (x+190, y+50), (0,0,255), 2)
        cv2.putText(frame, "DEL", (x+125, y+40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

        # EDIT button
        cv2.rectangle(frame, (x+110, y+60), (x+190, y+100), (0,255,255), 2)
        cv2.putText(frame, "EDIT", (x+115, y+90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

        cards.append({
            "rect": (x, y, x+CARD_W, y+CARD_H),
            "index": i
        })

    return cards


def handle_click(x, y, cards, profiles):

    for card in cards:
        x1, y1, x2, y2 = card["rect"]
        idx = card["index"]

        if x1 < x < x2 and y1 < y < y2:

            # DELETE area
            if (x2-80 < x < x2-10) and (y1+10 < y < y1+50):
                return ("delete", idx)

            # EDIT area
            if (x2-80 < x < x2-10) and (y1+60 < y < y1+100):
                return ("edit", idx)

            return ("select", idx)

    return (None, None)