# YOLOv8 Live Instance Segmentation

Run instance segmentation on a live camera feed using OpenCV and Ultralytics YOLOv8.
The default model is `yolov8m-seg.pt`; Ultralytics downloads it automatically the
first time it is run if it is not already available.

## Windows setup

Open PowerShell in this project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents environment activation, allow it for the current terminal
only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run

```powershell
python webcam_segmentation.py
```

Configure the confidence threshold, maximum detections per frame, camera index,
and segmentation model path with command-line options:

```powershell
python webcam_segmentation.py --threshold 0.4 --max-detections 5 --camera-index 0 --model yolov8m-seg.pt
```

Use a local segmentation model by supplying its path, for example:

```powershell
python webcam_segmentation.py --model "models\my-segmentation-model.pt"
```

Press `q` while the video window is focused to stop the camera. The model must
support segmentation; a detection-only weights file cannot produce instance masks.
