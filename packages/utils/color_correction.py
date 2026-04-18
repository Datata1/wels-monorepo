import cv2
import numpy as np

# ================================================================
# TEIL 1: VIDEO ANALYSIEREN – Brauchen wir überhaupt eine Korrektur?
# ================================================================

def analyze_video(input_path, sample_interval=30):
    """
    Analysiert das Video und gibt einen Bericht zurück,
    welche Beleuchtungsprobleme vorliegen.
    """
    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    brightness_values = []
    color_casts = []       # Abweichung von neutralem Grau
    contrast_values = []
    local_brightness = []  # Unterschied links vs. rechts

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % sample_interval == 0:
            h, w = frame.shape[:2]
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            v = hsv[:, :, 2]

            # 1. Helligkeit
            brightness_values.append(v.mean())

            # 2. Kontrast (Standardabweichung der Helligkeit)
            contrast_values.append(v.std())

            # 3. Farbstich messen (Abweichung von Grau im LAB-Farbraum)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            avg_a = lab[:, :, 1].mean() - 128  # 0 = neutral
            avg_b = lab[:, :, 2].mean() - 128  # 0 = neutral
            color_casts.append((avg_a, avg_b))

            # 4. Ungleichmäßigkeit: linke vs. rechte Hälfte
            left_brightness = v[:, :w // 2].mean()
            right_brightness = v[:, w // 2:].mean()
            local_brightness.append(abs(left_brightness - right_brightness))

        frame_count += 1

    cap.release()

    # === ERGEBNISSE AUSWERTEN ===
    report = {
        'total_frames': total_frames,
        'samples': len(brightness_values),
    }

    # Flackern: Wie stark schwankt die Helligkeit?
    brightness_std = np.std(brightness_values)
    report['brightness_mean'] = np.mean(brightness_values)
    report['brightness_std'] = brightness_std
    report['needs_flicker_fix'] = brightness_std > 3.0

    # Farbstich: Wie weit weg von neutral?
    avg_cast_a = np.mean([c[0] for c in color_casts])
    avg_cast_b = np.mean([c[1] for c in color_casts])
    cast_strength = np.sqrt(avg_cast_a ** 2 + avg_cast_b ** 2)
    report['color_cast_strength'] = cast_strength
    report['color_cast_a'] = avg_cast_a  # + = Grün, - = Magenta
    report['color_cast_b'] = avg_cast_b  # + = Gelb,  - = Blau
    report['needs_white_balance'] = cast_strength > 5.0

    # Kontrast: Ist das Bild zu flach?
    avg_contrast = np.mean(contrast_values)
    report['contrast_mean'] = avg_contrast
    report['needs_clahe'] = avg_contrast < 40.0

    # Ungleichmäßigkeit: Große Helligkeitsunterschiede im Bild?
    avg_unevenness = np.mean(local_brightness)
    report['unevenness'] = avg_unevenness
    report['needs_local_correction'] = avg_unevenness > 15.0

    return report


def print_report(report):
    """Gibt die Analyse übersichtlich aus."""
    print("=" * 55)
    print("  BELEUCHTUNGSANALYSE")
    print("=" * 55)
    print(f"  Frames analysiert: {report['samples']} Stichproben")
    print()

    # Flackern
    status = "⚠️  JA" if report['needs_flicker_fix'] else "✅ NEIN"
    print(f"  Flackern:          {status}")
    print(f"    Helligkeit ø:    {report['brightness_mean']:.1f}")
    print(f"    Schwankung:      ±{report['brightness_std']:.1f}"
          f"  (Grenzwert: 3.0)")
    print()

    # Farbstich
    status = "⚠️  JA" if report['needs_white_balance'] else "✅ NEIN"
    cast_dir = ""
    if report['needs_white_balance']:
        if report['color_cast_b'] > 2:
            cast_dir = "(gelblich)"
        elif report['color_cast_b'] < -2:
            cast_dir = "(bläulich)"
        if report['color_cast_a'] > 2:
            cast_dir += " (grünlich)"
        elif report['color_cast_a'] < -2:
            cast_dir += " (rötlich)"
    print(f"  Farbstich:         {status} {cast_dir}")
    print(f"    Stärke:          {report['color_cast_strength']:.1f}"
          f"  (Grenzwert: 5.0)")
    print()

    # Kontrast
    status = "⚠️  JA (zu flach)" if report['needs_clahe'] else "✅ NEIN"
    print(f"  Kontrastproblem:   {status}")
    print(f"    Kontrast ø:      {report['contrast_mean']:.1f}"
          f"  (Grenzwert: < 40.0)")
    print()

    # Ungleichmäßigkeit
    status = "⚠️  JA" if report['needs_local_correction'] else "✅ NEIN"
    print(f"  Ungleichmäßig:     {status}")
    print(f"    Links/Rechts Δ:  {report['unevenness']:.1f}"
          f"  (Grenzwert: 15.0)")
    print()

    # Zusammenfassung
    fixes = []
    if report['needs_white_balance']:
        fixes.append("Weißabgleich")
    if report['needs_flicker_fix']:
        fixes.append("Flicker-Korrektur")
    if report['needs_clahe']:
        fixes.append("CLAHE")
    if report['needs_local_correction']:
        fixes.append("Lokale Helligkeitskorrektur")

    print("-" * 55)
    if fixes:
        print(f"  EMPFEHLUNG: {', '.join(fixes)} anwenden")
    else:
        print("  EMPFEHLUNG: Keine Korrektur nötig! ✅")
        print("  Das Video hat bereits gute Beleuchtung.")
    print("=" * 55)

    return fixes


# ================================================================
# TEIL 2: NUR DIE NÖTIGEN KORREKTUREN ANWENDEN
# ================================================================

def correct_white_balance(frame):
    b, g, r = cv2.split(frame.astype(np.float32))
    avg_b, avg_g, avg_r = b.mean(), g.mean(), r.mean()
    avg_gray = (avg_b + avg_g + avg_r) / 3
    b = np.clip(b * (avg_gray / avg_b), 0, 255)
    g = np.clip(g * (avg_gray / avg_g), 0, 255)
    r = np.clip(r * (avg_gray / avg_r), 0, 255)
    return cv2.merge([b, g, r]).astype(np.uint8)


def correct_flicker(frame, target_brightness):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    current = v.mean()
    if current > 0:
        factor = np.clip(target_brightness / current, 0.8, 1.2)
        v = np.clip(v.astype(np.float32) * factor, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)


def apply_clahe(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lightness = clahe.apply(lightness)
    return cv2.cvtColor(
        cv2.merge([lightness, a_channel, b_channel]),
        cv2.COLOR_LAB2BGR,
    )


def process_video(input_path, output_path, report):
    """Wendet nur die nötigen Korrekturen an."""
    fixes = []
    if report['needs_white_balance']:
        fixes.append('white_balance')
    if report['needs_flicker_fix']:
        fixes.append('flicker')
    if report['needs_clahe']:
        fixes.append('clahe')

    if not fixes:
        print("Keine Korrektur nötig – Video wird nicht verändert.")
        return

    print(f"Wende an: {fixes}")

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if 'white_balance' in fixes:
            frame = correct_white_balance(frame)
        if 'flicker' in fixes:
            frame = correct_flicker(frame, report['brightness_mean'])
        if 'clahe' in fixes:
            frame = apply_clahe(frame)

        out.write(frame)
        frame_count += 1

        if frame_count % 500 == 0:
            print(f"  Fortschritt: {(frame_count/total_frames)*100:.1f}%")

    cap.release()
    out.release()
    print(f"Fertig! {frame_count} Frames → {output_path}")


def color_correction(input_path, output_path):
    report = analyze_video(input_path)
    print_report(report)
    process_video(input_path, output_path, report)