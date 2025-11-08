import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_and_save_correlation_matrix(df, exclude_cols=None, save_dir='data', save_filename='pearson_correlation.csv'):
    if exclude_cols is None:
        exclude_cols = ['title', 'id_laptop']

    cols_to_use = [col for col in df.columns if col not in exclude_cols]
    print(df[cols_to_use].select_dtypes(include='number'))

    df_sub = df[cols_to_use].select_dtypes(include='number')

    # Заполнение пропусков средними значениями по столбцам
    df_sub = df_sub.fillna(df_sub.mean(numeric_only=True))

    corr_matrix = df_sub.corr(method='pearson')

    # Создаем папку для сохранения, если не существует
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, save_filename)
    corr_matrix.to_csv(save_path)
    print(f"Корреляционная матрица сохранена в файл: {save_path}")

    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm')
    plt.title('Корреляционная матрица признаков (Пирсон)')
    plt.show()


if __name__ == "__main__":
    df = pd.read_csv('data/filled_laptops.csv')
    plot_and_save_correlation_matrix(df)
