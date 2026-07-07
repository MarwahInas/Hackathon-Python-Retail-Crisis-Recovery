import sys
import matplotlib
import pandas as pd
import mlxtend
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)


"""# Analysis Data"""

print("===== Memuat data penjualan =====")

df = pd.read_excel('data_penjualan.xlsx')

# Cek data
df['tgl_transaksi'] = pd.to_datetime(df['tgl_transaksi'])
df['jumlah_terjual'] = pd.to_numeric(df['jumlah_terjual'], errors='coerce')
df['harga']          = pd.to_numeric(df['harga'],          errors='coerce')
df['total_nilai']    = pd.to_numeric(df['total_nilai'],    errors='coerce')

print(
    f"Data berhasil dimuat: {len(df)} baris, "
    f"periode {df['tgl_transaksi'].min().date()} "
    f"s/d {df['tgl_transaksi'].max().date()}"
)

df.head()

# Menghitung Moving Average
daily_df = (
    df.groupby(['tgl_transaksi', 'kode_produk', 'nama_produk'])['total_nilai']
      .sum()
      .reset_index()
      .sort_values(['kode_produk', 'tgl_transaksi'])
      .reset_index(drop=True)
)

daily_df['MA'] = (
    daily_df.groupby('kode_produk')['total_nilai']
            .transform(lambda x: x.rolling(window=3).mean())
)

# Identifikasi Tren Naik dan Consecutive Days

daily_df['MA_prev'] = daily_df.groupby('kode_produk')['MA'].shift(1)
daily_df['is_rising'] = daily_df['MA'] > daily_df['MA_prev']


def count_consecutive(series):
    """Hitung streak consecutive True secara berurutan."""
    result = []
    count  = 0
    for val in series:
        count = count + 1 if val else 0
        result.append(count)
    return result


daily_df['consec_rising'] = (
    daily_df.groupby('kode_produk')['is_rising']
            .transform(count_consecutive)
)

max_consec = (
    daily_df.groupby('kode_produk')['consec_rising']
            .max()
            .reset_index()
            .rename(columns={'consec_rising': 'max_consec_rising'})
)



# Filter Rising Star

rising_star_codes = (
    max_consec[max_consec['max_consec_rising'] >= 12]['kode_produk'].tolist()
)
print(f"Ditemukan {len(rising_star_codes)} produk Rising Star: {rising_star_codes}\n")


# Hitung Growth %

rising_df = daily_df[daily_df['kode_produk'].isin(rising_star_codes)].copy()


def cari_sesi_tren_terpanjang(group):
    group = group.sort_values('tgl_transaksi').reset_index(drop=True)
    max_streak = group['consec_rising'].max()

    # Cari posisi akhir streak
    idx_akhir = group[group['consec_rising'] == max_streak].index[0]

    # KUNCI FINAL: Titik AWAL tren adalah hari pertama Sesi Kenaikan (saat consec == 1)
    # Mundur sejauh (max_streak - 1) langkah dari titik akhir
    idx_awal = idx_akhir - (max_streak - 1)

    # Safety check agar tidak keluar dari index 0
    idx_awal = max(idx_awal, 0)

    return group.loc[idx_awal, 'MA'], group.loc[idx_akhir, 'MA']

growth_list = []
for kode, group in rising_df.groupby('kode_produk'):
    group      = group.sort_values('tgl_transaksi')
    nama       = group['nama_produk'].iloc[0]
    total_penj = group['total_nilai'].sum()

    ma_awal, ma_akhir = cari_sesi_tren_terpanjang(group)

    growth_pct = ((ma_akhir / ma_awal) - 1) * 100 if ma_awal and ma_awal != 0 else 0.0

    growth_list.append({
        'kode_produk'    : kode,
        'nama_produk'    : nama,
        'Growth_Pct'     : round(growth_pct, 2),   # angka, untuk sort & plot
        'Growth_Pct_Str' : f"{round(growth_pct, 2)}%",  # string tampilan
        'Total_Penjualan': round(total_penj, 2)
    })

final_report_full = (
    pd.DataFrame(growth_list)
      .sort_values('Growth_Pct', ascending=False)
      .reset_index(drop=True)
)

