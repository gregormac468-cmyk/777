"""
Insight Whisper Desktop — десктопное приложение для транскрибации
и AI-анализа звонков. Главный модуль с GUI.
"""
import customtkinter as ctk
import threading
import time
import json
import os
from tkinter import filedialog, messagebox, END
from pathlib import Path
from datetime import datetime

from config import (
    load_config, save_config, list_instructions, load_instruction,
    save_instruction, delete_instruction, RESULTS_DIR, ensure_dirs,
)
from transcriber import transcribe
from analyzer import analyze
import database as db
from ui_history import HistoryTab
from ui_dashboard import DashboardTab
from ui_managers import ManagersTab


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Insight Whisper — Анализ звонков")
        self.geometry("1200x820")
        self.minsize(1000, 650)

        ensure_dirs()
        db.init_db()
        self.cfg = load_config()
        ctk.set_appearance_mode(self.cfg.get("theme", "dark"))

        self.files: list[str] = []
        self.current_results: list[dict] = []  # звонки текущей сессии загрузки
        self.processing = False

        self._build_ui()



    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_upload = self.tabview.add("Загрузка")
        self.tab_dashboard = self.tabview.add("Дашборд")
        self.tab_history = self.tabview.add("История")
        self.tab_managers = self.tabview.add("Менеджеры")
        self.tab_instructions = self.tabview.add("Инструкции")
        self.tab_settings = self.tabview.add("Настройки")

        self._build_upload_tab()
        self.dashboard = DashboardTab(self.tab_dashboard, self)
        self.history = HistoryTab(self.tab_history, self)
        self.managers = ManagersTab(self.tab_managers, self)
        self._build_instructions_tab()
        self._build_settings_tab()

        # При переключении на дашборд/историю — обновлять
        self.tabview.configure(command=self._on_tab_change)

    def _on_tab_change(self):
        try:
            current = self.tabview.get()
        except Exception:
            return
        if current == "Дашборд":
            self.dashboard.refresh()
        elif current == "История":
            self.history.refresh()

    def notify_managers_changed(self):
        """Обновить выпадающие списки менеджеров везде."""
        names = db.list_manager_names()
        if hasattr(self, "manager_menu"):
            values = ["(не выбран)"] + names
            self.manager_menu.configure(values=values)
            if self.manager_var.get() not in values:
                self.manager_var.set("(не выбран)")
        if hasattr(self, "history"):
            self.history.refresh_managers()
        if hasattr(self, "dashboard"):
            self.dashboard.refresh_managers()



    # ===== UPLOAD TAB =====
    def _build_upload_tab(self):
        frame = self.tab_upload

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(top, text="Менеджер:").pack(side="left", padx=(10, 5))
        manager_names = db.list_manager_names()
        self.manager_var = ctk.StringVar(value="(не выбран)")
        self.manager_menu = ctk.CTkOptionMenu(
            top, variable=self.manager_var,
            values=["(не выбран)"] + manager_names, width=200,
        )
        self.manager_menu.pack(side="left", padx=5)

        ctk.CTkButton(top, text="+ Менеджер", width=100,
                      command=self._quick_add_manager).pack(side="left", padx=4)

        ctk.CTkLabel(top, text="Пауза (сек):").pack(side="left", padx=(20, 5))
        self.delay_var = ctk.StringVar(
            value=str(self.cfg.get("delay_between_files", 15)))
        ctk.CTkEntry(top, textvariable=self.delay_var, width=60).pack(
            side="left", padx=5)

        # Кнопки действий
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.btn_add = ctk.CTkButton(btn_frame, text="Добавить файлы",
                                      command=self._add_files)
        self.btn_add.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(btn_frame, text="Очистить",
                                        command=self._clear_files,
                                        fg_color="gray")
        self.btn_clear.pack(side="left", padx=5)

        self.btn_start = ctk.CTkButton(btn_frame, text="Начать анализ",
                                        command=self._start_processing,
                                        fg_color="#16a34a")
        self.btn_start.pack(side="left", padx=5)

        # Список файлов
        self.file_listbox = ctk.CTkTextbox(frame, height=140)
        self.file_listbox.pack(fill="x", padx=10, pady=5)

        # Прогресс
        self.progress_label = ctk.CTkLabel(frame, text="Готов к работе")
        self.progress_label.pack(padx=10, pady=(5, 2))

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)

        # Лог
        self.log_box = ctk.CTkTextbox(frame, height=200)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(5, 10))



    def _quick_add_manager(self):
        dlg = ctk.CTkInputDialog(text="Имя нового менеджера:",
                                 title="Добавить менеджера")
        name = dlg.get_input()
        if not name:
            return
        if db.add_manager(name.strip()):
            self.notify_managers_changed()
            self.manager_var.set(name.strip())
        else:
            messagebox.showerror("Ошибка", f"Менеджер «{name}» уже существует")

    # ===== INSTRUCTIONS TAB =====
    def _build_instructions_tab(self):
        frame = self.tab_instructions

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top, text="Инструкции:").pack(side="left", padx=5)
        self.instr_list = list_instructions()
        self.instr_var = ctk.StringVar(value=self.cfg.get("active_instruction", ""))
        self.instr_menu = ctk.CTkOptionMenu(
            top, variable=self.instr_var,
            values=self.instr_list or ["(нет)"],
            command=self._on_instruction_select,
        )
        self.instr_menu.pack(side="left", padx=5)

        ctk.CTkButton(top, text="Новая", command=self._new_instruction,
                      width=80).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Из файла", command=self._load_instr_file,
                      width=80).pack(side="left", padx=5)
        ctk.CTkButton(top, text="Сохранить", command=self._save_current_instr,
                      width=90, fg_color="#16a34a").pack(side="left", padx=5)
        ctk.CTkButton(top, text="Удалить", command=self._delete_instr,
                      width=80, fg_color="#dc2626",
                      hover_color="#991b1b").pack(side="left", padx=5)

        # Название
        name_frame = ctk.CTkFrame(frame)
        name_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(name_frame, text="Название:").pack(side="left", padx=5)
        self.instr_name_var = ctk.StringVar()
        ctk.CTkEntry(name_frame, textvariable=self.instr_name_var,
                     width=400).pack(side="left", padx=5, fill="x", expand=True)

        # Текст
        self.instr_text = ctk.CTkTextbox(frame, wrap="word")
        self.instr_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if self.instr_var.get() and self.instr_var.get() != "(нет)":
            self._on_instruction_select(self.instr_var.get())



    # ===== SETTINGS TAB =====
    def _build_settings_tab(self):
        frame = self.tab_settings
        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Тема
        ctk.CTkLabel(scroll, text="Тема", font=("", 14, "bold")).pack(
            anchor="w", pady=(10, 5))
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme", "dark"))
        theme_frame = ctk.CTkFrame(scroll)
        theme_frame.pack(fill="x", pady=5)
        ctk.CTkRadioButton(theme_frame, text="Тёмная", variable=self.theme_var,
                           value="dark",
                           command=self._change_theme).pack(side="left", padx=10)
        ctk.CTkRadioButton(theme_frame, text="Светлая", variable=self.theme_var,
                           value="light",
                           command=self._change_theme).pack(side="left", padx=10)

        # Транскрибация
        ctk.CTkLabel(scroll, text="Транскрибация",
                     font=("", 14, "bold")).pack(anchor="w", pady=(15, 5))
        t_frame = ctk.CTkFrame(scroll)
        t_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(t_frame, text="Провайдер:").pack(side="left", padx=5)
        self.trans_provider_var = ctk.StringVar(
            value=self.cfg.get("transcription_provider", "google"))
        ctk.CTkOptionMenu(t_frame, variable=self.trans_provider_var,
                          values=["google", "openai"]).pack(side="left", padx=5)
        ctk.CTkLabel(t_frame, text="Модель:").pack(side="left", padx=(15, 5))
        self.trans_model_var = ctk.StringVar(
            value=self.cfg.get("transcription_model", "gemini-2.5-flash"))
        ctk.CTkEntry(t_frame, textvariable=self.trans_model_var,
                     width=200).pack(side="left", padx=5)

        # Анализ
        ctk.CTkLabel(scroll, text="Анализ",
                     font=("", 14, "bold")).pack(anchor="w", pady=(15, 5))
        a_frame = ctk.CTkFrame(scroll)
        a_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(a_frame, text="Провайдер:").pack(side="left", padx=5)
        self.anal_provider_var = ctk.StringVar(
            value=self.cfg.get("analysis_provider", "google"))
        ctk.CTkOptionMenu(a_frame, variable=self.anal_provider_var,
                          values=["google", "openai", "deepseek",
                                  "anthropic", "qwen"]).pack(side="left", padx=5)
        ctk.CTkLabel(a_frame, text="Модель:").pack(side="left", padx=(15, 5))
        self.anal_model_var = ctk.StringVar(
            value=self.cfg.get("analysis_model", "gemini-2.5-flash"))
        ctk.CTkEntry(a_frame, textvariable=self.anal_model_var,
                     width=200).pack(side="left", padx=5)



        # API ключи
        ctk.CTkLabel(scroll, text="API Ключи",
                     font=("", 14, "bold")).pack(anchor="w", pady=(15, 5))
        self.key_vars = {}
        keys = [
            ("google_api_key", "Google API Key"),
            ("openai_api_key", "OpenAI API Key"),
            ("deepseek_api_key", "DeepSeek API Key"),
            ("anthropic_api_key", "Anthropic API Key"),
            ("qwen_api_key", "Qwen API Key"),
        ]
        for key_name, label in keys:
            kf = ctk.CTkFrame(scroll)
            kf.pack(fill="x", pady=3)
            ctk.CTkLabel(kf, text=f"{label}:", width=150).pack(
                side="left", padx=5)
            var = ctk.StringVar(value=self.cfg.get(key_name, ""))
            self.key_vars[key_name] = var
            ctk.CTkEntry(kf, textvariable=var, width=400, show="*").pack(
                side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(scroll, text="Сохранить настройки",
                      command=self._save_settings,
                      fg_color="#16a34a").pack(pady=20)

    # ===== UPLOAD ACTIONS =====
    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Выберите аудиофайлы",
            filetypes=[
                ("Аудио",
                 "*.mp3 *.wav *.m4a *.ogg *.oga *.aac *.flac *.webm *.mp4 *.opus *.amr *.3gp"),
                ("Все файлы", "*.*"),
            ]
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
        self._refresh_file_list()

    def _clear_files(self):
        self.files.clear()
        self._refresh_file_list()

    def _refresh_file_list(self):
        self.file_listbox.delete("1.0", END)
        for i, f in enumerate(self.files, 1):
            name = Path(f).name
            try:
                size_mb = os.path.getsize(f) / 1024 / 1024
                self.file_listbox.insert(END, f"{i}. {name} ({size_mb:.1f} МБ)\n")
            except OSError:
                self.file_listbox.insert(END, f"{i}. {name}\n")

    def _log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(END, f"[{timestamp}] {msg}\n")
        self.log_box.see(END)



    def _start_processing(self):
        if self.processing:
            return
        if not self.files:
            messagebox.showwarning("Внимание",
                                    "Добавьте аудиофайлы для анализа")
            return

        cfg = self.cfg
        t_provider = self.trans_provider_var.get()
        a_provider = self.anal_provider_var.get()
        t_key = cfg.get(f"{t_provider}_api_key", "")
        a_key = cfg.get(f"{a_provider}_api_key", "")

        if not t_key:
            messagebox.showerror("Ошибка",
                f"Не задан API ключ для транскрибации ({t_provider}). "
                "Перейдите в Настройки.")
            return
        if not a_key:
            messagebox.showerror("Ошибка",
                f"Не задан API ключ для анализа ({a_provider}). "
                "Перейдите в Настройки.")
            return

        self.processing = True
        self.btn_start.configure(state="disabled", text="Обработка...")
        self.current_results.clear()
        threading.Thread(target=self._process_files, daemon=True).start()

    def _process_files(self):
        cfg = self.cfg
        t_provider = self.trans_provider_var.get()
        a_provider = self.anal_provider_var.get()
        t_model = self.trans_model_var.get()
        a_model = self.anal_model_var.get()
        t_key = cfg.get(f"{t_provider}_api_key", "")
        a_key = cfg.get(f"{a_provider}_api_key", "")

        instr_name = self.instr_var.get()
        instruction = ""
        if instr_name and instr_name != "(нет)":
            instruction = load_instruction(instr_name)

        try:
            delay = int(self.delay_var.get() or 15)
        except ValueError:
            delay = 15

        manager = self.manager_var.get()
        if manager == "(не выбран)":
            manager = ""

        total = len(self.files)



        for i, file_path in enumerate(self.files):
            fname = Path(file_path).name
            self.after(0, lambda i=i, t=total:
                       self.progress_bar.set(i / t if t else 0))
            self.after(0, lambda f=fname, i=i, t=total:
                       self.progress_label.configure(
                           text=f"Обработка {i+1}/{t}: {f}"))
            self.after(0, lambda f=fname: self._log(f"▶ Транскрибация: {f}"))

            result = {
                "file_name": fname,
                "file_path": file_path,
                "manager": manager,
                "manager_name": manager,
                "instruction_name": instr_name if instr_name != "(нет)" else "",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "transcript": "",
                "analysis": None,
                "error": "",
            }

            try:
                transcript = transcribe(t_provider, t_key, file_path, t_model)
                result["transcript"] = transcript
                self.after(0, lambda f=fname:
                           self._log(f"✓ Транскрипт получен: {f}"))

                self.after(0, lambda f=fname: self._log(f"▶ Анализ: {f}"))
                analysis = analyze(a_provider, a_key, transcript,
                                   instruction, a_model)
                result["analysis"] = analysis
                result["status"] = "done"

                score = analysis.get("overall_score", "?")
                call_type = analysis.get("call_type", "?")
                self.after(0, lambda f=fname, s=score, ct=call_type:
                           self._log(
                               f"✓ Анализ готов: {f} — {s}/10, тип: {ct}"))
            except Exception as e:
                result["error"] = str(e)
                self.after(0, lambda f=fname, e=str(e):
                           self._log(f"✗ Ошибка ({f}): {e}"))

            # Сохраняем в БД
            try:
                call_id = db.save_call(result)
                result["id"] = call_id
            except Exception as e:
                self.after(0, lambda e=str(e):
                           self._log(f"⚠ Ошибка сохранения в БД: {e}"))

            self.current_results.append(result)

            if i < total - 1 and delay > 0:
                for s in range(delay, 0, -1):
                    self.after(0, lambda s=s:
                               self.progress_label.configure(
                                   text=f"Пауза: {s} сек..."))
                    time.sleep(1)



        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(0, lambda: self.progress_label.configure(
            text=f"Готово! Обработано: {total}"))
        self.after(0, lambda: self._log(
            f"═══ Обработка завершена: {total} файлов ═══"))
        self.after(0, lambda: self.btn_start.configure(
            state="normal", text="Начать анализ"))

        # Обновить вкладки
        self.after(0, lambda: self.history.refresh()
                   if hasattr(self, "history") else None)
        self.after(0, lambda: self.dashboard.refresh()
                   if hasattr(self, "dashboard") else None)

        self.processing = False

    # ===== INSTRUCTIONS =====
    def _on_instruction_select(self, name: str):
        if name == "(нет)":
            return
        content = load_instruction(name)
        self.instr_name_var.set(name)
        self.instr_text.delete("1.0", END)
        self.instr_text.insert("1.0", content)
        self.cfg["active_instruction"] = name
        save_config(self.cfg)

    def _new_instruction(self):
        self.instr_name_var.set("")
        self.instr_text.delete("1.0", END)

    def _load_instr_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Текстовые", "*.txt *.md"), ("Все", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        name = Path(path).stem
        self.instr_name_var.set(name)
        self.instr_text.delete("1.0", END)
        self.instr_text.insert("1.0", content)

    def _save_current_instr(self):
        name = self.instr_name_var.get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Укажите название инструкции")
            return
        content = self.instr_text.get("1.0", END).strip()
        if not content:
            messagebox.showwarning("Внимание", "Инструкция пуста")
            return
        save_instruction(name, content)
        self.cfg["active_instruction"] = name
        save_config(self.cfg)
        self._refresh_instr_list()
        messagebox.showinfo("Готово",
                             f"Инструкция «{name}» сохранена и активирована")



    def _delete_instr(self):
        name = self.instr_name_var.get().strip()
        if not name:
            return
        if messagebox.askyesno("Подтверждение",
                                f"Удалить инструкцию «{name}»?"):
            delete_instruction(name)
            self.instr_name_var.set("")
            self.instr_text.delete("1.0", END)
            if self.cfg.get("active_instruction") == name:
                self.cfg["active_instruction"] = ""
                save_config(self.cfg)
            self._refresh_instr_list()

    def _refresh_instr_list(self):
        self.instr_list = list_instructions()
        values = self.instr_list if self.instr_list else ["(нет)"]
        self.instr_menu.configure(values=values)
        if self.instr_list and self.instr_var.get() not in self.instr_list:
            self.instr_var.set(self.instr_list[0])

    # ===== SETTINGS =====
    def _save_settings(self):
        self.cfg["transcription_provider"] = self.trans_provider_var.get()
        self.cfg["transcription_model"] = self.trans_model_var.get()
        self.cfg["analysis_provider"] = self.anal_provider_var.get()
        self.cfg["analysis_model"] = self.anal_model_var.get()
        self.cfg["theme"] = self.theme_var.get()
        try:
            self.cfg["delay_between_files"] = int(self.delay_var.get() or 15)
        except ValueError:
            self.cfg["delay_between_files"] = 15

        for key_name, var in self.key_vars.items():
            self.cfg[key_name] = var.get()

        save_config(self.cfg)
        messagebox.showinfo("Готово", "Настройки сохранены")

    def _change_theme(self):
        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        self.cfg["theme"] = theme
        save_config(self.cfg)


if __name__ == "__main__":
    ensure_dirs()
    app = App()
    app.mainloop()
