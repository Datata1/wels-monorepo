import cv2
import numpy as np

def detect_court_roi(frame):
    """
    Erkennt das Spielfeld automatisch anhand der Bodenfarbe.
    Optimiert für Kamera-Position: mittig an der unteren Bande.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    img_h, img_w = frame.shape[:2]

    # Spielfeld-Farbe aus dem unteren-mittleren Bereich samplen
    # (da ist bei dieser Kameraposition sicher Spielfeld)
    sample_region = hsv[
        int(img_h * 0.5):int(img_h * 0.8),  # Untere Hälfte
        int(img_w * 0.3):int(img_w * 0.7)   # Mittlerer Bereich
    ]

    median_h = np.median(sample_region[:, :, 0])
    median_s = np.median(sample_region[:, :, 1])
    median_v = np.median(sample_region[:, :, 2])

    # Farbmaske für Spielfeld
    lower = np.array([
        max(0, median_h - 15),
        max(0, median_s - 50),
        max(0, median_v - 50)
    ])
    upper = np.array([
        min(179, median_h + 15),
        min(255, median_s + 50),
        min(255, median_v + 50)
    ])

    court_mask = cv2.inRange(hsv, lower, upper)

    # Rauschen entfernen
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    court_mask = cv2.morphologyEx(court_mask, cv2.MORPH_CLOSE, kernel)
    court_mask = cv2.morphologyEx(court_mask, cv2.MORPH_OPEN, kernel)

    # Größte Fläche = Spielfeld
    contours, _ = cv2.findContours(
        court_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return (0, 0, img_w, img_h), court_mask

    largest_contour = max(contours, key=lambda c: cv2.contourArea(c))
    x, y, w, h = cv2.boundingRect(largest_contour)

    return (x, y, w, h), court_mask


def get_stable_roi(input_path, num_samples=100):
    """
    Berechnet eine stabile ROI über mehrere Frames.
    
    Angepasst für Kamera unten mittig:
    - Oben wird mehr abgeschnitten (Tribüne, Wand)
    - Unten wird wenig/nichts abgeschnitten (Kamera ist nah)
    - X = volle Breite (Kamera schwenkt horizontal)
    """
    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    sample_interval = max(1, total_frames // num_samples)
    y_tops = []
    y_bottoms = []

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % sample_interval == 0:
            roi, _ = detect_court_roi(frame)
            x, y, w, h = roi
            y_tops.append(y)
            y_bottoms.append(y + h)

        frame_count += 1

    cap.release()

    if not y_tops:
        print("  Warnung: Keine ROI erkannt, verwende ganzes Bild")
        return (0, 0, width, height)

    # === ASYMMETRISCHE ROI ===

    # OBEN: Aggressiver abschneiden
    # Median + etwas Sicherheitspuffer nach oben
    stable_y_top = int(np.median(y_tops))
    # Noch etwas Padding für Spieler die hochspringen (Torwurf!)
    top_padding = int(height * 0.1)  # 12% des Bildes als Puffer
    stable_y_top = max(0, stable_y_top - top_padding)

    # UNTEN: Konservativ – wenig abschneiden
    # Die Kamera steht nah am Feld, unterer Rand ist fast am Spielfeld
    stable_y_bottom = int(np.percentile(y_bottoms, 90))  # 90. Perzentil
    # Minimales Padding, Bänke/Kamerabereich leicht einschließen
    bottom_padding = 15
    stable_y_bottom = min(height, stable_y_bottom + bottom_padding)

    stable_roi = (0, stable_y_top, width, stable_y_bottom - stable_y_top)

    # Statistik ausgeben
    top_cut_percent = (stable_y_top / height) * 100
    bottom_cut_percent = ((height - stable_y_bottom) / height) * 100

    print(f"  Oben abgeschnitten:  {stable_y_top}px ({top_cut_percent:.1f}%)")
    print(f"  Unten abgeschnitten: {height - stable_y_bottom}px ({bottom_cut_percent:.1f}%)")
    print("  → Oben deutlich mehr als unten (wie erwartet)")

    return stable_roi


def visualize_roi(input_path, roi):
    """
    Zeigt die ROI auf 3 verschiedenen Frames an:
    - Anfang, Mitte, Ende des Videos
    So sieht man ob die ROI bei verschiedenen Kamera-Positionen passt.
    """
    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 3 Frames aus verschiedenen Zeitpunkten
    positions = [
        int(total_frames * 0.2),  # Anfang
        int(total_frames * 0.5),  # Mitte
        int(total_frames * 0.8),  # Ende
    ]

    x, y, w, h = roi
    frames = []

    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue

        # ROI visualisieren
        mask = np.zeros_like(frame)
        mask[y:y + h, x:x + w] = 1
        darkened = cv2.addWeighted(frame, 0.3, np.zeros_like(frame), 0.7, 0)
        result = np.where(mask == 1, frame, darkened)

        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Beschriftung: Was oben/unten abgeschnitten wird
        cv2.putText(result, "OBEN: abgeschnitten (Tribuene/Wand)",
                    (20, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)
        cv2.putText(result, "UNTEN: minimal (Kamera nah am Feld)",
                    (20, y + h + 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 200, 255), 2)

        # Frame-Nummer anzeigen
        time_sec = pos / cap.get(cv2.CAP_PROP_FPS)
        cv2.putText(result, f"Frame {pos} ({time_sec:.0f}s)",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 2)

        frames.append(result)

    cap.release()

    # Alle 3 Frames nebeneinander oder nacheinander zeigen
    for i, frame in enumerate(frames):
        scale = 0.6  # Verkleinern damit es auf den Bildschirm passt
        small = cv2.resize(frame, None, fx=scale, fy=scale)
        cv2.imshow(f'ROI Vorschau {i+1}/3 (Taste druecken)', small)
        cv2.waitKey(0)

    cv2.destroyAllWindows()


def apply_roi_to_video(input_path, output_path, roi):
    """Schneidet das Video auf die ROI zu."""
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    x, y, w, h = roi
    w = w - (w % 2)
    h = h - (h % 2)

    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cropped = frame[y:y + h, x:x + w]
        out.write(cropped)
        frame_count += 1

        if frame_count % 500 == 0:
            print(f"  Fortschritt: {(frame_count/total_frames)*100:.1f}%")

    cap.release()
    out.release()
    print(f"Fertig! {frame_count} Frames → {output_path}")

def isolate_roi(input_path, output_path):
    print("\n1️⃣ Berechne stabile ROI über mehrere Frames...")
    roi = get_stable_roi(input_path)

    print("\n2️⃣ Visualisiere die ROI auf Beispiel-Frames...")
    visualize_roi(input_path, roi)

    print("\n3️⃣ Schneide das Video auf die ROI zu...")
    apply_roi_to_video(input_path, output_path, roi)