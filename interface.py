import time
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
from PIL import Image, ImageTk

from detection import CutterDetection


BG_COLOR = "#F5F0E9"
NAVY = "#305070"
DARK_NAVY = "#112250"
WHITE = "#F5F0E9"
TEXT_COLOR = "#112250"
MUTED = "#305070"
BORDER = "#E0C58F"
GREEN = "#e6f9af"
RED = "#FF8A80"
YELLOW = "#FFD966"

LOCK_DURATION = 3.0  # detik - kelas harus stabil selama ini sebelum dikunci


# Kunci = nama kelas dari model (sudah dinormalisasi: huruf kecil, spasi/- jadi "_")
# SESUAIKAN dengan model.names di tuwek.pt kamu.
CLASS_INFO = {
    "normal": {
        "label": "NORMAL",
        "desc": "End mill dalam kondisi baik, tidak ditemukan kerusakan.",
        "wp_short": "Tidak perlu pengasahan. End mill siap digunakan.",
        "wp_detail": "",
        "color": "#2E7D32",
    },
    "pecah": {
        "label": "PECAH",
        "desc": "End mill pecah / patah dan sudah tidak dapat diperbaiki.",
        "wp_short": "TIDAK BISA DIASAH. Buang end mill ini.",
        "wp_detail": (
            "Buang end mill ini. Kondisi sudah pecah/patah sehingga tidak ada "
            "prosedur pengasahan yang dapat dilakukan."
        ),
        "color": "#C62828",
    },
    "chipping_ujung": {
        "label": "CHIPPING UJUNG",
        "desc": "Terdapat chipping pada bagian ujung end mill.",
        "wp_short": "Bisa diasah: lakukan regrinding pada bagian ujung (end face).",
        "wp_detail": """Penggerindaan muka:
Melakukan penggerindaan yang bertujuan untuk menghilangkan aus atau gempil pada ujung cutter hingga rata, sehingga dapat menjadi titik referensi nol.

Penggerindaan clearance angle:
Keterangan:
1. Penggerindaan sudut bebas 2° turun menuju pusat cutter
2. Penggerindaan sudut bebas 5° turun ke belakang terhadap sisi potong
3. Penggerindaan sudut bebas 15° turun ke belakang terhadap sisi potong

Bidang clearance angle 1:
- Setting sudut Index Head Slide Rest sebesar 2º untuk membentuk sudut bebas 2º masuk menuju senter.
- Setting sudut Swivel Mount (sumbu putar tengah mesin) sebesar 5° untuk membentuk sudut bebas 5º turun terhadap sisi potong.
- Atur 2 (dua) ujung sisi potong yang berseberangan sama tingginya terhadap meja mesin.
- Atur tinggi posisi pusat cutter terhadap sumbu batu gerinda, sehingga saat penggerindaan salah satu sisi potong, batu gerinda tidak memotong sisi yang lain (pedoman: semakin banyak jumlah sisi potong cutter, semakin rendah pusat cutter terhadap sumbu batu gerinda).
- Pasang stopper untuk pembatas langkah penggerindaan (panjang penggerindaan sampai batas alur cutter).

Bidang clearance angle 2:
- Setting sudut Index Head Slide Rest sebesar 2º untuk membentuk sudut bebas 2º turun menuju senter.
- Setting sudut Swivel Mount (sumbu putar tengah mesin) sebesar 15° untuk membentuk sudut bebas 15° turun terhadap sisi potong.
- Atur tinggi posisi pusat cutter terhadap sumbu batu gerinda, sehingga saat penggerindaan salah satu sisi potong batu gerinda tidak memotong sisi yang lain (pedoman sama seperti di atas).
- Pasang stopper untuk pembatas langkah penggerindaan (panjang penggerindaan sampai batas alur cutter).
- Setelah disetting semua, penggerindaan bidang bebas 2 dimulai dengan me-roughing semua sisi potong terlebih dahulu, kemudian finishing satu per satu, sehingga semua bidang bebas 2 memiliki kondisi yang sama.

Pembuatan Groove Cutter:
- Atur jarak kedua sisi potong yang berseberangan sama panjang terhadap permukaan slide menggunakan kaliper.
- Setting Index Head pada sudut 5° untuk membuat alur cutter menyimpang 5º terhadap pusat cutter.
- Setting Swivel Mount (sumbu putar tengah mesin) pada sudut 60° untuk membuat alur cutter menyudut 30° terhadap permukaan cutter.
- Setting Indexing Head Slide Rest pada sudut 5º untuk membuat rake angle cutter.
- Gunakan batu gerinda berbentuk pipih (disk).

Penggerindaan Pembuatan Chamfer:
- Atur jarak kedua sisi potong yang berseberangan sama tinggi terhadap permukaan meja mesin dengan height gauge, kemudian putar cutter 15° berlawanan arah jarum jam (dilihat dari muka cutter).
- Setting sudut Swivel Base mesin pada sudut 45°.
- Gunakan batu gerinda berbentuk mangkok miring (fairing cup).""",
        "color": "#E65100",
    },
    "chipping_flute": {
        "label": "CHIPPING FLUTE",
        "desc": "Terdapat chipping pada bagian flute end mill.",
        "wp_short": "Bisa diasah: lakukan regrinding pada bagian flute.",
        "wp_detail": """Menghitung spiral pitch (SP) / spiral lead / steigung milling cutter yang akan digerinda, apabila data spiral pitch tidak tercantum pada tangkai cutter.
Rumus: SP = (360 x L) / T
- L = Panjang langkah index head slide secukupnya (contoh 15-20mm)
- T = Sudut putar index head

Menentukan pasangan roda gigi dan diameter piringan yang akan dipasang pada indexing head berdasarkan SP:
- Lihat data pada tabel roda gigi dan diameter piringan.
- Sesuaikan dengan nilai yang mendekati perhitungan SP.
- Sesuaikan diameter piringan yang didapat dengan nilai yang tertulis pada piringan.

Memasang roda gigi dan piringan pada indexing head:
- Pastikan pemasangan sudah kencang dan aman.
- Memasang pita baja / senar penggerak pada piringan yang terpasang pada indexing head.

Menghitung sudut spiral milling cutter untuk penggerindaan spiral dalam (untuk penggerindaan spiral luar tidak perlu):
Rumus: Tan alpha = (Diameter milling x phi) / spiral pitch
- Memutar head sebesar sudut spiral milling cutter ditambah 1°-3° untuk penggerindaan spiral dalam; untuk spiral luar cukup diputar 1°-3° saja.
- Arah pemutaran (dipandang dari atas) berdasarkan arah spiral milling cutter: untuk arah spiral kanan, arah pemutaran head berlawanan arah jarum jam, dan sebaliknya.
- Mengatur posisi cutter terhadap batu gerinda.""",
        "color": "#E65100",
    },
}


def normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def run_app():
    # ---------- Inisialisasi deteksi ----------
    try:
        detector = CutterDetection()
    except Exception as e:
        messagebox.showerror("Error", f"Gagal memulai deteksi:\n{e}")
        return

    # ---------- Window utama ----------
    root = tk.Tk()
    root.title("Cutter Detection")
    root.geometry("1200x700")
    root.configure(bg=BG_COLOR)

    # Header
    header = tk.Frame(root, bg=NAVY, height=75)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="Cutter Detection", font=("Helvetica", 18, "bold"),
             fg=WHITE, bg=NAVY).pack(side="left", padx=25, pady=20)

    system_status = tk.Label(header, text="SYSTEM READY", font=("Helvetica", 14, "bold"),
                             bg=NAVY, fg=GREEN)
    system_status.pack(side="right", padx=25)

    # Footer (pack sebelum main_container agar tidak tertutup)
    footer = tk.Frame(root, bg=NAVY, height=35)
    footer.pack(fill="x", side="bottom")
    footer.pack_propagate(False)
    tk.Label(footer, text="© 2026 Cutter Detection. AI Based Tool Condition Monitoring.",
             font=("Helvetica", 10), bg=NAVY, fg=WHITE).pack(side="left", padx=20, pady=8)

    # Container utama
    main_container = tk.Frame(root, bg=BG_COLOR)
    main_container.pack(fill="both", expand=True, padx=20, pady=20)
    main_container.grid_columnconfigure(0, weight=1)
    main_container.grid_columnconfigure(1, weight=0)
    main_container.grid_rowconfigure(0, weight=1)

    # Panel kamera
    camera_panel = tk.Frame(main_container, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
    camera_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    tk.Label(camera_panel, text="CAMERA MONITOR", font=("Helvetica", 14, "bold"),
             bg=WHITE, fg=TEXT_COLOR).pack(anchor="w", padx=20, pady=20)

    camera_view = tk.Label(camera_panel, bg=DARK_NAVY)
    camera_view.pack(fill="both", expand=True, padx=20, pady=(0, 15))
    camera_placeholder = tk.Label(camera_view, text="CAMERA PREVIEW\n\nWaiting for camera input...",
                                  font=("Helvetica", 15), bg=DARK_NAVY, fg="#C8D4E0", justify="center")
    camera_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    camera_info = tk.Label(camera_panel, text="Camera Status: Connected", font=("Helvetica", 12),
                           bg=WHITE, fg=MUTED)
    camera_info.pack(anchor="w", padx=20, pady=(0, 15))

    # Panel informasi
    info_panel = tk.Frame(main_container, bg=WHITE, width=330,
                          highlightbackground=BORDER, highlightthickness=1)
    info_panel.grid(row=0, column=1, sticky="nsew")
    info_panel.grid_propagate(False)
    info_panel.pack_propagate(False)

    tk.Label(info_panel, text="INFORMATION", font=("Helvetica", 14, "bold"),
             bg=WHITE, fg=TEXT_COLOR).pack(anchor="w", padx=20, pady=20)

    # Status LIVE / TERKUNCI + tombol Scan Ulang
    status_row = tk.Frame(info_panel, bg=WHITE)
    status_row.pack(fill="x", padx=20, pady=(0, 5))

    lock_status_value = tk.Label(status_row, text="🟢 LIVE - mendeteksi...",
                                  font=("Helvetica", 10, "bold"), bg=WHITE, fg=MUTED)
    lock_status_value.pack(side="left")

    scan_button = tk.Button(status_row, text="🔄 Scan Ulang", font=("Helvetica", 10, "bold"),
                            bg=NAVY, fg=WHITE, relief="flat", cursor="hand2",
                            state="disabled")
    scan_button.pack(side="right")

    tk.Label(info_panel, text="Detection Result:", font=("Helvetica", 10, "bold"),
             bg=WHITE, fg=MUTED).pack(anchor="w", padx=20, pady=(10, 5))
    result_value = tk.Label(info_panel, text="WAITING", font=("Helvetica", 22, "bold"),
                            bg=WHITE, fg=NAVY)
    result_value.pack(anchor="w", padx=20, pady=5)
    confidence_value = tk.Label(info_panel, text="Confidence: -", font=("Helvetica", 10),
                                bg=WHITE, fg=MUTED)
    confidence_value.pack(anchor="w", padx=20)

    ttk.Separator(info_panel, orient="horizontal").pack(fill="x", padx=20, pady=20)

    tk.Label(info_panel, text="CONDITION DESCRIPTION:", font=("Helvetica", 10, "bold"),
             bg=WHITE, fg=MUTED).pack(anchor="w", padx=20, pady=5)
    description_value = tk.Label(info_panel, text="No inspection data available.",
                                 font=("Helvetica", 12), bg=WHITE, fg=TEXT_COLOR,
                                 wraplength=280, justify="left")
    description_value.pack(anchor="w", padx=20, pady=5)

    ttk.Separator(info_panel, orient="horizontal").pack(fill="x", padx=20, pady=20)

    tk.Label(info_panel, text="WORK PREPARATION", font=("Helvetica", 10, "bold"),
             bg=WHITE, fg=MUTED).pack(anchor="w", padx=20, pady=5)
    wp_value = tk.Label(info_panel, text="Waiting for detection..", font=("Helvetica", 10, "bold"),
                        bg=WHITE, fg=NAVY, wraplength=280, justify="left")
    wp_value.pack(anchor="w", padx=20, pady=5)

    wp_detail_button = tk.Button(info_panel, text="Lihat Detail Pengerjaan →",
                                  font=("Helvetica", 10, "bold"),
                                  bg=NAVY, fg=WHITE, relief="flat", cursor="hand2",
                                  state="disabled")
    wp_detail_button.pack(anchor="w", padx=20, pady=(10, 5))

    # ---------- State ----------
    state = {
        "running": True,
        "photo": None,
        "current_class": None,
        "locked": False,
        "candidate_class": None,
        "candidate_start": None,
    }

    # ---------- Jendela detail Work Preparation ----------
    def open_wp_detail(title, detail_text):
        win = tk.Toplevel(root)
        win.title(f"Detail Pengerjaan - {title}")
        win.geometry("650x550")
        win.configure(bg=BG_COLOR)

        tk.Label(win, text=title, font=("Helvetica", 16, "bold"),
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", padx=20, pady=(20, 10))

        frame = tk.Frame(win, bg=BG_COLOR)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(frame, wrap="word", font=("Helvetica", 11),
                              bg=WHITE, fg=TEXT_COLOR, relief="flat",
                              yscrollcommand=scrollbar.set, padx=15, pady=15)
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.tag_configure("subheader", font=("Helvetica", 12, "bold"),
                                  foreground=NAVY, spacing1=10, spacing3=4)
        text_widget.tag_configure("bullet", font=("Helvetica", 11),
                                  lmargin1=20, lmargin2=35, spacing3=3)
        text_widget.tag_configure("normal", font=("Helvetica", 11), spacing3=3)

        for line in detail_text.strip("\n").split("\n"):
            stripped = line.strip()
            if not stripped:
                text_widget.insert("end", "\n")
            elif stripped.endswith(":") and len(stripped) < 60:
                text_widget.insert("end", stripped + "\n", "subheader")
            elif stripped.startswith("-"):
                text_widget.insert("end", "• " + stripped.lstrip("- ") + "\n", "bullet")
            else:
                text_widget.insert("end", stripped + "\n", "normal")

        text_widget.config(state="disabled")

    def show_detail():
        key = state["current_class"]
        info = CLASS_INFO.get(key)
        if info:
            open_wp_detail(info["label"], info.get("wp_detail", ""))

    wp_detail_button.config(command=show_detail)

    # ---------- Update info panel ----------
    def update_info(cls_name, conf):
        if cls_name == "WAITING":
            result_value.config(text="WAITING", fg=NAVY)
            confidence_value.config(text="Confidence: -")
            description_value.config(text="No inspection data available.")
            wp_value.config(text="Waiting for detection..", fg=NAVY)
            wp_detail_button.config(state="disabled")
            state["current_class"] = None
            return

        key = normalize(cls_name)
        info = CLASS_INFO.get(key)
        if info is None:  # kelas tak dikenal
            result_value.config(text=cls_name.upper(), fg=NAVY)
            description_value.config(text="Kelas tidak terdaftar di CLASS_INFO.")
            wp_value.config(text="-", fg=NAVY)
            wp_detail_button.config(state="disabled")
            state["current_class"] = None
        else:
            result_value.config(text=info["label"], fg=info["color"])
            description_value.config(text=info["desc"])
            wp_value.config(text=info["wp_short"], fg=info["color"])
            state["current_class"] = key
            if info.get("wp_detail"):
                wp_detail_button.config(state="normal")
            else:
                wp_detail_button.config(state="disabled")
        confidence_value.config(text=f"Confidence: {conf * 100:.1f}%")

    # ---------- Logika lock / stability timer ----------
    def lock_result():
        state["locked"] = True
        lock_status_value.config(text="🔒 HASIL TERKUNCI", fg="#C62828")
        scan_button.config(state="normal")
        system_status.config(text="LOCKED - KLIK SCAN ULANG", fg=YELLOW)

    def reset_scan():
        state["locked"] = False
        state["candidate_class"] = None
        state["candidate_start"] = None
        lock_status_value.config(text="🟢 LIVE - mendeteksi...", fg=MUTED)
        scan_button.config(state="disabled")
        system_status.config(text="SYSTEM RUNNING", fg=GREEN)

    scan_button.config(command=reset_scan)

    def check_lock(cls_name):
        now = time.time()
        if cls_name == "WAITING":
            state["candidate_class"] = None
            state["candidate_start"] = None
            return

        key = normalize(cls_name)
        if key != state["candidate_class"]:
            state["candidate_class"] = key
            state["candidate_start"] = now
        else:
            elapsed = now - state["candidate_start"]
            if elapsed >= LOCK_DURATION:
                lock_result()

    # ---------- Loop update kamera ----------
    def update_frame():
        if not state["running"]:
            return

        if state["locked"]:
            # Saat terkunci, tampilan terakhir dibiarkan diam.
            # Tidak membaca kamera / menjalankan deteksi untuk hemat resource.
            root.after(15, update_frame)
            return

        frame, cls_name, conf = detector.get_frame()

        if frame is None:
            camera_info.config(text="Camera Status: Frame tidak terbaca")
            system_status.config(text="CAMERA ERROR", fg=RED)
        else:
            camera_info.config(text="Camera Status: Connected")
            system_status.config(text="SYSTEM RUNNING", fg=GREEN)
            camera_placeholder.place_forget()

            # Resize mengikuti ukuran area kamera, aspect ratio tetap
            w = max(camera_view.winfo_width(), 1)
            h = max(camera_view.winfo_height(), 1)
            fh, fw = frame.shape[:2]
            scale = min(w / fw, h / fh)
            new_size = (max(int(fw * scale), 1), max(int(fh * scale), 1))

            rgb = cv2.cvtColor(cv2.resize(frame, new_size), cv2.COLOR_BGR2RGB)
            state["photo"] = ImageTk.PhotoImage(Image.fromarray(rgb))  # simpan referensi!
            camera_view.config(image=state["photo"])

            update_info(cls_name, conf)
            check_lock(cls_name)

        root.after(15, update_frame)

    def on_close():
        state["running"] = False
        detector.release()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    update_frame()
    root.mainloop()
