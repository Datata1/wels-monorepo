import cv2
import numpy as np

"""Spielfeld-Maskierung auf Basis von Linienerkennung.

Hauptidee:
1) Mehrere Linien-Detektionsmethoden pro Frame kombinieren (Voting).
2) Daraus eine stabile Spielfeldmaske ableiten.
3) Alles ausserhalb des Felds abdunkeln.

Typischer Aufruf:
    detector = CourtLineDetectorV3()
    stable_mask = detector.apply_field_mask_to_video("input.mp4", "masked.mp4")
"""


class CourtLineDetectorV3:
    """
    Mehrere Methoden zur Spielfeldlinien-Erkennung.
    Kann einzeln oder kombiniert verwendet werden.
    """

    def _run_line_methods(self, frame):
        """Führt alle Linien-Methoden aus und liefert die binären Masken."""
        mask_color = self.method_remove_color(frame)
        mask_color_adaptive, _, _ = self.method_remove_color_adaptive(frame)
        mask_tophat, _ = self.method_tophat(frame)
        mask_adaptive = self.method_adaptive_edges(frame)
        mask_channel, _ = self.method_channel_difference(frame)
        return {
            "color": mask_color,
            "color_adaptive": mask_color_adaptive,
            "tophat": mask_tophat,
            "adaptive": mask_adaptive,
            "channel": mask_channel,
        }

    def _vote_line_masks(self, masks):
        """Kombiniert Masken über ein einfaches Voting."""
        votes = (
            (masks["color"] > 0).astype(np.float32)
            + (masks["color_adaptive"] > 0).astype(np.float32)
            + (masks["tophat"] > 0).astype(np.float32)
            + (masks["adaptive"] > 0).astype(np.float32)
            + (masks["channel"] > 0).astype(np.float32)
        )

        combined = np.zeros_like(masks["color"])
        combined[votes >= 3] = 255
        return combined, votes

    def _cleanup_binary_mask(self, mask, kernel_size=(3, 3)):
        """Räumt eine binäre Maske mit Morphologie auf."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return mask

    def _build_field_mask_from_lines(self, combined_mask, shape):
        """Erzeugt aus Linienmasken eine gefüllte Spielfeld-Maske."""
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 40))
        filled = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, close_kernel)

        contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = shape[:2]
        field_mask = np.zeros((h, w), dtype=np.uint8)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(largest)
            cv2.drawContours(field_mask, [hull], -1, 255, thickness=cv2.FILLED)

        return field_mask

    def _apply_dim_mask(self, frame, field_mask, dim_factor):
        """Dunkelt alles außerhalb der Maske ab."""
        outside = (frame * dim_factor).astype(np.uint8)
        mask_3ch = cv2.merge([field_mask, field_mask, field_mask])
        return np.where(mask_3ch == 255, frame, outside)

    def _open_video_writer(self, input_path, output_path):
        """Öffnet Input/Output für die Videobearbeitung."""
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        return cap, out

    def method_remove_color(self, frame):
        """
        Entfernt alles was Farbe hat → übrig bleiben weiße Linien.

        Logik:
        - Weiß hat NIEDRIGE Sättigung (wenig Farbe)
        - Spielfeld, Trikots, Werbung haben HOHE Sättigung
        - Also: Niedrige Sättigung + Hohe Helligkeit = Linie
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Sättigung und Helligkeit
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]

        # Weiß = wenig Sättigung + hell
        # Je nach Halle die Werte anpassen
        white_mask = np.zeros_like(saturation)
        white_mask[(saturation < 70) & (value > 150)] = 255

        return white_mask

    def method_remove_color_adaptive(self, frame):
        """
        Verbesserte Version: Schwellwerte adaptiv bestimmen.
        Passt sich automatisch an die Hallenbeleuchtung an.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, w = frame.shape[:2]

        saturation = hsv[:, :, 1].astype(np.float32)
        value = hsv[:, :, 2].astype(np.float32)

        # Spielfeld-Boden als Referenz (Mitte des Bildes)
        floor_sat = saturation[int(h * 0.4) : int(h * 0.7), int(w * 0.3) : int(w * 0.7)]
        floor_val = value[int(h * 0.4) : int(h * 0.7), int(w * 0.3) : int(w * 0.7)]

        # Linien haben deutlich WENIGER Sättigung als der Boden
        floor_sat_median = np.median(floor_sat)
        floor_val_median = np.median(floor_val)

        # Schwellwerte relativ zum Boden berechnen
        sat_threshold = floor_sat_median * 0.4  # Linie hat < 40% der Boden-Sättigung
        val_threshold = floor_val_median * 0.9  # Linie ist mindestens 90% so hell wie Boden

        white_mask = np.zeros((h, w), dtype=np.uint8)
        white_mask[(saturation < sat_threshold) & (value > val_threshold)] = 255

        return white_mask, sat_threshold, val_threshold

    def method_tophat(self, frame):
        """
        Findet helle DÜNNE Strukturen auf gleichmäßigem Hintergrund.

        Perfekt für Linien auf dem Hallenboden!

        Wie es funktioniert:
        1. Morphologisches Opening entfernt dünne helle Strukturen
        2. Original - Opening = nur die dünnen Strukturen (= Linien)

        ┌──────────────────┐     ┌──────────────────┐
        │  ████████████    │     │                   │
        │  █ Boden ── █    │ →   │         ──        │  ← Nur die Linie!
        │  ████████████    │     │                   │
        └──────────────────┘     └──────────────────┘
        Original                  Top-Hat Ergebnis
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Kernel muss GRÖSSER sein als die Linienbreite
        # Spielfeldlinien sind typischerweise 5-15 Pixel breit
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

        # Automatischer Schwellwert (Otsu)
        _, binary = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary, tophat

    def method_adaptive_edges(self, frame):
        """
        Findet Kanten zwischen Boden und Linien.

        Vorteil: Funktioniert auch wenn Linien nicht perfekt weiß sind,
        solange sie sich VOM BODEN UNTERSCHEIDEN.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Gaussian Blur um Rauschen zu reduzieren
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive Schwellwertbildung
        # Vergleicht jeden Pixel mit seiner lokalen Umgebung
        adaptive = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=51,  # Nachbarschaftsgröße
            C=-12,  # Nur deutlich hellere Pixel als Umgebung
        )

        return adaptive

    def method_channel_difference(self, frame):
        """
        Nutzt die Eigenschaft, dass weiße Pixel in ALLEN Kanälen
        gleich hell sind, während farbige Pixel Unterschiede haben.

        Weißer Pixel:  R=200, G=200, B=200  → Differenz = 0
        Blauer Boden:  R=80,  G=100, B=180  → Differenz = 100
        Roter Trikot:  R=200, G=50,  B=50   → Differenz = 150
        """
        b, g, r = cv2.split(frame.astype(np.float32))

        # Maximale Differenz zwischen den Kanälen
        max_channel = np.maximum(np.maximum(r, g), b)
        min_channel = np.minimum(np.minimum(r, g), b)
        channel_diff = max_channel - min_channel

        # Durchschnittliche Helligkeit
        avg_brightness = (r + g + b) / 3

        # Weiß = Geringe Kanal-Differenz + Hohe Helligkeit
        white_mask = np.zeros_like(channel_diff, dtype=np.uint8)
        white_mask[(channel_diff < 40) & (avg_brightness > 150)] = 255

        return white_mask, channel_diff

    def method_combined(self, frame):
        """
        Kombiniert alle Methoden mit einem Voting-System.

        Eine Linie wird nur akzeptiert wenn MEHRERE Methoden
        sie erkennen → sehr wenig Falsch-Positive.

        Aufruf:
            combined_mask, votes = detector.method_combined(frame)
        """
        masks = self._run_line_methods(frame)
        combined, votes = self._vote_line_masks(masks)
        combined = self._cleanup_binary_mask(combined, kernel_size=(3, 3))

        return combined, votes

    def extract_lines(self, binary_mask):
        """Extrahiert Hough-Linien aus einer binären Maske."""
        lines = cv2.HoughLinesP(
            binary_mask, rho=1, theta=np.pi / 180, threshold=50, minLineLength=40, maxLineGap=25
        )
        return lines

    def classify_and_merge(self, lines, merge_distance=25):
        """Klassifiziert und fasst Linien zusammen."""
        if lines is None:
            return {"horizontal": [], "vertical": [], "other": []}

        horizontal = []
        vertical = []
        other = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            info = {
                "points": (x1, y1, x2, y2),
                "angle": angle,
                "length": length,
                "midpoint": ((x1 + x2) / 2, (y1 + y2) / 2),
            }

            if abs(angle) < 30:
                horizontal.append(info)
            elif abs(angle) > 60:
                vertical.append(info)
            else:
                other.append(info)

        horizontal = self._merge_nearby(horizontal, "y", merge_distance)
        vertical = self._merge_nearby(vertical, "x", merge_distance)

        return {"horizontal": horizontal, "vertical": vertical, "other": other}

    def _merge_nearby(self, lines, axis, threshold):
        """Fasst nahe Linien zusammen."""
        if not lines:
            return []

        idx = 1 if axis == "y" else 0
        lines.sort(key=lambda line_item: line_item["midpoint"][idx])

        groups = [[lines[0]]]
        for line in lines[1:]:
            if abs(line["midpoint"][idx] - groups[-1][-1]["midpoint"][idx]) < threshold:
                groups[-1].append(line)
            else:
                groups.append([line])

        merged = []
        for group in groups:
            x1 = int(min(line_item["points"][0] for line_item in group))
            y1 = int(np.mean([line_item["points"][1] for line_item in group]))
            x2 = int(max(line_item["points"][2] for line_item in group))
            y2 = int(np.mean([line_item["points"][3] for line_item in group]))
            merged.append(
                {
                    "points": (x1, y1, x2, y2),
                    "angle": np.mean([line_item["angle"] for line_item in group]),
                    "length": np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2),
                    "midpoint": ((x1 + x2) / 2, (y1 + y2) / 2),
                    "count": len(group),
                }
            )

        return merged

    def mask_field(self, frame, dim_factor=0.15):
        """
        Erkennt das Spielfeld und gibt eine abgedunkelte Version zurück.
        Alles außerhalb des Spielfelds wird auf dim_factor * Originalwert abgedunkelt.

        Ablauf:
        1. method_combined() → Linien-Pixel-Maske
        2. Morphologisches Schließen → Lücken füllen
        3. Größte zusammenhängende Fläche → Spielfeld-Kontur
        4. Konvexe Hülle → robuste Spielfeld-Grenze
        5. Alles außerhalb abdunkeln

        Args:
            frame:      BGR-Frame
            dim_factor: Helligkeit außerhalb (0.0 = schwarz, 1.0 = original)

        Returns:
            (masked_frame, field_mask): abgedunkelter Frame + binäre Maske

        Aufruf:
            detector = CourtLineDetectorV3()
            masked_frame, field_mask = detector.mask_field(frame, dim_factor=0.2)
        """
        combined_mask, _ = self.method_combined(frame)
        field_mask = self._build_field_mask_from_lines(combined_mask, frame.shape)
        masked_frame = self._apply_dim_mask(frame, field_mask, dim_factor)

        return masked_frame, field_mask

    def get_stable_field_mask(self, input_path, num_samples=30):
        """
        Schätzt eine stabile Spielfeld-Maske über mehrere Frames.
        Verhindert Flackern der Maske durch Spielerbewegung.

        Args:
            input_path:  Pfad zum Video
            num_samples: Anzahl der Stichproben

        Returns:
            stable_mask: Akkumulierte, stabile binäre Maske (uint8, 0/255)

        Aufruf:
            detector = CourtLineDetectorV3()
            stable_mask = detector.get_stable_field_mask("input.mp4", num_samples=40)
        """
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sample_interval = max(1, total_frames // num_samples)

        accumulated = np.zeros((height, width), dtype=np.float32)
        count = 0
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_interval == 0:
                _, mask = self.mask_field(frame)
                accumulated += mask.astype(np.float32)
                count += 1

            frame_count += 1

        cap.release()

        if count == 0:
            return np.full((height, width), 255, dtype=np.uint8)

        stable_mask = np.where(accumulated / count >= 0.5, 255, 0).astype(np.uint8)
        stable_mask = self._cleanup_binary_mask(stable_mask, kernel_size=(20, 20))

        return stable_mask

    def apply_field_mask_to_video(self, input_path, output_path, dim_factor=0.15, num_samples=30):
        """
        Dunkelt alles außerhalb des Spielfelds ab und schreibt das Video.

        Ablauf:
        1. Stabile Maske aus Stichproben berechnen (get_stable_field_mask)
        2. Optional: Maske auf 3 Frames visualisieren
        3. Video Frame-für-Frame mit stabiler Maske maskieren

        Args:
            input_path:  Pfad zum Input-Video
            output_path: Pfad zum Output-Video
            dim_factor:  Helligkeit außerhalb des Spielfelds (0.0 - 1.0)
            num_samples: Anzahl Stichproben für stabile Maske
            preview:     Vorschau auf 3 Frames anzeigen (cv2.imshow)

        Returns:
            stable_mask: Die fuer alle Frames verwendete stabile Spielfeldmaske.

        Aufruf:
            detector = CourtLineDetectorV3()
            stable_mask = detector.apply_field_mask_to_video(
                "input.mp4",
                "masked.mp4",
                dim_factor=0.15,
                num_samples=30,
            )
        """
        stable_mask = self.get_stable_field_mask(input_path, num_samples=num_samples)
        cap, out = self._open_video_writer(input_path, output_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            masked = self._apply_dim_mask(frame, stable_mask, dim_factor)
            out.write(masked)

        cap.release()
        out.release()

        return stable_mask
