import re
import pandas as pd

HEADER =  re.compile(
     r"(?:Lihat semua lowongan kerja)?\s*Lokasi(?P<lokasi>.*?)Industri(?P<industri>.*?)"
    r"Jenis pekerjaan(?P<tipe>.*?)Gaji(?P<gaji>.*?)Diposting\s*(?P<posting>.*?)"
    r"(?:Pelamar[^L]*?)?Lamaran Cepat\s*Simpan(?P<isi>.*)", re.S)
CUT_MARKERS = ["Pertanyaan dari perusahaan",
    "Profil perusahaan",
    "Selengkapnya tentang perusahaan ini",
    "Apa yang bisa saya dapatkan sebagai",
    "Laporkan iklan lowongan ini",
    "Laporkan lowongan kerja",
    "Hati-hatiJangan berikan",
    "Jelajahi Saran Karier"]

def parse_text0(t: str):
    m = HEADER.search(t)
    if not m:
        return None
    isi = m.group("isi")
    isi = re.sub(
        r"(?:Bagaimana Anda cocok|Info kecocokan keterampilan).*?(?:selengkapnya|Tampilkan semua)[\u2060\xa0\s]*", 
        "", 
        isi, 
        flags=re.S
    )
    cuts = [isi.find(x) for x in CUT_MARKERS if x in isi]
    if cuts:
        isi = isi[:min(cuts)]
    isi = re.sub(r"[\u2060\xa0]", " ", isi)
    isi = re.sub(r"\s+", " ", isi).strip()
    gaji = m.group("gaji").strip()
    return {
        "Industri": m.group("industri").strip(),
        "Gaji": None if "tidak ditampilkan" in gaji else gaji,
        "Deskripsi_lengkap": isi,
    }

def deep_clean_deskripsi(teks):
    if not isinstance(teks, str):
        return teks
        
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  
        "\U0001f300-\U0001f5ff"  
        "\U0001f680-\U0001f6ff"  
        "\U0001f900-\U0001f9ff"  
        "\u2600-\u26ff"          
        "\u2700-\u27bf"          
        "]+", flags=re.UNICODE)
    teks = emoji_pattern.sub(r'', teks)

    teks = re.sub(r'([a-z])([A-Z])', r'\1. \2', teks) 
    
    
    teks = re.sub(r'\.([a-zA-Z])', r'. \1', teks)
    teks = re.sub(r':([a-zA-Z])', r': \1', teks)
    

    teks = re.sub(r'\s+', ' ', teks).strip()
    return teks

def get_clean_data(file_csv):
    df = pd.read_csv(file_csv)

    df_bersih = df[['data', 'data2', 'data3', 'data9', 'item_page_link', 'text_0']].copy()
    df_bersih.columns = ['Posisi', 'Perusahaan', 'Lokasi', 'Tipe_Kerja', 'URL', 'teks_mentah']
    df_bersih = df_bersih.dropna(subset=['Posisi', 'teks_mentah'])
    
  
    parsed = df_bersih["teks_mentah"].map(parse_text0)
    gagal = parsed.isna().sum()
    if gagal:
        print(f"PERINGATAN: {gagal} baris gagal di-parse, dibuang")
        
   
    df_bersih = df_bersih[parsed.notna()].copy()
    df_bersih = df_bersih.join(pd.DataFrame(list(parsed.dropna()), index=df_bersih.index))
    
    
    df_bersih["Job_ID"] = df_bersih["URL"].str.extract(r"/job/(\d+)")[0]
    df_bersih["URL"] = "https://id.jobstreet.com/id/job/" + df_bersih["Job_ID"]
    
   
    df_bersih = df_bersih.dropna(subset=["Job_ID"]).drop_duplicates("Job_ID")
    df_bersih = df_bersih.drop(columns=["teks_mentah"])

    df_bersih["Deskripsi_lengkap"] = df_bersih["Deskripsi_lengkap"].apply(deep_clean_deskripsi)
    
    return df_bersih

if __name__ == "__main__":
    file_path = 'id-jobstreet-com-2026-10-05-2.csv'
    df_test =  get_clean_data(file_path)
    print(df_test.head(10))
    df_test.to_csv('jobstreet_cleaned_ready.csv', index=False)
    print("✅ File jobstreet_cleaned_ready.csv berhasil dibuat!")