"""VietOCR integration for Docling."""
import logging
from typing import ClassVar, Iterable

from docling_core.types.doc import BoundingBox, CoordOrigin, Size
from PIL import Image, ImageEnhance

from docling.datamodel.base_models import Page, TextCell
from docling.datamodel.pipeline_options import OcrOptions
from docling.models.base_ocr_model import BaseOcrModel

_log = logging.getLogger(__name__)


class VietOcrOptions(OcrOptions):
    """Options for VietOCR."""

    kind: ClassVar[str] = "vietocr"
    config_name: str = "vgg_transformer"  # VietOCR model config: vgg_transformer (best quality), vgg_seq2seq, resnet_transformer, resnet_seq2seq
    lang: list[str] = ["vi"]  # Default to Vietnamese
    
    # Quality improvement parameters
    beamsearch: bool = False  # Enable beam search for better accuracy (slower)
    batch_size: int = 1  # Batch size for processing (higher = faster but more memory)
    device: str = "cpu"  # Device: 'cpu' or 'cuda' for GPU acceleration
    workers: int = 0  # Number of workers for data loading (0 = main thread)
    
    # Image preprocessing for better OCR
    contrast: float = 1.0  # Contrast adjustment (1.0 = no change, >1.0 = higher contrast)
    brightness: float = 1.0  # Brightness adjustment (1.0 = no change)
    sharpness: float = 1.0  # Sharpness adjustment (1.0 = no change, >1.0 = sharper)


class VietOcrModel(BaseOcrModel):
    """VietOCR model implementation for Docling."""

    def __init__(self, enabled: bool, options: VietOcrOptions):
        super().__init__(enabled=enabled, options=options)
        self.options: VietOcrOptions = options
        self.predictor = None

        if enabled:
            try:
                from vietocr.tool.config import Cfg
                from vietocr.tool.predictor import Predictor

                # Load VietOCR configuration
                config = Cfg.load_config_from_name(self.options.config_name)
                config["cnn"]["pretrained"] = False
                config["device"] = self.options.device
                config["predictor"]["beamsearch"] = self.options.beamsearch
                
                # Batch processing settings
                if self.options.batch_size > 1:
                    config["batch_size"] = self.options.batch_size
                
                # Data loading workers
                if self.options.workers > 0:
                    config["workers"] = self.options.workers

                self.predictor = Predictor(config)
                _log.info(
                    f"VietOCR initialized - model: {self.options.config_name}, "
                    f"device: {self.options.device}, beamsearch: {self.options.beamsearch}"
                )
            except ImportError:
                _log.error(
                    "VietOCR is not installed. Install it with: pip install vietocr"
                )
                raise
            except Exception as e:
                _log.error(f"Failed to initialize VietOCR: {e}")
                raise

    @classmethod
    def get_options_type(cls) -> type[VietOcrOptions]:
        """Return the options type for this model."""
        return VietOcrOptions

    def __call__(self, page_batch: Iterable[Page]) -> Iterable[Page]:
        """Process pages with VietOCR."""
        if not self.enabled or self.predictor is None:
            yield from page_batch
            return

        for page in page_batch:
            if page.image is None:
                yield page
                continue

            # Convert page image to PIL Image
            pil_image = page.image.pil_image

            # Get page dimensions
            page_width = page.size.width
            page_height = page.size.height

            # Process each cell (text region) on the page
            ocr_cells = []
            for cell in page.cells:
                if cell.text:  # Skip cells that already have text
                    continue

                # Get cell bounding box
                bbox = cell.bbox
                if bbox is None:
                    continue

                # Crop image to cell region
                try:
                    # Convert coordinates based on origin
                    if bbox.coord_origin == CoordOrigin.BOTTOMLEFT:
                        # Convert from bottom-left to top-left
                        x1 = bbox.l
                        y1 = page_height - bbox.t
                        x2 = bbox.r
                        y2 = page_height - bbox.b
                    else:  # TOPLEFT
                        x1 = bbox.l
                        y1 = bbox.t
                        x2 = bbox.r
                        y2 = bbox.b

                    # Ensure coordinates are within image bounds
                    x1 = max(0, min(x1, page_width))
                    y1 = max(0, min(y1, page_height))
                    x2 = max(0, min(x2, page_width))
                    y2 = max(0, min(y2, page_height))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    # Crop and recognize text
                    cell_image = pil_image.crop((x1, y1, x2, y2))
                    
                    # Apply image enhancements for better OCR quality
                    if (self.options.contrast != 1.0 or 
                        self.options.brightness != 1.0 or 
                        self.options.sharpness != 1.0):
                        
                        if self.options.contrast != 1.0:
                            enhancer = ImageEnhance.Contrast(cell_image)
                            cell_image = enhancer.enhance(self.options.contrast)
                        
                        if self.options.brightness != 1.0:
                            enhancer = ImageEnhance.Brightness(cell_image)
                            cell_image = enhancer.enhance(self.options.brightness)
                        
                        if self.options.sharpness != 1.0:
                            enhancer = ImageEnhance.Sharpness(cell_image)
                            cell_image = enhancer.enhance(self.options.sharpness)
                    
                    # VietOCR prediction
                    text = self.predictor.predict(cell_image)
                    
                    if text and text.strip():
                        # Create TextCell with recognized text
                        text_cell = TextCell(
                            id=len(ocr_cells),
                            text=text.strip(),
                            bbox=bbox,
                        )
                        ocr_cells.append(text_cell)

                except Exception as e:
                    _log.warning(f"Failed to process cell: {e}")
                    continue

            # Add OCR cells to page
            if ocr_cells:
                if page.predictions.ocr_cells is None:
                    page.predictions.ocr_cells = []
                page.predictions.ocr_cells.extend(ocr_cells)

            yield page

    @classmethod
    def available_models(cls) -> list[str]:
        """Return list of available VietOCR models."""
        return [
            "vgg_transformer",
            "vgg_seq2seq",
            "resnet_transformer",
            "resnet_seq2seq",
        ]

    @classmethod
    def supports_languages(cls, languages: Iterable[str]) -> bool:
        """Check if VietOCR supports the given languages."""
        # VietOCR primarily supports Vietnamese
        supported = {"vi", "vie", "vietnamese"}
        return any(lang.lower() in supported for lang in languages)
