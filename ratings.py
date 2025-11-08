import random
import pandas as pd

# Настройка параметров генерации
class RatingGenerationConfig:
    def __init__(self, num_ratings_per_product_range=(0, 80), ratings_weights=None, max_ratings_per_user=3):
        self.num_ratings_per_product_range = num_ratings_per_product_range
        self.ratings_weights = ratings_weights or [0.02, 0.08, 0.1, 0.15, 0.3, 0.35]
        self.max_ratings_per_user = max_ratings_per_user
        self.rating_values = [0, 1, 2, 3, 4, 5]

def generate_ratings_dataset(df, config, save_path=None):
    ratings_list = []

    num_products = df['id_laptop'].nunique()
    num_users = int(num_products * config.max_ratings_per_user)
    user_ids = list(range(num_users))

    # Track how many products each user has rated
    user_rated_counts = {user: 0 for user in user_ids}
    # Track which products each user has rated (to prevent multiple ratings for same product)
    user_rated_products = {user: set() for user in user_ids}

    for product_id in range(num_products):
        num_ratings = random.randint(*config.num_ratings_per_product_range)
        users_for_estimates = []

        # Only users who have not exceeded max ratings and haven't rated this product yet
        available_users = [user for user in user_ids
                           if user_rated_counts[user] < config.max_ratings_per_user and
                           product_id not in user_rated_products[user]]

        while len(users_for_estimates) < num_ratings and available_users:
            user = random.choice(available_users)
            users_for_estimates.append(user)
            user_rated_counts[user] += 1
            user_rated_products[user].add(product_id)
            # Update available users again
            available_users = [user for user in user_ids
                               if user_rated_counts[user] < config.max_ratings_per_user and
                               product_id not in user_rated_products[user]]

        for user in users_for_estimates:
            rating = random.choices(config.rating_values, weights=config.ratings_weights, k=1)[0]
            ratings_list.append({'id_laptop': product_id, 'id_user': user, 'user_rating': rating})

    ratings_df = pd.DataFrame(ratings_list)
    if save_path:
        ratings_df.to_csv(save_path, index=False)
        print(f"Рейтинги сохранены в файл: {save_path}")
    return ratings_df


def calculate_average_ratings_and_save(laptops_csv, ratings_csv, output_csv):
    laptops = pd.read_csv(laptops_csv)
    ratings = pd.read_csv(ratings_csv)

    # Группируем по id_laptop и считаем средний рейтинг
    avg_ratings = ratings.groupby('id_laptop')['user_rating'].mean().reset_index()
    avg_ratings.rename(columns={'user_rating': 'average_rating'}, inplace=True)

    # Объединяем данные ноутбуков с их средними рейтингами
    laptops_with_ratings = laptops.merge(avg_ratings, on='id_laptop', how='left')

    # Сохраняем результат в CSV
    laptops_with_ratings.to_csv(output_csv, index=False)

    return laptops_with_ratings

if __name__ == "__main__":
    df = pd.read_csv('data/filled_laptops.csv')
    config = RatingGenerationConfig()
    ratings = generate_ratings_dataset(df, config, save_path='data/generated_ratings.csv')
    result_df = calculate_average_ratings_and_save('data/filled_laptops.csv', 'data/generated_ratings.csv',
                                                   'data/laptops_with_avg_rating.csv')