# Versi untuk export Excel: Growth ditampilkan sebagai string persen
final_report = final_report_full[[
    'kode_produk', 'nama_produk', 'Growth_Pct', 'Total_Penjualan'
]].rename(columns={
    'kode_produk'     : 'Kode Produk',
    'nama_produk'     : 'Nama Produk',
    'Growth_Pct'      : 'Growth %',
    'Total_Penjualan' : 'Total Penjualan'
})

print(final_report.to_string(index=False))

# Potential Packaging - Apriori Association rules


basket = (
    df.groupby('nomor_struk')['nama_produk']
      .apply(list)
      .reset_index()
)
transactions = basket['nama_produk'].tolist()

te        = TransactionEncoder()
te_arr    = te.fit(transactions).transform(transactions)
basket_df = pd.DataFrame(te_arr, columns=te.columns_)

# Apriori: min_support 0.01 (1%)
frequent_itemsets = apriori(
    basket_df,
    min_support=0.01,
    use_colnames=True
)

# Association rules: lift ≥ 1, min_threshold = 1
rules = association_rules(
    frequent_itemsets,
    metric='lift',
    min_threshold=1
)

# Filter: salah satu sisi mengandung Rising Star & lift ≥ 2
rising_names = (
    daily_df[daily_df['kode_produk'].isin(rising_star_codes)]['nama_produk']
    .unique()
    .tolist()
)


def contains_rising(itemset):
    return any(item in rising_names for item in itemset)


rules['has_rising'] = (
    rules['antecedents'].apply(contains_rising) |
    rules['consequents'].apply(contains_rising)
)

rules_filtered = (
    rules[(rules['has_rising']) & (rules['lift'] >= 2)]
    .copy()
    .sort_values(by=['lift', 'support', 'confidence'], ascending=False)
    .reset_index(drop=True)
)

rules_filtered['antecedents_str'] = rules_filtered['antecedents'].apply(
    lambda x: ', '.join(sorted(x))
)
rules_filtered['consequents_str'] = rules_filtered['consequents'].apply(
    lambda x: ', '.join(sorted(x))
)

# Hitung Jumlah_Invoice & bangun packaging_out secara eksplisit
'''

rows_packaging = []

for _, row in rules_filtered.iterrows():

    ant_items  = list(row['antecedents'])

    con_items  = list(row['consequents'])

    all_items  = ant_items + con_items

    valid_items = [item for item in all_items if item in basket_df.columns]

    jumlah_inv  = int(basket_df[valid_items].all(axis=1).sum()) if valid_items else 0



    rows_packaging.append({

        'Jika Membeli'  : ', '.join(sorted(ant_items, reverse=True)),

        'Maka Membeli'  : ', '.join(sorted(con_items, reverse=True)),

        'Jumlah Invoice': jumlah_inv, 

        'Support'       : round(float(row['support']),    2),

        'Confidence'    : round(float(row['confidence']), 2),

        'Lift'          : round(float(row['lift']),       2),

    })



# Pastikan di saat membuat DataFrame juga menggunakan spasi kosong

packaging_out = pd.DataFrame(rows_packaging, columns=[

    'Jika Membeli', 'Maka Membeli', 'Jumlah Invoice', 'Support', 'Confidence', 'Lift'

])

'''

# Hitung Jumlah_Invoice & bangun packaging_out secara eksplisit
rows_packaging = []
for _, row in rules_filtered.iterrows():
    # Konversi dari frozenset ke list
    ant_items  = list(row['antecedents'])
    con_items  = list(row['consequents'])
    
    all_items  = ant_items + con_items
    valid_items = [item for item in all_items if item in basket_df.columns]
    jumlah_inv  = int(basket_df[valid_items].all(axis=1).sum()) if valid_items else 0

    # KUNCI PERBAIKAN FINAL: HAPUS fungsi sorted() sepenuhnya!
    # Biarkan Python merangkai teks sesuai urutan bawaan frozenset algoritma
    ant_str = ', '.join(ant_items)
    con_str = ', '.join(con_items)

    rows_packaging.append({
        'Jika Membeli'  : ant_str,
        'Maka Membeli'  : con_str,
        'Jumlah Invoice': jumlah_inv,
        'Support'       : round(float(row['support']),    2),
        'Confidence'    : round(float(row['confidence']), 2),
        'Lift'          : round(float(row['lift']),       2),
    })

