"""Entry point for VietOCR plugin registration."""
from docling_serve.ocr_plugins.vietocr_plugin import VietOcrModel, VietOcrOptions


# Docling plugin interface
OCR_MODELS = {
    "vietocr": {
        "model": VietOcrModel,
        "options": VietOcrOptions,
    }
}
