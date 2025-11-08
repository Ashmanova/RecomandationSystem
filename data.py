import numpy as np
import pandas as pd
import seaborn as sns
import math
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import re
from sklearn.preprocessing import LabelEncoder


data_path= "data/laptops.csv"

def load_dataset(filepath):
    """Загрузка датасета из CSV и начальный обзор"""
    df = pd.read_csv(filepath)
    print(f"Датасет загружен, размер: {df.shape}")
    return df

def drop_columns(df, columns_to_drop, save_path=None):
    existing_cols = [col for col in columns_to_drop if col in df.columns]
    df_new = df.drop(columns=existing_cols)

    print(f"Удалены колонки: {existing_cols}")
    print(f"Новый размер датасета: {df_new.shape}")

    if save_path:
        df_new.to_csv(save_path, index=False)
        print(f"Новый датасет сохранен в файл: {save_path}")

    return df_new


def add_id_laptop_and_save(df, save_path=None):
    df['id_laptop'] = pd.factorize(df['title'])[0]
    print("Столбец 'id_laptop' добавлен.")
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")
    return df

def clean_price_column(df, price_col='price', save_path=None):
    def clean_price(price_str):
        if isinstance(price_str, str):
            num_str = re.sub(r'[^\d]', '', price_str)
            if num_str:
                return int(num_str)
        return None

    df[price_col] = df[price_col].apply(clean_price)

    print(f"Столбец '{price_col}' очищен.")
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")
    return df


def remove_duplicates(df, save_path=None):
    duplicates_count = df.duplicated().sum()
    print(f"Количество дубликатов до удаления: {duplicates_count}")

    df_cleaned = df.drop_duplicates()
    print(f"Новый размер датасета после удаления дубликатов: {df_cleaned.shape}")

    if save_path:
        df_cleaned.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df_cleaned


def process_ssd_column(df, ssd_col='SSD', save_path=None):
    def extract_ssd_size(ssd_val):
        if pd.isna(ssd_val):
            return 0
        ssd_str = str(ssd_val)
        matches = re.findall(r'(\d+)\s*TB\s*SSD|(\d+)\s*GB\s*SSD', ssd_str, flags=re.IGNORECASE)
        if not matches:
            return 0
        size_gb = 0
        for tb_val, gb_val in matches:
            if tb_val:
                size_gb += int(tb_val) * 1024
            elif gb_val:
                size_gb += int(gb_val)
        return size_gb

    df[ssd_col] = df[ssd_col].apply(extract_ssd_size)
    df = df[df[ssd_col] != 0]

    print(f"Обработка столбца '{ssd_col}' завершена. Размер после удаления SSD=0: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")
    return df

