import threading
from paddleocr import PaddleOCR
from typing import Tuple

class OCRService:
    """
    Singleton wrapper for PaddleOCR to ensure it is only loaded once.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if OCRService._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            # Initialize PaddleOCR
            # use_angle_cls=True allows it to recognize text that's upside down or rotated
            # lang='en' specifies English
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            OCRService._instance = self

    @staticmethod
    def get_instance():
        """
        Returns the singleton instance of OCRService.
        """
        if OCRService._instance is None:
            with OCRService._lock:
                if OCRService._instance is None:
                    OCRService()
        return OCRService._instance

    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """
        Extracts text from an image using PaddleOCR.
        Returns a tuple of (extracted_text, average_confidence).
        """
        # Run OCR
        result = self.ocr.ocr(image_path, cls=True)
        
        extracted_text = []
        confidences = []

        if not result or not result[0]:
            return "", 0.0

        # PaddleOCR returns a list of lists. The inner list contains the results for a single page.
        for line in result[0]:
            if line and len(line) >= 2:
                # line[1] contains a tuple of (text, confidence)
                text_info = line[1]
                text = text_info[0]
                confidence = float(text_info[1])
                
                extracted_text.append(text)
                confidences.append(confidence)

        final_text = "\n".join(extracted_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return final_text, avg_confidence
