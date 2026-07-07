# Retail Crisis & Recovery - Python Data Analytics

Proyek ini merupakan solusi teknis untuk "Hackathon Python DQLab" dengan tema Retail Crisis and Recovery.

Latar Belakang BisnisDQFresh Mart Retail, sebuah toko retail sukses, mengalami masalah serius berupa penurunan total nilai penjualan dalam 6 bulan terakhir. Strategi awal manajemen untuk bertahan dengan mempertahankan produk bestseller, memperbesar stok historis terbaik, dan menekan risiko inventaris ternyata tidak membuahkan hasil. 

Melalui investigasi data transaksi secara mendalam, ditemukan adanya anomali: terdapat beberapa produk tidak kasat mata (Rising Star) yang menunjukkan pertumbuhan penjualan konsisten, namun luput dari sistem karena kontribusi revenue totalnya yang masih tergolong kecil dan stoknya sering habis.

Tujuan Proyek

Proyek ini dibuat menggunakan skrip Python (solusi-retail.py) untuk mengotomatisasi temuan tersebut dengan tujuan:  
- Mengidentifikasi Produk Rising Star: Menemukan produk tersembunyi yang memiliki tren kenaikan penjualan secara konsisten.  
- Membangun Strategi Potential Packaging: Menemukan kombinasi produk (frequent itemset) yang sering dibeli bersamaan dengan produk Rising Star untuk keperluan strategi bundling, promo paket, atau cross-selling.

Metodologi Analisis

- Identifikasi Tren (Smoothing & Growth): Menggunakan perhitungan Moving Average (MA) 3 hari berdasarkan hari transaksi aktif untuk meminimalkan fluktuasi harian. Produk disaring berdasarkan tren kenaikan nilai MA secara konsisten minimal selama 12 hari transaksi berturut-turut. Persentase pertumbuhan dihitung menggunakan perbandingan antara nilai MA pada titik akhir dan titik awal dari sesi tren kenaikan terpanjang tersebut.
- Market Basket Analysis: Menerapkan algoritma Apriori untuk mencari asosiasi produk dalam keranjang belanja. Aturan (rules) disaring dengan syarat minimal support 1% (0.01), metrik lift minimal 2, dan diwajibkan memuat setidaknya satu produk Rising Star di dalam kombinasinya untuk menemukan peluang paket penjualan yang saling menguntungkan.

Tech Stack & Library

Proyek ini dikembangkan menggunakan Python versi 3.10-3.14 dengan memanfaatkan library berikut:  
- Pandas (v2.3.1): Untuk manipulasi dan pengolahan data transaksi.  
- Matplotlib (v3.10.7): Untuk pembuatan visualisasi data.  
- Mlxtend (v0.23.4): Untuk implementasi algoritma Apriori (association rules).  
- Openpyxl (v3.1.5): Untuk mengekspor hasil analisis data ke dalam format Excel.

Output Proyek

Menjalankan skrip akan secara otomatis menghasilkan tiga output analisis di dalam folder kerja:  
1. retail_insight.xlsx: File laporan Excel yang memuat daftar metrik produk Rising Star dan rekomendasi aturan Potential Packaging (diurutkan berdasarkan Lift, Support, lalu Confidence).  
2. rising_star_index.png: Visualisasi perbandingan kecepatan pertumbuhan (indeks Base 100) antara seluruh produk Rising Star dengan Top 3 produk penyumbang penjualan.  
3. rising_star_actual.png: Visualisasi yang menampilkan nilai penjualan aktual dari produk Rising Star terhadap Top 3 produk.  