#!/usr/bin/env python3
"""
Summarize benchmark_summary_*.json into a markdown table for the journal.
"""

import argparse
import json
from pathlib import Path


def load_summary(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_table(summary: dict) -> str:
    by_lighting = summary.get("by_lighting", {})

    rows = []
    total = summary.get("total", 0)
    correct = summary.get("correct", 0)
    detect_failed = summary.get("detect_failed", 0)
    recognition_failed = summary.get("recognition_failed", 0)

    for lighting in sorted(by_lighting.keys()):
        data = by_lighting[lighting]
        accuracy = 0.0
        if data.get("total", 0) > 0:
            accuracy = round((data.get("correct", 0) / data.get("total", 1)) * 100.0, 2)

        rows.append(
            f"| {lighting} | {data.get('total', 0)} | {data.get('correct', 0)} | {data.get('detect_failed', 0)} | {data.get('recognition_failed', 0)} | {accuracy} |"
        )

    total_accuracy = 0.0
    if total > 0:
        total_accuracy = round((correct / total) * 100.0, 2)

    header = "| Kondisi Pencahayaan | Jumlah Sampel | Benar | Gagal Deteksi | Salah Kenal | Akurasi (%) |\n"
    header += "|---|---:|---:|---:|---:|---:|\n"

    table = header + "\n".join(rows)
    table += f"\n| **Total** | {total} | {correct} | {detect_failed} | {recognition_failed} | {total_accuracy} |\n"

    return table


def main():
    parser = argparse.ArgumentParser(description="Summarize benchmark JSON into markdown table")
    parser.add_argument("--summary", required=True, help="Path to benchmark_summary_*.json")
    parser.add_argument("--output", default="Doc/ACCURACY_TABLE_AUTOFILL.md", help="Output markdown file")
    args = parser.parse_args()

    summary_path = Path(args.summary).resolve()
    output_path = Path(args.output).resolve()

    summary = load_summary(summary_path)
    table = render_table(summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("# Tabel Akurasi (Auto)\n\n" + table + "\n", encoding="utf-8")

    print(f"[Summary] Output written to: {output_path}")


if __name__ == "__main__":
    main()
