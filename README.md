# 🚗 Hệ Thống Giám Sát Lái Xe Thông Minh (Driver Monitoring System - DMS)

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)
![AI-Powered](https://img.shields.io/badge/AI-YOLOv8%20|%20ArcFace-green.svg)
![UI](https://img.shields.io/badge/Framework-Flet%20(Flutter)-orange.svg)

## 📌 Giới thiệu Tổng quan
Hệ thống **Giám sát Lái xe (Driver Monitoring System)** là giải pháp ứng dụng Trí tuệ nhân tạo (AI) giúp nâng cao an toàn giao thông bằng cách theo dõi hành vi và trạng thái của người lái xe trong quãng thời gian thực. Hệ thống sử dụng các mô hình thị giác máy tính tiên tiến nhất để nhận diện danh tính và phát hiện các dấu hiệu mất tập trung, mệt mỏi hoặc các hành vi nguy hiểm khác.

Dự án được xây dựng với kiến trúc hiện đại, giao diện thân thiện và khả năng xử lý mượt mà, phù hợp để triển khai trên các thiết bị giám sát hành trình thế hệ mới.

---

## ✨ Tính năng Nổi bật

### 🔐 1. Đăng nhập Bảo mật Đa phương thức
*   **Face ID Login:** Sử dụng thuật toán **ArcFace (InsightFace)** để nhận diện khuôn mặt với độ chính xác cao ngay cả trong điều kiện ánh sáng yếu.
*   **Xác thực 2 lớp:** Kết hợp giữa Tên đăng nhập/Mật khẩu và nhận diện khuôn mặt để đảm bảo chỉ người lái xe được ủy quyền mới có thể vận hành hệ thống.
*   **Quản lý tài khoản:** Cho phép đăng ký nhân viên mới, lưu trữ vector đặc trưng (Embeddings) cục bộ giúp nhận diện Offline.

### 🎥 2. Giám sát Hành vi Thời gian thực (Live Monitoring)
*   **AI Detection (YOLOv8):** Tích hợp mô hình YOLOv8 được tinh chỉnh để nhận diện các trạng thái của người dùng.
*   **Phát hiện bất thường:** Hệ thống tự động phân tích khung hình để tìm kiếm các dấu hiệu như buồn ngủ (ngáp, nhắm mắt lâu), sử dụng điện thoại, hoặc không tập trung nhìn đường.
*   **Cảnh báo tức thời:** Hiển thị thông báo đỏ và ghi nhận trạng thái "Anomaly" ngay trên giao diện khi phát hiện hành vi nguy hiểm.

### 📊 3. Hỗ trợ và Điều khiển thông minh
*   **Trợ lý ảo (Chatbot):** Tích hợp Chatbot thông minh giúp giải đáp thắc mắc của người dùng về quy trình vận hành, xử lý lỗi kỹ thuật hoặc tra cứu nhanh lịch sử.
*   **Tùy chỉnh Thông báo:** Hệ thống cho phép người dùng sửa đổi nội dung, âm thanh và mức độ ưu tiên của các cảnh báo (Hệ thống sửa thông báo động).
*   **Quản trị và Báo cáo:** Giao diện Dashboard cho phép xem biểu đồ hành động, quản lý tài xế và xuất báo cáo PDF/Excel phục vụ quản lý nhân sự.

---

## 🏗️ Nghiệp vụ Hệ thống (Business Logic)

### 🔄 Luồng làm việc chính:
1.  **Giai đoạn Khởi động:**
    *   Hệ thống kiểm tra cấu hình phần cứng (Camera, GPU/CPU).
    *   Tải các mô hình AI (YOLO, ArcFace) vào bộ nhớ đệm (Pre-load) để tối ưu tốc độ.
2.  **Giai đoạn Xác thực:**
    *   Tài xế nhập thông tin hoặc sử dụng nhận diện khuôn mặt.
    *   Hệ thống so sánh đặc trưng khuôn mặt (Cosine Similarity) với cơ sở dữ liệu để cho phép truy cập.
3.  **Giai đoạn Giám sát:**
    *   Camera quét liên tục 30 FPS.
    *   Mô hình AI phân tích từng Frame để xác định vật thể và hành vi.
    *   Nếu có hành vi bất thường, hệ thống sẽ kích hoạt cờ `is_anomaly` và hiển thị cảnh báo.
4.  **Giai đoạn Kết thúc:**
    *   Lưu trữ dữ liệu phiên làm việc vào hệ thống logs.
    *   Giải phóng tài nguyên Camera và AI Model.

---

## 🛠️ Công nghệ Sử dụng

| Thành phần | Công nghệ / Thư viện |
| :--- | :--- |
| **Ngôn ngữ chính** | Python 3.9+ |
| **Giao diện người dùng (UI)** | Flet (Dựa trên nền tảng Flutter) |
| **Nhận diện vật thể** | YOLOv8 (Ultralytics) |
| **Nhận diện khuôn mặt** | ArcFace (InsightFace, ONNX Runtime) |
| **Xử lý hình ảnh** | OpenCV (Open Source Computer Vision Library) |
| **Quản lý dữ liệu** | JSON (Database-less architecture cho môi trường Edge) |

---

## 📂 Cấu trúc Thư mục Dự án
```text
giam_sat_lai_xe/
├── main.py                # File khởi chạy chính (Launcher)
├── requirements.txt       # Danh sách thư viện phụ thuộc
├── yolov8n.pt             # Trọng số mô hình AI Detection
├── models/                # Lưu trữ các file models AI (ONNX, PT)
├── src/
│   ├── bll/               # Business Logic Layer (Xử lý nghiệp vụ)
│   │   ├── ai_core/       # Code xử lý AI (Detection & Recognition)
│   │   └── ui_core/       # Logic điều khiển trạng thái UI
│   ├── ui/                # User Interface Layer (Giao diện)
│   │   ├── admin/         # Giao diện dành cho quản trị viên
│   │   ├── user/          # Giao diện dành cho tài xế
│   │   └── theme.py       # Cấu hình phong cách thiết kế (Theme)
│   ├── config_loader.py   # Quản lý cấu hình hệ thống
│   └── GUI/data/          # Chứa dữ liệu tĩnh (Ảnh, Account, Icons)
└── README.md              # Tài liệu hướng dẫn dự án
```

---

## 🚀 Hướng dẫn Cài đặt

1.  **Tải mã nguồn (Clone):**
    ```bash
    git clone https://github.com/quocthaihehe/giam_sat_lai_xe.git
    cd giam_sat_lai_xe
    ```

2.  **Khởi tạo môi trường ảo (Khuyến nghị):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Trên Linux/Mac
    .venv\Scripts\activate     # Trên Windows
    ```

3.  **Cài đặt thư viện:**
    ```bash
    pip install flet ultralytics insightface onnxruntime opencv-python numpy scikit-learn pycryptodome
    ```

4.  **Chạy ứng dụng:**
    ```bash
    python main.py
    ```

---

## 📝 Lưu ý cho Báo cáo
*   **Về AI:** Hệ thống có khả năng mở rộng để nhận diện thêm nhiều hành vi khác bằng cách huấn luyện bổ sung Model YOLO.
*   **Về Bảo mật:** Dữ liệu khuôn mặt được mã hóa và lưu trữ dưới dạng vector nhị phân, không lưu trữ ảnh gốc để đảm bảo quyền riêng tư.
*   **Về Hiệu năng:** Ứng dụng hỗ trợ tăng tốc phần cứng (CUDA/TensorRT) nếu thiết bị có GPU NVIDIA hỗ trợ.

---
**© 2026 Driver Monitoring System Project — Safe Drive, Smart Life.**
