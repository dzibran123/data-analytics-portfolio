from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


PAID_FILE = Path("cleaned_sales_paid.csv")
CANCELLED_FILE = Path("sales_cancelled.csv")
REFUNDED_FILE = Path("sales_refunded.csv")
OUTPUT_FILE = Path("executive_sales_dashboard.html")

PAID_COLOR = "#168AAD"
CANCELLED_COLOR = "#6C757D"
REFUND_COLOR = "#E76F51"
TEXT_COLOR = "#24313A"


def format_rupiah(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


def load_sales_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paid = pd.read_csv(PAID_FILE)
    cancelled = pd.read_csv(CANCELLED_FILE)
    refunded = pd.read_csv(REFUNDED_FILE)

    for sales in (paid, cancelled, refunded):
        sales["total_harga"] = pd.to_numeric(
            sales["total_harga"], errors="coerce"
        ).abs()
        sales["jumlah_beli"] = pd.to_numeric(
            sales["jumlah_beli"], errors="coerce"
        )
        sales["tanggal_transaksi"] = pd.to_datetime(
            sales["tanggal_transaksi"], errors="coerce"
        )

    return paid, cancelled, refunded


def add_kpi_card(
    figure: go.Figure,
    x0: float,
    x1: float,
    title: str,
    value: str,
    detail: str,
    color: str,
) -> None:
    figure.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=x0,
        x1=x1,
        y0=1.06,
        y1=1.22,
        line={"color": color, "width": 1.5},
        fillcolor="#FFFFFF",
    )
    figure.add_annotation(
        x=(x0 + x1) / 2,
        y=1.185,
        xref="paper",
        yref="paper",
        text=f"<b>{title}</b>",
        showarrow=False,
        font={"size": 13, "color": color},
    )
    figure.add_annotation(
        x=(x0 + x1) / 2,
        y=1.135,
        xref="paper",
        yref="paper",
        text=f"<b>{value}</b>",
        showarrow=False,
        font={"size": 20, "color": TEXT_COLOR},
    )
    figure.add_annotation(
        x=(x0 + x1) / 2,
        y=1.085,
        xref="paper",
        yref="paper",
        text=detail,
        showarrow=False,
        font={"size": 11, "color": "#5C6B73"},
    )


