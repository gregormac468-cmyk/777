"""
Вкладка 'Менеджеры' — управление списком менеджеров.
"""
import customtkinter as ctk
from tkinter import messagebox, END, ttk

import database as db


class ManagersTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.selected_id: int | None = None
        self._build()
        self.refresh()

    def _build(self):
        # Форма
        form = ctk.CTkFrame(self.parent)
        form.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form, text="Имя:", width=80).grid(row=0, column=0,
                                                        padx=5, pady=5, sticky="e")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.name_var, width=300).grid(
            row=0, column=1, padx=5, pady=5, sticky="we")

        ctk.CTkLabel(form, text="Должность:", width=80).grid(
            row=1, column=0, padx=5, pady=5, sticky="e")
        self.position_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.position_var, width=300).grid(
            row=1, column=1, padx=5, pady=5, sticky="we")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=2, column=0, columnspan=2, pady=8)

        self.btn_add = ctk.CTkButton(btns, text="Добавить",
                                      command=self._add, fg_color="#16a34a")
        self.btn_add.pack(side="left", padx=4)

        self.btn_update = ctk.CTkButton(btns, text="Обновить выбранного",
                                         command=self._update,
                                         fg_color="#2563eb")
        self.btn_update.pack(side="left", padx=4)

        self.btn_clear = ctk.CTkButton(btns, text="Очистить форму",
                                        command=self._clear_form,
                                        fg_color="gray")
        self.btn_clear.pack(side="left", padx=4)

        self.btn_delete = ctk.CTkButton(btns, text="Удалить выбранного",
                                         command=self._delete,
                                         fg_color="#dc2626",
                                         hover_color="#991b1b")
        self.btn_delete.pack(side="left", padx=4)



        # Таблица менеджеров
        list_frame = ctk.CTkFrame(self.parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("name", "position", "created")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings",
                                  selectmode="browse")
        self.tree.heading("name", text="Имя")
        self.tree.heading("position", text="Должность")
        self.tree.heading("created", text="Добавлен")
        self.tree.column("name", width=240, anchor="w")
        self.tree.column("position", width=240, anchor="w")
        self.tree.column("created", width=180, anchor="w")

        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for m in db.list_managers():
            self.tree.insert("", END, iid=str(m["id"]),
                              values=(m["name"], m.get("position", "") or "",
                                      m.get("created_at", "") or ""))
        # уведомить остальные вкладки
        if hasattr(self.app, "notify_managers_changed"):
            self.app.notify_managers_changed()

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            self.selected_id = None
            return
        try:
            mid = int(sel[0])
        except ValueError:
            return
        self.selected_id = mid
        for m in db.list_managers():
            if m["id"] == mid:
                self.name_var.set(m["name"])
                self.position_var.set(m.get("position", "") or "")
                break

    def _clear_form(self):
        self.name_var.set("")
        self.position_var.set("")
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())



    def _add(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Укажите имя менеджера")
            return
        ok = db.add_manager(name, self.position_var.get().strip())
        if not ok:
            messagebox.showerror("Ошибка", f"Менеджер «{name}» уже существует")
            return
        self._clear_form()
        self.refresh()

    def _update(self):
        if self.selected_id is None:
            messagebox.showinfo("Инфо", "Выберите менеджера в списке")
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Укажите имя менеджера")
            return
        try:
            db.update_manager(self.selected_id, name,
                              self.position_var.get().strip())
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self._clear_form()
        self.refresh()

    def _delete(self):
        if self.selected_id is None:
            messagebox.showinfo("Инфо", "Выберите менеджера в списке")
            return
        if not messagebox.askyesno(
            "Подтверждение",
            "Удалить менеджера? Звонки этого менеджера останутся в истории."
        ):
            return
        db.delete_manager(self.selected_id)
        self._clear_form()
        self.refresh()
