import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity


def get_top_laptops_by_tmdb_rating(laptops_csv, ratings_csv,
                                     id_col='id_laptop', title_col='title', rating_col='user_rating'):
    # Загрузка ноутбуков
    laptops_df = pd.read_csv(laptops_csv)
    # Загрузка оценок
    ratings_df = pd.read_csv(ratings_csv)

    # Группируем по ноутбукам: средний рейтинг R и количество голосов v
    ratings_summary = ratings_df.groupby(id_col).agg({rating_col: ['mean', 'count']})
    ratings_summary.columns = ['R', 'v']
    ratings_summary = ratings_summary.reset_index()

    # Средний рейтинг по всем ноутбукам (C)
    C = ratings_summary['R'].mean()
    # 90-й перцентиль количества голосов (m)
    m = ratings_summary['v'].quantile(0.90)

    def weighted_rating(row, m=m, C=C):
        v, R = row['v'], row['R']
        return (v / (v + m)) * R + (m / (v + m)) * C

    ratings_summary['weighted_rating'] = ratings_summary.apply(weighted_rating, axis=1)

    # Оставляем ноутбуки с голосами >= m
    qualified = ratings_summary[ratings_summary['v'] >= m]

    # Объединяем с данными о ноутбуках
    top_laptops = qualified.merge(laptops_df[[id_col, title_col]].drop_duplicates(), on=id_col)

    top_10 = top_laptops.sort_values('weighted_rating', ascending=False).head(5)

    result = top_10[[title_col, 'weighted_rating', 'v', 'R']]
    print(result)
    return result

# Пример вызова:
# get_top_10_laptops_by_tmdb_rating('data/filled_laptops.csv', 'data/generated_ratings.csv')
def recommend_similar_laptops(csv_path, input_laptop_id, top_n=5):
    df = pd.read_csv(csv_path)
    features = ['price', 'SSD', 'RAM_GB', 'RAM_Type', 'Display_inch', 'Proc_Cores']

    # Предобработка признаков
    scaler = MinMaxScaler()
    df_scaled = df.copy()
    df_scaled[features] = scaler.fit_transform(df[features])

    laptop_id_to_idx = {laptop_id: idx for idx, laptop_id in enumerate(df_scaled['id_laptop'])}

    if input_laptop_id not in laptop_id_to_idx:
        print(f"Ноутбук с id {input_laptop_id} не найден в данных")
        return pd.DataFrame()

    feature_matrix = df_scaled[features].values
    laptop_idx = laptop_id_to_idx[input_laptop_id]

    target_features = feature_matrix[laptop_idx].reshape(1, -1)
    similarity_scores = cosine_similarity(feature_matrix, target_features).flatten()

    similarity_scores[laptop_idx] = -1  # исключить сам ноутбук
    similar_idx = similarity_scores.argsort()[-top_n:][::-1]

    recommended = df.iloc[similar_idx]
    return recommended[['title', 'price', 'SSD', 'RAM_GB', 'RAM_Type', 'Display_inch', 'Proc_Cores','id_laptop']]


def recommend_laptops_for_user(user_id, laptops_csv, ratings_csv, top_n=5):
    # Загрузка данных
    laptops = pd.read_csv(laptops_csv)
    ratings = pd.read_csv(ratings_csv)

    # Матрица предпочтений
    user_item = ratings.pivot(index='id_user', columns='id_laptop', values='user_rating').fillna(0)

    if user_id not in user_item.index:
        print("Пользователь не найден в данных.")
        return pd.DataFrame()

    # Считаем косинусную схожесть между пользователями
    user_sim_matrix = pd.DataFrame(
        cosine_similarity(user_item),
        index=user_item.index,
        columns=user_item.index
    )

    # Получаем оценки данного пользователя
    user_ratings = user_item.loc[user_id]

    # Находим пользователей, похожих на текущего
    sim_scores = user_sim_matrix[user_id]

    # Исключаем самих себя
    sim_scores = sim_scores.drop(user_id)

    # Вычисляем взвешенные оценки для ноутбуков, которые пользователь еще не оценил
    unrated_laptops = user_ratings[user_ratings == 0].index
    scores = {}
    for laptop in unrated_laptops:
        # Оценки ноутбука другими пользователями
        ratings_for_laptop = user_item[laptop]

        # Взвешенная сумма оценок
        numerator = (ratings_for_laptop * sim_scores).sum()
        denominator = sim_scores[ratings_for_laptop > 0].sum()

        if denominator > 0:
            scores[laptop] = numerator / denominator

    # Сортируем рекомендуемые ноутбуки по рейтингу
    recommended = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    recommended_ids = [r[0] for r in recommended]
    recommended_scores = [r[1] for r in recommended]

    # Формируем датафрейм с рекомендациями и названиями ноутбуков
    rec_df = laptops[laptops['id_laptop'].isin(recommended_ids)].copy()
    rec_df['predicted_rating'] = rec_df['id_laptop'].map(dict(zip(recommended_ids, recommended_scores)))
    rec_df = rec_df.sort_values('predicted_rating', ascending=False)

    return rec_df[['id_laptop', 'title', 'predicted_rating']]