import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np
import time

# ============================
# INITIAL SETUP
# ============================
TOTAL_INSTANCES = 10
RESOURCES = {f"R{i}": TOTAL_INSTANCES for i in range(1, 6)}
processes = {}          # Allocated resources per process
waiting_requests = {}   # Waiting requests per process
process_counter = 1

print("\n🎉 RESOURCE ALLOCATION SIMULATOR WITH ANIMATION 🎉")

# Node positions
pos = {f"R{i}": (i*2.2-5.5, 2) for i in range(1, 6)}

# ============================
# DRAW NODES
# ============================
def draw_nodes(current_pid=None):
    """Draw the entire graph. Only animate the arrows for current_pid."""
    plt.close("all")
    fig, ax = plt.subplots(figsize=(14,9))
    ax.set_xlim(-7, 7)
    ax.set_ylim(-process_counter*1.6-1, 4)
    ax.axis('off')

    # Draw resource boxes and dots
    for r in RESOURCES:
        x, y = pos[r]
        box = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8,
                             boxstyle="round,pad=0.15", facecolor="lightblue",
                             edgecolor="navy", linewidth=3)
        ax.add_patch(box)
        ax.text(x, y+0.55, r, ha='center', fontsize=16, fontweight='bold')

        allocated = sum(processes[p].get(r,0) for p in processes)
        remaining = TOTAL_INSTANCES - allocated
        for i in range(remaining):
            row = i // 5
            col = i % 5
            ax.add_patch(Circle((x-0.45 + col*0.22, y-0.15 - row*0.25), 0.07, color="green"))

    # Draw all processes
    for p in processes:
        x, y = pos[p]
        ax.add_patch(Circle((x, y), 0.45, color="lightgreen", ec="darkgreen", lw=3))
        ax.text(x, y, p, ha='center', va='center', fontsize=16, fontweight='bold')

    # Draw all previous allocations as static arrows (without animation)
    for proc in processes:
        if proc == current_pid:
            continue
        for r, cnt in processes[proc].items():
            rx, ry = pos[r]
            pxp, pyp = pos[proc]
            for i in range(cnt):
                offset = (i - (cnt-1)/2)*0.15
                ax.annotate('', xy=(pxp-offset, pyp+0.4), xytext=(rx+offset, ry-0.4),
                            arrowprops=dict(arrowstyle="->", color="orange", lw=2))

        # Draw previous waiting requests as green arrows
        for r, cnt in waiting_requests.get(proc, {}).items():
            rx, ry = pos[r]
            pxp, pyp = pos[proc]
            for i in range(cnt):
                offset = (i - (cnt-1)/2)*0.15
                ax.annotate('', xy=(rx-offset, ry+0.4), xytext=(pxp+offset, pyp-0.45),
                            arrowprops=dict(arrowstyle="->", color="limegreen", lw=2, linestyle='dashed'))

    return fig, ax

# ============================
# Animate arrows for new process
# ============================
def animate_arrow(ax, start, end, color="orange", steps=20):
    x0, y0 = start
    x1, y1 = end
    for i in range(1, steps+1):
        t = i / steps
        ax.annotate('', xy=(x0 + t*(x1-x0), y0 + t*(y1-y0)), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", color=color, lw=3))
        plt.pause(0.03)

def animate_wait_arrow(ax, start, end, color="green", steps=20, curve_height=1.0):
    x0, y0 = start
    x1, y1 = end
    cx, cy = (x0+x1)/2, max(y0, y1)+curve_height
    for i in range(1, steps+1):
        t = i / steps
        x = (1-t)**2*x0 + 2*(1-t)*t*cx + t**2*x1
        y = (1-t)**2*y0 + 2*(1-t)*t*cy + t**2*y1
        if i == 1:
            line, = ax.plot([x0, x], [y0, y], color=color, lw=3, linestyle='dashed')
        else:
            line.set_data([x0, x], [y0, y])
        plt.pause(0.03)

# ============================
# Deadlock detection
# ============================
def detect_deadlock():
    for req in waiting_requests.values():
        if req:
            return True
    return False

# ============================
# MAIN LOOP
# ============================
while True:
    choice = input("\nAdd a new process? (yes/no): ").strip().lower()
    if choice not in ("yes", "y"):
        break

    pid = f"P{process_counter}"
    pos[pid] = (0, -process_counter*1.6)
    processes[pid] = {}
    waiting_requests[pid] = {}
    print(f"\n➕ Adding {pid}")

    # Show resource availability
    for r in RESOURCES:
        allocated = sum(processes[p].get(r,0) for p in processes)
        remaining = TOTAL_INSTANCES - allocated
        print(f"{r} → {remaining} available")

    # Select resources
    selected = input("Resources (R1,R2,... or ALL): ").replace(" ", "").upper()
    if selected == "ALL":
        selected = list(RESOURCES.keys())
    else:
        selected = selected.split(",")

    # Allocate or mark waiting
    for r in selected:
        if r not in RESOURCES:
            continue
        remaining = TOTAL_INSTANCES - sum(processes[p].get(r,0) for p in processes)
        if remaining == 0:
            waiting_requests[pid][r] = int(input(f"{r} requested but unavailable. How many do you want? "))
            continue
        requested = int(input(f"{r} instances (0-{remaining} available): "))
        if requested <= remaining:
            processes[pid][r] = requested
        else:
            processes[pid][r] = remaining
            waiting_requests[pid][r] = requested - remaining

    # Draw current graph
    fig, ax = draw_nodes(current_pid=pid)
    px, py = pos[pid]

    # Animate allocation arrows only for this process
    for r, cnt in processes[pid].items():
        rx, ry = pos[r]
        for i in range(cnt):
            offset = (i - (cnt-1)/2)*0.15
            animate_arrow(ax, (rx+offset, ry-0.4), (px-offset, py+0.4), color="orange")

    # Animate waiting arrows only for this process
    for r, cnt in waiting_requests[pid].items():
        rx, ry = pos[r]
        for i in range(cnt):
            offset = (i - (cnt-1)/2)*0.15
            animate_wait_arrow(ax, (px+offset, py-0.45), (rx-offset, ry+0.4), color="limegreen")

    # Deadlock warning
    if detect_deadlock():
        ax.text(0, -process_counter*0.9, "⚠️ DEADLOCK OCCURRED ⚠️", color="red",
                fontsize=20, fontweight="bold", ha="center")

    plt.show(block=False)
    plt.pause(0.2)
    process_counter += 1

# ============================
# FINAL STATUS
# ============================
print("\n📊 FINAL RESOURCE STATUS:")
for r in RESOURCES:
    remaining = TOTAL_INSTANCES - sum(processes[p].get(r,0) for p in processes)
    print(f"{r} → {remaining} instances remaining")

print("\n📄 Process Allocations:")
for p, alloc in processes.items():
    print(f"{p}:")
    for r, v in alloc.items():
        print(f"  {r} → {v} instance(s)")

draw_nodes()
print("\n🎓 Simulation Finished")
