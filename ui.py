import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class SitemapApp:
    def __init__(self, root, logic_module):
        self.logic = logic_module
        self.root = root
        self.root.title("Sitemap Parser")
        self.root.geometry("750x500")

        # URL sitemap
        tk.Label(root, text="URL sitemap:").pack(pady=5)
        self.url_entry = tk.Entry(root, width=85)
        self.url_entry.pack(pady=5)
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate('<<Paste>>'))
        self.url_entry.bind("<Button-3>", lambda e: self.url_entry.event_generate('<<Paste>>'))

        # Вибір файлу Excel
        tk.Label(root, text="Excel файл для збереження:").pack(pady=5)
        frame = tk.Frame(root)
        frame.pack(pady=5)
        self.output_entry = tk.Entry(frame, width=65)
        self.output_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Огляд", command=self.browse_file).pack(side=tk.LEFT)

        # Кількість потоків
        tk.Label(root, text="Кількість потоків:").pack(pady=5)
        self.threads_spin = tk.Spinbox(root, from_=1, to=20, width=5)
        self.threads_spin.pack(pady=5)

        # Чекбокси для полів
        tk.Label(root, text="Що парсити:").pack(pady=5)
        self.fields = {}
        checkbox_frame = tk.Frame(root)
        checkbox_frame.pack()
        for text, key in [("Статус код", "status_code"),
                          ("H1", "h1"),
                          ("Title", "title"),
                          ("Description", "description"),
                          ("Canonical", "canonical"),
                          ("OG Title", "og_title"),
                          ("OG Description", "og_description")]:
            var = tk.BooleanVar(value=True if key in ["status_code","h1"] else False)
            cb = tk.Checkbutton(checkbox_frame, text=text, variable=var)
            cb.pack(side=tk.LEFT, padx=5)
            self.fields[key] = var

        # Кнопка запуску
        tk.Button(root, text="Обробити", command=self.start_processing).pack(pady=10)

        # Прогрес-бар
        self.progress = ttk.Progressbar(root, orient="horizontal", length=650, mode="determinate")
        self.progress.pack(pady=10)

        # Лог
        self.log_text = tk.Text(root, height=15)
        self.log_text.pack(pady=5)

    def browse_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def start_processing(self):
        threading.Thread(target=self.process_sitemap, daemon=True).start()

    def process_sitemap(self):
        sitemap_url = self.url_entry.get()
        output_file = self.output_entry.get()
        threads = int(self.threads_spin.get())

        fields = [key for key, var in self.fields.items() if var.get()]
        if not sitemap_url or not output_file or not fields:
            messagebox.showerror("Помилка", "Введіть URL sitemap, файл для збереження і виберіть хоча б одне поле")
            return

        self.log("Завантаження URL зі sitemap...")
        urls = self.logic.parse_sitemap_recursive(sitemap_url)
        if not urls:
            self.log("Сайтмап порожній або недоступний.")
            return

        self.log(f"Знайдено {len(urls)} URL")
        self.progress["maximum"] = len(urls)
        self.progress["value"] = 0

        def progress_callback(result):
            self.progress["value"] += 1
            self.log(f"Оброблено: {result['URL']}")

        data = self.logic.process_urls(urls, fields=fields, threads=threads, progress_callback=progress_callback)
        self.logic.save_to_excel(data, output_file)
        self.log(f"\nЗвіт збережено у файлі {output_file}")
