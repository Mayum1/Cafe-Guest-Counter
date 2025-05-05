import cv2
import os
import subprocess
from ultralytics import YOLO

model = YOLO('guests/model/best.pt')  # путь к предобученной модели YOLOv8

def count_people(image_path):
    results = model(image_path, save=False)[0]
    boxes = results.boxes
    names = model.names

    image = cv2.imread(image_path)
    person_count = 0

    for i in range(len(boxes.cls)):
        cls_id = int(boxes.cls[i])
        if cls_id == 0:  # только "person"
            person_count += 1
            box = boxes.xyxy[i].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            label = f"{names[cls_id]}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    os.makedirs('media/results', exist_ok=True)
    filename = os.path.basename(image_path)
    result_path = os.path.join('media/results', filename)
    cv2.imwrite(result_path, image)

    return person_count, str(result_path)


def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = int(cap.get(cv2.CAP_PROP_FPS))

    os.makedirs('media/results', exist_ok=True)

    # формируем имя выходного файла с _processed.mp4
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = base_name + '_processed.mp4'
    output_path = os.path.join('media/results', output_filename)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    max_persons = 0
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % 10 == 0:  # обрабатываем каждый 10-й кадр
            results = model(frame, save=False)[0]
            boxes = results.boxes
            names = model.names

            persons_on_frame = 0

            for i in range(len(boxes.cls)):
                cls_id = int(boxes.cls[i])
                if cls_id == 0:  # только "person"
                    persons_on_frame += 1
                    box = boxes.xyxy[i].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = box
                    label = f"{names[cls_id]}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            max_persons = max(max_persons, persons_on_frame)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    output_path = convert_to_h264(output_path)

    return max_persons, output_path

def process_rtsp(rtsp_url, frame_interval=10):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return 0, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(fps * frame_interval) if fps else 250  # default fallback

    frame_idx = 0
    person_count = 0
    saved_frame = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % delay == 0:
            results = model(frame, save=False)[0]
            boxes = results.boxes
            names = model.names

            person_count = 0
            for i in range(len(boxes.cls)):
                if int(boxes.cls[i]) == 0:
                    person_count += 1
                    box = boxes.xyxy[i].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = box
                    label = f"{names[0]}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            saved_frame = frame
            break  # берём только первый нужный кадр

        frame_idx += 1

    cap.release()

    if saved_frame is not None:
        os.makedirs('media/results', exist_ok=True)
        result_path = os.path.join('media/results', 'rtsp_snapshot.jpg')
        cv2.imwrite(result_path, saved_frame)
        return person_count, result_path

    return 0, None

def convert_to_h264(input_path):
    output_h264 = input_path.replace('.mp4', '_h264.mp4')
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-pix_fmt', 'yuv420p',
        '-threads', 'auto',
        output_h264
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_h264