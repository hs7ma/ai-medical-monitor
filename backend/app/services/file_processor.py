import io
import logging
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"}
ALLOWED_PDF_TYPE = "application/pdf"

DEFAULT_PDF_RENDER_DPI = 150
DEFAULT_PDF_MAX_PAGES = 6


class FileProcessor:
    def is_image(self, mime_type: str) -> bool:
        return mime_type in ALLOWED_IMAGE_TYPES

    def is_pdf(self, mime_type: str) -> bool:
        return mime_type == ALLOWED_PDF_TYPE

    def extract_text_from_pdf(self, data: bytes) -> str:
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("PDF text extraction error: %s", e)
            return ""

    def pdf_to_images(
        self,
        data: bytes,
        max_pages: int = DEFAULT_PDF_MAX_PAGES,
        dpi: int = DEFAULT_PDF_RENDER_DPI,
    ) -> list[bytes]:
        """Render PDF pages to PNG images using PyMuPDF (fitz).

        This lets Vision analyze graphical content in PDFs (e.g. ECG waveforms,
        charts, imaging) that pdfplumber cannot capture as text.
        """
        try:
            import fitz  # PyMuPDF

            images: list[bytes] = []
            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            with fitz.open(stream=data, filetype="pdf") as doc:
                total = len(doc)
                page_count = min(total, max_pages)
                for i in range(page_count):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(matrix=matrix)
                    png_bytes = pix.tobytes(output="png")
                    prepared = self.prepare_image_for_vision(png_bytes)
                    if prepared:
                        images.append(prepared)
            logger.info("Rendered %d/%d PDF pages to images", len(images), total)
            return images
        except Exception as e:
            logger.error("PDF to images error: %s", e)
            return []

    def extract_text_from_image(self, data: bytes) -> str:
        try:
            import pytesseract

            image = Image.open(io.BytesIO(data))
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = ImageEnhance.Contrast(image).enhance(1.5)
            image = image.filter(ImageFilter.SHARPEN)
            text = pytesseract.image_to_string(image, lang="eng+ara")
            return text.strip()
        except Exception as e:
            logger.error("OCR error: %s", e)
            return ""

    def extract_text(self, data: bytes, mime_type: str) -> str:
        if self.is_pdf(mime_type):
            return self.extract_text_from_pdf(data)
        if self.is_image(mime_type):
            return self.extract_text_from_image(data)
        return ""

    def prepare_image_for_vision(self, data: bytes, max_size: int = 1568) -> Optional[bytes]:
        try:
            image = Image.open(io.BytesIO(data))
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            image = ImageEnhance.Contrast(image).enhance(1.3)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error("Image preparation error: %s", e)
            return None

    def encode_image_for_vision(self, data: bytes) -> str:
        import base64
        return base64.b64encode(data).decode("utf-8")


file_processor = FileProcessor()
