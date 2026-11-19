
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import queue
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TEST_URL = "https://api.ipify.org?format=json"
TIMEOUT = 8
MAX_WORKERS = 10

results_queue = queue.Queue()
results = []
running = False


def parse_proxies(text):
    proxies = []
    for line in text.splitlines():
        line = line.strip()
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}", line):
            ip, port = line.split(":")
            if all(0 <= int(x) <= 255 for x in ip.split(".")) and 1 <= int(port) <= 65535:
                if line not in proxies:
                    proxies.append(line)
    return proxies


def check_proxy(proxy):
    start = time.time()
    config = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }

    try:
        response = requests.get(
            TEST_URL,
            proxies=config,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            latency = round((time.time() - start) * 1000)
            return proxy, "LIVE", latency

        return proxy, "DEAD", 0

    except requests.exceptions.Timeout:
        return proxy, "TIMEOUT", 0
    except requests.exceptions.RequestException:
        return proxy, "DEAD", 0


def start_check():
    global running, results

    if running:
        return

    proxies = parse_proxies(input_area.get("1.0", tk.END))

    if not proxies:
        messagebox.showwarning("Attention", "Aucun proxy valide trouvé.")
        return

    results = []
    running = True

    for item in tree.get_children():
        tree.delete(item)

    progress["maximum"] = len(proxies)
    progress["value"] = 0

    status_label.config(text=f"Test de {len(proxies)} proxies...")
    start_button.config(state="disabled")

    threading.Thread(
        target=run_tests,
        args=(proxies,),
        daemon=True
    ).start()

    root.after(100, process_queue)


def run_tests(proxies):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(check_proxy, proxy)
            for proxy in proxies
        ]

        for future in as_completed(futures):
            results_queue.put(future.result())

    results_queue.put(None)


def process_queue():
    global running

    try:
        while True:
            item = results_queue.get_nowait()

            if item is None:
                running = False
                start_button.config(state="normal")
                live = sum(1 for r in results if r[1] == "LIVE")
                status_label.config(
                    text=f"Terminé ! {live} proxies fonctionnels sur {len(results)}."
                )
                return

            proxy, status, latency = item
            results.append(item)

            tree.insert(
                "",
                tk.END,
                values=(
                    proxy,
                    status,
                    f"{latency} ms" if status == "LIVE" else "-"
                )
            )

            progress["value"] += 1
            live = sum(1 for r in results if r[1] == "LIVE")
            counter_label.config(
                text=f"{len(results)} / {int(progress['maximum'])} | LIVE : {live}"
            )

    except queue.Empty:
        pass

    if running:
        root.after(100, process_queue)


def export_results():
    live_proxies = [
        proxy for proxy, status, latency in results
        if status == "LIVE"
    ]

    if not live_proxies:
        messagebox.showinfo("Export", "Aucun proxy fonctionnel à exporter.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Fichier TXT", "*.txt")],
        initialfile="working_proxies.txt"
    )

    if path:
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(live_proxies))

        messagebox.showinfo("Export", "Export terminé !")


# INTERFACE

root = tk.Tk()
root.title("Proxy Checker")
root.geometry("850x650")
root.minsize(700, 550)
root.configure(bg="#111318")

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    background="#1b1e25",
    foreground="white",
    fieldbackground="#1b1e25",
    rowheight=27
)
style.configure(
    "Treeview.Heading",
    background="#252a34",
    foreground="white"
)
style.configure(
    "Horizontal.TProgressbar",
    troughcolor="#252a34",
    background="#38bdf8"
)

title = tk.Label(
    root,
    text="PROXY CHECKER",
    font=("Arial", 23, "bold"),
    fg="#38bdf8",
    bg="#111318"
)
title.pack(pady=(20, 5))

subtitle = tk.Label(
    root,
    text="HTTP Proxy Connectivity Tester",
    font=("Arial", 10),
    fg="#999999",
    bg="#111318"
)
subtitle.pack(pady=(0, 15))

tk.Label(
    root,
    text="Liste des proxies (IP:PORT)",
    fg="white",
    bg="#111318",
    font=("Arial", 11, "bold")
).pack(anchor="w", padx=25)

input_area = tk.Text(
    root,
    height=8,
    bg="#1b1e25",
    fg="white",
    insertbackground="white",
    font=("Consolas", 10),
    relief="flat"
)
input_area.pack(fill="x", padx=25, pady=10)

start_button = tk.Button(
    root,
    text="▶  LANCER LES TESTS",
    command=start_check,
    bg="#2563eb",
    fg="white",
    activebackground="#1d4ed8",
    relief="flat",
    font=("Arial", 11, "bold"),
    pady=10
)
start_button.pack(fill="x", padx=25, pady=5)

progress = ttk.Progressbar(
    root,
    mode="determinate",
    style="Horizontal.TProgressbar"
)
progress.pack(fill="x", padx=25, pady=10)

counter_label = tk.Label(
    root,
    text="0 / 0 | LIVE : 0",
    fg="#aaaaaa",
    bg="#111318"
)
counter_label.pack()

columns = ("proxy", "status", "latency")

tree = ttk.Treeview(
    root,
    columns=columns,
    show="headings",
    height=11
)

tree.heading("proxy", text="PROXY")
tree.heading("status", text="STATUS")
tree.heading("latency", text="LATENCY")

tree.column("proxy", width=350)
tree.column("status", width=150, anchor="center")
tree.column("latency", width=150, anchor="center")

tree.pack(fill="both", expand=True, padx=25, pady=10)

tree.tag_configure("LIVE", foreground="#4ade80")
tree.tag_configure("DEAD", foreground="#f87171")
tree.tag_configure("TIMEOUT", foreground="#facc15")

status_label = tk.Label(
    root,
    text="En attente...",
    fg="#999999",
    bg="#111318"
)
status_label.pack(pady=5)

export_button = tk.Button(
    root,
    text="↓  EXPORTER LES PROXIES LIVE",
    command=export_results,
    bg="#252a34",
    fg="white",
    relief="flat",
    font=("Arial", 10, "bold"),
    pady=9
)
export_button.pack(fill="x", padx=25, pady=(5, 20))

root.mainloop()
