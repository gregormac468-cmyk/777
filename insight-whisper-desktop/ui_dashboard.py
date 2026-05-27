"""
Вкладка 'Дашборд' с графиками и статистикой.
"""
import customtkinter as ctk
from tkinter import END
from datetime import datetime, timedelta
from collections import defaultdict

import database as db

# matplotlib для графиков
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def _classify(call_type: str) -> str:
    if not call_type:
        return "other"
    t = call_type.lower()
    if "нерезульт" in t:
        return "fail"
    if "обеспеч" in t:
        return "secure"
    if "результат" in t:
        return "result"
    return "other"


class DashboardTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.canvas = None
        self._build()
        self.refresh()

    def _build(self):
        # Фильтры
        filters = ctk.CTkFrame(self.parent)
        filters.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(filters, text="Период:").pack(side="left", padx=(10, 4))
        self.period_var = ctk.StringVar(value="Сегодня")
        ctk.CTkOptionMenu(filters, variable=self.period_var,
                          values=["Сегодня", "7 дней", "30 дней",
                                  "Этот месяц", "Всё время"],
                          command=lambda _: self.refresh(),
                          width=140).pack(side="left", padx=4)

        ctk.CTkLabel(filters, text="Менеджер:").pack(side="left", padx=(10, 4))
        self.manager_var = ctk.StringVar(value="__all__")
        self.manager_menu = ctk.CTkOptionMenu(filters, variable=self.manager_var,
                                              values=["__all__"], width=160,
                                              command=lambda _: self.refresh())
        self.manager_menu.pack(side="left", padx=4)

        ctk.CTkButton(filters, text="Обновить", command=self.refresh,
                      width=100).pack(side="left", padx=10)



        # KPI-карточки
        self.kpi_frame = ctk.CTkFrame(self.parent)
        self.kpi_frame.pack(fill="x", padx=10, pady=10)

        self.kpi_cards = {}
        kpis = [
            ("total", "Всего звонков", "#3b82f6"),
            ("avg_score", "Средняя оценка", "#8b5cf6"),
            ("good_pct", "Хороших (≥7)", "#16a34a"),
            ("fail_count", "Нерезультативных", "#dc2626"),
        ]
        for i, (key, label, color) in enumerate(kpis):
            card = ctk.CTkFrame(self.kpi_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")
            self.kpi_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=label, font=("", 12),
                         text_color="white").pack(pady=(10, 0))
            value_lbl = ctk.CTkLabel(card, text="—", font=("", 28, "bold"),
                                     text_color="white")
            value_lbl.pack(pady=(0, 10))
            self.kpi_cards[key] = value_lbl

        # Контейнер для графиков
        self.charts_frame = ctk.CTkFrame(self.parent)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_managers(self):
        names = ["__all__"] + db.list_manager_names()
        self.manager_menu.configure(values=names)
        if self.manager_var.get() not in names:
            self.manager_var.set("__all__")

    def _date_range(self):
        period = self.period_var.get()
        today = datetime.now().date()
        if period == "Сегодня":
            return today.isoformat(), today.isoformat()
        if period == "7 дней":
            return (today - timedelta(days=6)).isoformat(), today.isoformat()
        if period == "30 дней":
            return (today - timedelta(days=29)).isoformat(), today.isoformat()
        if period == "Этот месяц":
            return today.replace(day=1).isoformat(), today.isoformat()
        return None, None



    def refresh(self):
        self.refresh_managers()
        df, dt = self._date_range()
        mgr = self.manager_var.get()
        calls = db.list_calls(
            date_from=df, date_to=dt,
            manager=mgr if mgr != "__all__" else None,
            limit=100000,
        )

        # KPI
        total = len(calls)
        scored = [c["overall_score"] for c in calls
                  if c.get("overall_score") is not None]
        avg = (sum(scored) / len(scored)) if scored else 0
        good = sum(1 for s in scored if s >= 7)
        fail_count = sum(1 for c in calls if _classify(c.get("call_type", "")) == "fail")

        self.kpi_cards["total"].configure(text=str(total))
        self.kpi_cards["avg_score"].configure(
            text=f"{avg:.2f}" if scored else "—"
        )
        self.kpi_cards["good_pct"].configure(
            text=f"{good*100//len(scored)}%" if scored else "—"
        )
        self.kpi_cards["fail_count"].configure(text=str(fail_count))

        # Графики
        self._draw_charts(calls)

    def _draw_charts(self, calls):
        # Очистить старый canvas
        for w in self.charts_frame.winfo_children():
            w.destroy()
        if self.canvas:
            self.canvas = None

        if not calls:
            ctk.CTkLabel(self.charts_frame,
                         text="Нет данных за выбранный период",
                         font=("", 14)).pack(expand=True)
            return

        fig = Figure(figsize=(12, 7), dpi=90, facecolor="#f8fafc")
        fig.subplots_adjust(left=0.07, right=0.97, top=0.93, bottom=0.12,
                            wspace=0.3, hspace=0.45)

        # 1. Динамика по дням
        ax1 = fig.add_subplot(2, 2, 1)
        self._chart_by_day(ax1, calls)

        # 2. Распределение типов
        ax2 = fig.add_subplot(2, 2, 2)
        self._chart_by_type(ax2, calls)

        # 3. Топ менеджеров
        ax3 = fig.add_subplot(2, 2, 3)
        self._chart_by_manager(ax3, calls)

        # 4. Распределение оценок
        ax4 = fig.add_subplot(2, 2, 4)
        self._chart_score_dist(ax4, calls)

        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas



    def _chart_by_day(self, ax, calls):
        by_day = defaultdict(list)
        for c in calls:
            s = c.get("overall_score")
            created = c.get("created_at", "")
            if isinstance(created, str) and created:
                try:
                    d = datetime.fromisoformat(created).date().isoformat()
                except Exception:
                    d = created[:10]
            else:
                continue
            if s is not None:
                by_day[d].append(s)

        days = sorted(by_day.keys())
        if not days:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Средняя оценка по дням", fontsize=11)
            return

        avgs = [sum(by_day[d]) / len(by_day[d]) for d in days]
        ax.plot(days, avgs, marker="o", color="#3b82f6", linewidth=2)
        ax.fill_between(days, avgs, alpha=0.2, color="#3b82f6")
        ax.set_ylim(0, 10)
        ax.set_title("Средняя оценка по дням", fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)

    def _chart_by_type(self, ax, calls):
        counts = {"Результативный": 0, "Обеспечительный": 0,
                  "Нерезультативный": 0, "Другое": 0}
        for c in calls:
            k = _classify(c.get("call_type", ""))
            if k == "result":
                counts["Результативный"] += 1
            elif k == "secure":
                counts["Обеспечительный"] += 1
            elif k == "fail":
                counts["Нерезультативный"] += 1
            else:
                counts["Другое"] += 1

        labels = [k for k, v in counts.items() if v > 0]
        sizes = [v for v in counts.values() if v > 0]
        colors_map = {"Результативный": "#16a34a", "Обеспечительный": "#d97706",
                      "Нерезультативный": "#dc2626", "Другое": "#94a3b8"}
        chart_colors = [colors_map[l] for l in labels]

        if sizes:
            ax.pie(sizes, labels=labels, colors=chart_colors,
                   autopct="%1.0f%%", startangle=90,
                   textprops={"fontsize": 9})
        ax.set_title("Типы звонков", fontsize=11)



    def _chart_by_manager(self, ax, calls):
        by_mgr = defaultdict(list)
        for c in calls:
            m = c.get("manager_name") or "(без менеджера)"
            s = c.get("overall_score")
            if s is not None:
                by_mgr[m].append(s)

        if not by_mgr:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Средняя оценка по менеджерам", fontsize=11)
            return

        items = sorted(by_mgr.items(),
                       key=lambda x: sum(x[1]) / len(x[1]),
                       reverse=True)[:10]
        names = [i[0][:18] for i in items]
        avgs = [sum(s) / len(s) for _, s in items]

        bar_colors = ["#16a34a" if a >= 7 else ("#d97706" if a >= 4 else "#dc2626")
                      for a in avgs]
        bars = ax.barh(names, avgs, color=bar_colors)
        ax.set_xlim(0, 10)
        ax.set_title("Средняя оценка по менеджерам", fontsize=11)
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=8)
        ax.invert_yaxis()
        for bar, v in zip(bars, avgs):
            ax.text(v + 0.1, bar.get_y() + bar.get_height() / 2,
                    f"{v:.1f}", va="center", fontsize=8)

    def _chart_score_dist(self, ax, calls):
        scored = [c["overall_score"] for c in calls
                  if c.get("overall_score") is not None]
        if not scored:
            ax.text(0.5, 0.5, "Нет оценок", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Распределение оценок", fontsize=11)
            return

        bins = [0, 4, 7, 10.01]
        n_bad = sum(1 for s in scored if s < 4)
        n_mid = sum(1 for s in scored if 4 <= s < 7)
        n_good = sum(1 for s in scored if s >= 7)

        ax.bar(["Низкие\n(<4)", "Средние\n(4-7)", "Хорошие\n(≥7)"],
               [n_bad, n_mid, n_good],
               color=["#dc2626", "#d97706", "#16a34a"])
        ax.set_title("Распределение оценок", fontsize=11)
        ax.tick_params(axis="both", labelsize=9)
        for i, v in enumerate([n_bad, n_mid, n_good]):
            ax.text(i, v + 0.05, str(v), ha="center", fontsize=10, fontweight="bold")