def process_ram_column(df, ram_col='RAM', save_path=None):
    def extract_ram_info(ram_val):
        if pd.isna(ram_val):
            return pd.Series([0, 'Unknown'])
        ram_str = str(ram_val)

        size_match = re.search(r'(\d+)\s*GB', ram_str, flags=re.IGNORECASE)
        size_gb = int(size_match.group(1)) if size_match else 0

        ram_types = ['DDR5', 'DDR4', 'DDR3', 'LPDDR5', 'LPDDR4X', 'LPDDR4', 'LPDDR3', 'Unified Memory']
        ram_type = 'Unknown'
        for t in ram_types:
            if t.lower() in ram_str.lower():
                ram_type = t
                break

        return pd.Series([size_gb, ram_type])

    df[['RAM_GB', 'RAM_Type']] = df[ram_col].apply(extract_ram_info)
    df = df[df['RAM_GB'] > 0]
    df = df.drop(columns=[ram_col])

    print(f"Обработка столбца '{ram_col}' завершена. Размер после удаления RAM=0: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df


def process_processor_column(df, proc_col='Processor', save_path=None):
    def extract_processor_info(proc_str):
        if pd.isna(proc_str):
            return pd.Series([None, None, None, None])
        proc = str(proc_str)

        manufacturer = None
        for m in ['Intel', 'AMD', 'Apple']:
            if m.lower() in proc.lower():
                manufacturer = m
                break

        series_match = re.search(r'(Core i[3579]|Ryzen \d|M\d+|Pentium|Celeron|Athlon)', proc, re.I)
        series = series_match.group(1) if series_match else None

        gen_match = re.search(r'(\d{1,2})(?:th|nd|rd|st)?\s*Gen', proc, re.I)
        generation = int(gen_match.group(1)) if gen_match else None

        cores_match = re.search(r'(Dual|Quad|Hexa|Octa|Single|Octo|Deca|Duo|Tetra|Hex|Oct|Deca) Core', proc, re.I)
        cores_map = {'Dual': 2, 'Duo': 2, 'Single': 1, 'Quad': 4, 'Tetra': 4, 'Hexa': 6, 'Hex': 6, 'Octa': 8, 'Octo': 8, 'Deca': 10}
        cores = None
        if cores_match:
            key = cores_match.group(1).capitalize()
            cores = cores_map.get(key)

        return pd.Series([manufacturer, series, generation, cores])

    df[['Proc_Manufacturer', 'Proc_Series', 'Proc_Generation', 'Proc_Cores']] = df[proc_col].apply(extract_processor_info)
    df = df.drop(columns=[proc_col])

    print(f"Обработка столбца '{proc_col}' завершена. Размер датасета: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df

def process_os_column(df, os_col='OS', save_path=None):
    def extract_os_info(os_str):
        if pd.isna(os_str):
            return pd.Series([None, None])
        os_desc = str(os_str).strip()

        # Дополнительное выравнивание похожих строк
        if os_desc == 'Windows 11 Operating System':
            os_desc = '64 bit Windows 11 Operating System'
        elif os_desc == 'Windows 10 Operating System':
            os_desc = '64 bit Windows 10 Operating System'

        bitness_match = re.search(r'(32|64) bit', os_desc, re.I)
        bitness = bitness_match.group(1) if bitness_match else None

        os_types = ['Windows', 'Mac OS', 'DOS', 'Chrome OS', 'Linux', 'Ubuntu']
        main_os = None
        for os_type in os_types:
            if os_type.lower() in os_desc.lower():
                main_os = os_type
                break
        if main_os is None:
            main_os = 'Other'

        return pd.Series([main_os, bitness])

    df[['OS_Name', 'OS_Bitness']] = df[os_col].apply(extract_os_info)
    df = df.drop(columns=[os_col])

    print(f"Обработка столбца '{os_col}' завершена. Размер датасета: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df


def process_display_column(df, display_col='Display', save_path=None):
    def extract_display_size(display_str):
        if pd.isna(display_str):
            return pd.Series([None, 0])
        display = str(display_str)

        match = re.search(r'(\d+(\.\d+)?)\s*inch', display, flags=re.IGNORECASE)
        size = float(match.group(1)) if match else None

        touchscreen = 1 if 'touchscreen' in display.lower() else 0

        return pd.Series([size, touchscreen])

    df[['Display_inch', 'Touchscreen']] = df[display_col].apply(extract_display_size)
    df['Touchscreen'] = df['Touchscreen'].astype(int)
    df = df.drop(columns=[display_col])

    # Удаляем строки с пропущенными значениями в столбце 'Display_inch'
    df = df.dropna(subset=['Display_inch'])

    print(f"Обработка столбца '{display_col}' завершена. Размер датасета: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df


def process_warranty_column(df, warranty_col='warranty', save_path=None):
    def extract_warranty_info(warranty_str):
        if pd.isna(warranty_str) or warranty_str.strip() == '':
            return pd.Series([0, 'Unknown'])

        warranty = str(warranty_str).lower()

        duration_match = re.search(r'(\d+)\s*year', warranty)
        duration_years = int(duration_match.group(1)) if duration_match else 0

        if 'onsite' in warranty:
            warranty_type = 'Onsite'
        elif 'international' in warranty:
            warranty_type = 'International'
        elif 'limited' in warranty:
            warranty_type = 'Limited'
        elif 'premium' in warranty:
            warranty_type = 'Premium Support'
        elif 'accidental' in warranty:
            warranty_type = 'Accidental Damage'
        else:
            warranty_type = 'Other'

        return pd.Series([duration_years, warranty_type])

    df[['Warranty_Years', 'Warranty_Type']] = df[warranty_col].apply(extract_warranty_info)
    df = df.drop(columns=[warranty_col])

    print(f"Обработка столбца '{warranty_col}' завершена. Размер датасета: {df.shape}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df

def label_encode_columns(df, categorical_cols, save_path=None):
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = df[col].astype(str)
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    print(f"Проведено кодирование столбцов: {categorical_cols}")
    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")
    return df, label_encoders


def fillna_with_mode(df, column, save_path=None):
    mode_value = df[column].mode()[0]
    df[column] = df[column].fillna(mode_value)
    print(f"Пропуски в колонке '{column}' заполнены значением моды: {mode_value}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Обновлённый датасет сохранён в файл: {save_path}")

    return df



if __name__ == "__main__":
    df = load_dataset(data_path)
    df = drop_columns(df, ['Unnamed: 0', 'discount'], save_path='data/drop_columns_laptops.csv')
    df = add_id_laptop_and_save(df, save_path='data/add_id_laptops.csv')
    df = clean_price_column(df, price_col='price', save_path='data/price_laptops.csv')
    df = remove_duplicates(df, save_path='data/cleaned_no_duplicates_laptops.csv')
    df = process_ssd_column(df, ssd_col='SSD', save_path='data/cleaned_ssd_laptops.csv')
    df = process_ram_column(df, ram_col='RAM', save_path='data/cleaned_ram_laptopes.csv')
    df = process_processor_column(df, proc_col='Processor', save_path='data/cleaned_processor_laptops.csv')
    df = process_os_column(df, os_col='OS', save_path='data/cleaned_os_laptops.csv')
    df = process_display_column(df, display_col='Display', save_path='data/cleaned_display_laptops.csv')
    df = process_warranty_column(df, warranty_col='warranty', save_path='data/cleaned_warranty_laptops.csv')
    categorical_cols = ['RAM_Type', 'Proc_Manufacturer', 'Proc_Series', 'OS_Name', 'Warranty_Type']
    df, encoders = label_encode_columns(df, categorical_cols, save_path='data/encoded_laptops.csv')
    df = fillna_with_mode(df, 'Proc_Cores', save_path='data/filled_laptops.csv')

   # Датасет для расчетов filled_laptops.csv
   # Для вывода информации о продукте cleaned_warranty_laptops.csv


