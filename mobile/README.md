# HoloDraw Mobile

**纯前端手势画板** — 无需 Python 后端，手机/平板直接打开网页即可使用。

基于 [MediaPipe Hands (JS)](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker/web_js) 在浏览器端实时检测手部关键点。

## 与桌面版的区别

| | 桌面版 (gesture-canvas) | 手机版 (gesture-canvas-mobile) |
|--|--|--|
| 架构 | Python后端 + WebSocket | **纯前端，零后端** |
| 检测 | Python MediaPipe | **浏览器 MediaPipe JS + WebGPU** |
| 部署 | 需要 Python 环境 | **静态文件，任何 HTTP 服务器** |
| 帧率 | ~30fps (受限于后端) | **30-60fps (GPU加速)** |
| 移动端 | ❌ 不支持 | ✅ 完整适配 |

## 快速开始

### 方式一：本地双击打开
直接用浏览器打开 `index.html`（需要允许摄像头权限）。

> ⚠️ 部分浏览器限制本地文件访问摄像头，建议用方式二。

### 方式二：本地 HTTP 服务
```bash
# Python
python -m http.server 8000

# Node.js
npx serve .
```
然后访问 `http://localhost:8000`

### 方式三：手机访问
确保手机和电脑在同一局域网：
```bash
python -m http.server 8000 --bind 0.0.0.0
```
手机浏览器访问 `http://<电脑IP>:8000`

> ⚠️ 手机浏览器需要 HTTPS 才能访问摄像头。可使用 ngrok 或部署到有 HTTPS 的服务器。

## 手势操作

| 手势 | 功能 |
|------|------|
| 右手捏合（拇指+食指） | 画笔落下，空中书写 |
| 右手松开 | 画笔抬起 |
| 左手移动 | 拖动画布翻页 |

## UI 功能

- 🗑️ 清除画布
- ↩️ 撤销上一笔
- 📄 快速翻页（共 6 页虚拟画布）
- 📷 切换前置/后置摄像头
- 5 种霓虹色切换

## 技术栈

- MediaPipe Hand Landmarker (JS, GPU delegate)
- 纯 Canvas 2D 渲染
- 1-Euro Filter 笔迹平滑
- Tailwind CSS (CDN)
- 零依赖，单文件部署

## 浏览器要求

- Chrome 90+ / Edge 90+ / Safari 16.4+
- 需要摄像头权限
- 需要 HTTPS（手机端）

## License

MIT
