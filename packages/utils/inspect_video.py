import os
import cv2

def inspect_video(video_path):
    video_path = os.path.expanduser(video_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Fehler: Konnte Video nicht laden, überprüfe den Pfad.")
        cap.release()
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps else 0

    print(f"Video: {video_path}")
    print(f"FPS: {fps}")
    print(f"Total Frames: {total_frames}")
    print(f"Auflösung: {width} x {height} px")
    print(f"Dauer: {duration} Sekunden")

    cap.release()

    return {
        "video_path": video_path,
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration": duration,
    }