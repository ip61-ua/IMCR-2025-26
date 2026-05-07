from ultralytics import YOLO

model = YOLO("yolov8s.pt")
model.train(
    data="Fire-and-Smoke-Industrial-10/data.yaml",
    epochs=10,
    imgsz=640
)
