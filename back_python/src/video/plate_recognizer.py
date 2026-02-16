"""
License plate recognizer based on EasyOCR + OpenCV preprocessing.
"""
import re
import unicodedata
from typing import List, Dict, Optional

from config import Config

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False


class PlateRecognizer:
    """Recognize Chinese license plates from an image file."""

    # Common Mainland China plate patterns:
    # Normal: 京A12345
    # New energy: 京AD12345 / 京A12345D
    PLATE_PATTERNS = [
        re.compile(r"^[\u4e00-\u9fa5][A-Z][A-Z0-9]{5}$"),
        re.compile(r"^[\u4e00-\u9fa5][A-Z][A-Z0-9]{6}$"),
    ]
    RELAXED_PATTERNS = [
        re.compile(r"^[A-Z][A-Z0-9]{5}$"),
        re.compile(r"^[A-Z][A-Z0-9]{6}$"),
    ]

    def __init__(self):
        self.reader = None
        self.available = CV2_AVAILABLE and EASYOCR_AVAILABLE
        if self.available:
            langs = [x.strip() for x in Config.EASYOCR_LANGS.split(",") if x.strip()]
            if not langs:
                langs = ["ch_sim", "en"]
            self.reader = easyocr.Reader(langs, gpu=False)

    def _preprocess(self, image):
        """Generate multiple preprocessed variants for better OCR robustness."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.bilateralFilter(gray, 11, 17, 17)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 8
        )
        # Upscale helps OCR on distant plates.
        up2 = cv2.resize(image, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        return [image, gray, th, adaptive, up2]

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        s = unicodedata.normalize("NFKC", text)
        s = s.upper().replace(" ", "").replace("-", "").replace("_", "")
        s = re.sub(r"[^A-Z0-9\u4e00-\u9fa5]", "", s)
        return s

    @staticmethod
    def _is_valid_plate(text: str) -> bool:
        for pattern in PlateRecognizer.PLATE_PATTERNS:
            if pattern.match(text):
                return True
        return False

    @staticmethod
    def _is_relaxed_plate(text: str) -> bool:
        for pattern in PlateRecognizer.RELAXED_PATTERNS:
            if pattern.match(text):
                return True
        return False

    def _extract_from_one_text(self, text: str, strict: bool = True) -> List[str]:
        """
        Extract possible plate candidates from one OCR text via sliding windows.
        """
        cleaned = self._normalize_text(text)
        if not cleaned:
            return []

        results = []
        # direct match first
        canon = self._canonicalize_candidate(cleaned)
        if canon and ((self._is_valid_plate(canon) if strict else self._is_relaxed_plate(canon))):
            results.append(canon)

        # try every 7/8-char window
        for n in (8, 7):
            if len(cleaned) < n:
                continue
            for i in range(0, len(cleaned) - n + 1):
                seg = cleaned[i : i + n]
                canon = self._canonicalize_candidate(seg)
                if canon and ((self._is_valid_plate(canon) if strict else self._is_relaxed_plate(canon))):
                    results.append(canon)

        # keep order, deduplicate
        seen = set()
        uniq = []
        for x in results:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return uniq

    @staticmethod
    def _canonicalize_candidate(text: str) -> str:
        """
        Position-aware correction:
        - 1st char: Chinese province char
        - 2nd char: letter
        - remaining: alnum (favor digits for common OCR confusions)
        """
        if len(text) not in (7, 8):
            return text

        chars = list(text)
        if not re.match(r"[\u4e00-\u9fa5]", chars[0]):
            return text

        second_map = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z"}
        tail_map = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8"}

        chars[1] = second_map.get(chars[1], chars[1])
        if not re.match(r"[A-Z]", chars[1]):
            return text

        for i in range(2, len(chars)):
            chars[i] = tail_map.get(chars[i], chars[i])
            if not re.match(r"[A-Z0-9]", chars[i]):
                return text
        return "".join(chars)

    def _extract_candidates(self, raw_texts: List[Dict]) -> List[Dict]:
        strict_candidates = []
        relaxed_candidates = []
        for item in raw_texts:
            conf = float(item.get("confidence", 0.0))
            text = item.get("text", "")
            for plate in self._extract_from_one_text(text, strict=True):
                strict_candidates.append(
                    {"plate_number": plate, "confidence": conf, "strict": True}
                )
            for plate in self._extract_from_one_text(text, strict=False):
                relaxed_candidates.append(
                    {"plate_number": plate, "confidence": conf * 0.9, "strict": False}
                )

        # Prefer strict results; use relaxed only when strict is empty
        candidates = strict_candidates if strict_candidates else relaxed_candidates

        # Deduplicate by plate and keep highest confidence
        best = {}
        for c in candidates:
            plate = c["plate_number"]
            if plate not in best or c["confidence"] > best[plate]["confidence"]:
                best[plate] = c
        return sorted(best.values(), key=lambda x: x["confidence"], reverse=True)

    def recognize(self, image_path: str) -> Dict:
        if not self.available:
            return {
                "success": False,
                "message": "Plate recognition dependencies missing: install opencv-python and easyocr",
                "plate_number": None,
                "confidence": 0.0,
                "candidates": [],
            }

        image = cv2.imread(image_path)
        if image is None:
            return {
                "success": False,
                "message": "Cannot read uploaded image",
                "plate_number": None,
                "confidence": 0.0,
                "candidates": [],
            }

        raw_results = []
        for variant in self._preprocess(image):
            ocr_results = self.reader.readtext(variant, detail=1, paragraph=False)
            variant_texts = []
            confs = []
            for r in ocr_results:
                if len(r) >= 3:
                    txt = str(r[1])
                    cf = float(r[2])
                    raw_results.append(
                        {"text": txt, "confidence": cf}
                    )
                    variant_texts.append(txt)
                    confs.append(cf)
            # OCR often splits plate into 2-3 tokens; merge variant-level text once.
            if variant_texts:
                merged = "".join(variant_texts)
                raw_results.append(
                    {
                        "text": merged,
                        "confidence": float(sum(confs) / max(len(confs), 1)),
                    }
                )

        candidates = self._extract_candidates(raw_results)
        best: Optional[Dict] = candidates[0] if candidates else None

        if not best:
            return {
                "success": False,
                "message": "No valid plate number detected",
                "plate_number": None,
                "confidence": 0.0,
                "candidates": [],
            }

        message = "Plate recognized"
        if not best.get("strict", True):
            message = "Partial plate recognized (province character may be missing)"

        return {
            "success": True,
            "message": message,
            "plate_number": best["plate_number"],
            "confidence": float(best["confidence"]),
            "candidates": candidates[:5],
        }
