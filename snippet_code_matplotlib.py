    # ============================================================
    # A. SPESIFIKASI FIGURE
    # ============================================================
    fig = plt.figure(figsize=(15, 8), dpi=100)
    ax = fig.add_subplot(111)

    # ============================================================
    # B. PENGATURAN WARNA CUSTOM BERDASARKAN PERINGKAT
    # ============================================================

    # Urutkan berdasarkan growth tertinggi
    sorted_report = final_report.sort_values(
        by='Growth_Pct',
        ascending=False
    )

    # Palet warna custom
    custom_palette = [
        '#FFD700',  # Gold
        '#C0C0C0',  # Silver
        '#CD7F32',  # Bronze
        '#2ecc71',  # Emerald Green
        '#3498db',  # Blue
        '#9b59b6',  # Purple
        '#e74c3c',  # Red
        '#34495e',  # Dark Blue Grey
    ]

    default_color = '#95a5a6'

    # Mapping warna & ranking
    color_mapping = {}
    rank_mapping = {}

    for i, row in enumerate(sorted_report.itertuples()):

        kode_produk = row.kode_produk

        color_mapping[kode_produk] = (
            custom_palette[i]
            if i < len(custom_palette)
            else default_color
        )

        rank_mapping[kode_produk] = i + 1

    # ============================================================
    # C. TOP 3 PRODUK BERDASARKAN TOTAL PENJUALAN
    # ============================================================

    top3_sales = (
        df.groupby(['kode_produk', 'nama_produk'])['total_nilai']
          .sum()
          .reset_index()
          .sort_values(by='total_nilai', ascending=False)
          .head(3)
    )

    top3_codes = top3_sales['kode_produk'].tolist()

    top3_plot_df = daily_df[
        daily_df['kode_produk'].isin(top3_codes)
    ].copy()

    # ============================================================
    # D. PLOT TOP 3 SALES (ABU-ABU)
    # ============================================================

    grey_colors = [
        '#B0B0B0',
        '#909090',
        '#707070'
    ]

    for idx, (kode_produk, group) in enumerate(
        top3_plot_df.groupby('kode_produk')
    ):

        nama_produk = group['nama_produk'].iloc[0]

        grey_color = (
            grey_colors[idx]
            if idx < len(grey_colors)
            else '#808080'
        )

        ax.plot(
            group['tgl_transaksi'],
            group['Normalized'],
            linestyle='--',
            linewidth=2,
            marker='o',
            markersize=3,
            color=grey_color,
            alpha=0.7,
            label=f"Top Sales: {nama_produk}"
        )

    # ============================================================
    # E. PLOT RISING STAR
    # ============================================================

    for kode_produk, group in plot_df.groupby('kode_produk'):

        nama_produk = group['nama_produk'].iloc[0]

        line_color = color_mapping.get(
            kode_produk,
            default_color
        )

        rank = rank_mapping.get(
            kode_produk,
            '?'
        )

        label_with_rank = f"Rank {rank}: {nama_produk}"

        ax.plot(
            group['tgl_transaksi'],
            group['Normalized'],
            marker='o',
            markersize=4,
            linewidth=2.5,
            color=line_color,
            label=label_with_rank
        )

    # ============================================================
    # F. TITLE & LABEL
    # ============================================================

    font_title = {
        'family': 'sans-serif',
        'color': 'black',
        'weight': 'bold',
        'size': 16
    }

    font_label = {
        'family': 'sans-serif',
        'weight': 'normal',
        'size': 12
    }

    ax.set_title(
        'ANALISIS PERTUMBUHAN RELATIF PRODUK RISING STAR\n'
        '(Dengan Benchmark Top 3 Total Penjualan)',
        fontdict=font_title,
        pad=20
    )

    ax.set_xlabel(
        'Periode Tanggal',
        fontdict=font_label,
        labelpad=10
    )

    ax.set_ylabel(
        'Indeks Pertumbuhan (Base 100)',
        fontdict=font_label,
        labelpad=10
    )

    # ============================================================
    # G. GRID & BASELINE
    # ============================================================

    ax.grid(
        True,
        linestyle='--',
        linewidth=0.5,
        alpha=0.5
    )

    ax.axhline(
        y=100,
        color='black',
        linestyle='-',
        linewidth=1,
        alpha=0.5
    )

    # ============================================================
    # H. FORMAT AXIS
    # ============================================================

    plt.xticks(
        rotation=45,
        ha='right',
        fontsize=10
    )

    plt.yticks(fontsize=10)

    # ============================================================
    # I. SORT LEGEND BERDASARKAN RANK
    # ============================================================

    handles, labels = ax.get_legend_handles_labels()

    # Pisahkan Top Sales & Rising Star
    top_sales_items = []
    rising_items = []

    for h, l in zip(handles, labels):

        if l.startswith('Top Sales'):
            top_sales_items.append((h, l))
        else:
            rising_items.append((h, l))

    # Sort rising star berdasarkan ranking
    rising_items = sorted(
        rising_items,
        key=lambda x: int(
            x[1].split(':')[0].split()[1]
        )
    )

    # Gabungkan kembali
    final_legend = top_sales_items + rising_items

    final_handles = [x[0] for x in final_legend]
    final_labels = [x[1] for x in final_legend]

    # ============================================================
    # J. LEGEND
    # ============================================================

    ax.legend(
        final_handles,
        final_labels,
        title="Kategori Produk",
        title_fontsize=12,
        fontsize=10,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0,
        frameon=True,
        shadow=True
    )

    # ============================================================
    # K. LAYOUT & SAVE
    # ============================================================

    plt.tight_layout()

    plt.savefig(
        'analisis_rising_star_ranked_colors.png',
        bbox_inches='tight'
    )

    print(
        "\nGrafik detail disimpan sebagai "
        "'analisis_rising_star_ranked_colors.png'"
    )

    # plt.show()

