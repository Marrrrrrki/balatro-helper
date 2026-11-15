
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

from core.save_reader import (
    read_jkr_retry,
    extract_state,
    find_steam_save,
)
from core.advisor import analyze
from ui.card_renderer import CardRenderer
from ui.joker_renderer import JokerRenderer


BG = "#10131b"
PANEL = "#191f2b"
TEXT = "#f1f4fa"
MUTED = "#9aa6ba"
ACCENT = "#5de0e6"
GOLD = "#f5c86a"


class AdvisorWindow:
    def __init__(self, root, initial_path=None):
        self.root = root
        self.path = initial_path
        self.state = None
        self.last_mtime = None
        self.analysis_result = None
        self.busy = False

        self.auto_refresh = tk.BooleanVar(value=True)
        self.simulations = tk.IntVar(value=120)

        self.card_renderer = CardRenderer(root)
        self.card_images = []

        self.joker_renderer = JokerRenderer(root)
        self.joker_images = []

        self._style()
        self._build()

        if self.path and Path(self.path).exists():
            self.load_save()
        else:
            self.show_empty()

        self.root.after(1500, self._watch_loop)

    def _style(self):
        self.root.configure(bg=BG)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)

        style.configure(
            "TLabel",
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Muted.TLabel",
            background=BG,
            foreground=MUTED,
        )

        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=("Segoe UI", 22, "bold"),
        )

        style.configure(
            "Section.TLabel",
            background=PANEL,
            foreground=ACCENT,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#10131b",
        )

        style.map(
            "Accent.TButton",
            background=[("active", "#8df0f2")],
        )

        style.configure(
            "Treeview",
            background="#111722",
            fieldbackground="#111722",
            foreground=TEXT,
            rowheight=27,
        )

        style.configure(
            "Treeview.Heading",
            background="#252e3d",
            foreground=TEXT,
            font=("Segoe UI", 9, "bold"),
        )

    def _build(self):
        header = ttk.Frame(self.root, padding=(22, 18))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="BALATRO ADVISOR",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Label(
            header,
            text="VANILLA • READ-ONLY ANALYSIS",
            style="Muted.TLabel",
        ).pack(side="left", padx=18, pady=(8, 0))

        controls = ttk.Frame(header)
        controls.pack(side="right")

        ttk.Button(
            controls,
            text="Open save.jkr",
            command=self.choose_file,
        ).pack(side="left", padx=4)

        ttk.Button(
            controls,
            text="Refresh",
            command=self.load_save,
        ).pack(side="left", padx=4)

        self.path_label = ttk.Label(
            self.root,
            text="No save selected",
            style="Muted.TLabel",
        )
        self.path_label.pack(anchor="w", padx=24, pady=(0, 12))

        self.content = ttk.Frame(
            self.root,
            padding=(22, 0, 22, 20),
        )
        self.content.pack(fill="both", expand=True)

        # Run statistics
        self.top = ttk.Frame(self.content)
        self.top.pack(fill="x")

        self.stat_labels = {}

        for key, label in [
            ("blind", "BLIND"),
            ("target", "TARGET"),
            ("hands", "HANDS"),
            ("discards", "DISCARDS"),
            ("deck", "DECK"),
            ("ante", "ANTE"),
        ]:
            box = tk.Frame(
                self.top,
                bg=PANEL,
                padx=14,
                pady=12,
            )
            box.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 8),
            )

            tk.Label(
                box,
                text=label,
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")

            val = tk.Label(
                box,
                text="—",
                bg=PANEL,
                fg=TEXT,
                font=("Segoe UI", 14, "bold"),
            )
            val.pack(anchor="w", pady=(4, 0))

            self.stat_labels[key] = val

        # Main panels
        mid = ttk.Frame(self.content)
        mid.pack(fill="both", expand=True, pady=14)

        left = tk.Frame(
            mid,
            bg=PANEL,
            padx=16,
            pady=14,
        )
        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8),
        )

        tk.Label(
            left,
            text="YOUR HAND",
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        self.hand_frame = tk.Frame(left, bg=PANEL)
        self.hand_frame.pack(fill="x", pady=12)

        # Joker collection
        tk.Label(
            left,
            text="JOKERS",
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(10, 4))

        self.joker_frame = tk.Frame(left, bg=PANEL)
        self.joker_frame.pack(fill="x", pady=(4, 8))

        # Recommendation panel
        right = tk.Frame(
            mid,
            bg=PANEL,
            padx=16,
            pady=14,
            width=410,
        )
        right.pack(side="right", fill="both", expand=True)
        right.pack_propagate(False)

        tk.Label(
            right,
            text="RECOMMENDATION",
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        self.recommend_label = tk.Label(
            right,
            text="Load a save to begin",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 20, "bold"),
            wraplength=350,
            justify="left",
        )
        self.recommend_label.pack(anchor="w", pady=(14, 4))

        self.score_label = tk.Label(
            right,
            text="",
            bg=PANEL,
            fg=GOLD,
            font=("Segoe UI", 18, "bold"),
        )
        self.score_label.pack(anchor="w", pady=3)

        self.reason_label = tk.Label(
            right,
            text="",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
            wraplength=350,
            justify="left",
        )
        self.reason_label.pack(anchor="w", pady=(8, 12))

        ttk.Button(
            right,
            text="Analyze hand + simulate discards",
            style="Accent.TButton",
            command=self.run_analysis,
        ).pack(anchor="w", pady=4)

        opts = tk.Frame(right, bg=PANEL)
        opts.pack(anchor="w", pady=8)

        tk.Label(
            opts,
            text="Discard simulations:",
            bg=PANEL,
            fg=MUTED,
        ).pack(side="left")

        ttk.Spinbox(
            opts,
            from_=30,
            to=500,
            increment=30,
            textvariable=self.simulations,
            width=6,
        ).pack(side="left", padx=8)

        ttk.Checkbutton(
            opts,
            text="Watch save automatically",
            variable=self.auto_refresh,
        ).pack(side="left", padx=8)

        self.status = ttk.Label(
            self.content,
            text="Ready",
            style="Muted.TLabel",
        )
        self.status.pack(anchor="w", pady=(2, 0))

        # Scoring breakdown
        bottom = tk.Frame(
            self.content,
            bg=PANEL,
            padx=14,
            pady=12,
        )
        bottom.pack(fill="both", expand=True)

        tk.Label(
            bottom,
            text="SCORING BREAKDOWN",
            bg=PANEL,
            fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        self.breakdown = tk.Text(
            bottom,
            height=8,
            bg="#111722",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Consolas", 9),
            wrap="word",
        )
        self.breakdown.pack(
            fill="both",
            expand=True,
            pady=(8, 0),
        )
        self.breakdown.configure(state="disabled")

    def show_empty(self):
        self.path_label.configure(
            text=(
                "Choose your save.jkr file, or place it in "
                "%APPDATA%\\Balatro\\<profile>\\save.jkr"
            )
        )

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Select Balatro save.jkr",
            filetypes=[
                ("Balatro save", "*.jkr"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.path = Path(path)
            self.load_save()

    def load_save(self):
        if not self.path or not Path(self.path).exists():
            self.path = find_steam_save()

        if not self.path or not Path(self.path).exists():
            self.show_empty()
            messagebox.showinfo(
                "Save not found",
                "Choose your save.jkr with the Open save.jkr button.",
            )
            return

        try:
            root = read_jkr_retry(self.path)
            self.state = extract_state(root)

            self.last_mtime = Path(self.path).stat().st_mtime
            self.path_label.configure(text=f"Reading: {self.path}")

            self._render_state()

            self.status.configure(
                text=(
                    f"Loaded Balatro {self.state['version']} "
                    "• Save is read-only"
                )
            )

        except Exception as exc:
            self.status.configure(text="Could not load save")
            messagebox.showerror("Save read error", str(exc))

    def _render_state(self):
        s = self.state

        self.stat_labels["blind"].configure(text=s["blind_name"])
        self.stat_labels["target"].configure(
            text=f"{s['blind_target']:,}"
        )
        self.stat_labels["hands"].configure(
            text=str(s["hands_left"])
        )
        self.stat_labels["discards"].configure(
            text=str(s["discards_left"])
        )
        self.stat_labels["deck"].configure(
            text=str(len(s["deck"]))
        )
        self.stat_labels["ante"].configure(
            text=str(s["ante"])
        )

        # Render playing cards
        for child in self.hand_frame.winfo_children():
            child.destroy()

        self.card_images.clear()

        for card in s["hand"]:
            card_frame = tk.Frame(
                self.hand_frame,
                bg=PANEL,
                padx=2,
            )
            card_frame.pack(side="left", padx=2)

            photo = self.card_renderer.get_card_image(card)

            if photo:
                self.card_images.append(photo)

                tk.Label(
                    card_frame,
                    image=photo,
                    bg=PANEL,
                    bd=0,
                ).pack()
            else:
                suit_symbols = {
                    "Hearts": "♥",
                    "Diamonds": "♦",
                    "Clubs": "♣",
                    "Spades": "♠",
                }

                red = card["suit"] in ("Hearts", "Diamonds")
                fg = "#e05b68" if red else "#273044"

                fallback = tk.Frame(
                    card_frame,
                    bg="#ffffff",
                    width=71,
                    height=95,
                    highlightbackground="#c9c1b3",
                    highlightthickness=1,
                )
                fallback.pack()
                fallback.pack_propagate(False)

                tk.Label(
                    fallback,
                    text=str(card["rank_name"]),
                    bg="#ffffff",
                    fg=fg,
                    font=("Segoe UI", 12, "bold"),
                ).pack(anchor="nw", padx=5)

                tk.Label(
                    fallback,
                    text=suit_symbols.get(card["suit"], "?"),
                    bg="#ffffff",
                    fg=fg,
                    font=("Segoe UI", 24, "bold"),
                ).pack(expand=True)

            extras = []

            enhancement = card.get("enhancement")
            if enhancement and enhancement != "Base":
                extras.append(str(enhancement).replace("m_", ""))

            edition = card.get("edition")
            if edition:
                extras.append(str(edition))

            seal = card.get("seal")
            if seal:
                extras.append(str(seal).replace("Red", "Red Seal"))

            if extras:
                tk.Label(
                    card_frame,
                    text=" ".join(extras),
                    bg=PANEL,
                    fg=GOLD,
                    font=("Segoe UI", 7, "bold"),
                    wraplength=75,
                ).pack(pady=(3, 0))

        # Render Joker icons
        for child in self.joker_frame.winfo_children():
            child.destroy()

        self.joker_images.clear()

        jokers = s.get("jokers", [])

        if not jokers:
            tk.Label(
                self.joker_frame,
                text="No Jokers",
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 10),
            ).pack(anchor="w")
        else:
            for joker in jokers:
                save_fields = joker.get("save_fields", {}) or {}

                name = save_fields.get("center", "Unknown Joker")
                display_name = (
                    name.replace("j_", "")
                    .replace("_", " ")
                    .title()
                )

                joker_card = tk.Frame(
                    self.joker_frame,
                    bg="#252e3d",
                    padx=5,
                    pady=5,
                    highlightbackground="#46536a",
                    highlightthickness=1,
                )
                joker_card.pack(side="left", padx=(0, 8), pady=3)

                photo = None

                try:
                    photo = self.joker_renderer.get_joker_image(joker)
                except Exception:
                    photo = None

                if photo:
                    self.joker_images.append(photo)

                    tk.Label(
                        joker_card,
                        image=photo,
                        bg="#252e3d",
                        bd=0,
                    ).pack()
                else:
                    # Fallback icon if the Joker image is unavailable.
                    tk.Label(
                        joker_card,
                        text="★",
                        bg="#252e3d",
                        fg=GOLD,
                        font=("Segoe UI", 25, "bold"),
                        width=4,
                        height=2,
                    ).pack()

                tk.Label(
                    joker_card,
                    text=display_name,
                    bg="#252e3d",
                    fg=TEXT,
                    font=("Segoe UI", 8, "bold"),
                    wraplength=85,
                    justify="center",
                ).pack(pady=(4, 0))

        if not self.card_renderer.available:
            self.status.configure(
                text=(
                    "Card atlas unavailable. "
                    "Check assets/8BitDeck.png and install Pillow."
                )
            )

    def run_analysis(self):
        if not self.state or self.busy:
            return

        self.busy = True

        self.status.configure(
            text="Analyzing combinations and simulating discards…"
        )

        simulation_count = max(
            30,
            min(500, int(self.simulations.get())),
        )

        state_snapshot = self.state

        def worker():
            try:
                result = analyze(
                    state_snapshot,
                    simulation_count,
                )

                self.root.after(
                    0,
                    lambda: self._show_analysis(result),
                )

            except Exception as exc:
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Analysis error",
                        str(exc),
                    ),
                )

            finally:
                self.root.after(
                    0,
                    lambda: setattr(self, "busy", False),
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def _show_analysis(self, result):
        self.analysis_result = result
        best = result["best"]

        if not best:
            return

        self.recommend_label.configure(
            text=result["recommendation"]
        )

        self.score_label.configure(
            text=(
                f"{best['evaluation']['name']} "
                f"• {best['score']:,} estimated points"
            )
        )

        self.reason_label.configure(text=result["reason"])

        cards = ", ".join(
            card["name"] for card in best["cards"]
        )

        lines = [
            f"BEST CURRENT PLAY: {best['evaluation']['name']}",
            f"Cards selected: {cards}",
            f"Estimated score: {best['score']:,}",
            (
                f"Chips: {best['chips']:,.1f}    "
                f"Mult: {best['mult']:,.2f}"
            ),
            "",
            "TRIGGER BREAKDOWN",
            *[
                f"  • {line}"
                for line in best["notes"]
            ],
        ]

        if result.get("discard"):
            discard = result["discard"]

            lines += [
                "",
                (
                    "BEST DISCARD CANDIDATE "
                    f"(Monte Carlo EV {discard['ev']:,.0f})"
                ),
                "Discard: " + ", ".join(
                    card["name"]
                    for card in discard["cards"]
                ),
            ]

        if best.get("unsupported_jokers"):
            lines += [
                "",
                "ACCURACY WARNING: Unsupported Joker effects not calculated:",
                "  • " + ", ".join(
                    best["unsupported_jokers"]
                ),
            ]

        lines += [
            "",
            (
                "Model limitations: vanilla Joker coverage is partial; "
                "probabilistic effects, retriggers, debuffs, special blind "
                "rules and some card interactions are not fully simulated."
            ),
        ]

        self.breakdown.configure(state="normal")
        self.breakdown.delete("1.0", "end")
        self.breakdown.insert("1.0", "\n".join(lines))
        self.breakdown.configure(state="disabled")

        self.status.configure(
            text=(
                "Analysis complete • estimates only; "
                "verify special effects in-game"
            )
        )

    def _watch_loop(self):
        try:
            if (
                self.auto_refresh.get()
                and self.path
                and Path(self.path).exists()
            ):
                mtime = Path(self.path).stat().st_mtime

                if (
                    self.last_mtime is not None
                    and mtime != self.last_mtime
                    and not self.busy
                ):
                    self.load_save()

            self.root.after(1500, self._watch_loop)

        except Exception:
            self.root.after(3000, self._watch_loop)
