from pathlib import Path
import random

import pandas as pd


OUTPUT_FILE = Path("sample_sales_50.csv")
RANDOM_SEED = 20260309

PRODUCTS = [
    ("Mechanical Keyboard RGB", "Elektronik", 450000),
    ("Mouse Gaming Wireless", "Elektronik", 250000),
    ("Monitor 24 Inch 144Hz", "Elektronik", 1750000),
    ("TWS Bluetooth Earphone", "Elektronik", 199000),
    ("Kaos Polos Cotton 30s", "Fashion", 65000),
    ("Hoodie Oversize", "Fashion", 180000),
    ("Celana Chino Slim", "Fashion", 145000),
    ("Botol Minum Tumbler", "Perlengkapan", 85000),
    ("Lampu Meja Belajar", "Perlengkapan", 120000),
    ("Mousepad XL Gaming", "Perlengkapan", 95000),
]
CITIES = [
    "Jakarta",
    "Surabaya",
    "Bandung",
    "Medan",
    "Samarinda",
    "Yogyakarta",
    "Makassar",
]
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")


def dirty_category(category: str, random_generator: random.Random) -> str:
    style = random_generator.choice(("lower", "upper", "title"))
    if style == "lower":
        return category.lower()
    if style == "upper":
        return category.upper()
    return category


def format_date(day: int, random_generator: random.Random) -> str:
    date = pd.Timestamp(2026, 3, day)
    return date.strftime(random_generator.choice(DATE_FORMATS))


def create_record(
    order_number: int,
    status: str,
    random_generator: random.Random,
) -> dict[str, object]:
    product, category, price = random_generator.choice(PRODUCTS)
    quantity = random_generator.randint(1, 5)
    if status == "REFUND":
        quantity = -quantity

    transaction_date = ""
    if order_number not in (1012, 1031, 1044):
        transaction_date = format_date(
            random_generator.randint(1, 20), random_generator
        )

    return {
        "order_id": f"ORD-{order_number}",
        "tanggal_transaksi": transaction_date,
        "nama_produk": product,
        "kategori": dirty_category(category, random_generator),
        "harga_satuan": f"Rp {price:,.0f}".replace(",", "."),
        "jumlah_beli": quantity,
        "kota_pembeli": random_generator.choice(CITIES),
        "status_pembayaran": status,
    }


def main() -> None:
    random_generator = random.Random(RANDOM_SEED)
    statuses = ["PAID"] * 34 + ["CANCELLED"] * 8 + ["REFUND"] * 5
    random_generator.shuffle(statuses)

    records = [
        create_record(1001 + index, status, random_generator)
        for index, status in enumerate(statuses)
    ]

    # Salin tiga transaksi PAID agar distribusi status tetap 37/8/5.
    paid_records = [record for record in records if record["status_pembayaran"] == "PAID"]
    duplicate_sources = (paid_records[0], paid_records[1], paid_records[2])
    records.extend(record.copy() for record in duplicate_sources)
    random_generator.shuffle(records)

    pd.DataFrame(records).to_csv(OUTPUT_FILE, index=False)
    print(f"Berhasil membuat {len(records)} baris data di {OUTPUT_FILE}")


if __name__ == "__main__":
    main()