else:

    print(
        "\nTidak ada data untuk di-plot "
        "(mungkin tidak ada produk memenuhi kriteria)."
    )
    

# ============================================================
# 9. VISUALISASI NILAI PENJUALAN ASLI
# ============================================================

fig2 = plt.figure(figsize=(15, 8), dpi=100)
ax2 = fig2.add_subplot(111)

# ============================================================
# A. PLOT TOP 3 SALES
# ============================================================

for idx, (kode_produk, group) in enumerate(
    top3_plot_df.groupby('kode_produk')
):

    nama_produk = group['nama_produk'].iloc[0]

    grey_color = (
        grey_colors[idx]
        if idx < len(grey_colors)
        else '#808080'
    )

    ax2.plot(
        group['tgl_transaksi'],
        group['total_nilai'],
        linestyle='--',
        linewidth=2,
        marker='o',
        markersize=3,
        color=grey_color,
        alpha=0.7,
        label=f"Top Sales: {nama_produk}"
    )

# ============================================================
# B. PLOT RISING STAR BERDASARKAN NILAI ASLI
# ============================================================

for kode_produk, group in plot_df.groupby('kode_produk'):

    nama_produk = group['nama_produk'].iloc[0]

    line_color = color_mapping.get(
        kode_produk,
        default_color
    )

    rank = rank_mapping.get(
        kode_produk,
        '?'
    )

    label_with_rank = f"Rank {rank}: {nama_produk}"

    ax2.plot(
        group['tgl_transaksi'],
        group['total_nilai'],
        marker='o',
        markersize=4,
        linewidth=2.5,
        color=line_color,
        label=label_with_rank
    )

# ============================================================
# C. TITLE & LABEL
# ============================================================

ax2.set_title(
    'ANALISIS NILAI PENJUALAN PRODUK RISING STAR\n'
    '(Nilai Penjualan Asli)',
    fontdict=font_title,
    pad=20
)

ax2.set_xlabel(
    'Periode Tanggal',
    fontdict=font_label,
    labelpad=10
)

ax2.set_ylabel(
    'Total Nilai Penjualan',
    fontdict=font_label,
    labelpad=10
)

# ============================================================
# D. GRID
# ============================================================

ax2.grid(
    True,
    linestyle='--',
    linewidth=0.5,
    alpha=0.5
)

# ============================================================
# E. FORMAT AXIS
# ============================================================

plt.xticks(
    rotation=45,
    ha='right',
    fontsize=10
)

plt.yticks(fontsize=10)

# ============================================================
# F. SORT LEGEND
# ============================================================

handles2, labels2 = ax2.get_legend_handles_labels()

top_sales_items2 = []
rising_items2 = []

for h, l in zip(handles2, labels2):

    if l.startswith('Top Sales'):
        top_sales_items2.append((h, l))
    else:
        rising_items2.append((h, l))

rising_items2 = sorted(
    rising_items2,
    key=lambda x: int(
        x[1].split(':')[0].split()[1]
    )
)

final_legend2 = top_sales_items2 + rising_items2

final_handles2 = [x[0] for x in final_legend2]
final_labels2 = [x[1] for x in final_legend2]

# ============================================================
# G. LEGEND
# ============================================================

ax2.legend(
    final_handles2,
    final_labels2,
    title="Kategori Produk",
    title_fontsize=12,
    fontsize=10,
    bbox_to_anchor=(1.02, 1),
    loc='upper left',
    borderaxespad=0,
    frameon=True,
    shadow=True
)

# ============================================================
# H. LAYOUT & SAVE
# ============================================================

plt.tight_layout()

plt.savefig(
    'analisis_rising_star_actual_sales.png',
    bbox_inches='tight'
)