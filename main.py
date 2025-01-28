import threading
import queue
import time
import random
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------------------- Gestión de Procesos -------------------- #
class Process:
    def __init__(self, pid, priority, execution_time):
        self.pid = pid
        self.priority = priority
        self.execution_time = execution_time
        self.state = "Nuevo"

    def __repr__(self):
        return f"Process(ID={self.pid}, Priority={self.priority}, Time={self.execution_time:.2f}, State={self.state})"

class Scheduler:
    def __init__(self, algorithm="FCFS"):
        self.algorithm = algorithm
        self.ready_queue = queue.Queue()
        self.running_process = None

    def add_process(self, process):
        if process.state != "Bloqueado":  # Only add processes with allocated memory
            process.state = "Listo"
            self.ready_queue.put(process)

    def schedule(self):
        if self.algorithm == "FCFS":
            return self.ready_queue.get() if not self.ready_queue.empty() else None
        elif self.algorithm == "SJF":
            # Shortest Job First
            all_processes = list(self.ready_queue.queue)
            all_processes.sort(key=lambda p: p.execution_time)
            self.ready_queue = queue.Queue()
            for proc in all_processes:
                self.ready_queue.put(proc)
            return self.ready_queue.get() if not self.ready_queue.empty() else None
        elif self.algorithm == "Round Robin":
            return self.ready_queue.get() if not self.ready_queue.empty() else None

    def run(self):
        while not self.ready_queue.empty():
            self.running_process = self.schedule()
            if self.running_process:
                self.running_process.state = "Ejecutando"
                update_ui()
                print(f"Executing {self.running_process}")
                time.sleep(self.running_process.execution_time)
                self.running_process.state = "Terminado"
                update_ui()
                print(f"Finished {self.running_process}")

# -------------------- Gestión de Memoria -------------------- #
class MemoryManager:
    def __init__(self, total_frames=10):
        self.total_frames = total_frames
        self.page_table = {}
        self.free_frames = list(range(total_frames))

    def allocate_memory(self, process_id, pages):
        if len(self.free_frames) < pages:
            print(f"Not enough memory for Process {process_id}")
            return False

        allocated = []
        for _ in range(pages):
            frame = self.free_frames.pop(0)
            allocated.append(frame)

        self.page_table[process_id] = allocated
        print(f"Process {process_id} allocated frames: {allocated}")
        update_memory_ui(self)
        return True

    def deallocate_memory(self, process_id):
        if process_id in self.page_table:
            freed_frames = self.page_table.pop(process_id)
            self.free_frames.extend(freed_frames)
            print(f"Process {process_id} deallocated frames: {freed_frames}")
            update_memory_ui(self)

# -------------------- Gestión de E/S -------------------- #
class IOManager:
    def __init__(self):
        self.device_queue = queue.Queue()

    def request_io(self, process):
        print(f"Process {process.pid} requesting I/O...")
        self.device_queue.put(process)
        process.state = "Bloqueado"
        update_ui()
        time.sleep(random.uniform(0.5, 2))
        process.state = "Listo"
        update_ui()
        print(f"Process {process.pid} I/O completed.")

# -------------------- Concurrencia -------------------- #
def simulate_concurrent_execution(scheduler):
    def run():
        while not scheduler.ready_queue.empty():
            process = scheduler.schedule()
            if process:
                execute_process(process)
                time.sleep(0.1)  # Breve pausa entre la programación de procesos

    threading.Thread(target=run).start()

# -------------------- Ejecución de Procesos -------------------- #
def execute_process(process):
    process.state = "Ejecutando"
    update_ui()
    update_monitoring_ui()
    print(f"Executing {process}")

    def run_process_step():
        if process.execution_time > 0:
            process.execution_time -= 0.1
            update_monitoring_ui()
            app.root.after(100, run_process_step)  # Llamar a esta función nuevamente después de 100ms
        else:
            process.state = "Terminado"
            update_ui()
            update_monitoring_ui()
            print(f"Finished {process}")

    run_process_step()

