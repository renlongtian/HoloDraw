# HoloDraw ✋🎨

**实时手势识别空中画板** — 用手指在空中书写、绘画，体验赛博朋克风格的量子全息交互终端。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-SocketIO-green?logo=flask)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 演示效果

> 启动后打开浏览器，对着摄像头伸出手即可体验空中书写和 3D 星云球操控。

## 功能特性

### 🖊️ 模式 A — 空中写字
- **右手捏合**（拇指 + 食指）即可在空中书写/绘画
- 支持 **12 页 × 3 行** 虚拟画布，左手拖动平移视口
- 5 种霓虹色可选（左手张开悬停唤出工具盘）
- 1-Euro Filter 双端平滑（后端关键点 + 前端笔迹），书写丝滑无抖动

### 🔮 模式 B — 量子星云球
- Three.js 粒子球体，双手控制旋转和形态
- 手部张合影响粒子扩散效果

### 🎛️ 交互手势一览

| 手势 | 功能 |
|------|------|
| 右手捏合 | 画笔落下 / 确认选色 |
| 右手松开 | 画笔抬起 |
| 左手移动 | 拖动画布平移 |
| 左手张开静止 600ms | 唤出颜色工具盘 |
| 右手食指悬停 + 捏合 | 在工具盘中选色 |

### 🎨 UI 设计
- 深色赛博朋克风格「量子终端」界面
- 实时摄像头画面作为半透明背景
- 扫描线 + 粒子星空 + 网格动效
- HUD 骨骼连线实时可视化
- 可折叠侧边栏（状态面板 + 快捷操作）

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   Browser (前端)                      │
│  Canvas × 4 层: 背景 / WebGL(Three.js) / 绘画 / HUD │
│  WebSocket 接收关键点 → 手势判定 → 绘制/交互        │
└─────────────────────┬───────────────────────────────┘
                      │ WebSocket (Socket.IO)
                      │ + MJPEG video stream
┌─────────────────────▼───────────────────────────────┐
│                Python 后端 (Flask)                    │
│  OpenCV 摄像头采集 → MediaPipe HandLandmarker        │
│  21 关键点 × 2 手 → 1-Euro Filter 平滑 → 推送      │
└─────────────────────────────────────────────────────┘
```

**关键技术点：**
- **MediaPipe HandLandmarker** — 每只手 21 个 3D 关键点，VIDEO 模式逐帧检测
- **1-Euro Filter** — 自适应低通滤波，静止时超平滑、快速移动时零延迟
- **双端滤波** — 后端平滑原始关键点，前端平滑笔尖轨迹（消除微颤）
- **MJPEG 视频流** — `/video_feed` 端点，实时摄像头画面传输到前端作为背景
- **WebSocket 实时通信** — Flask-SocketIO 推送手部数据，~30fps

## 快速开始

### 环境要求

- Python 3.10+
- 摄像头（内置或外接 USB）
- 现代浏览器（Chrome / Edge / Firefox）

### 安装

```bash
# 克隆仓库
git clone https://github.com/renlongtian/HoloDraw.git
cd HoloDraw

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python app.py
```

启动后访问 **http://127.0.0.1:5001**，对着摄像头伸出手即可开始体验。

## 项目结构

```
HoloDraw/
├── app.py                  # Flask 主程序（摄像头采集 + MediaPipe + WebSocket）
├── hand_landmarker.task    # MediaPipe 手部检测模型文件
├── requirements.txt        # Python 依赖
├── templates/
│   └── index.html          # 前端单页应用（Canvas + Three.js + Socket.IO）
└── README.md
```

## 配置参数

### 后端 (app.py)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 摄像头分辨率 | 1280×720 | `cap.set(CAP_PROP_FRAME_WIDTH/HEIGHT)` |
| 检测帧率 | ~30fps | `time.sleep(0.025)` 控制 |
| 最大检测手数 | 2 | `num_hands=2` |
| 检测置信度 | 0.6 | `min_hand_detection_confidence` |
| 滤波参数 | min_cutoff=1.7, beta=0.01 | 1-Euro Filter |

### 前端 (index.html)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| PINCH_THRESHOLD | 0.055 | 捏合判定距离阈值 |
| VIRTUAL_PAGES | 12 | 虚拟画布列数 |
| VIRTUAL_ROWS | 3 | 虚拟画布行数 |
| TOOL_HOLD_MS | 600 | 工具盘唤出静止时间(ms) |
| PAN_GAIN | 1.35 | 画布平移灵敏度 |

## 依赖

```
flask
flask-socketio
eventlet
mediapipe
opencv-python
numpy
```

## 浏览器兼容性

| 浏览器 | 支持 |
|--------|------|
| Chrome 90+ | ✅ |
| Edge 90+ | ✅ |
| Firefox 85+ | ✅ |
| Safari 15+ | ⚠️ 需测试 |

## License

MIT License
