# Video kürzen (Clip erstellen)
import cv2

def cut_video_clip(input_path, output_path, start_sec, end_sec):
    """
    Schneidet einen Zeitbereich aus einem Video heraus.

    Args:
        input_path:  Pfad zum Original-Video
        output_path: Pfad für den gespeicherten Clip
        start_sec:   Startzeit in Sekunden
        end_sec:     Endzeit in Sekunden
    """
    cap = cv2.VideoCapture(input_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Start- und End-Frame berechnen
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)

    # VideoWriter erstellen (Ausgabeformat: MP4)
    fourcc = cv2.VideoWriter.fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Zum Start-Frame springen
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    current_frame = start_frame
    while current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        current_frame += 1

    cap.release()
    out.release()

    duration = end_sec - start_sec
    print(f"✅ Clip gespeichert: {output_path}")
    print(f"   Zeitraum: {start_sec}s – {end_sec}s ({duration}s)")
    print(f"   Frames:   {end_frame - start_frame}")