# -------------------- Interfaz Gráfica con Plano de Monitoreo -------------------- #
class SimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OS Simulator")

        # Process List
        self.process_frame = ttk.LabelFrame(root, text="Process Management")
        self.process_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.process_list = ttk.Treeview(self.process_frame, columns=("PID", "Priority", "Time", "State"),
                                         show="headings")
        self.process_list.heading("PID", text="PID")
        self.process_list.heading("Priority", text="Priority")
        self.process_list.heading("Time", text="Time")
        self.process_list.heading("State", text="State")
        self.process_list.pack(fill="both", expand=True)

        # Memory Management
        self.memory_frame = ttk.LabelFrame(root, text="Memory Management")
        self.memory_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.memory_canvas = tk.Canvas(self.memory_frame, height=200, width=400)
        self.memory_canvas.pack(fill="both", expand=True)

        # Monitoring Panel
        self.monitor_frame = ttk.LabelFrame(root, text="Process Monitoring")
        self.monitor_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        self.figure, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.monitor_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Control Buttons
        self.control_frame = ttk.Frame(root)
        self.control_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.start_button = ttk.Button(self.control_frame, text="Start Simulation", command=start_simulation)
        self.start_button.pack(side="left", padx=5)


# -------------------- Actualización del Plano de Monitoreo -------------------- #
def update_monitoring_ui():
    app.ax.clear()
    app.ax.set_title("Process Execution Monitoring")
    app.ax.set_xlabel("Time Remaining")
    app.ax.set_ylabel("Process ID")

    # Data for the chart
    process_ids = [process.pid for process in processes]
    times = [process.execution_time if process.state != "Terminado" else 0 for process in processes]
    colors = ["blue" if process.state == "Ejecutando" else "gray" for process in processes]

    app.ax.barh(process_ids, times, color=colors)

    app.canvas.draw()



# -------------------- Actualización UI -------------------- #
def update_ui():
    app.process_list.delete(*app.process_list.get_children())
    for process in processes:
        app.process_list.insert("", "end", values=(process.pid, process.priority, f"{process.execution_time:.2f}", process.state))
    app.root.update_idletasks()

def update_memory_ui(memory_manager):
    app.memory_canvas.delete("all")
    x, y = 10, 10
    for frame in range(memory_manager.total_frames):
        color = "green" if frame in memory_manager.free_frames else "red"
        app.memory_canvas.create_rectangle(x, y, x + 30, y + 30, fill=color, outline="black")
        x += 40
        if (frame + 1) % 10 == 0:
            x = 10
            y += 40
    app.root.update_idletasks()

# -------------------- Simulación -------------------- #
def start_simulation():
    threading.Thread(target=run_simulation).start()

def run_simulation():
    simulate_concurrent_execution(scheduler)
    app.root.after(1000, finalize_simulation)  # Verificar finalización después de 1 segundo

def finalize_simulation():
    for process in processes:
        memory_manager.deallocate_memory(process.pid)
    print("Simulation finished.")
    update_ui()
    update_memory_ui(memory_manager)

def main():
    global app, processes, scheduler, memory_manager

    print("Initializing OS Simulator...")

    # Scheduler Setup
    scheduler = Scheduler(algorithm="FCFS")

    # Memory Manager Setup
    memory_manager = MemoryManager(total_frames=20)  # Increased memory to handle more processes

    # Start GUI
    root = tk.Tk()
    app = SimulatorApp(root)

    # Start the GUI loop
    root.after(100, initialize_simulation)  # Initialize simulation after GUI is ready
    root.mainloop()

def initialize_simulation():
    global processes, scheduler, memory_manager

    # Create Processes
    processes = [Process(pid=i, priority=random.randint(1, 5), execution_time=random.uniform(1, 3)) for i in range(10)]

    for process in processes:
        if memory_manager.allocate_memory(process.pid, pages=2):
            scheduler.add_process(process)
        else:
            process.state = "Bloqueado"  # Mark as blocked if no memory is available

    # Update UI with initial state
    update_ui()
    update_memory_ui(memory_manager)

if __name__ == "__main__":
    main()