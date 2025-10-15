import os
import cv2
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import winsound

# SMTP 설정 - 이메일 인증 정보는 환경 변수로 설정하는 것이 좋습니다.
sender_email = os.getenv('SENDER_EMAIL', 't92364155@pess.cnehs.kr')
sender_password = os.getenv('SENDER_PASSWORD', 'onetwo02015')
receiver_email = "sonb0318@pess.cnehs.kr"

def send_email_alert():
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "경고! 주변에 흉기를 소지한 사람이 있습니다! 경고!"
        body = "주변에 흉기를 소지한 사람이 돌아다니고 있음을 포착했습니다. 어서 그 자리에서 대피하시길 바랍니다. We have detected a person with a weapon in the area. Please evacuate the area immediately."
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("Email alert sent!")
    except Exception as e:
        print("Failed to send email:", e)

# 파일 경로 설정
config_file = "yolov4.cfg"
weights_file = "yolov4.weights"
names_file = "coco.names"
sound_file = "C:/Users/DGHS/Documents/beep-1.wav"  # 올바른 경로 설정

# YOLO 네트워크 로드
net = cv2.dnn.readNet(weights_file, config_file)

# GPU 가속 사용을 위한 설정
if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

layer_names = net.getLayerNames()
unconnected_out_layers = net.getUnconnectedOutLayers()

# 반환 값이 2D 배열일 경우 처리
if isinstance(unconnected_out_layers, np.ndarray):
    unconnected_out_layers = unconnected_out_layers.flatten()

# 출력 레이어 인덱스 처리
output_layers = [layer_names[i - 1] for i in unconnected_out_layers]

# 클래스 이름 로드
with open(names_file, "r") as f:
    classes = [line.strip() for line in f.readlines()]

# 흉기 클래스 리스트
weapon_classes = ['knife', 'scissors']

def process_frame(frame):
    height, width, channels = frame.shape

    # YOLO 네트워크를 위한 입력 데이터 생성 (프레임 리사이징)
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # 감지된 객체 정보를 처리
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # 흉기라고 간주할 수 있는 클래스들을 확인
            if confidence > 0.5 and classes[class_id] in weapon_classes:
                # 객체의 위치와 크기 계산
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # 사각형 좌표 계산
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    if len(indexes) > 0:
        indexes = indexes.flatten()
        for i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            confidence = confidences[i]
            color = (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{label} {confidence:.2f}", (x, y + 30), cv2.FONT_HERSHEY_PLAIN, 3, color, 3)
        return frame, True

    return frame, False

# 웹캠 열기
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame, detected = process_frame(frame)

    # 흉기가 감지되면 이메일 알림과 소리 알림을 보냅니다.
    if detected:
        send_email_alert()
        try:
            # 소리 재생
            if os.path.isfile(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME)  # 경고음 파일 재생
            else:
                print(f"Error: The file {sound_file} does not exist.")
        except Exception as e:
            print(f"Failed to play sound: {e}")

    # 화면에 프레임 표시
    cv2.imshow('Frame', frame)

    # 'q' 키를 눌러 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
