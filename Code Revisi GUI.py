import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import time

# Konfigurasi serial
serial_port = "COM7"  # Sesuaikan dengan port Arduino Anda
baud_rate = 9600

try:
    arduino = serial.Serial(serial_port, baud_rate, timeout=1)
except Exception as e:
    print(f"Error: {e}")
    arduino = None

# Variabel global untuk data
time_data = []
rpm_data = []
setpoint_data = []

# Fungsi untuk mengirim perintah ke Arduino
def send_command(command):
    if arduino and arduino.is_open:
        arduino.write((command + "\n").encode())
    else:
        print("Error: Koneksi serial tidak tersedia.")

# Fungsi kontrol motor
def start_motor(direction):
    rpm = rpm_entry.get()
    if rpm.isdigit():
        if direction == "forward":
            send_command(f"F{rpm}")
        elif direction == "reverse":
            send_command(f"R{rpm}")
    else:
        ctk.CTkMessagebox.show_error("Error", "Masukkan nilai RPM yang valid.")

def stop_motor():
    send_command("STOP")

# Fungsi memperbarui parameter PID
def update_pid():
    try:
        kp = float(kp_entry.get())
        ki = float(ki_entry.get())
        kd = float(kd_entry.get())
        send_command(f"PID,{kp},{ki},{kd}")
    except ValueError:
        ctk.CTkMessagebox.show_error("Error", "Masukkan nilai PID yang valid.")

# Fungsi membaca data dari Arduino
def read_data():
    global time_data, rpm_data, setpoint_data
    start_time = time.time()
    while True:
        if arduino and arduino.is_open:
            try:
                line = arduino.readline().decode().strip()
                if line.startswith("DATA:"):
                    timestamp, rpm, setpoint = line[5:].split(",")
                    current_time = round(float(timestamp), 2)
                    rpm = float(rpm)
                    setpoint = float(setpoint)

                    # Perbarui data
                    time_data.append(current_time)
                    rpm_data.append(rpm)
                    setpoint_data.append(setpoint)

                    # Jaga ukuran data agar tidak terlalu besar
                    if len(time_data) > 100:
                        time_data.pop(0)
                        rpm_data.pop(0)
                        setpoint_data.pop(0)

                    update_graph()

                    # Perbarui label data
                    data_label.configure(
                        text=f"Waktu: {current_time} s\nRPM: {rpm}\nSetpoint: {setpoint}"
                    )
            except Exception as e:
                print(f"Error membaca data: {e}")
        time.sleep(0.1)

# Fungsi memperbarui grafik
def update_graph():
    ax.clear()
    ax.plot(time_data, rpm_data, label="RPM", color="blue")
    ax.plot(time_data, setpoint_data, label="Setpoint", color="red", linestyle="--")
    ax.set_title("Grafik RPM vs Waktu")
    ax.set_xlabel("Waktu (s)")
    ax.set_ylabel("RPM")
    ax.legend()
    canvas.draw()

# GUI dengan CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Kontrol Motor DC dengan PID")
root.geometry("900x500")

# Frame kiri untuk kontrol
left_frame = ctk.CTkFrame(root, width=300, height=500)
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

# Input RPM
rpm_label = ctk.CTkLabel(left_frame, text="RPM Target:")
rpm_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
rpm_entry = ctk.CTkEntry(left_frame)
rpm_entry.grid(row=1, column=0, padx=10, pady=5)

# Tombol kontrol motor
forward_button = ctk.CTkButton(
    left_frame, text="Maju", command=lambda: start_motor("forward")
)
forward_button.grid(row=2, column=0, padx=10, pady=5)

reverse_button = ctk.CTkButton(
    left_frame, text="Mundur", command=lambda: start_motor("reverse")
)
reverse_button.grid(row=3, column=0, padx=10, pady=5)

stop_button = ctk.CTkButton(left_frame, text="Stop", command=stop_motor)
stop_button.grid(row=4, column=0, padx=10, pady=5)

# Input PID
pid_label = ctk.CTkLabel(left_frame, text="Parameter PID:")
pid_label.grid(row=5, column=0, padx=10, pady=(20, 0), sticky="w")

kp_label = ctk.CTkLabel(left_frame, text="Kp:")
kp_label.grid(row=6, column=0, padx=10, pady=(10, 0), sticky="w")
kp_entry = ctk.CTkEntry(left_frame)
kp_entry.grid(row=7, column=0, padx=10, pady=5)
kp_entry.insert(0, "1.0")

ki_label = ctk.CTkLabel(left_frame, text="Ki:")
ki_label.grid(row=8, column=0, padx=10, pady=(10, 0), sticky="w")
ki_entry = ctk.CTkEntry(left_frame)
ki_entry.grid(row=9, column=0, padx=10, pady=5)
ki_entry.insert(0, "0.5")

kd_label = ctk.CTkLabel(left_frame, text="Kd:")
kd_label.grid(row=10, column=0, padx=10, pady=(10, 0), sticky="w")
kd_entry = ctk.CTkEntry(left_frame)
kd_entry.grid(row=11, column=0, padx=10, pady=5)
kd_entry.insert(0, "0.1")

update_pid_button = ctk.CTkButton(left_frame, text="Perbarui PID", command=update_pid)
update_pid_button.grid(row=12, column=0, padx=10, pady=(20, 10))

# Label data
data_label = ctk.CTkLabel(left_frame, text="Data akan muncul di sini.", justify="left")
data_label.grid(row=13, column=0, padx=10, pady=(10, 0))

# Frame kanan untuk grafik
right_frame = ctk.CTkFrame(root, width=600, height=500)
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

fig = Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)
ax.set_title("Grafik RPM vs Waktu")
ax.set_xlabel("Waktu (s)")
ax.set_ylabel("RPM")

canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack()

# Thread untuk membaca data
if arduino:
    read_thread = threading.Thread(target=read_data, daemon=True)
    read_thread.start()

# Jalankan GUI
root.mainloop()

# Tutup koneksi serial saat aplikasi ditutup
if arduino:
    arduino.close()
