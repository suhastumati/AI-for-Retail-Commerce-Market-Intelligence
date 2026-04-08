from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
ASSET_PATH = BASE_DIR / "demo_app/assets/competitor_sample.html"
OUTPUT_PATH = BASE_DIR / "data_sources/competitor_prices/raw/competitor_prices.csv"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_td = False
        self.current_row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        if tag == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_td:
            self.current_row.append(data.strip())


def main() -> None:
    parser = TableParser()
    parser.feed(ASSET_PATH.read_text())

    df = pd.DataFrame(parser.rows, columns=["date", "sku", "competitor", "price"])
    df["price"] = df["price"].astype(float)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
