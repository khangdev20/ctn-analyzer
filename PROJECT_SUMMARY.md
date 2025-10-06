# Project Summary – Trending Intelligence System

_Cập nhật ngày: 2025-10-06_

## 1. Tổng quan hiện tại

Hệ thống là một nền tảng phân tích "trending intelligence" lấy dữ liệu mạng xã hội (API `social.legitreal.com`), xử lý nhiều giai đoạn (collect → clean → score → multi-LLM analysis → format Discord) và gửi thông báo qua Discord Webhook. Nền tảng chạy dưới dạng Flask API + một `BackgroundWorker` bất đồng bộ trong thread riêng.

Trong các phiên làm việc gần đây, vấn đề lớn nhất là **scheduler (APScheduler) không thực thi bất kỳ job nào** dù đã thêm nhiều lớp fallback. Kết quả: tác vụ chính không chạy tự động, heartbeat không tăng. Giải pháp đã triển khai: **loại bỏ APScheduler và thay bằng custom lightweight async scheduler** chạy trực tiếp trên event loop của worker.

## 2. Kiến trúc kỹ thuật rút gọn

```
Flask (REST) ──▶ BackgroundWorker Thread (asyncio loop)
                        │
                        ├─ Custom Scheduler Loop (tick mỗi 1s)
                        │    ├─ trending_intelligence (90s debug / dự kiến 300–900s prod)
                        │    ├─ heartbeat (60s)
                        │    └─ maintenance_cleanup (30 phút)
                        │
                        └─ Intelligence Pipeline (multi-stage + LLM + Discord)
```

## 3. Thành phần chính

| Thành phần                                        | Mô tả                                       | Trạng thái                                          |
| ------------------------------------------------- | ------------------------------------------- | --------------------------------------------------- |
| `BackgroundWorker`                                | Quản lý loop async, vòng đời, bọc task      | Ổn định                                             |
| Custom Scheduler (`worker/scheduler.py`)          | Thay thế APScheduler, tick 1s, quản lý lịch | Mới, hoạt động đơn giản                             |
| Trending Intelligence Pipeline                    | Nhiều stage + timeout + cleanup             | Chạy khi trigger tay / sẽ chạy tự động sau refactor |
| Heartbeat Task                                    | Tăng `heartbeat_count`, theo dõi sống       | Hoạt động qua scheduler mới (dự kiến)               |
| Discord Notifier                                  | Gửi embed / text Webhook                    | Phụ thuộc pipeline chạy thành công                  |
| Cleanup & Force Cancel                            | Hủy task kẹt + dọn active_tasks             | Có, cần quan sát thêm                               |
| Manual Trigger Endpoint (`/trigger-intelligence`) | Chạy tay pipeline                           | Hoạt động                                           |
| Monitoring Endpoints (`/status`, `/heartbeat`)    | Báo số liệu runtime                         | Có nhưng thiếu enriched metrics                     |

## 4. Những hạng mục đã hoàn thành ✅

- Thay thế hoàn toàn APScheduler bằng custom scheduler nội bộ.
- Thêm bảo vệ chống chạy chồng trending nếu lần trước chưa xong.
- Giữ nguyên wrapper `_run_trending_intelligence_task_with_cleanup()` với logging chi tiết + timeout.
- Heartbeat logic giữ nguyên, đã được đưa vào lịch mới (delay khởi tạo 10s).
- Cơ chế cleanup định kỳ (`maintenance_cleanup`) vẫn tồn tại trong lịch (interval 30 phút).
- Logging chi tiết cho start / done từng task, state tick mỗi 15s.
- Giảm độ phức tạp (loại bỏ fallback injections, date jobs, listener events cũ).

## 5. Những hạng mục chưa hoàn thành / còn tồn tại ⚠️

