import pandas as pd
def get_clean_data(file_csv):

    df = pd.read_csv(file_csv)
    df_bersih = df[['data', 'data2', 'data3', 'data9', 'item_page_link', 'text_0']].copy()
    df_bersih.columns = ['Posisi', 'Perusahaan', 'Lokasi', 'Tipe_Kerja', 'URL', 'Deskripsi_lengkap']
    

    df_bersih = df_bersih.dropna()
    
    return df_bersih

if __name__ == "__main__":
    file_path = 'id-jobstreet-com-2026-10-05-2.csv'
    df_test =  get_clean_data(file_path)
    print(df_test.head(10))