def build_dashboard(
    paid: pd.DataFrame,
    cancelled: pd.DataFrame,
    refunded: pd.DataFrame,
) -> go.Figure:
    status_totals = pd.Series(
        {
            "PAID": paid["total_harga"].sum(),
            "CANCELLED": cancelled["total_harga"].sum(),
            "REFUND": refunded["total_harga"].sum(),
        }
    )

    category_revenue = (
        paid.groupby("kategori", dropna=False)["total_harga"]
        .sum()
        .sort_values(ascending=True)
    )
    city_revenue = (
        paid.groupby("kota_pembeli", dropna=False)["total_harga"]
        .sum()
        .sort_values(ascending=False)
    )
    daily_revenue = (
        paid.dropna(subset=["tanggal_transaksi"])
        .groupby("tanggal_transaksi", as_index=False)["total_harga"]
        .sum()
        .sort_values("tanggal_transaksi")
    )

    figure = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}], [{"type": "xy"}, {"type": "xy"}]],
        subplot_titles=(
            "Proporsi Nilai Transaksi",
            "Revenue Bersih per Kategori",
            "Pengeluaran Belanja per Kota",
            "Tren Penjualan Harian",
        ),
        vertical_spacing=0.16,
        horizontal_spacing=0.12,
    )

    status_labels = ["PAID", "CANCELLED", "REFUND"]
    status_colors = [PAID_COLOR, CANCELLED_COLOR, REFUND_COLOR]
    status_hover = [format_rupiah(value) for value in status_totals]
    figure.add_trace(
        go.Pie(
            labels=status_labels,
            values=status_totals.tolist(),
            marker={"colors": status_colors, "line": {"color": "#FFFFFF", "width": 2}},
            hole=0.52,
            customdata=status_hover,
            textinfo="label+percent",
            hovertemplate="Status: %{label}<br>Nominal: %{customdata}<br>Proporsi: %{percent}<extra></extra>",
            sort=False,
        ),
        row=1,
        col=1,
    )

    category_values = category_revenue.tolist()
    figure.add_trace(
        go.Bar(
            x=category_values,
            y=category_revenue.index,
            orientation="h",
            marker_color=PAID_COLOR,
            customdata=[format_rupiah(value) for value in category_values],
            hovertemplate="Kategori: %{y}<br>Revenue: %{customdata}<extra></extra>",
            name="Revenue Kategori",
        ),
        row=1,
        col=2,
    )

    city_values = city_revenue.tolist()
    figure.add_trace(
        go.Bar(
            x=city_revenue.index,
            y=city_values,
            marker_color="#4C956C",
            customdata=[format_rupiah(value) for value in city_values],
            hovertemplate="Kota: %{x}<br>Revenue: %{customdata}<extra></extra>",
            name="Revenue Kota",
        ),
        row=2,
        col=1,
    )

    daily_values = daily_revenue["total_harga"].tolist()
    figure.add_trace(
        go.Scatter(
            x=daily_revenue["tanggal_transaksi"],
            y=daily_values,
            mode="lines+markers",
            line={"color": PAID_COLOR, "width": 3},
            marker={"color": PAID_COLOR, "size": 8},
            customdata=[format_rupiah(value) for value in daily_values],
            hovertemplate="Tanggal: %{x|%d %b %Y}<br>Revenue: %{customdata}<extra></extra>",
            name="Revenue Harian",
        ),
        row=2,
        col=2,
    )

    add_kpi_card(
        figure,
        0.02,
        0.32,
        "REVENUE BERSIH (PAID)",
        format_rupiah(status_totals["PAID"]),
        f"{len(paid):,} transaksi".replace(",", "."),
        PAID_COLOR,
    )
    add_kpi_card(
        figure,
        0.35,
        0.65,
        "ORDER BATAL (CANCELLED)",
        format_rupiah(status_totals["CANCELLED"]),
        f"{len(cancelled):,} transaksi".replace(",", "."),
        CANCELLED_COLOR,
    )
    add_kpi_card(
        figure,
        0.68,
        0.98,
        "RETUR / REFUND",
        format_rupiah(status_totals["REFUND"]),
        f"{refunded['jumlah_beli'].abs().sum():,.0f} unit".replace(",", "."),
        REFUND_COLOR,
    )

    figure.update_xaxes(title_text="Revenue (Rupiah)", row=1, col=2, tickformat=",.")
    figure.update_xaxes(title_text="Kota Pembeli", row=2, col=1)
    figure.update_xaxes(title_text="Tanggal Transaksi", row=2, col=2)
    figure.update_yaxes(title_text="Kategori", row=1, col=2)
    figure.update_yaxes(title_text="Revenue (Rupiah)", row=2, col=1, tickformat=",.")
    figure.update_yaxes(title_text="Revenue (Rupiah)", row=2, col=2, tickformat=",.")
    figure.update_layout(
        title={
            "text": "Executive Sales Dashboard",
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 28, "color": TEXT_COLOR},
        },
        template="plotly_white",
        height=900,
        margin={"l": 80, "r": 40, "t": 190, "b": 75},
        paper_bgcolor="#F5F7F8",
        plot_bgcolor="#FFFFFF",
        font={"family": "Arial, sans-serif", "color": TEXT_COLOR},
        showlegend=False,
    )
    return figure


def main() -> None:
    paid, cancelled, refunded = load_sales_data()
    figure = build_dashboard(paid, cancelled, refunded)
    figure.write_html(OUTPUT_FILE, full_html=True, include_plotlyjs=True)
    print(f"Dashboard berhasil disimpan ke: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()