| Mục                                             | Trạng thái                         | Ghi chú                                         |
| ----------------------------------------------- | ---------------------------------- | ----------------------------------------------- |
| Xác nhận thực thi tự động sau refactor          | Chưa kiểm chứng runtime cuối       | Cần chạy thực tế ≥ 2 chu kỳ (≥ 100s)            |
| Đồng bộ hóa metrics nâng cao (`/status`)        | Thiếu next_run, last_run từng task | Có thể bổ sung dễ dàng                          |
| Loại bỏ `apscheduler` khỏi `requirements.txt`   | Chưa làm                           | Đợi xác nhận không còn nhu cầu fallback         |
| Thêm test tự động (unit / smoke)                | Chưa có                            | Cần bộ test cho scheduler + pipeline stub       |
| Giảm verbosity logging (production profile)     | Chưa                               | Hiện log khá nhiều ký tự emoji / banner         |
| Backoff khi pipeline lỗi liên tiếp              | Chưa                               | Tránh spam Discord / API khi lỗi chu kỳ         |
| Circuit breaker cho API trending nguồn          | Chưa                               | API hay 503, cần tái thử có kiểm soát           |
| Cache / dedupe batch IDs                        | Một phần                           | Kiểm tra tránh phân tích trùng dữ liệu gần nhau |
| Observability nâng cao (latency, stage timings) | Chưa                               | Có thể gắn vào `result` và /metrics sau         |
| Kiểm soát kích thước log file (“log rotation”)  | Chưa                               | `bot.log` có thể phình to                       |
| Kiểm tra memory leak / zombie tasks             | Chưa đo                            | Nên thêm thống kê `len(asyncio.all_tasks())`    |

## 6. Rủi ro & Nguyên nhân gốc

| Rủi ro                              | Mô tả                                             | Ảnh hưởng                            |
| ----------------------------------- | ------------------------------------------------- | ------------------------------------ |
| Scheduler cũ không kích hoạt        | APScheduler chạy ở thread khác loop không chia sẻ | Mất toàn bộ thực thi định kỳ         |
| Over-logging                        | Log khối lượng lớn → khó lọc sự cố                | Giảm khả năng giám sát               |
| Không có test                       | Mỗi refactor mang rủi ro hồi quy                  | Giảm tốc độ triển khai               |
| Phụ thuộc API không ổn định         | API 503 nhiều                                     | Khoảng trống dữ liệu / phân tích sai |
| Không có backoff / retry chiến lược | Task lỗi lặp nhanh                                | Tăng lỗi hệ thống / tốn chi phí LLM  |

## 7. Gốc vấn đề ban đầu (Root Cause)

1. APScheduler được khởi tạo nhưng job callback gọi coroutine không đúng event loop.
2. Thread chứa scheduler không sở hữu loop chạy real tasks → `call_soon_threadsafe` không được dùng ngay từ đầu.
3. Sau nhiều lớp fallback, bản chất luồng / loop mismatch vẫn không giải quyết triệt để.
4. Độ phức tạp tăng khiến khó xác nhận đường thực thi nào còn sống.
   → Giải pháp dứt điểm: Bỏ APScheduler, gom toàn bộ vào một vòng `while is_running: sleep(1)` kiểm soát explícit.

## 8. Lộ trình đề xuất (Roadmap Ưu tiên)

| Ưu tiên | Công việc                                                           | Thời gian ước tính | Ghi chú                                 |
| ------- | ------------------------------------------------------------------- | ------------------ | --------------------------------------- |
| P1      | Xác nhận scheduler mới chạy đủ 2–3 chu kỳ (log + endpoint)          | 0.5h               | Kiểm tra heartbeat & trending xuất hiện |
| P1      | Bổ sung `last_run`, `next_run`, `run_count` từng task vào `/status` | 0.5h               | Đọc từ cấu trúc scheduler               |
| P1      | Điều chỉnh interval sản xuất (trending 300–900s)                    | 0.1h               | Env flag hoặc config JSON               |
| P1      | Loại bỏ `apscheduler` khỏi deps + cleanup code dead comment         | 0.2h               | Giảm footprint                          |
| P2      | Thêm retry/backoff linear + max_failures → skip tạm                 | 1h                 | Bảo vệ API & LLM                        |
| P2      | Thêm test đơn giản: fake worker + mock task                         | 2h                 | Pytest                                  |
| P2      | Thêm metrics JSON `/metrics` (success_rate, avg_duration)           | 1h                 | Dễ trực quan                            |
| P3      | Log stage timing chi tiết pipeline                                  | 1h                 | Bọc instrumentation                     |
| P3      | Circuit breaker API nguồn (mở lại sau cooldown)                     | 1.5h               | Giảm spam 503                           |
| P3      | Log rotation (logging.handlers.RotatingFileHandler)                 | 0.5h               | Bảo trì                                 |
| P4      | Tối ưu chi phí LLM: cache prompt / few-shot reuse                   | 2–3h               | Khi ổn định mới làm                     |

