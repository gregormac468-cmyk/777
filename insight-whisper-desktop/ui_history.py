"""
Вкладка 'История звонков' с фильтрацией.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, END, ttk
from datetime import datetime, timedelta

import database as db


CALL_TYPES = ["__all__", "Результативный", "Обеспечительный", "Нерезультативный"]
STATUSES = ["__all__", "done", "error"]


class HistoryTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.calls: list[dict] = []
        self._build()
        self.refresh()

    def _build(self):
        # Панель фильтров
        filters = ctk.CTkFrame(self.parent)
        filters.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(filters, text="С:").grid(row=0, column=0, padx=(10, 4), pady=5)
        self.date_from = ctk.CTkEntry(filters, width=110, placeholder_text="ГГГГ-ММ-ДД")
        self.date_from.grid(row=0, column=1, padx=4, pady=5)

        ctk.CTkLabel(filters, text="По:").grid(row=0, column=2, padx=(10, 4), pady=5)
        self.date_to = ctk.CTkEntry(filters, width=110, placeholder_text="ГГГГ-ММ-ДД")
        self.date_to.grid(row=0, column=3, padx=4, pady=5)

        ctk.CTkLabel(filters, text="Менеджер:").grid(row=0, column=4, padx=(10, 4))
        self.manager_var = ctk.StringVar(value="__all__")
        self.manager_menu = ctk.CTkOptionMenu(filters, variable=self.manager_var,
                                              values=["__all__"], width=160)
        self.manager_menu.grid(row=0, column=5, padx=4, pady=5)

        ctk.CTkLabel(filters, text="Тип:").grid(row=1, column=0, padx=(10, 4), pady=5)
        self.type_var = ctk.StringVar(value="__all__")
        ctk.CTkOptionMenu(filters, variable=self.type_var, values=CALL_TYPES,
                          width=160).grid(row=1, column=1, columnspan=2,
                                          padx=4, pady=5, sticky="w")

        ctk.CTkLabel(filters, text="Статус:").grid(row=1, column=3, padx=(10, 4))
        self.status_var = ctk.StringVar(value="__all__")
        ctk.CTkOptionMenu(filters, variable=self.status_var, values=STATUSES,
                          width=120).grid(row=1, column=4, padx=4, pady=5, sticky="w")



        ctk.CTkLabel(filters, text="Поиск:").grid(row=2, column=0, padx=(10, 4), pady=5)
        self.search_entry = ctk.CTkEntry(filters, width=240,
                                         placeholder_text="Имя файла или текст транскрипта")
        self.search_entry.grid(row=2, column=1, columnspan=3, padx=4, pady=5, sticky="we")

        ctk.CTkButton(filters, text="Применить", command=self.refresh,
                      width=110).grid(row=2, column=4, padx=4, pady=5)
        ctk.CTkButton(filters, text="Сброс", command=self._reset,
                      width=80, fg_color="gray").grid(row=2, column=5, padx=4, pady=5)

        # Кнопки действий
        actions = ctk.CTkFrame(self.parent)
        actions.pack(fill="x", padx=10, pady=5)

        self.count_label = ctk.CTkLabel(actions, text="Найдено: 0")
        self.count_label.pack(side="left", padx=10)

        ctk.CTkButton(actions, text="Открыть детали", command=self._open_detail,
                      width=130).pack(side="right", padx=4)
        ctk.CTkButton(actions, text="Экспорт PDF (выбранный)",
                      command=self._export_pdf_one,
                      width=180).pack(side="right", padx=4)
        ctk.CTkButton(actions, text="Сводный PDF",
                      command=self._export_pdf_summary,
                      width=130).pack(side="right", padx=4)
        ctk.CTkButton(actions, text="Excel (все)",
                      command=self._export_excel,
                      width=110).pack(side="right", padx=4)
        ctk.CTkButton(actions, text="Удалить выбранный",
                      command=self._delete_selected,
                      width=140, fg_color="#dc2626",
                      hover_color="#991b1b").pack(side="right", padx=4)

        # Таблица — используем ttk.Treeview (CustomTkinter не имеет своей)
        tree_frame = ctk.CTkFrame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("date", "file", "manager", "type", "score", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 selectmode="browse")
        self.tree.heading("date", text="Дата")
        self.tree.heading("file", text="Файл")
        self.tree.heading("manager", text="Менеджер")
        self.tree.heading("type", text="Тип")
        self.tree.heading("score", text="Оценка")
        self.tree.heading("status", text="Статус")
        self.tree.column("date", width=130, anchor="w")
        self.tree.column("file", width=260, anchor="w")
        self.tree.column("manager", width=140, anchor="w")
        self.tree.column("type", width=160, anchor="w")
        self.tree.column("score", width=70, anchor="center")
        self.tree.column("status", width=90, anchor="center")



        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._open_detail())

        # Раскраска строк по оценке
        self.tree.tag_configure("good", background="#dcfce7")
        self.tree.tag_configure("mid", background="#fef9c3")
        self.tree.tag_configure("bad", background="#fee2e2")
        self.tree.tag_configure("err", background="#fecaca")

    def _reset(self):
        self.date_from.delete(0, END)
        self.date_to.delete(0, END)
        self.manager_var.set("__all__")
        self.type_var.set("__all__")
        self.status_var.set("__all__")
        self.search_entry.delete(0, END)
        self.refresh()

    def refresh_managers(self):
        names = ["__all__"] + db.list_manager_names()
        self.manager_menu.configure(values=names)
        if self.manager_var.get() not in names:
            self.manager_var.set("__all__")

    def refresh(self):
        self.refresh_managers()
        df = self.date_from.get().strip() or None
        dt = self.date_to.get().strip() or None
        mgr = self.manager_var.get()
        ct = self.type_var.get()
        st = self.status_var.get()
        search = self.search_entry.get().strip() or None

        # type filter — по подстроке
        type_filter = None
        if ct != "__all__":
            type_filter = ct

        self.calls = db.list_calls(
            date_from=df, date_to=dt,
            manager=mgr if mgr != "__all__" else None,
            call_type=type_filter,
            status=st if st != "__all__" else None,
            search=search,
        )
        self._populate_tree()
        self.count_label.configure(text=f"Найдено: {len(self.calls)}")



    def _populate_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for c in self.calls:
            created = c.get("created_at", "")
            if isinstance(created, str) and "T" in created:
                try:
                    created = datetime.fromisoformat(created).strftime("%d.%m.%Y %H:%M")
                except Exception:
                    pass
            score = c.get("overall_score")
            score_str = f"{score:.1f}" if score is not None else "—"

            tag = ""
            if c.get("status") == "error":
                tag = "err"
            elif score is not None:
                if score >= 7:
                    tag = "good"
                elif score >= 4:
                    tag = "mid"
                else:
                    tag = "bad"

            self.tree.insert("", END, iid=str(c["id"]),
                             values=(
                                 str(created)[:16],
                                 c.get("file_name", ""),
                                 c.get("manager_name", "—") or "—",
                                 c.get("call_type", "—") or "—",
                                 score_str,
                                 c.get("status", ""),
                             ),
                             tags=(tag,))

    def _selected_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _open_detail(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showinfo("Инфо", "Выберите звонок в списке")
            return
        from ui_call_detail import open_call_detail
        open_call_detail(self.app, cid, on_change=self.refresh)



    def _delete_selected(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showinfo("Инфо", "Выберите звонок")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранный звонок безвозвратно?"):
            db.delete_call(cid)
            self.refresh()

    def _export_pdf_one(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showinfo("Инфо", "Выберите звонок")
            return
        call = db.get_call(cid)
        if not call:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"call_{cid}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if not path:
            return
        try:
            from pdf_export import export_call_to_pdf
            export_call_to_pdf(call, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать PDF: {e}")

    def _export_pdf_summary(self):
        if not self.calls:
            messagebox.showinfo("Инфо", "Нет звонков для экспорта")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        if not path:
            return
        try:
            from pdf_export import export_calls_summary_to_pdf
            export_calls_summary_to_pdf(self.calls, path,
                                        title=f"Сводный отчёт ({len(self.calls)} звонков)")
            messagebox.showinfo("Готово", f"Сохранено: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать PDF: {e}")



    def _export_excel(self):
        if not self.calls:
            messagebox.showinfo("Инфо", "Нет звонков для экспорта")
            return
        try:
            from openpyxl import Workbook
        except ImportError:
            messagebox.showerror("Ошибка", "Установите openpyxl: pip install openpyxl")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile=f"history_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "История звонков"
        ws.append(["Дата", "Файл", "Менеджер", "Тип", "Оценка",
                   "Статус", "Резюме", "Сильные", "Слабые", "Рекомендации"])

        for c in self.calls:
            a = c.get("analysis") or {}
            ws.append([
                c.get("created_at", ""),
                c.get("file_name", ""),
                c.get("manager_name", "") or "",
                c.get("call_type", "") or "",
                c.get("overall_score", ""),
                c.get("status", ""),
                a.get("summary", ""),
                "; ".join(a.get("strengths", [])),
                "; ".join(a.get("weaknesses", [])),
                "; ".join(a.get("recommendations", [])),
            ])

        wb.save(path)
        messagebox.showinfo("Готово", f"Сохранено: {path}")
