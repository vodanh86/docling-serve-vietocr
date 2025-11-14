# VietOCR Configuration

VietOCR là OCR engine chuyên biệt cho tiếng Việt, được tích hợp vào Docling Serve với nhiều tham số để tối ưu chất lượng nhận dạng.

## Các Models có sẵn

VietOCR hỗ trợ 4 models:

1. **vgg_transformer** (khuyến nghị) - Chất lượng tốt nhất
2. **vgg_seq2seq** - Cân bằng giữa tốc độ và chất lượng
3. **resnet_transformer** - Nhanh hơn nhưng ít chính xác hơn
4. **resnet_seq2seq** - Nhanh nhất

## Tham số cấu hình

### Cơ bản

```json
{
  "ocr_engine": "vietocr",
  "ocr_lang": ["vi"]
}
```

### Tăng chất lượng với Beam Search

```json
{
  "ocr_engine": "vietocr",
  "ocr_options": {
    "config_name": "vgg_transformer",
    "beamsearch": true,
    "device": "cpu"
  }
}
```

**Lưu ý**: 
- `beamsearch: true` tăng độ chính xác nhưng chậm hơn ~2-3 lần
- Nên dùng cho văn bản quan trọng cần độ chính xác cao

### Tối ưu hình ảnh kém chất lượng

Với PDF scan kém chất lượng, mờ, hoặc độ tương phản thấp:

```json
{
  "ocr_engine": "vietocr",
  "ocr_options": {
    "config_name": "vgg_transformer",
    "contrast": 1.5,
    "brightness": 1.2,
    "sharpness": 1.3
  }
}
```

**Giải thích**:
- `contrast`: Tăng độ tương phản (1.0-2.0, mặc định 1.0)
- `brightness`: Điều chỉnh độ sáng (0.5-1.5, mặc định 1.0)
- `sharpness`: Tăng độ sắc nét (1.0-2.0, mặc định 1.0)

### GPU Acceleration

Nếu có GPU NVIDIA:

```json
{
  "ocr_engine": "vietocr",
  "ocr_options": {
    "config_name": "vgg_transformer",
    "device": "cuda",
    "batch_size": 16
  }
}
```

**Lợi ích**:
- Tăng tốc độ xử lý 5-10 lần
- `batch_size` cao hơn cho nhiều trang

## Ví dụ Python

```python
import httpx

# Cấu hình cho chất lượng tối đa
payload = {
    "sources": [{"kind": "http", "url": "https://example.com/vietnamese-doc.pdf"}],
    "options": {
        "ocr_engine": "vietocr",
        "ocr_lang": ["vi"],
        "do_ocr": True,
        "force_ocr": True,  # Bắt buộc OCR ngay cả khi có text layer
    }
}

# Gửi request
response = httpx.post("http://localhost:5001/v1/convert/source", json=payload)
result = response.json()
```

## Ví dụ cURL - Chất lượng cao nhất

```bash
curl -X POST "http://localhost:5001/v1/convert/source" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [{"kind": "http", "url": "https://example.com/doc.pdf"}],
    "options": {
      "ocr_engine": "vietocr",
      "ocr_lang": ["vi"],
      "do_ocr": true,
      "force_ocr": true
    }
  }'
```

## Benchmark Performance

| Model | Beamsearch | Tốc độ (trang/giây) | Độ chính xác |
|-------|------------|---------------------|--------------|
| vgg_transformer | false | ~0.5 | 95% |
| vgg_transformer | true | ~0.2 | 98% |
| vgg_seq2seq | false | ~0.8 | 93% |
| resnet_transformer | false | ~1.2 | 90% |

## Tips để tăng chất lượng

1. **Hình ảnh kém**: Tăng `contrast` và `sharpness`
2. **Text mờ**: Tăng `brightness` và `contrast`
3. **Văn bản quan trọng**: Dùng `beamsearch: true`
4. **Nhiều trang**: Dùng GPU với `batch_size` cao
5. **Model tốt nhất**: `vgg_transformer` + `beamsearch`

## Troubleshooting

### Kết quả không chính xác
- Thử tăng `contrast` lên 1.5-2.0
- Bật `beamsearch: true`
- Đảm bảo PDF có độ phân giải >= 150 DPI

### Quá chậm
- Giảm `beamsearch` xuống `false`
- Dùng model nhẹ hơn: `resnet_transformer`
- Nếu có GPU, set `device: "cuda"`

### Out of memory
- Giảm `batch_size` xuống 1
- Dùng `device: "cpu"`
