import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from paddleocr import PaddleOCR


@dataclass
class OcrToken:
    """
    Represents a single token from OCR output.

    Attributes
    ----------
    text : str
        Original text as recognized by OCR.
    normalized : str
        Normalized text (lowercased, trimmed, basic corrections).
    box : Tuple[Tuple[float, float], ...]
        Bounding box coordinates of the token (4 points).
    """

    text: str
    normalized: str
    box: Tuple[Tuple[float, float], ...]


class VitalExtractor:
    """
    Main class responsible for running OCR and extracting vital signs.
    """

    # Keywords for each vital type (in lowercase)
    HEART_KEYWORDS = {"hr", "bpm", "ecg"}
    BP_KEYWORDS = {"bp", "nibp", "ibp"}
    # Include common OCR variants such as "sp02" (0 instead of o).
    SPO2_KEYWORDS = {"spo2", "spo", "sp02"}
    RESP_KEYWORDS = {"resp", "rr"}
    TEMP_KEYWORDS = {"temp", "t"}

    def __init__(self) -> None:
        """
        Initialize PaddleOCR once so it can be reused for multiple images.
        """
        # Use basic, widely supported parameters so this works across
        # different PaddleOCR versions.
        self.ocr_engine = PaddleOCR(
            lang="en",
            use_angle_cls=True,
        )

    # ------------------------------------------------------------------
    # OCR AND NORMALIZATION HELPERS
    # ------------------------------------------------------------------
    def run_ocr(self, image: np.ndarray) -> List[OcrToken]:
        """
        Run PaddleOCR on an image and convert results to tokens.

        PaddleOCR has evolved over several major versions and the exact
        structure of the OCR output can differ (lists, tuples, dicts,
        additional wrappers, etc.). To stay compatible with v2 / v3 / v5
        style outputs, this function walks the result recursively and
        extracts any (box, text, score) triplets it can recognize.
        """
        # Some PaddleOCR versions do not support the `cls` flag here,
        # so we call `ocr` with only the image argument for compatibility.
        raw_results = self.ocr_engine.ocr(image)

        # Debug: show the raw structure coming back from PaddleOCR so it is
        # easier to see which branch below is being used.
        print("OCR raw result:", raw_results)

        if not raw_results:
            print("Detected OCR tokens: [] (no text detected, empty raw_results)")
            return []

        # ------------------------------------------------------------------
        # Step 1: recursively walk the raw results and collect candidates
        #         in the form (box, text, score).
        # ------------------------------------------------------------------
        candidates: List[Tuple[Optional[Any], str, Optional[float]]] = []

        def first_not_none(*values: Any, default: Any = None) -> Any:
            """
            Return the first value that is not None. This avoids using Python's
            `or` on numpy arrays, which raises 'truth value is ambiguous'.
            """
            for v in values:
                if v is not None:
                    return v
            return default


        def is_box_like(value: Any) -> bool:
            """
            Heuristic: a box is a list/tuple of at least 4 points,
            each point being a 2D coordinate.
            """
            if not isinstance(value, (list, tuple)) or len(value) < 4:
                return False
            first = value[0]
            return isinstance(first, (list, tuple)) and len(first) == 2

        def walk(obj: Any) -> None:
            """
            Recursively inspect the OCR result and pull out any text entries.
            """
            # Dict-style results (common in newer pipelines)
            if isinstance(obj, dict):
                # Case 1: direct text entry (older/simple formats)
                if "text" in obj and isinstance(obj.get("text"), str):
                    box = (
                        obj.get("box")
                        or obj.get("bbox")
                        or obj.get("points")
                        or obj.get("poly")
                    )
                    text = str(obj.get("text", ""))
                    score = obj.get("score") or obj.get("confidence")
                    candidates.append((box, text, score))

                # Case 2: PaddleOCR v3/v5 style: arrays of rec_text / rec_score /
                # rec_boxes (naming can vary slightly).
                texts = first_not_none(
                    obj.get("rec_text"),
                    obj.get("rec_texts"),
                    obj.get("texts"),
                    default=[],
                )
                scores = first_not_none(
                    obj.get("rec_score"),
                    obj.get("rec_scores"),
                    default=[],
                )
                polys = first_not_none(
                    obj.get("rec_boxes"),
                    obj.get("dt_polys"),
                    obj.get("polys"),
                    default=[],
                )
                if isinstance(texts, (list, tuple)) and texts:
                    for idx, t in enumerate(texts):
                        box = polys[idx] if idx < len(polys) else None
                        score = scores[idx] if idx < len(scores) else None
                        candidates.append((box, str(t), score))

                # Case 3: some builds use "rec_res": [{"text": ..., "score": ...}]
                if "rec_res" in obj and isinstance(obj["rec_res"], (list, tuple)):
                    polys = first_not_none(
                        obj.get("rec_boxes"),
                        obj.get("dt_polys"),
                        obj.get("polys"),
                        default=[],
                    )
                    for idx, entry in enumerate(obj["rec_res"]):
                        if not isinstance(entry, dict):
                            continue
                        text = entry.get("text") or entry.get("label")
                        if not text:
                            continue
                        box = polys[idx] if idx < len(polys) else None
                        score = entry.get("score") or entry.get("confidence")
                        candidates.append((box, str(text), score))

                # Also recurse into all values
                for v in obj.values():
                    walk(v)

            # List / tuple: could be a whole line or a single entry
            elif isinstance(obj, (list, tuple)):
                # Pattern: [box, (text, score)] or [box, text, score]
                if len(obj) >= 2 and is_box_like(obj[0]):
                    box = obj[0]
                    second = obj[1]
                    text = ""
                    score = None

                    if isinstance(second, (list, tuple)) and len(second) >= 1:
                        text = str(second[0])
                        if len(second) >= 2:
                            score = second[1]
                    else:
                        text = str(second)
                        if len(obj) >= 3:
                            score = obj[2]

                    candidates.append((box, text, score))

                    # Still recurse into children in case more information
                    # is nested inside.
                    for elem in obj:
                        walk(elem)
                else:
                    for elem in obj:
                        walk(elem)

            # Other types are ignored (numbers, strings at this level, etc.).

        walk(raw_results)

        tokens: List[OcrToken] = []

        for box, text, _score in candidates:
            if not isinstance(text, str):
                continue

            cleaned = text.strip()
            if not cleaned:
                continue

            # Basic correction for typical OCR mistakes before normalization
            corrected = self._correct_ocr_mistakes(cleaned)
            normalized = self._normalize_text(corrected)

            # Skip mostly decorative or waveform-like strings
            if all(ch in "-_=~" for ch in normalized):
                continue

            # Fallback box if OCR did not provide one; we do not use the
            # coordinates in the current extraction logic, but we keep a
            # consistent shape for debugging / future extensions.
            if box is None:
                box = ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0))

            tokens.extend(
                self._split_into_tokens(
                    normalized,
                    box,
                    original_text=corrected,
                )
            )

        # Debug: print all detected OCR tokens so we can see what OCR
        # actually found before any vital-sign extraction logic runs.
        if tokens:
            print("Detected OCR Tokens with Coordinates:", flush=True)

            for token in tokens:
                print(
                    f"Text: {token.text:15} "
                    f"Normalized: {token.normalized:15} "
                    f"Box: {token.box}",
                    flush=True
                )
        else:
            print("Detected OCR tokens: [] (no text detected)", flush=True)

        return tokens

    def _split_into_tokens(
    self, text: str, box: Tuple[Tuple[float, float], ...], original_text: str
    ) -> List[OcrToken]:
        """
        Split OCR text into individual tokens and estimate a separate
        bounding box for each token based on its position in the OCR line.
        """
        raw_tokens = re.split(r"\s+", text.strip())
        original_tokens = re.split(r"\s+", original_text.strip())

        if not raw_tokens or not raw_tokens[0]:
            return []

        try:
            points = np.array(box, dtype=float).reshape(-1, 2)
            x_min = float(points[:, 0].min())
            x_max = float(points[:, 0].max())
        
            y_min = float(points[:, 1].min())
            y_max = float(points[:, 1].max())
        except (TypeError, ValueError):
            return [
                OcrToken(text=orig, normalized=norm, box=box)
                for norm, orig in zip(raw_tokens, original_tokens)
                if norm
            ]

        total_chars = sum(len(token) for token in raw_tokens)
        if total_chars == 0:
            return []

        line_width = x_max - x_min
        line_height = y_max - y_min
        current_x = x_min

        tokens: List[OcrToken] = []

        for norm, orig in zip(raw_tokens, original_tokens):
            if not norm:
                continue

            token_width = line_width * len(norm) / total_chars

            token_box = (
                (current_x, y_min),
                (current_x + token_width, y_min),
                (current_x + token_width, y_max),
                (current_x, y_max),
            )

            tokens.append(
                OcrToken(
                    text=orig,
                    normalized=norm,
                    box=token_box,
                )
            )

            current_x += token_width

        return tokens

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for easier matching: lowercase and collapse spaces.
        """
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _correct_ocr_mistakes(text: str) -> str:
        """
        Apply simple heuristic corrections for very common OCR confusions.

        Examples:
        - 'O' ↔ '0'
        - 'B' ↔ '8'
        - 'I'/'l' ↔ '1'
        """
        # Only apply character replacements when they appear near digits
        def replace_if_near_digits(s: str, wrong: str, right: str) -> str:
            pattern = rf"(?<=\d){wrong}|{wrong}(?=\d)"
            return re.sub(pattern, right, s)

        corrected = text
        corrected = replace_if_near_digits(corrected, "O", "0")
        corrected = replace_if_near_digits(corrected, "o", "0")
        corrected = replace_if_near_digits(corrected, "B", "8")
        corrected = replace_if_near_digits(corrected, "I", "1")
        corrected = replace_if_near_digits(corrected, "l", "1")

        return corrected

    # ------------------------------------------------------------------
    # PUBLIC EXTRACTION API
    # ------------------------------------------------------------------
    def extract_vitals_from_image(self, image: np.ndarray) -> Dict[str, Optional[Any]]:
        """
        Convenience method that runs OCR and then extracts vitals.
        """
        tokens = self.run_ocr(image)
        return self.extract_vitals_from_tokens(tokens)

    def extract_vitals_from_tokens(
        self, tokens: List[OcrToken]
    ) -> Dict[str, Optional[Any]]:
        """
        Given OCR tokens, find the best guess for each vital sign.
        """
        heart_rate = self._find_heart_rate(tokens)
        blood_pressure = self._find_blood_pressure(tokens)
        spo2 = self._find_spo2(tokens)
        respiration = self._find_respiration(tokens)
        temperature = self._find_temperature(tokens)

        return {
            "heart_rate": heart_rate,
            "blood_pressure": blood_pressure,
            "spo2": spo2,
            "respiration": respiration,
            "temperature": temperature,
        }

    # ------------------------------------------------------------------
    # VITAL-SPECIFIC EXTRACTION METHODS
    # ------------------------------------------------------------------
    def _find_heart_rate(self, tokens: List[OcrToken]) -> Optional[int]:
        """
        Search for heart rate near HR/BPM/ECG keywords.
        """
        # Prefer spatial proximity (bounding boxes) over token order.
        value = self._find_numeric_near_keywords(
            tokens,
            keywords=self.HEART_KEYWORDS,
            min_value=30,
            max_value=250,
        )
        if value is not None:
            return value

        return self._find_numeric_after_keywords(
            tokens,
            keywords=self.HEART_KEYWORDS,
            min_value=30,
            max_value=250,
            max_distance=3,
        )

    def _find_blood_pressure(self, tokens: List[OcrToken]) -> Optional[str]:
        """
        Search for a systolic/diastolic pattern near BP/NIBP/IBP.
        """
        keyword_indices = self._find_keyword_indices(tokens, self.BP_KEYWORDS)
        if not keyword_indices:
            # Sometimes the value appears without an explicit keyword
            return self._scan_for_bp_pattern(tokens)

        # Collect all BP candidates that appear near any BP-like keyword.
        candidates: List[str] = []
        for idx in keyword_indices:
            bp = self._scan_for_bp_pattern(tokens, center_index=idx, window=5)
            if bp:
                candidates.append(bp)

        if candidates:
            # If multiple BP values are present (e.g. NIBP 90/55 and arterial
            # 120/78), prefer the one with the highest systolic pressure,
            # which is usually the main arterial line on monitors.
            best_bp = None
            best_systolic = -1
            for bp in candidates:
                try:
                    systolic = int(str(bp).split("/")[0])
                except (ValueError, IndexError):
                    continue
                if systolic > best_systolic:
                    best_systolic = systolic
                    best_bp = bp
            if best_bp is not None:
                return best_bp

        # Fallback: global search
        return self._scan_for_bp_pattern(tokens)

    def _find_spo2(self, tokens: List[OcrToken]) -> Optional[int]:
        """
        Search for SpO2 (oxygen saturation) near SpO2 keyword.
        """
        value = self._find_numeric_after_keywords(
            tokens,
            keywords=self.SPO2_KEYWORDS,
            min_value=50,
            max_value=100,
            max_distance=3,
        )
        if value is not None:
            return value

        # Fallback: look for any percentage-like token in a plausible range.
        for token in tokens:
            if "%" in token.normalized:
                num = self._parse_int(token.normalized)
                if num is not None and 50 <= num <= 100:
                    return num

        return None

    def _find_respiration(self, tokens: List[OcrToken]) -> Optional[int]:
        """
        Search for respiratory rate near RESP keyword.
        """
        value = self._find_numeric_near_keywords(
            tokens,
            keywords=self.RESP_KEYWORDS,
            min_value=5,
            max_value=60,
        )
        if value is not None:
            return value

        return self._find_numeric_after_keywords(
            tokens,
            keywords=self.RESP_KEYWORDS,
            min_value=5,
            max_value=60,
            max_distance=3,
        )

    def _find_temperature(self, tokens: List[OcrToken]) -> Optional[float]:
        """
        Search for temperature near TEMP keyword.
        """
        value = self._find_float_near_keywords(
            tokens,
            keywords=self.TEMP_KEYWORDS,
            min_value=30.0,
            max_value=45.0,
        )
        if value is not None:
            return round(value, 1)

        # Fallback to older token-order heuristic.
        keyword_indices = self._find_keyword_indices(tokens, self.TEMP_KEYWORDS)
        for idx in keyword_indices:
            for j in range(max(0, idx - 3), min(len(tokens), idx + 4)):
                v = self._parse_float(tokens[j].normalized)
                if v is None:
                    continue
                if 30.0 <= v <= 45.0:
                    return round(v, 1)
        return None

    # ------------------------------------------------------------------
    # GENERIC SEARCH UTILITIES
    # ------------------------------------------------------------------
    def _find_keyword_indices(
        self, tokens: List[OcrToken], keywords: set
    ) -> List[int]:
        """
        Find indices of tokens that match any of the given keywords.
        """
        indices: List[int] = []
        for i, token in enumerate(tokens):
            norm = token.normalized
            # Some screens may show 'hr:' or 'hr=' etc., so strip punctuation
            cleaned = re.sub(r"[^a-z0-9]", "", norm)
            if cleaned in keywords:
                indices.append(i)
        return indices

    def _find_numeric_after_keywords(
        self,
        tokens: List[OcrToken],
        keywords: set,
        min_value: int,
        max_value: int,
        max_distance: int,
    ) -> Optional[int]:
        """
        Generic helper to find a numeric value close to given keywords.
        """
        keyword_indices = self._find_keyword_indices(tokens, keywords)

        # Prefer numbers that appear after the keyword, but also allow before
        for idx in keyword_indices:
            # Look forward
            for j in range(idx + 1, min(len(tokens), idx + 1 + max_distance)):
                num = self._parse_int(tokens[j].normalized)
                if num is not None and min_value <= num <= max_value:
                    return num

            # Look backward (value might be placed before label)
            for j in range(max(0, idx - max_distance), idx):
                num = self._parse_int(tokens[j].normalized)
                if num is not None and min_value <= num <= max_value:
                    return num

        return None

    @staticmethod
    def _box_center(box: Any) -> Optional[Tuple[float, float]]:
        """
        Compute a center point for different box formats.

        Supports:
        - polygon: [[x,y], [x,y], [x,y], [x,y]]
        - flat: [x1,y1,x2,y2,...]
        - rect: [x1,y1,x2,y2]
        - numpy arrays of the above
        """
        if box is None:
            return None
        try:
            arr = np.array(box, dtype=float)
        except Exception:
            return None

        if arr.ndim == 2 and arr.shape[1] == 2 and arr.shape[0] >= 2:
            return float(arr[:, 0].mean()), float(arr[:, 1].mean())

        if arr.ndim == 1 and arr.size >= 4:
            flat = arr.flatten()
            xs = flat[0::2]
            ys = flat[1::2]
            if xs.size == 0 or ys.size == 0:
                return None
            return float(xs.mean()), float(ys.mean())

        return None

    def _find_numeric_near_keywords(
    self,
    tokens: List[OcrToken],
    keywords: set,
    min_value: int,
    max_value: int,
    ) -> Optional[int]:
        """
        Find a numeric value near a keyword, prioritizing values on the
        same horizontal row and to the right of the keyword.
        Reject candidates that are too far away.
        """
        keyword_indices = self._find_keyword_indices(tokens, keywords)
        if not keyword_indices:
            return None

        best_value: Optional[int] = None
        best_score: Optional[float] = None

        for ki in keyword_indices:
            keyword_box = tokens[ki].box
            keyword_center = self._box_center(keyword_box)

            if keyword_center is None:
                continue

            kx, ky = keyword_center

            try:
                keyword_points = np.array(keyword_box, dtype=float).reshape(-1, 2)
                keyword_height = float(
                    keyword_points[:, 1].max() - keyword_points[:, 1].min()
                )
            except (TypeError, ValueError):
                keyword_height = 0.0

            for ti, token in enumerate(tokens):
                if ti == ki:
                    continue

                value = self._parse_int(token.normalized)

                if value is None or not (min_value <= value <= max_value):
                    continue

                value_center = self._box_center(token.box)

                if value_center is None:
                    continue

                vx, vy = value_center

                # Reject numbers that are not to the right of the keyword.
                horizontal_distance = vx - kx
                if horizontal_distance <= 0:
                    continue

                # Reject numbers on a different row.
                vertical_distance = abs(vy - ky)
                allowed_vertical_distance = max(keyword_height * 1.5, 12.0)

                if vertical_distance > allowed_vertical_distance:
                    continue

                # Reject numbers that are too far from the keyword.
                if horizontal_distance > 300:
                    continue

                # Prefer the closest candidate on the same row.
                score = horizontal_distance + (vertical_distance * 2)

                if best_score is None or score < best_score:
                    best_score = score
                    best_value = value

                return best_value
    def _find_float_near_keywords(
        self,
        tokens: List[OcrToken],
        keywords: set,
        min_value: float,
        max_value: float,
    ) -> Optional[float]:
        """
        Float version of proximity search (used for temperature).
        """
        keyword_indices = self._find_keyword_indices(tokens, keywords)
        if not keyword_indices:
            return None

        best_value: Optional[float] = None
        best_dist2: Optional[float] = None

        for ki in keyword_indices:
            kc = self._box_center(tokens[ki].box)
            if kc is None:
                continue
            kx, ky = kc

            for t in tokens:
                val = self._parse_float(t.normalized)
                if val is None or not (min_value <= val <= max_value):
                    continue
                nc = self._box_center(t.box)
                if nc is None:
                    continue
                nx, ny = nc
                d2 = (nx - kx) ** 2 + (ny - ky) ** 2
                if best_dist2 is None or d2 < best_dist2:
                    best_dist2 = d2
                    best_value = val

        return best_value

    def _scan_for_bp_pattern(
        self,
        tokens: List[OcrToken],
        center_index: Optional[int] = None,
        window: int = 6,
    ) -> Optional[str]:
        """
        Look for patterns like '120/80' or '120 / 80' in a local window or globally.
        """
        indices = range(len(tokens))
        if center_index is not None:
            start = max(0, center_index - window)
            end = min(len(tokens), center_index + window + 1)
            indices = range(start, end)

        best_bp: Optional[str] = None
        best_systolic: int = -1

        # First pass: look for patterns in single tokens, like '120/80'
        bp_pattern = re.compile(r"(\d{2,3})\s*[/\\]\s*(\d{2,3})")
        for i in indices:
            match = bp_pattern.search(tokens[i].normalized)
            if match:
                systolic = int(match.group(1))
                diastolic = int(match.group(2))
                if 50 <= systolic <= 250 and 30 <= diastolic <= 200:
                    if systolic > best_systolic:
                        best_systolic = systolic
                        best_bp = f"{systolic}/{diastolic}"

        # Second pass: numbers split across adjacent tokens, like '120', '/', '80'
        token_texts = [t.normalized for t in tokens]
        for i in indices:
            # S / D or S \ D pattern spread over up to 3 tokens
            if i + 2 < len(tokens):
                left = self._parse_int(token_texts[i])
                sep = token_texts[i + 1]
                right = self._parse_int(token_texts[i + 2])
                if left is None or right is None:
                    continue
                if sep in {"/", "\\"}:
                    if 50 <= left <= 250 and 30 <= right <= 200:
                        if left > best_systolic:
                            best_systolic = left
                            best_bp = f"{left}/{right}"

        return best_bp

    @staticmethod
    def _parse_int(text: str) -> Optional[int]:
        """
        Safely parse an integer from text.
        """
        match = re.search(r"\d{1,3}", text)
        if not match:
            return None
        try:
            return int(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _parse_float(text: str) -> Optional[float]:
        """
        Safely parse a float from text.
        """
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None


def example_test(image_path: str) -> Dict[str, Optional[Any]]:
    """
    Example function that loads an image, runs OCR, and prints JSON output.

    This is meant as a simple demonstration of how to call the extractor
    from Python code. Replace `image_path` with the path to a real monitor
    screenshot in your environment.
    """
    from .preprocess import load_and_preprocess

    original, preprocessed = load_and_preprocess(image_path)
    extractor = VitalExtractor()
    vitals = extractor.extract_vitals_from_image(preprocessed)

    print("Extracted vitals:")
    print(json.dumps(vitals, indent=2))
    return vitals