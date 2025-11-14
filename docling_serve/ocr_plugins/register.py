"""Register VietOCR at runtime."""
import logging

_log = logging.getLogger(__name__)


def register_vietocr():
    """Register VietOCR with Docling's OCR factory."""
    try:
        from docling.models.factories import get_ocr_factory
        from docling_serve.ocr_plugins.vietocr_plugin import (
            VietOcrModel,
            VietOcrOptions,
        )

        # Get the factory
        factory = get_ocr_factory(allow_external_plugins=True)

        # Check if already registered
        if VietOcrOptions not in factory._classes:
            # Register: key is Options class, value is Model class
            factory._classes[VietOcrOptions] = VietOcrModel
            _log.info("VietOCR successfully registered with Docling OCR factory")
        else:
            _log.info("VietOCR already registered")

        return True
    except Exception as e:
        _log.error(f"Failed to register VietOCR: {e}", exc_info=True)
        return False
