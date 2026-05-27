"""
手势画板 - Python 后端
架构：Python (摄像头 + MediaPipe HandLandmarker) → WebSocket → 前端纯渲染
"""
import os
import cv2
import json
import time
import threading
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)
from flask import Flask, render_template, Response
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 模型路径
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

# 全局状态
running = False
cap = None
latest_frame = None
frame_lock = threading.Lock()
start_lock = threading.Lock()


def create_landmarker():
    """创建手部检测器"""
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    return HandLandmarker.create_from_options(options)


class OneEuroFilter:
    """1-Euro Filter - 自适应低通滤波，静止时平滑、快速移动时响应"""
    def __init__(self, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        if self.t_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t
            return x
        dt = t - self.t_prev
        if dt <= 0:
            dt = 1/30
        # derivative
        a_d = self._alpha(self.d_cutoff, dt)
        dx = (x - self.x_prev) / dt
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        # adaptive cutoff
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self.x_prev
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat


# 每只手21个关键点，每个3轴 → 最多2手
filters = [[None]*21 for _ in range(2)]  # filters[hand_idx][landmark_idx] = (fx, fy, fz)


def get_or_create_filter(hand_idx, lm_idx):
    if filters[hand_idx][lm_idx] is None:
        filters[hand_idx][lm_idx] = (
            OneEuroFilter(min_cutoff=1.7, beta=0.01),
            OneEuroFilter(min_cutoff=1.7, beta=0.01),
            OneEuroFilter(min_cutoff=1.7, beta=0.01),
        )
    return filters[hand_idx][lm_idx]


def smooth_landmarks(landmarks, hand_idx, t):
    """使用1-Euro滤波器平滑关键点"""
    smoothed = []
    for li, lm in enumerate(landmarks):
        fx, fy, fz = get_or_create_filter(hand_idx, li)
        smoothed.append({
            'x': fx(lm['x'], t),
            'y': fy(lm['y'], t),
            'z': fz(lm['z'], t),
        })
    return smoothed


def detection_loop():
    """后台检测循环"""
    global running, cap, latest_frame
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[错误] 无法打开摄像头")
        running = False
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    landmarker = create_landmarker()
    ts = 0
    frame_time = 0.0
    
    print("[启动] 摄像头检测循环开始")
    
    while running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        
        # 镜像翻转
        frame = cv2.flip(frame, 1)
        
        # 保存最新帧用于视频流
        with frame_lock:
            latest_frame = frame.copy()
        
        # MediaPipe 检测
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts += 33
        result = landmarker.detect_for_video(mp_image, ts)
        
        # 组装数据
        frame_time = time.time()
        hands_data = []
        if result.hand_landmarks:
            for i, hand_lms in enumerate(result.hand_landmarks):
                if i >= 2:
                    break
                # 提取21个关键点
                points = [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand_lms]
                
                # 1-Euro滤波平滑
                smoothed = smooth_landmarks(points, i, frame_time)
                
                # 手性判断
                handedness = 'Unknown'
                if result.handedness and i < len(result.handedness):
                    handedness = result.handedness[i][0].category_name
                
                hands_data.append({
                    'landmarks': smoothed,
                    'handedness': handedness,
                })
        else:
            # 无手时重置滤波器
            for hi in range(2):
                filters[hi] = [None]*21
        
        # 通过 WebSocket 推送
        socketio.emit('hands', json.dumps(hands_data))
        
        # 控制帧率 ~30fps
        time.sleep(0.025)
    
    cap.release()
    print("[停止] 摄像头检测循环结束")


def start_detection_loop():
    """确保摄像头检测线程已启动"""
    global running
    with start_lock:
        if running:
            return
        running = True
        t = threading.Thread(target=detection_loop, daemon=True)
        t.start()


@app.route('/')
def index():
    return render_template('index.html')


def gen_video():
    """MJPEG视频流生成器"""
    while True:
        with frame_lock:
            f = latest_frame
        if f is None:
            time.sleep(0.03)
            continue
        _, buf = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        time.sleep(0.033)


@app.route('/video_feed')
def video_feed():
    start_detection_loop()
    return Response(gen_video(), mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('connect')
def on_connect():
    print("[WebSocket] 客户端连接")
    start_detection_loop()


@socketio.on('disconnect')
def on_disconnect():
    global running
    print("[WebSocket] 客户端断开")
    # 暂不停止，保持运行


@socketio.on('stop')
def on_stop():
    global running
    running = False


if __name__ == '__main__':
    print("=" * 50)
    print("  手势画板 - 服务启动")
    print("  打开浏览器访问: http://127.0.0.1:5001")
    print("=" * 50)
    start_detection_loop()
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
