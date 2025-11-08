import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from recomendation_system import (
    get_top_laptops_by_tmdb_rating,
    recommend_similar_laptops,
    recommend_laptops_for_user
)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Приложение ноутбуков")
        self.root.geometry("700x500")  # фиксированный размер окна

        # Загрузка CSV с ноутбуками и рейтингами
        try:
            self.ratings_df = pd.read_csv('data/generated_ratings.csv')
            self.laptops_df = pd.read_csv('data/laptops_with_avg_rating.csv')
            self.laptops_specs_df = pd.read_csv('data/cleaned_warranty_laptops.csv')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных:\n{e}")
            root.destroy()
            return
        self.filtered_sorted_df = self.laptops_df.copy()

        # Фрейм входа
        self.frame_login = tk.Frame(root)
        self.frame_login.pack(fill='both', expand=True)

        # Внутренний frame для центрирования контента
        center_frame = tk.Frame(self.frame_login)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(center_frame, text="ID пользователя:").pack(pady=10)
        self.id_user_entry = tk.Entry(center_frame)
        self.id_user_entry.pack(pady=5)
        self.id_user_entry.focus_set()

        self.id_user_entry.bind('<Return>', self.login)
        tk.Button(center_frame, text="Войти", command=self.login).pack(pady=10)

        # Фрейм основного приложения (по умолчанию скрыт)
        self.frame_main = tk.Frame(root)

        self.notebook = ttk.Notebook(self.frame_main)
        self.notebook.pack(fill='both', expand=True)



        self.tab_user = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_user, text="Информация о пользователе")

        self.tab_all = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_all, text="Все ноутбуки")

        controls_frame = tk.Frame(self.tab_all)
        controls_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(controls_frame, text="Поиск по названию:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(controls_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind('<KeyRelease>', lambda event: self.update_treeview())

        tk.Label(controls_frame, text="Сортировать по:").pack(side=tk.LEFT, padx=10)

        self.sort_var = tk.StringVar(value="price_asc")
        options = [
            ("Цена ↑", "price_asc"),
            ("Цена ↓", "price_desc"),
            ("Средний рейтинг ↑", "rating_asc"),
            ("Средний рейтинг ↓", "rating_desc"),
        ]
        for text, mode in options:
            rb = ttk.Radiobutton(controls_frame, text=text, value=mode, variable=self.sort_var,
                                 command=self.update_treeview)
            rb.pack(side=tk.LEFT, padx=5)

        columns = ('title', 'price', 'avg_rating')
        self.tree = ttk.Treeview(self.tab_all, columns=columns, show='headings')

        self.tree.heading('title', text='Название')
        self.tree.heading('price', text='Цена')
        self.tree.heading('avg_rating', text='Средняя оценка')

        self.tree.column('title', width=350, anchor='w')
        self.tree.column('price', width=100, anchor='center')
        self.tree.column('avg_rating', width=100, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        def update_treeview(self):
            query = self.search_var.get().lower() if hasattr(self, 'search_var') else ""

            # Фильтрация по названию с учетом NaN
            filtered = self.laptops_df[
                self.laptops_df['title'].fillna("").str.lower().str.contains(query)
            ].copy()

            sort_mode = self.sort_var.get() if hasattr(self, 'sort_var') else "price_asc"

            # Сортировка
            if sort_mode == "price_asc":
                filtered = filtered.sort_values(by='price', ascending=True, na_position='last')
            elif sort_mode == "price_desc":
                filtered = filtered.sort_values(by='price', ascending=False, na_position='last')
            elif sort_mode == "rating_asc":
                filtered = filtered.sort_values(by='average_rating', ascending=True, na_position='last')
            elif sort_mode == "rating_desc":
                filtered = filtered.sort_values(by='average_rating', ascending=False, na_position='last')

            self.filtered_sorted_df = filtered

            # Очистить Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Заполнить Treeview новыми данными
            for _, row in filtered.iterrows():
                title = row['title']
                short_title = (title[:25] + '...') if len(title) > 25 else title
                price = row['price']
                avg_rating = row.get('average_rating', None)
                avg_rating_str = f"{avg_rating:.2f}" if avg_rating is not None and not pd.isna(avg_rating) else "0"

                self.tree.insert('', 'end', values=(short_title, price, avg_rating_str))


        for _, row in self.laptops_df.iterrows():
            title = row['title']
            short_title = (title[:25] + '...') if len(title) > 25 else title
            price = row['price']
            avg_rating = row.get('average_rating', None)
            avg_rating_str = f"{avg_rating:.2f}" if avg_rating is not None and not pd.isna(avg_rating) else "0"

            self.tree.insert('', tk.END, values=(short_title, price, avg_rating_str))

        self.tree.bind('<Double-1>', self.show_details_treeview)

        self.id_user = None  # будет установлен после входа

    def create_new_user_info_tab(self):
        frame = self.tab_user
        for widget in frame.winfo_children():
            widget.destroy()

        tk.Label(frame, text="Вы новый пользователь и еще ничего не оценивали.", padx=10, pady=10).pack()

        tk.Label(frame, text="Рекомендуемые топ ноутбуки:", font=('Arial', 14, 'bold'), padx=10, pady=15).pack(anchor='w')

        top_10_df = get_top_laptops_by_tmdb_rating('data/laptops_with_avg_rating.csv', 'data/generated_ratings.csv')

        if top_10_df.empty:
            tk.Label(frame, text="Нет доступных рекомендаций.", padx=10, pady=10).pack()
        else:
            for _, row in top_10_df.iterrows():
                rec_info = f"{row['title']} | Взвешенный рейтинг: {row['weighted_rating']:.2f}"
                tk.Label(frame, text=rec_info, padx=10).pack(anchor='w')

    def update_treeview(self):
        query = self.search_var.get().lower() if hasattr(self, 'search_var') else ""

        # Фильтрация по названию с учетом NaN
        filtered = self.laptops_df[
            self.laptops_df['title'].fillna("").str.lower().str.contains(query)
        ].copy()

        sort_mode = self.sort_var.get() if hasattr(self, 'sort_var') else "price_asc"

        # Сортировка
        if sort_mode == "price_asc":
            filtered = filtered.sort_values(by='price', ascending=True, na_position='last')
        elif sort_mode == "price_desc":
            filtered = filtered.sort_values(by='price', ascending=False, na_position='last')
        elif sort_mode == "rating_asc":
            filtered = filtered.sort_values(by='average_rating', ascending=True, na_position='last')
        elif sort_mode == "rating_desc":
            filtered = filtered.sort_values(by='average_rating', ascending=False, na_position='last')

        self.filtered_sorted_df = filtered

        # Очистить Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Заполнить Treeview новыми данными
        for _, row in filtered.iterrows():
            title = row['title']
            short_title = (title[:25] + '...') if len(title) > 25 else title
            price = row['price']
            avg_rating = row.get('average_rating', None)
            avg_rating_str = f"{avg_rating:.2f}" if avg_rating is not None and not pd.isna(avg_rating) else "0"

            self.tree.insert('', 'end', values=(short_title, price, avg_rating_str))

    def login(self, event=None):
        id_user = self.id_user_entry.get()
        if not id_user.isdigit():
            messagebox.showerror("Ошибка", "Введите корректный ID пользователя.")
            return

        id_user_int = int(id_user)
        self.frame_login.pack_forget()
        self.frame_main.pack(fill='both', expand=True)

        if id_user_int in self.ratings_df['id_user'].values:
            self.id_user = id_user_int
            self.create_user_info_tab()
        else:
            self.id_user = None
            self.create_new_user_info_tab()

        self.notebook.select(self.tab_user)

    def show_details_treeview(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showinfo("Внимание", "Пожалуйста, выберите ноутбук из списка.")
            return

        item_idx = self.tree.index(selected_item)
        laptop_id = self.laptops_df.iloc[item_idx]['id_laptop']

        row = self.laptops_specs_df[self.laptops_specs_df['id_laptop'] == laptop_id].iloc[0]
        avg_rating_row = self.laptops_df[self.laptops_df['id_laptop'] == laptop_id]
        avg_rating = avg_rating_row['average_rating'].values[0] if not avg_rating_row.empty else 0
        ram_info = f"{row['RAM_GB']} ГБ {row['RAM_Type']}"

        proc_info = (
            f"{row['Proc_Manufacturer']} {row['Proc_Series']} {row['Proc_Generation']} "
            f"({row['Proc_Cores']} ядер)"
        )

        os_info = f"{row['OS_Name']} {row['OS_Bitness']}-бит"

        warranty_info = f"{row['Warranty_Years']} лет, {row['Warranty_Type']}"

        touchscreen_info = ""
        if row['Touchscreen'] == 1:
            touchscreen_info = "Сенсорный экран: есть"
        elif row['Touchscreen'] != 0:
            touchscreen_info = f"Сенсорный экран: {row['Touchscreen']}"

        info = (
                f"Название: {row['title']}\n"
                f"Цена: {row['price']}\n"
                f"SSD: {row['SSD']}\n"
                f"In_build_sw: {row['In_build_sw']}\n"
                f"id_laptop: {row['id_laptop']}\n"
                f"RAM: {ram_info}\n"
                f"Процессор: {proc_info}\n"
                f"ОС: {os_info}\n"
                f"Диагональ экрана (дюймы): {row['Display_inch']}\n"
                + (touchscreen_info + "\n" if touchscreen_info else "") +
                f"Гарантия: {warranty_info}\n"
                f"Средний рейтинг: {avg_rating:.2f}\n"
        )

        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали: {row['title']}")

        tk.Label(details_window, text=info, justify=tk.LEFT, padx=10, pady=10).pack()

        similar_df = recommend_similar_laptops('data/laptops_with_avg_rating.csv', row['id_laptop'], top_n=5)

        if not similar_df.empty:
            tk.Label(details_window, text="\nПохожие ноутбуки:", font=('Arial', 12, 'bold')).pack(pady=(10, 0))

            columns = ('title', 'price', 'avg_rating', 'SSD', 'RAM_GB', 'RAM_Type', 'Display_inch', 'Proc_Cores')
            tree_similar = ttk.Treeview(details_window, columns=columns, show='headings', height=6)
            tree_similar.pack(fill='both', expand=True, padx=10, pady=10)

            tree_similar.heading('title', text='Название')
            tree_similar.heading('price', text='Цена')
            tree_similar.heading('avg_rating', text='Средняя оценка')
            tree_similar.heading('SSD', text='SSD')
            tree_similar.heading('RAM_GB', text='RAM (ГБ)')
            tree_similar.heading('RAM_Type', text='Тип RAM')
            tree_similar.heading('Display_inch', text='Диагональ (дюймы)')
            tree_similar.heading('Proc_Cores', text='Ядер процессора')

            tree_similar.column('title', width=200, anchor='w')
            tree_similar.column('price', width=80, anchor='center')
            tree_similar.column('avg_rating', width=80, anchor='center')
            tree_similar.column('SSD', width=80, anchor='center')
            tree_similar.column('RAM_GB', width=80, anchor='center')
            tree_similar.column('RAM_Type', width=100, anchor='center')
            tree_similar.column('Display_inch', width=100, anchor='center')
            tree_similar.column('Proc_Cores', width=100, anchor='center')

            for _, sim_row in similar_df.iterrows():
                laptop_id = sim_row['id_laptop']
                # Получаем тип RAM из laptops_specs_df по id_laptop
                ram_type_row = self.laptops_specs_df[self.laptops_specs_df['id_laptop'] == laptop_id]
                ram_type = ram_type_row['RAM_Type'].values[0] if not ram_type_row.empty else ""

                title = sim_row['title']
                short_title = (title[:25] + '...') if len(title) > 25 else title
                price = sim_row['price']
                avg_rating = sim_row.get('average_rating', None)
                avg_rating_str = f"{avg_rating:.2f}" if avg_rating is not None and not pd.isna(avg_rating) else "0"

                tree_similar.insert('', tk.END, values=(
                    short_title,
                    price,
                    avg_rating_str,
                    sim_row.get('SSD', ''),
                    sim_row.get('RAM_GB', ''),
                    ram_type,
                    sim_row.get('Display_inch', ''),
                    sim_row.get('Proc_Cores', ''),
                ))

        else:
            tk.Label(details_window, text="Похожие ноутбуки не найдены.", padx=10, pady=10).pack()

    def create_user_info_tab(self):
        frame = self.tab_user
        for widget in frame.winfo_children():
            widget.destroy()

        if self.id_user is None:
            tk.Label(frame, text="Пользователь не вошёл в систему.", padx=10, pady=10).pack()
            return

        # Вывод ID пользователя
        tk.Label(frame, text=f"ID пользователя: {self.id_user}", font=("Arial", 12, "bold"), padx=10, pady=10).pack(
            anchor='w')

        # Вывод таблицы оцененных ноутбуков
        user_ratings = self.ratings_df[self.ratings_df['id_user'] == self.id_user]
        if user_ratings.empty:
            tk.Label(frame, text="Вы еще ничего не оценивали.", padx=10, pady=10).pack()
        else:
            rated_frame = tk.Frame(frame)
            rated_frame.pack(fill='both', expand=True, padx=10, pady=5)

            columns = ('title', 'user_rating')
            tree_rated = ttk.Treeview(rated_frame, columns=columns, show='headings', height=7)
            tree_rated.pack(fill='both', expand=True)

            tree_rated.heading('title', text='Название')
            tree_rated.heading('user_rating', text='Оценка')

            tree_rated.column('title', anchor='w', width=400)
            tree_rated.column('user_rating', anchor='center', width=100)

            # Объединяем для названия
            user_laptops = pd.merge(user_ratings, self.laptops_df[['id_laptop', 'title']], on='id_laptop', how='left')

            for _, row in user_laptops.iterrows():
                title = row['title']
                short_title = (title[:25] + '...') if len(title) > 25 else title
                tree_rated.insert('', 'end', values=(short_title, row['user_rating']))

        # Вывод таблицы рекомендаций
        tk.Label(frame, text="Рекомендации для вас:", font=('Arial', 14, 'bold'), padx=10, pady=15).pack(anchor='w')

        recommended_df = recommend_laptops_for_user(self.id_user, 'data/laptops_with_avg_rating.csv',
                                                    'data/generated_ratings.csv', top_n=5)

        if recommended_df.empty:
            tk.Label(frame, text="Невозможно построить рекомендации.", padx=10, pady=10).pack()
        else:
            rec_frame = tk.Frame(frame)
            rec_frame.pack(fill='both', expand=True, padx=10, pady=5)

            columns = ('title', 'predicted_rating')
            tree_rec = ttk.Treeview(rec_frame, columns=columns, show='headings', height=10)
            tree_rec.pack(fill='both', expand=True)

            tree_rec.heading('title', text='Название')
            tree_rec.heading('predicted_rating', text='Цена')

            tree_rec.column('title', anchor='w', width=400)
            tree_rec.column('predicted_rating', anchor='center', width=150)

            for _, row in recommended_df.iterrows():
                title = row['title']
                short_title = (title[:25] + '...') if len(title) > 25 else title
                price_row = self.laptops_df[self.laptops_df['id_laptop'] == row['id_laptop']]
                price = price_row['price'].values[0] if not price_row.empty else "0"

                tree_rec.insert('', 'end', values=(short_title, price))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()