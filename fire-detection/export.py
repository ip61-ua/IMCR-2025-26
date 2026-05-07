from ultralytics import YOLO

model = YOLO("fire-and-smoke-industrial-10/best.pt")
model.export(format="onnx", imgsz=640)
