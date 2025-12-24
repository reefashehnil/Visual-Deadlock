import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time

# ============================
# SYSTEM CONFIGURATION
# ============================
RESOURCES = {
    "R1": 10,
    "R2": 8,
    "R3": 6,
    "R4": 4,
    "R5": 2
}

processes = {}
waiting_requests = {}
process_counter = 1
deadlock_flag = False

pos = {
    "R1": (-4.4, 2),
    "R2": (-2.2, 2),
    "R3": (0.0, 2),
    "R4": (2.2, 2),
    "R5": (4.4, 2)
}

class DeadlockSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(" Resource Allocation & Deadlock Simulator ")
        self.root.configure(bg="#f0f4f8")
        self.root.geometry("1300x900")

        # Modern style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=12)
        style.configure('TLabel', font=('Helvetica', 12), background='#f0f4f8')
        style.configure('Header.TLabel', font=('Helvetica', 20, 'bold'), foreground='#2c3e50', background='#f0f4f8')

        # Header
        header = ttk.Label(root, text="Resource Allocation & Deadlock Simulator", style='Header.TLabel')
        header.pack(pady=30)

        # Graph canvas
        self.fig, self.ax = plt.subplots(figsize=(14, 7))
        self.fig.patch.set_facecolor('#f0f4f8')
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="➕ Add New Process", command=self.add_process).grid(row=0, column=0, padx=25)
        ttk.Button(btn_frame, text="✏️ Modify Process", command=self.modify_process).grid(row=0, column=1, padx=25)
        ttk.Button(btn_frame, text="🔄 Refresh Graph", command=self.refresh_graph).grid(row=0, column=2, padx=25)
        ttk.Button(btn_frame, text="🚪 Exit", command=root.quit).grid(row=0, column=3, padx=25)

        # Status
        self.status_label = ttk.Label(root, text="Status: Ready", font=('Helvetica', 14), foreground="#27ae60")
        self.status_label.pack(pady=10)

        self.draw_graph()

    def draw_graph(self, show_deadlock=False):
        self.ax.clear()
        self.ax.set_xlim(-7, 7)
        self.ax.set_ylim(-len(processes) * 1.6 - 1, 4)
        self.ax.axis("off")

        if show_deadlock:
            self.ax.text(0, 3.2, "🚨 DEADLOCK OCCURRED 🚨",
                         fontsize=28, color="red", fontweight="bold", ha="center")

        # Resources
        for r, total in RESOURCES.items():
            x, y = pos[r]
            self.ax.add_patch(FancyBboxPatch((x - 0.6, y - 0.4), 1.2, 0.8,
                                             boxstyle="round,pad=0.15", facecolor="lightblue",
                                             edgecolor="navy", linewidth=3))
            self.ax.text(x, y + 0.55, r, ha="center", fontsize=16, fontweight="bold")

            allocated = sum(processes.get(p, {}).get(r, 0) for p in processes)
            remaining = total - allocated
            for i in range(remaining):
                row, col = divmod(i, 5)
                self.ax.add_patch(Circle((x - 0.45 + col * 0.22, y - 0.15 - row * 0.25),
                                         0.07, color="green"))

        # Processes
        for p in processes:
            x, y = pos[p]
            self.ax.add_patch(Circle((x, y), 0.45, color="lightgreen", ec="darkgreen", lw=3))
            self.ax.text(x, y, p, ha="center", va="center", fontsize=16, fontweight="bold")

        # Allocated arrows
        for p in processes:
            px, py = pos[p]
            for r, cnt in processes[p].items():
                rx, ry = pos[r]
                for i in range(cnt):
                    off = (i - (cnt - 1) / 2) * 0.15
                    self.ax.annotate("", xy=(px - off, py + 0.4), xytext=(rx + off, ry - 0.4),
                                     arrowprops=dict(arrowstyle="->", lw=2.5, color="orange"))

        # Waiting arrows
        for p in waiting_requests:
            px, py = pos[p]
            for r, cnt in waiting_requests[p].items():
                rx, ry = pos[r]
                for i in range(cnt):
                    off = (i - (cnt - 1) / 2) * 0.15
                    self.ax.annotate("", xy=(rx - off, ry + 0.45), xytext=(px + off, py - 0.45),
                                     arrowprops=dict(arrowstyle="->", lw=2.5, color="limegreen", linestyle="dashed"))

        self.canvas.draw()

    def animate_arrow(self, start, end, color="orange", steps=20, pause=0.05):
        x0, y0 = start
        x1, y1 = end
        for i in range(1, steps + 1):
            t = i / steps
            self.ax.annotate("", xy=(x0 + t * (x1 - x0), y0 + t * (y1 - y0)),
                             xytext=(x0, y0),
                             arrowprops=dict(arrowstyle="->", lw=3, color=color))
            self.canvas.draw()
            self.root.update_idletasks()
            time.sleep(pause)
        self.draw_graph(deadlock_flag)

    def select_victim(self):
        return max(processes, key=lambda p: sum(processes[p].values()))

    def apply_preemption(self):
        global deadlock_flag
        victim = self.select_victim()
        self.status_label.config(text=f"Preempting victim process: {victim}", foreground="red")

        px, py = pos[victim]
        for r, cnt in list(processes[victim].items()):
            rx, ry = pos[r]
            for i in range(cnt):
                off = (i - (cnt - 1) / 2) * 0.15
                self.animate_arrow((px + off, py + 0.4), (rx - off, ry - 0.4), color="gold")

        processes[victim].clear()
        waiting_requests.pop(victim, None)
        self.update_waiting()
        deadlock_flag = False
        self.status_label.config(text="Deadlock resolved via preemption", foreground="#27ae60")
        self.draw_graph()

    def execute_request(self, pid, request):
        global deadlock_flag
        deadlock_flag = False
        potential_deadlock = False

        for r, req in request.items():
            remaining = RESOURCES[r] - sum(processes.get(p, {}).get(r, 0) for p in processes)
            alloc = min(req, remaining)
            wait = req - alloc

            rx, ry = pos[r]
            px, py = pos[pid]

            if alloc > 0:
                processes[pid][r] = processes[pid].get(r, 0) + alloc
                for i in range(alloc):
                    off = (i - (alloc - 1) / 2) * 0.15
                    self.animate_arrow((rx + off, ry - 0.4), (px - off, py + 0.4), color="orange")

            if wait > 0:
                potential_deadlock = True
                waiting_requests.setdefault(pid, {})[r] = waiting_requests[pid].get(r, 0) + wait
                for i in range(wait):
                    off = (i - (wait - 1) / 2) * 0.15
                    self.animate_arrow((px + off, py - 0.45), (rx - off, ry + 0.45), color="limegreen")

        if potential_deadlock:
            deadlock_flag = True
            self.draw_graph(True)
            if messagebox.askyesno("🚨 Deadlock Detected!", "A deadlock has been detected!\nApply preemption to resolve it?"):
                self.apply_preemption()
            else:
                self.status_label.config(text="Deadlock persists (preemption declined)", foreground="red")

        self.refresh_graph()

    def update_waiting(self):
        fulfilled = []
        for p in list(waiting_requests):
            for r in list(waiting_requests[p]):
                remaining = RESOURCES[r] - sum(processes.get(proc, {}).get(r, 0) for proc in processes)
                alloc = min(waiting_requests[p][r], remaining)
                if alloc > 0:
                    processes[p][r] = processes[p].get(r, 0) + alloc
                    waiting_requests[p][r] -= alloc
                    if waiting_requests[p][r] == 0:
                        del waiting_requests[p][r]
                    fulfilled.append((p, r, alloc))
            if not waiting_requests[p]:
                del waiting_requests[p]

        if fulfilled:
            for p, r, cnt in fulfilled:
                rx, ry = pos[r]
                px, py = pos[p]
                for i in range(cnt):
                    off = (i - (cnt - 1) / 2) * 0.15
                    self.animate_arrow((rx + off, ry - 0.4), (px - off, py + 0.4), color="orange")

    def get_resource_request(self):
        req = {}
        avail = {r: RESOURCES[r] - sum(processes.get(p, {}).get(r, 0) for p in processes) for r in RESOURCES}

        dialog = tk.Toplevel(self.root)
        dialog.title("Request Resources")
        dialog.configure(bg="#ecf0f1")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Current Availability", font=('Helvetica', 14, 'bold')).pack(pady=15)
        for r, a in avail.items():
            ttk.Label(dialog, text=f"{r}: {a} available", font=('Helvetica', 12)).pack()

        ttk.Label(dialog, text="\nEnter requested instances (0 = none):", font=('Helvetica', 12)).pack(pady=10)

        entries = {}
        for r in RESOURCES:
            frame = ttk.Frame(dialog)
            frame.pack(pady=8)
            ttk.Label(frame, text=f"{r}: ", width=5).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=10, font=('Helvetica', 12))
            entry.pack(side=tk.LEFT)
            entry.insert(0, "0")
            entries[r] = entry

        def submit():
            try:
                for r, e in entries.items():
                    val = int(e.get())
                    if val > 0:
                        req[r] = val
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")

        ttk.Button(dialog, text="Submit Request", command=submit).pack(pady=30)

        self.root.wait_window(dialog)
        return req

    def add_process(self):
        global process_counter
        pid = f"P{process_counter}"
        pos[pid] = (0, -process_counter * 1.6)
        processes[pid] = {}
        waiting_requests[pid] = {}
        self.status_label.config(text=f"New process {pid} created", foreground="#2980b9")
        req = self.get_resource_request()
        if req:
            self.execute_request(pid, req)
        process_counter += 1

    def release_resources_gui(self, pid):
        if not processes[pid]:
            messagebox.showinfo("Info", f"{pid} holds no resources.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Release Resources from {pid}")
        dialog.configure(bg="#ecf0f1")

        ttk.Label(dialog, text=f"Current holdings of {pid}:", font=('Helvetica', 14, 'bold')).pack(pady=15)
        for r, cnt in processes[pid].items():
            ttk.Label(dialog, text=f"{r}: {cnt}").pack()

        resource_var = tk.StringVar(value=list(processes[pid].keys())[0])
        ttk.Label(dialog, text="Resource to release:").pack(pady=10)
        ttk.Combobox(dialog, textvariable=resource_var, values=list(processes[pid].keys()), state="readonly").pack()

        amount_var = tk.IntVar(value=1)
        ttk.Label(dialog, text="Amount:").pack(pady=5)
        ttk.Entry(dialog, textvariable=amount_var).pack()

        def release():
            r = resource_var.get()
            rel = amount_var.get()
            if rel < 1 or rel > processes[pid][r]:
                messagebox.showerror("Error", "Invalid amount")
                return

            px, py = pos[pid]
            rx, ry = pos[r]
            for i in range(rel):
                off = (i - (rel - 1) / 2) * 0.15
                self.animate_arrow((px + off, py + 0.4), (rx - off, ry - 0.4), color="gold")

            processes[pid][r] -= rel
            if processes[pid][r] == 0:
                del processes[pid][r]

            self.update_waiting()
            dialog.destroy()
            self.refresh_graph()
            self.status_label.config(text="Resources released", foreground="#27ae60")

        ttk.Button(dialog, text="Release", command=release).pack(pady=20)

    def modify_process(self):
        if not processes:
            messagebox.showinfo("No Processes", "Create a process first.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Modify Process")
        dialog.configure(bg="#ecf0f1")

        ttk.Label(dialog, text="Select Process:", font=('Helvetica', 14)).pack(pady=15)
        proc_var = tk.StringVar(value=list(processes.keys())[0])
        ttk.Combobox(dialog, textvariable=proc_var, values=list(processes.keys()), state="readonly").pack(pady=5)

        action_var = tk.StringVar(value="request")
        ttk.Radiobutton(dialog, text="Request more resources", variable=action_var, value="request").pack(pady=10)
        ttk.Radiobutton(dialog, text="Release resources", variable=action_var, value="release").pack()

        def proceed():
            p = proc_var.get()
            act = action_var.get()
            dialog.destroy()
            if act == "request":
                req = self.get_resource_request()
                if req:
                    self.execute_request(p, req)
            else:
                self.release_resources_gui(p)

        ttk.Button(dialog, text="Proceed", command=proceed).pack(pady=30)

    def refresh_graph(self):
        self.draw_graph(deadlock_flag)
        self.status_label.config(text="Graph updated", foreground="#2980b9")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockSimulatorApp(root)
    root.mainloop()
    print("\n🎓 Simulation Finished")
