"""
Окно детального просмотра звонка с возможностью повторного анализа.
"""
import threading
from tkinter import filedialog, messagebox, END
from datetime import datetime
import customtkinter as ctk

import database as db
from analyzer import analyze
from config import load_config, load_instruction


class CallDetailWindow(ctk.CTkToplevel):
    def __init__(self, master, call_id: int, on_change=None):
        super().__init__(master)
        self.call_id = call_id
        self.on_change = on_change
        self.title(f"Звонок #{call_id}")
        self.geometry("1000x780")
        self.minsize(850, 600)
        self.transient(master)

        self.call = db.get_call(call_id)
        if not self.call:
            messagebox.showerror("Ошибка", "Звонок не найден")
            self.destroy()
            return

        self._build()
        self._populate()

    def _build(self):
        # Шапка
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(header, text="", font=("", 16, "bold"))
        self.title_label.pack(anchor="w", padx=10, pady=(8, 2))

        self.meta_label = ctk.CTkLabel(header, text="", font=("", 11),
                                       text_color="gray")
        self.meta_label.pack(anchor="w", padx=10, pady=(0, 8))

        # Кнопки действий
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_reanalyze = ctk.CTkButton(actions, text="Повторный анализ",
                                            command=self._reanalyze,
                                            fg_color="#2563eb")
        self.btn_reanalyze.pack(side="left", padx=4)

        ctk.CTkButton(actions, text="Экспорт в PDF",
                      command=self._export_pdf,
                      fg_color="#16a34a").pack(side="left", padx=4)

        ctk.CTkButton(actions, text="Удалить",
                      command=self._delete,
                      fg_color="#dc2626",
                      hover_color="#991b1b").pack(side="right", padx=4)



        # Табы — анализ + транскрипт
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_analysis = self.tabs.add("Анализ")
        self.tab_transcript = self.tabs.add("Транскрипт")

        # Анализ — прокручиваемый
        self.analysis_box = ctk.CTkTextbox(self.tab_analysis, wrap="word",
                                            font=("", 12))
        self.analysis_box.pack(fill="both", expand=True, padx=4, pady=4)

        # Транскрипт
        self.transcript_box = ctk.CTkTextbox(self.tab_transcript, wrap="word",
                                              font=("", 12))
        self.transcript_box.pack(fill="both", expand=True, padx=4, pady=4)

    def _populate(self):
        c = self.call
        a = c.get("analysis") or {}

        # Шапка
        self.title_label.configure(text=c.get("file_name", ""))
        created = c.get("created_at", "")
        if isinstance(created, str) and "T" in created:
            try:
                created = datetime.fromisoformat(created).strftime("%d.%m.%Y %H:%M")
            except Exception:
                pass
        meta_parts = [
            f"Менеджер: {c.get('manager_name') or '—'}",
            f"Дата: {created}",
            f"Статус: {c.get('status', '')}",
        ]
        if a.get("call_type"):
            meta_parts.append(f"Тип: {a['call_type']}")
        score = a.get("overall_score") if a else c.get("overall_score")
        if score is not None:
            meta_parts.append(f"Оценка: {score:.1f}/10")
        self.meta_label.configure(text="  •  ".join(meta_parts))

        # Анализ
        self.analysis_box.configure(state="normal")
        self.analysis_box.delete("1.0", END)

        if c.get("status") == "error":
            self.analysis_box.insert(END, "⚠ Ошибка анализа\n\n")
            self.analysis_box.insert(END, c.get("error_message", "") or "")
        elif a:
            self._render_analysis(a)
        else:
            self.analysis_box.insert(END, "Нет данных анализа")
        self.analysis_box.configure(state="disabled")

        # Транскрипт
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", END)
        self.transcript_box.insert(END, c.get("transcript", "") or "(пусто)")
        self.transcript_box.configure(state="disabled")



    def _render_analysis(self, a: dict):
        box = self.analysis_box
        box.insert(END, f"Тип звонка: {a.get('call_type', '—')}\n")
        score = a.get("overall_score")
        if score is not None:
            box.insert(END, f"Общая оценка: {score:.1f} / 10\n\n")

        if a.get("summary"):
            box.insert(END, "📝 Резюме\n")
            box.insert(END, f"{a['summary']}\n\n")

        criteria = a.get("criteria") or []
        if criteria:
            box.insert(END, "📊 Критерии оценки\n")
            box.insert(END, "─" * 60 + "\n")
            for cr in criteria:
                box.insert(END, f"  • {cr.get('name', '')}: ")
                box.insert(END, f"{cr.get('score', '—')}/10\n")
                if cr.get("comment"):
                    box.insert(END, f"    {cr['comment']}\n")
            box.insert(END, "\n")

        for title, key, icon in [
            ("Сильные стороны", "strengths", "✅"),
            ("Слабые стороны", "weaknesses", "⚠"),
            ("Рекомендации", "recommendations", "💡"),
        ]:
            items = a.get(key) or []
            if items:
                box.insert(END, f"{icon} {title}\n")
                box.insert(END, "─" * 60 + "\n")
                for item in items:
                    box.insert(END, f"  • {item}\n")
                box.insert(END, "\n")

    def _delete(self):
        if not messagebox.askyesno("Подтверждение",
                                    "Удалить звонок безвозвратно?"):
            return
        db.delete_call(self.call_id)
        if self.on_change:
            self.on_change()
        self.destroy()

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"call_{self.call_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            parent=self,
        )
        if not path:
            return
        try:
            from pdf_export import export_call_to_pdf
            export_call_to_pdf(self.call, path)
            messagebox.showinfo("Готово", f"Сохранено: {path}", parent=self)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)



    def _reanalyze(self):
        transcript = self.call.get("transcript", "")
        if not transcript:
            messagebox.showwarning("Внимание",
                "Нет транскрипта — повторный анализ невозможен.\n"
                "Загрузите файл заново через вкладку 'Загрузка'.",
                parent=self)
            return

        cfg = load_config()
        provider = cfg.get("analysis_provider", "google")
        model = cfg.get("analysis_model", "gemini-2.5-flash")
        api_key = cfg.get(f"{provider}_api_key", "")
        if not api_key:
            messagebox.showerror("Ошибка",
                f"Не задан API ключ для {provider}. Откройте Настройки.",
                parent=self)
            return

        instr_name = cfg.get("active_instruction", "")
        instruction = load_instruction(instr_name) if instr_name else ""

        self.btn_reanalyze.configure(state="disabled", text="Анализ...")
        thread = threading.Thread(target=self._run_reanalyze,
                                  args=(provider, api_key, transcript,
                                        instruction, model, instr_name),
                                  daemon=True)
        thread.start()

    def _run_reanalyze(self, provider, api_key, transcript, instruction,
                       model, instr_name):
        try:
            analysis = analyze(provider, api_key, transcript, instruction, model)
            db.update_call(self.call_id, {
                "status": "done",
                "transcript": transcript,
                "analysis": analysis,
            })
            self.call = db.get_call(self.call_id)
            self.after(0, self._on_reanalyze_done)
        except Exception as e:
            err = str(e)
            self.after(0, lambda: messagebox.showerror(
                "Ошибка анализа", err, parent=self))
            self.after(0, lambda: self.btn_reanalyze.configure(
                state="normal", text="Повторный анализ"))

    def _on_reanalyze_done(self):
        self._populate()
        self.btn_reanalyze.configure(state="normal", text="Повторный анализ")
        if self.on_change:
            self.on_change()
        messagebox.showinfo("Готово", "Анализ обновлён", parent=self)


def open_call_detail(master, call_id: int, on_change=None):
    win = CallDetailWindow(master, call_id, on_change=on_change)
    win.lift()
    win.focus_set()
    return win
