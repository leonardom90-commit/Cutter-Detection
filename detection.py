import cv2
from ultralytics import YOLO

DEFAULT_MODEL_PATH = "tuwek.pt"
DEFAULT_CONFIDENCE = 0.2
DEFAULT_MAX_DETECTIONS = 1
DEFAULT_CAMERA_INDEX = 1  # sesuaikan dengan hasil tes index kamera di PC kamu


class CutterDetection:
    """Mengurus model YOLO dan kamera. Tidak ada kode GUI di sini."""

    def __init__(
        self,
        model_path=DEFAULT_MODEL_PATH,
        confidence=DEFAULT_CONFIDENCE,
        max_detections=DEFAULT_MAX_DETECTIONS,
        camera_index=DEFAULT_CAMERA_INDEX,
    ):
        self.confidence = confidence
        self.max_detections = max_detections

        self.model = YOLO(model_path, task="detect")

        # cv2.CAP_DSHOW dipakai supaya lebih stabil dibanding backend MSMF
        # bawaan Windows yang sering gagal grabFrame terus-menerus.
        self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.camera.isOpened():
            self.camera.release()
            raise RuntimeError(
                f"Tidak bisa membuka kamera index {camera_index}. "
                "Cek koneksi kamera atau coba index lain."
            )

    def get_frame(self):
        """Baca 1 frame lalu deteksi.

        Return: (frame_beranotasi, nama_kelas, confidence)
          - frame None            -> kamera gagal membaca gambar
          - nama_kelas "WAITING"  -> tidak ada end mill terdeteksi
        Jika ada banyak deteksi, diambil yang confidence-nya tertinggi.
        """
        success, frame = self.camera.read()
        if not success:
            return None, "WAITING", 0.0

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            max_det=self.max_detections,
            verbose=False,
        )
        result = results[0]
        annotated = result.plot()

        if len(result.boxes) == 0:
            return annotated, "WAITING", 0.0

        best = max(result.boxes, key=lambda b: float(b.conf))
        class_name = result.names[int(best.cls)]
        return annotated, class_name, float(best.conf)

    def release(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None


# Tes mandiri tanpa GUI: python detection.py  (tekan q / Esc untuk keluar)
if __name__ == "__main__":
    det = CutterDetection()
    print("Kelas pada model:", det.model.names)
    try:
        while True:
            frame, name, conf = det.get_frame()
            if frame is None:
                break
            print(name, round(conf, 2))
            cv2.imshow("Test Detection", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
    finally:
        det.release()
        cv2.destroyAllWindows()
