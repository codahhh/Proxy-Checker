
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re

# =========================
# CONFIGURATION
# =========================

BG = "#111318"
PANEL = "#1b1e25"
ACCENT = "#38bdf8"
TEXT = "#ffffff"
MUTED = "#999999"

results = []
proxies = []


# =========================
# VALIDATION
# =========================

def validate_proxy(proxy):
    proxy = proxy.strip()

    match = re.fullmatch(
        r"(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})",
        proxy
    )

    if not match:
        return False

    ip = match.group(1)
    port = int(match.group(2))

    if not all(0 <= int(part) <= 255 for part in ip.split(".")):
        return False

    if not 1 <= port <= 65535:
        return False

    return True


def parse_list(text):
    valid = []
    invalid = []
    seen = set()

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line in seen:
            continue

        seen.add(line)

        if validate_proxy(line):
            valid.append(line)
        else:
            invalid.append(line)

    return valid, invalid


# =========================
# IMPORT
# =========================

def import_file():
    path = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not path:
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        input_area.delete("1.0", tk.END)
        input_area.insert(tk.END, content)

        refresh_list()

    except Exception as e:
        messagebox.showerror("Erreur", str(e))


# =========================
# REFRESH
# =========================

def refresh_list():
    global proxies, results

    proxies, invalid = parse_list(
        input_area.get("1.0", tk.END)
    )

    results = []

    for item in tree.get_children():
        tree.delete(item)

    total = len(proxies) + len(invalid)

    progress["maximum"] = max(total, 1)
    progress["value"] = total

    for proxy in proxies:
        tree.insert(
            "",
            tk.END,
            values=(proxy, "FORMAT OK", "—"),
            tags=("valid",)
        )

    for proxy in invalid:
        tree.insert(
            "",
            tk.END,
            values=(proxy, "INVALID", "—"),
            tags=("invalid",)
        )

    counter_label.config(
        text=f"{total} entrées | {len(proxies)} valides | {len(invalid)} invalides"
    )

    status_label.config(
        text="Liste analysée"
    )


# =========================
# EXPORT
# =========================

def export_valid():
    valid, invalid = parse_list(
        input_area.get("1.0", tk.END)
    )

    if not valid:
        messagebox.showinfo(
            "Export",
            "Aucune entrée valide à exporter."
        )
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        initialfile="valid_proxies.txt"
    )

    if not path:
        return

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(valid))

        messagebox.showinfo(
            "Export",
            f"{len(valid)} entrées exportées."
        )

    except Exception as e:
        messagebox.showerror("Erreur", str(e))


def clear_all():
    input_area.delete("1.0", tk.END)
    refresh_list()


# =========================
# GUI
# =========================

root = tk.Tk()
root.title("Proxy Checker")
root.geometry("850x650")
root.minsize(700, 550)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background=PANEL,
    foreground=TEXT,
    fieldbackground=PANEL,
    rowheight=29,
    borderwidth=0
)

style.configure(
    "Treeview.Heading",
    background="#252a34",
    foreground=TEXT,
    font=("Arial", 10, "bold")
)

style.map(
    "Treeview",
    background=[("selected", "#263e55")],
    foreground=[("selected", "white")]
)

style.configure(
    "Horizontal.TProgressbar",
    troughcolor="#252a34",
    background=ACCENT
)


# TITLE

tk.Label(
    root,
    text="PROXY CHECKER",
    font=("Arial", 24, "bold"),
    fg=ACCENT,
    bg=BG
).pack(pady=(20, 4))

tk.Label(
    root,
    text="Proxy list manager & validator",
    font=("Arial", 10),
    fg=MUTED,
    bg=BG
).pack(pady=(0, 18))


# INPUT

tk.Label(
    root,
    text="Proxy list (IP:PORT)",
    fg=TEXT,
    bg=BG,
    font=("Arial", 11, "bold")
).pack(anchor="w", padx=25)

input_area = tk.Text(
    root,
    height=8,
    bg=PANEL,
    fg=TEXT,
    insertbackground=TEXT,
    font=("Consolas", 10),
    relief="flat",
    padx=10,
    pady=8
)

input_area.pack(
    fill="x",
    padx=25,
    pady=10
)


# BUTTONS

button_frame = tk.Frame(root, bg=BG)
button_frame.pack(fill="x", padx=25)

tk.Button(
    button_frame,
    text="📂 IMPORT TXT",
    command=import_file,
    bg="#252a34",
    fg=TEXT,
    relief="flat",
    pady=9
).pack(side="left", expand=True, fill="x", padx=(0, 5))

tk.Button(
    button_frame,
    text="🔎 ANALYSER",
    command=refresh_list,
    bg="#2563eb",
    fg="white",
    relief="flat",
    pady=9
).pack(side="left", expand=True, fill="x", padx=5)

tk.Button(
    button_frame,
    text="🗑 EFFACER",
    command=clear_all,
    bg="#252a34",
    fg=TEXT,
    relief="flat",
    pady=9
).pack(side="left", expand=True, fill="x", padx=(5, 0))


# PROGRESS

progress = ttk.Progressbar(
    root,
    mode="determinate",
    style="Horizontal.TProgressbar"
)

progress.pack(fill="x", padx=25, pady=15)


# COUNTERS

counter_label = tk.Label(
    root,
    text="0 entrées",
    fg=MUTED,
    bg=BG
)

counter_label.pack()


# TABLE

columns = ("proxy", "status", "latency")

tree = ttk.Treeview(
    root,
    columns=columns,
    show="headings",
    height=12
)

tree.heading("proxy", text="PROXY")
tree.heading("status", text="STATUS")
tree.heading("latency", text="INFO")

tree.column("proxy", width=400)
tree.column("status", width=180, anchor="center")
tree.column("latency", width=120, anchor="center")

tree.tag_configure(
    "valid",
    foreground="#4ade80"
)

tree.tag_configure(
    "invalid",
    foreground="#f87171"
)

tree.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=10
)


# STATUS

status_label = tk.Label(
    root,
    text="En attente...",
    fg=MUTED,
    bg=BG
)

status_label.pack(pady=5)


# EXPORT

tk.Button(
    root,
    text="↓  EXPORTER LES ENTRÉES VALIDES",
    command=export_valid,
    bg="#252a34",
    fg=TEXT,
    relief="flat",
    font=("Arial", 10, "bold"),
    pady=10
).pack(fill="x", padx=25, pady=(5, 20))


root.mainloop()
