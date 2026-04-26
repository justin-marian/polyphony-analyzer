from pathlib import Path

from core.analyzer import PolyphonicAnalyzer
from core.parser import parse_chat_log
from core.reporter import save_text_report, save_json_report


INPUT_DIR = Path("data")
OUTPUT_DIR = Path("outputs")


def main():
    analyzer = PolyphonicAnalyzer()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in sorted(INPUT_DIR.glob("session_*.json")):
        print(f"Analyzing {path}...")

        utterances = parse_chat_log(path)
        result = analyzer.analyze(utterances, chat_log_name=path.stem)

        txt_path = save_text_report(result, OUTPUT_DIR)
        json_path = save_json_report(result, OUTPUT_DIR)

        print(f"  TXT : {txt_path}")
        print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