# Pastikan menggunakan spasi kosong untuk 'Jumlah Invoice'
packaging_out = pd.DataFrame(rows_packaging, columns=[
    'Jika Membeli', 'Maka Membeli', 'Jumlah Invoice', 'Support', 'Confidence', 'Lift'
])

print(f"  Ditemukan {len(packaging_out)} association rules (lift ≥ 2, ada rising star).")

#Menyimpan final file retail_insight

with pd.ExcelWriter('retail_insight.xlsx', engine='openpyxl') as writer:
    final_report.to_excel(writer, sheet_name='Rising Star',         index=False)
    packaging_out.to_excel(writer, sheet_name='Potential Packaging', index=False)

print("  retail_insight.xlsx berhasil disimpan.")

"""# Plot Graph"""

# Persiapan plot

# Urutkan berdasarkan growth
sorted_report = final_report_full.sort_values(by='Growth_Pct', ascending=False)

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

color_mapping = {}
rank_mapping  = {}

for i, row in enumerate(sorted_report.itertuples()):
    kode_produk = row.kode_produk
    color_mapping[kode_produk] = (
        custom_palette[i] if i < len(custom_palette) else default_color
    )
    rank_mapping[kode_produk] = i + 1

# Top 3 produk berdasarkan total penjualan
top3_sales = (
    df.groupby(['kode_produk', 'nama_produk'])['total_nilai']
      .sum()
      .reset_index()
      .sort_values(by='total_nilai', ascending=False)
      .head(3)
)
top3_codes   = top3_sales['kode_produk'].tolist()
top3_plot_df = daily_df[daily_df['kode_produk'].isin(top3_codes)].copy()

grey_colors  = ['#B0B0B0', '#909090', '#707070']

font_title = {'family': 'sans-serif', 'color': 'black', 'weight': 'bold', 'size': 16}
font_label = {'family': 'sans-serif', 'weight': 'normal', 'size': 12}

# Visualisasi Rising Star Index

if len(rising_star_codes) > 0:

    def normalize_base100(group):
        group = group.copy()
        # Ambil nilai MA pertama yang valid (bukan NaN)
        valid_ma = group['MA'].dropna()
        first_ma = valid_ma.iloc[0] if not valid_ma.empty else 0
        
        group['Normalized'] = (group['MA'] / first_ma * 100) if first_ma != 0 else 100.0
        return group

    plot_df = (
        rising_df.groupby('kode_produk', group_keys=False)
                 .apply(normalize_base100)
    )

    # Normalisasi Base 100 untuk top 3
    def normalize_top3(group):
        group = group.copy()
        # Ambil nilai MA pertama yang valid (bukan NaN)
        valid_ma = group['MA'].dropna()
        first_ma = valid_ma.iloc[0] if not valid_ma.empty else 0
        
        group['Normalized'] = (group['MA'] / first_ma * 100) if first_ma != 0 else 100.0
        return group

    top3_norm_df = (
        top3_plot_df.groupby('kode_produk', group_keys=False)
                    .apply(normalize_top3)
    )

    # Figure
    fig = plt.figure(figsize=(15, 8), dpi=100)
    ax  = fig.add_subplot(111)

    # Plot Top 3 Sales (abu-abu, dashed)
    for idx, (kode_produk, group) in enumerate(
        top3_norm_df.groupby('kode_produk')
    ):
        nama_produk = group['nama_produk'].iloc[0]
        grey_color  = grey_colors[idx] if idx < len(grey_colors) else '#808080'
        ax.plot(
            group['tgl_transaksi'], group['Normalized'],
            linestyle='--', linewidth=2, marker='o', markersize=3,
            color=grey_color, alpha=0.7,
            label=f"Top Sales: {nama_produk}"
        )

    # Plot Rising Star
    for kode_produk, group in plot_df.groupby('kode_produk'):
        nama_produk     = group['nama_produk'].iloc[0]
        line_color      = color_mapping.get(kode_produk, default_color)
        rank            = rank_mapping.get(kode_produk, '?')
        label_with_rank = f"Rank {rank}: {nama_produk}"
        ax.plot(
            group['tgl_transaksi'], group['Normalized'],
            marker='o', markersize=4, linewidth=2.5,
            color=line_color, label=label_with_rank
        )

    ax.set_title(
        'ANALISIS PERTUMBUHAN RELATIF PRODUK RISING STAR\n'
        '(Dengan Benchmark Top 3 Total Penjualan)',
        fontdict=font_title, pad=20
    )
    ax.set_xlabel('Periode Tanggal',             fontdict=font_label, labelpad=10)
    ax.set_ylabel('Indeks Pertumbuhan (Base 100)', fontdict=font_label, labelpad=10)

    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.axhline(y=100, color='black', linestyle='-', linewidth=1, alpha=0.5)

    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    # Sort legend
    handles, labels = ax.get_legend_handles_labels()
    top_sales_items, rising_items = [], []
    for h, l in zip(handles, labels):
        (top_sales_items if l.startswith('Top Sales') else rising_items).append((h, l))
    rising_items = sorted(rising_items, key=lambda x: int(x[1].split(':')[0].split()[1]))
    final_legend = top_sales_items + rising_items

    ax.legend(
        [x[0] for x in final_legend], [x[1] for x in final_legend],
        title='Kategori Produk', title_fontsize=12, fontsize=10,
        bbox_to_anchor=(1.02, 1), loc='upper left',
        borderaxespad=0, frameon=True, shadow=True
    )

    plt.tight_layout()
    plt.savefig('rising_star_index.png', bbox_inches='tight')
    plt.close(fig)
    print("  rising_star_index.png berhasil disimpan.")