## 9. Đề xuất cải tiến kỹ thuật nhanh

- Tách config scheduler (intervals) vào `config.json` hoặc `trending_config.py` để đổi nhanh.
- Thêm `TaskRegistry` object chứa metadata → dễ serialize ra API.
- Dùng `monotonic()` thay `datetime` cho drift chính xác hơn trong scheduler (hiện vẫn ổn vì độ lớn interval không quá nhỏ).
- Thêm guard: nếu thời gian thực thi > 70% interval → ghi cảnh báo “có nguy cơ trễ chu kỳ”.
- Gom các banner log lớn về 1 dòng compact khi vào production.

## 10. Giám sát đề xuất

| Chỉ số                   | Mô tả                         | Ngưỡng cảnh báo   |
| ------------------------ | ----------------------------- | ----------------- |
| trending_run_count / giờ | Số lần chạy pipeline          | < 2 (prod)        |
| heartbeat_lag_seconds    | now - last_heartbeat          | > 130s            |
| avg_trending_duration    | Thời gian trung bình pipeline | > 60% interval    |
| api_trending_fail_rate   | Tỷ lệ lỗi gọi nguồn           | > 30% 10 phút     |
| llm_call_fail_rate       | Tỷ lệ lỗi LLM                 | > 10%             |
| consecutive_failures     | Chuỗi thất bại liên tục       | ≥ 3 reset/backoff |

## 11. Công việc ngay lập tức khuyến nghị (Actionable Next)

1. Khởi chạy hệ thống và theo dõi log 2 phút để xác nhận: heartbeat + ít nhất 1 lần trending.
2. Nếu OK → chỉnh interval trending về 300s (5 phút) cho giai đoạn semi-prod.
3. Thêm exposed scheduler task meta vào `/status`.
4. Xóa `apscheduler` khỏi `requirements.txt` (sau khi confirm không rollback).
5. Viết 1 test tối thiểu: giả lập worker + chờ 6s xem trending đã gọi (giảm interval tạm trong test).

## 12. Ghi chú triển khai

- Khi thay đổi interval: tránh restart nhiều lần trong <30s để không “reset đồng hồ” liên tục.
- Discord rate limit: nếu thêm backoff cần tránh gửi spam lỗi liên tiếp (gom lỗi thành 1 summary embed sau N lần thất bại).
- API nguồn hay 503: cân nhắc thêm local mock data fallback tự động (đã có script manual, có thể tự động hóa: nếu 503 > 2 lần → dùng mock + flag).

## 13. Phụ lục – Thay đổi gần nhất quan trọng

| File                  | Thay đổi                                 | Ảnh hưởng                  |
| --------------------- | ---------------------------------------- | -------------------------- |
| `worker/scheduler.py` | Rewrite bỏ APScheduler, thêm custom loop | Khôi phục thực thi định kỳ |
| `worker/base.py`      | Không đổi logic chính (tương thích)      | An toàn                    |

---

_Đây là bản tổng hợp phục vụ theo dõi tiến độ và ra quyết định tiếp theo. Có thể cập nhật định kỳ (mỗi lần refactor lớn hoặc milestone)._
