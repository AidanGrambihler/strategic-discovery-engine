import json
import re
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoldStandardProcessor:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.inch_to_mm = 25.4

    def _extract_float(self, text):
        if not text: return 0.0
        # Handles cases like '0.63 in' or '$650'
        match = re.search(r"(\d+\.?\d*)", str(text))
        return float(match.group(1)) if match else 0.0

    def transform(self):
        if not os.path.exists(self.input_path):
            logger.error(f"Input file not found at: {self.input_path}")
            return

        cleaned_data = []
        with open(self.input_path, 'r', encoding='utf-8') as f:
            for line in f:
                raw = json.loads(line)
                processed = {
                    "brand_model": raw.get("brand_model"),
                    "price_usd": self._extract_float(raw.get("price")),
                    # Convert amplitude from inches to mm (Industry standard)
                    "amplitude_mm": round(self._extract_float(raw.get("amplitude")) * self.inch_to_mm, 1),
                    "stall_force_lbs": self._extract_float(raw.get("stall_force")),
                    "max_ppm": int(self._extract_float(raw.get("max_ppm"))),
                    "weight_lbs": self._extract_float(raw.get("weight")),
                    "noise_dba": self._extract_float(raw.get("sound_range"))
                }
                cleaned_data.append(processed)

        self._save(cleaned_data)

    def _save(self, data):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")
        logger.info(f"Successfully processed {len(data)} items to {self.output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../../"))

    raw_path = os.path.join(project_root, "data", "raw", "gold_standards.jsonl")
    processed_path = os.path.join(project_root, "data", "processed", "gold_standards_cleaned.jsonl")

    GoldStandardProcessor(raw_path, processed_path).transform()