else:
    print("  Tidak ada Rising Star, grafik index dilewati.")

# Visualisasi Rising Star Actual

if len(rising_star_codes) > 0:

    fig2 = plt.figure(figsize=(15, 8), dpi=100)
    ax2  = fig2.add_subplot(111)

    # Plot Top 3 Sales (nilai asli)
    for idx, (kode_produk, group) in enumerate(
        top3_plot_df.groupby('kode_produk')
    ):
        nama_produk = group['nama_produk'].iloc[0]
        grey_color  = grey_colors[idx] if idx < len(grey_colors) else '#808080'
        ax2.plot(
            group['tgl_transaksi'], group['total_nilai'],
            linestyle='--', linewidth=2, marker='o', markersize=3,
            color=grey_color, alpha=0.7,
            label=f"Top Sales: {nama_produk}"
        )

    # Plot Rising Star (nilai asli)
    for kode_produk, group in plot_df.groupby('kode_produk'):
        nama_produk     = group['nama_produk'].iloc[0]
        line_color      = color_mapping.get(kode_produk, default_color)
        rank            = rank_mapping.get(kode_produk, '?')
        label_with_rank = f"Rank {rank}: {nama_produk}"
        ax2.plot(
            group['tgl_transaksi'], group['total_nilai'],
            marker='o', markersize=4, linewidth=2.5,
            color=line_color, label=label_with_rank
        )

    ax2.set_title(
        'ANALISIS NILAI PENJUALAN PRODUK RISING STAR\n'
        '(Nilai Penjualan Asli)',
        fontdict=font_title, pad=20
    )
    ax2.set_xlabel('Periode Tanggal',      fontdict=font_label, labelpad=10)
    ax2.set_ylabel('Total Nilai Penjualan', fontdict=font_label, labelpad=10)

    ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)

    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    # Sort legend
    handles2, labels2 = ax2.get_legend_handles_labels()
    top_sales_items2, rising_items2 = [], []
    for h, l in zip(handles2, labels2):
        (top_sales_items2 if l.startswith('Top Sales') else rising_items2).append((h, l))
    rising_items2 = sorted(rising_items2, key=lambda x: int(x[1].split(':')[0].split()[1]))
    final_legend2 = top_sales_items2 + rising_items2

    ax2.legend(
        [x[0] for x in final_legend2], [x[1] for x in final_legend2],
        title='Kategori Produk', title_fontsize=12, fontsize=10,
        bbox_to_anchor=(1.02, 1), loc='upper left',
        borderaxespad=0, frameon=True, shadow=True
    )

    plt.tight_layout()
    plt.savefig('rising_star_actual.png', bbox_inches='tight')
    plt.close(fig2)
    print("  rising_star_actual.png berhasil disimpan.")

else:
    print("  Tidak ada Rising Star, grafik nilai asli dilewati.")
