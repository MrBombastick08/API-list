import customtkinter as ctk
import requests
import json
import os
from tkinter import messagebox, filedialog

# Настройки оформления
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Интеграция модулей через API")
        self.geometry("900x600")

        # Список доступных API
        self.available_apis = []
        self.current_api_url = ""

        # Сетка
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Боковая панель
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="API Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.load_json_btn = ctk.CTkButton(self.sidebar_frame, text="Загрузить список API", command=self.load_apis_from_json)
        self.load_json_btn.grid(row=1, column=0, padx=20, pady=10)

        self.api_option_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Локальный API"], command=self.change_api)
        self.api_option_menu.grid(row=2, column=0, padx=20, pady=10)

        self.refresh_button = ctk.CTkButton(self.sidebar_frame, text="Обновить данные", command=self.fetch_data)
        self.refresh_button.grid(row=3, column=0, padx=20, pady=10)

        self.api_info_label = ctk.CTkLabel(self.sidebar_frame, text=f"Текущий URL:\n{self.current_api_url}", font=ctk.CTkFont(size=10), wraplength=160)
        self.api_info_label.grid(row=4, column=0, padx=20, pady=10)

        # Основная область
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Заголовок и статус
        self.status_label = ctk.CTkLabel(self.main_frame, text="Готов к работе", font=ctk.CTkFont(size=14))
        self.status_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")

        # Список данных (Raw JSON view or formatted)
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Результаты запроса")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Текстовое поле для вывода сырых данных
        self.raw_data_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.raw_data_text.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Инициализация
        self.load_default_api()

    def load_default_api(self):
        """Загрузка дефолтного локального API"""
        self.available_apis = [{
            "name": "Локальный API",
            "url": "",
            "description": "Локальный сервер"
        }]
        self.update_api_menu()

    def load_apis_from_json(self):
        """Загрузка списка API из выбранного пользователем JSON файла"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.available_apis = data
                    self.update_api_menu()
                    messagebox.showinfo("Успех", f"Загружено {len(data)} API")
                else:
                    messagebox.showerror("Ошибка", "Неверный формат JSON (ожидался список)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {str(e)}")

    def update_api_menu(self):
        """Обновление выпадающего списка API"""
        names = [api['name'] for api in self.available_apis]
        self.api_option_menu.configure(values=names)
        if names:
            self.api_option_menu.set(names[0])
            self.change_api(names[0])

    def change_api(self, choice):
        """Смена текущего рабочего API"""
        api = next((a for a in self.available_apis if a['name'] == choice), None)
        if api:
            self.current_api_url = api['url']
            self.api_info_label.configure(text=f"Текущий URL:\n{self.current_api_url}")
            self.status_label.configure(text=f"Выбран API: {choice}")

    def fetch_data(self):
        """Получение данных из текущего API"""
        self.status_label.configure(text="Загрузка...")
        self.raw_data_text.delete("1.0", "end")
        
        # Очистка списка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            response = requests.get(self.current_api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Отображение сырых данных
            self.raw_data_text.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
            
            # Попытка красивого отображения
            self.display_data(data)
            self.status_label.configure(text=f"Данные получены успешно ({response.status_code})")
        except Exception as e:
            self.status_label.configure(text="Ошибка запроса")
            messagebox.showerror("Ошибка", f"Не удалось получить данные:\n{str(e)}")

    def display_data(self, data):
        """Визуализация данных в скролл-панели"""
        if isinstance(data, dict):
            # Если это объект, преобразуем в список для удобства
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = [{"value": str(data)}]

        # Ограничим вывод для очень больших списков
        display_items = items[:50] 

        for idx, item in enumerate(display_items):
            item_frame = ctk.CTkFrame(self.scrollable_frame)
            item_frame.grid(row=idx, column=0, padx=5, pady=2, sticky="ew")
            
            # Пытаемся вытащить человекочитаемое описание
            text = ""
            if isinstance(item, dict):
                # Ищем стандартные ключи
                title = item.get('title') or item.get('name') or item.get('fact') or "Элемент"
                desc = item.get('description') or item.get('body') or item.get('email') or ""
                text = f"{title}\n{desc}" if desc else str(title)
            else:
                text = str(item)

            label = ctk.CTkLabel(item_frame, text=text, justify="left", wraplength=500)
            label.pack(padx=10, pady=5, fill="x")

if __name__ == "__main__":
    app = App()
    app.mainloop()
