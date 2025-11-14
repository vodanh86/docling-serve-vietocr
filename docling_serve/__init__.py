"""Docling Serve - Register plugins early."""

# Register VietOCR plugin before any other imports that use the OCR factory
try:
    from docling_serve.ocr_plugins.register import register_vietocr
    register_vietocr()
except Exception:
    pass  # Silently fail if VietOCR registration fails
