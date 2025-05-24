import subprocess
import json
import os
import time
import tkinter as tk
import threading

CONFIG_FILE = "config.json"
MINER_DIR = "miner"

miner_process = None
loop_mining = False


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def build_command(cfg):
    miner_path = os.path.join(MINER_DIR, cfg["miner_exe"])
    cpu_threads = os.cpu_count() or 1
    print(f'Launching miner with {cpu_threads} CPU threads")

    return [
        miner_path,
        "-a", cfg["algorithm"],
        "-o", cfg["pool"],
        "-u", cfg["user"],
        "-p", cfg["password"],
        "-t", str(cpu_threads)
    ]

def estimate_profit(khash):
    try:
        network_hashrate_kh = 900_000_000  # 900 TH/s in kH/s
        block_reward = 6.25
        block_time = 150
        ltc_price = 72.0

        blocks_per_day = 86400 / block_time
        user_share = khash / network_hashrate_kh
        ltc_per_day = user_share * blocks_per_day * block_reward
        usd_per_day = ltc_per_day * ltc_price

        return ltc_per_day, usd_per_day
    except:
        return 0.0, 0.0


def start_miner():
    global miner_process, loop_mining
    cfg = load_config()

    def run():
        nonlocal cfg
        while True:
            cmd = build_command(cfg)
            output_text.insert(tk.END, "\n▶ Starting miner...\n")
            try:
                miner_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in miner_process.stdout:
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
            except Exception as e:
                output_text.insert(tk.END, f"\n❌ Error: {e}\n")

            if not loop_mining:
                break
            time.sleep(2)
            output_text.insert(tk.END, "\n🔁 Restarting miner...\n")

    threading.Thread(target=run, daemon=True).start()


def stop_miner():
    global miner_process
    if miner_process:
        miner_process.terminate()
        output_text.insert(tk.END, "\n⛔ Miner stopped.\n")
        miner_process = None


def update_profit():
    try:
        khs = float(hashrate_entry.get())
        ltc, usd = estimate_profit(khs)
        profit_result.config(text=f"Est. Profit: ~{ltc:.6f} LTC/day (~${usd:.2f}/day)")
    except:
        profit_result.config(text="Invalid input.")


# GUI Setup
root = tk.Tk()
root.title("Litecoin Miner GUI")

info_frame = tk.Frame(root)
info_frame.pack(pady=5)

cpu_label = tk.Label(info_frame, text=f"CPU Cores: {os.cpu_count()}")
cpu_label.pack(side=tk.LEFT, padx=10)

gpu_label = tk.Label(info_frame, text=f"GPUs: 0 (nvidia-smi not found)")
gpu_label.pack(side=tk.LEFT)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

start_btn = tk.Button(button_frame, text="Start Mining", command=start_miner)
start_btn.pack(side=tk.LEFT, padx=5)

stop_btn = tk.Button(button_frame, text="Stop", command=stop_miner)
stop_btn.pack(side=tk.LEFT, padx=5)

loop_var = tk.BooleanVar()
loop_toggle = tk.Checkbutton(button_frame, text="Loop", variable=loop_var, command=lambda: setattr(globals(), 'loop_mining', loop_var.get()))
loop_toggle.pack(side=tk.LEFT)

output_text = tk.Text(root, height=20, width=90)
output_text.pack(pady=5)

profit_frame = tk.Frame(root)
profit_frame.pack(pady=5)

# Add a label to display the estimated hashrate
hashrate_est_label = tk.Label(profit_frame, text="Estimated Hashrate: ~0.00 kH/s")
hashrate_est_label.pack(side=tk.LEFT, padx=10)

profit_result = tk.Label(profit_frame, text="Est. Profit: ~0.0000 LTC/day (~$0.00/day)")
profit_result.pack(side=tk.LEFT, padx=10)

root.mainloop()
