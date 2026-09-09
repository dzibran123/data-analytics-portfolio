from pathlib import Path

import pandas as pd


INPUT_FILE = Path("sample_sales_50.csv")
PAID_OUTPUT_FILE = Path("cleaned_sales_paid.csv")
REFUNDED_OUTPUT_FILE = Path("sales_refunded.csv")
CANCELLED_OUTPUT_FILE = Path("sales_cancelled.csv")


def format_amount(value: int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def clean_sales_data(input_file: Path) -> pd.DataFrame:
    sales = pd.read_csv(input_file)

    required_columns = {
        "order_id",
        "tanggal_transaksi",
        "kategori",
        "harga_satuan",
        "jumlah_beli",
        "kota_pembeli",
        "status_pembayaran",
    }
    missing_columns = required_columns.difference(sales.columns)
    if missing_columns:
        raise ValueError(
            f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing_columns))}"
        )

    sales = sales.drop_duplicates(subset="order_id", keep="first").copy()

    date_formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")

    def parse_date(value: object) -> pd.Timestamp:
        if pd.isna(value) or not str(value).strip():
            return pd.NaT
        for date_format in date_formats:
            parsed_date = pd.to_datetime(value, format=date_format, errors="coerce")
            if not pd.isna(parsed_date):
                return parsed_date
        return pd.NaT

    parsed_dates = sales["tanggal_transaksi"].map(parse_date)
    sales["tanggal_transaksi"] = parsed_dates.ffill().dt.strftime("%Y-%m-%d")
    unresolved_dates = sales["tanggal_transaksi"].isna().sum()
    if unresolved_dates:
        print(
            f"Peringatan: {unresolved_dates} tanggal tidak dapat diisi dan ditandai kosong."
        )

    sales["harga_satuan"] = (
        sales["harga_satuan"]
        .astype("string")
        .str.replace("Rp", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    sales["harga_satuan"] = pd.to_numeric(
        sales["harga_satuan"], errors="coerce"
    ).round().astype("Int64")
    sales["jumlah_beli"] = pd.to_numeric(
        sales["jumlah_beli"], errors="coerce"
    ).astype("Int64")
    sales["kategori"] = sales["kategori"].astype("string").str.strip().str.title()
    sales["status_pembayaran"] = (
        sales["status_pembayaran"].astype("string").str.strip().str.upper()
    )
    sales["total_harga"] = (sales["harga_satuan"] * sales["jumlah_beli"]).abs()

    return sales


def print_business_summary(sales: pd.DataFrame) -> None:
    paid_sales = sales[
        (sales["status_pembayaran"] == "PAID") & (sales["jumlah_beli"] > 0)
    ].copy()
    refunded_sales = sales[sales["status_pembayaran"] == "REFUND"].copy()
    cancelled_sales = sales[sales["status_pembayaran"] == "CANCELLED"].copy()

    total_revenue = paid_sales["total_harga"].sum()
    category_summary = paid_sales.groupby("kategori", dropna=False).agg(
        total_unit_terjual=("jumlah_beli", "sum"),
        total_omzet=("total_harga", "sum"),
    )
    city_summary = paid_sales.groupby("kota_pembeli", dropna=False)[
        "total_harga"
    ].sum()
    returned_units = refunded_sales["jumlah_beli"].abs().sum()
    refunded_total = refunded_sales["total_harga"].sum()
    cancelled_total = cancelled_sales["total_harga"].sum()
    unsuccessful_sales = pd.concat([refunded_sales, cancelled_sales])

    print(f"Total Revenue Bersih: Rp {total_revenue:,.0f}".replace(",", "."))
    if category_summary.empty:
        print("Kategori Produk Paling Laris: Tidak ada transaksi valid")
    else:
        top_units = category_summary["total_unit_terjual"].idxmax()
        top_revenue = category_summary["total_omzet"].idxmax()
        print(
            "Kategori Produk Paling Laris (unit): "
            f"{top_units} ({category_summary.loc[top_units, 'total_unit_terjual']} unit)"
        )
        print(
            "Kategori Produk Paling Laris (omzet): "
            f"{top_revenue} (Rp {category_summary.loc[top_revenue, 'total_omzet']:,.0f})"
            .replace(",", ".")
        )

    if city_summary.empty:
        print("Kota dengan pengeluaran belanja tertinggi: Tidak ada transaksi valid")
    else:
        top_city = city_summary.idxmax()
        print(
            "Kota dengan pengeluaran belanja tertinggi: "
            f"{top_city} (Rp {city_summary.loc[top_city]:,.0f})".replace(",", ".")
        )

    print(
        "Total Potensi Kerugian/Retur (REFUND): "
        f"{returned_units} unit, Rp {format_amount(refunded_total)}"
    )
    print(
        "Total Order Batal (CANCELLED): "
        f"{len(cancelled_sales)} transaksi, Rp {format_amount(cancelled_total)}"
    )
    if unsuccessful_sales.empty:
        print("Top 1 Produk Refund/Cancel: Tidak ada data")
    else:
        top_product = unsuccessful_sales["nama_produk"].value_counts().idxmax()
        top_product_count = unsuccessful_sales["nama_produk"].value_counts().max()
        print(
            "Top 1 Produk Refund/Cancel: "
            f"{top_product} ({top_product_count} transaksi)"
        )


def main() -> None:
    sales = clean_sales_data(INPUT_FILE)
    paid_sales = sales[
        (sales["status_pembayaran"] == "PAID") & (sales["jumlah_beli"] > 0)
    ].copy()
    refunded_sales = sales[sales["status_pembayaran"] == "REFUND"].copy()
    cancelled_sales = sales[sales["status_pembayaran"] == "CANCELLED"].copy()

    paid_sales.to_csv(PAID_OUTPUT_FILE, index=False)
    refunded_sales.to_csv(REFUNDED_OUTPUT_FILE, index=False)
    cancelled_sales.to_csv(CANCELLED_OUTPUT_FILE, index=False)
    print_business_summary(sales)
    print(f"Data PAID disimpan ke: {PAID_OUTPUT_FILE}")
    print(f"Data REFUND disimpan ke: {REFUNDED_OUTPUT_FILE}")
    print(f"Data CANCELLED disimpan ke: {CANCELLED_OUTPUT_FILE}")


if __name__ == "__main__":
    main()