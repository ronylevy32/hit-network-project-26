import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from protocol import send_line, recv_line

# --- הגדרות חיבור ---
SERVER_HOST = "127.0.0.1"
# וודא שזה תואם לפורט בשרת שלך (בקוד השרת שסיפקת זה היה 6543)
SERVER_PORT = 6543

# --- פלטת צבעים ורוד-לבן ---
THEME = {
    "bg_main": "#FFECF2",       # רקע כללי - ורוד בהיר מאוד
    "bg_white": "#FFFFFF",      # רקע לבן לתיבות טקסט
    "fg_text": "#880E4F",       # צבע טקסט ראשי - ורוד-בורדו כהה לקריאות
    "btn_bg": "#F48FB1",        # רקע כפתור - ורוד
    "btn_active": "#F06292",    # רקע כפתור בלחיצה - ורוד כהה יותר
    "btn_fg": "#FFFFFF",        # טקסט על כפתור - לבן
    "highlight": "#F8BBD0"      # צבע הדגשה למסגרות
}

# הגדרות גופן בסיסיות
FONT_MAIN = ("Helvetica", 11)
FONT_BTN = ("Helvetica", 10, "bold")


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pink P2P Chat")
        self.root.configure(bg=THEME["bg_main"])
        self.sock = None
        self.name = ""

        # בניית הממשק
        self.setup_ui()

    def setup_ui(self):
        # מיכל ראשי שמחזיק הכל
        main_container = tk.Frame(self.root, bg=THEME["bg_main"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- צד שמאל: אזור הצ'אט וההקלדה ---
        left_frame = tk.Frame(main_container, bg=THEME["bg_main"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # תיבת תצוגת הודעות (ScrolledText)
        self.chat_area = scrolledtext.ScrolledText(
            left_frame, state='disabled', wrap=tk.WORD,
            bg=THEME["bg_white"], fg=THEME["fg_text"],
            font=FONT_MAIN, relief=tk.FLAT,
            highlightthickness=2, highlightbackground=THEME["highlight"], highlightcolor=THEME["btn_bg"]
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # מסגרת להקלדת הודעה וכפתור שליחה
        entry_frame = tk.Frame(left_frame, bg=THEME["bg_main"])
        entry_frame.pack(fill=tk.X)

        self.msg_entry = tk.Entry(
            entry_frame, bg=THEME["bg_white"], fg=THEME["fg_text"], font=FONT_MAIN,
            relief=tk.FLAT, highlightthickness=2, highlightbackground=THEME["highlight"]
        )
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        send_btn = tk.Button(
            entry_frame, text="➤ Send", command=self.send_message,
            bg=THEME["btn_bg"], activebackground=THEME["btn_active"],
            fg=THEME["btn_fg"], activeforeground=THEME["btn_fg"],
            font=FONT_BTN, relief=tk.FLAT, padx=15, cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # --- צד ימין: סרגל כלים וכפתורי פקודה ---
        sidebar_frame = tk.Frame(main_container, bg=THEME["bg_main"], width=150)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        tk.Label(sidebar_frame, text="Controls", bg=THEME["bg_main"], fg=THEME["fg_text"], font=FONT_BTN).pack(pady=(0, 10))

        # כפתור התחלת צ'אט
        btn_chat = tk.Button(
            sidebar_frame, text="💬 Start Chat", command=self.cmd_start_chat,
            bg=THEME["btn_bg"], activebackground=THEME["btn_active"],
            fg=THEME["btn_fg"], font=FONT_BTN, relief=tk.FLAT, cursor="hand2"
        )
        btn_chat.pack(fill=tk.X, pady=5, ipady=5)

        # כפתור עזיבת צ'אט
        btn_leave = tk.Button(
            sidebar_frame, text="🏃 Leave Chat", command=self.cmd_leave_chat,
            bg=THEME["btn_bg"], activebackground=THEME["btn_active"],
            fg=THEME["btn_fg"], font=FONT_BTN, relief=tk.FLAT, cursor="hand2"
        )
        btn_leave.pack(fill=tk.X, pady=5, ipady=5)

        # קו מפריד
        tk.Frame(sidebar_frame, bg=THEME["highlight"], height=2).pack(fill=tk.X, pady=15)

        # כפתור יציאה מהתוכנה
        btn_quit = tk.Button(
            sidebar_frame, text="✖ Quit App", command=self.on_closing,
            bg="#D32F2F", activebackground="#B71C1C", # אדום ליציאה, אבל עדיין משתלב
            fg=THEME["btn_fg"], font=FONT_BTN, relief=tk.FLAT, cursor="hand2"
        )
        btn_quit.pack(side=tk.BOTTOM, fill=tk.X, pady=5, ipady=5)

        # הגדרת פרוטוקול סגירה
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- לוגיקה ---

    def log(self, message):
        self.chat_area.configure(state='normal')
        # הוספת תגיות צבע להודעות מערכת או שגיאות
        tag = None
        if message.startswith("SYS"):
             self.chat_area.tag_config("sys", foreground="#AD1457", font=(FONT_MAIN[0], FONT_MAIN[1], "italic"))
             tag = "sys"
        elif message.startswith("ERR"):
             self.chat_area.tag_config("err", foreground="red", font=FONT_BTN)
             tag = "err"

        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.configure(state='disabled')
        self.chat_area.yview(tk.END)

    def connect_to_server(self, name):
        try:
            self.name = name
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            send_line(self.sock, f"HELLO {name}")
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            return False

    def receive_loop(self):
        try:
            while True:
                line = recv_line(self.sock)
                if line:
                    self.log(line)
        except Exception:
            self.log("SYS Disconnected from server.")
        finally:
            if self.sock:
                self.sock.close()

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg:
            return
        self._send_raw(msg)
        self.msg_entry.delete(0, tk.END)

    def _send_raw(self, line):
        """פונקציית עזר לשליחת פקודות לשרת"""
        if not self.sock: return
        try:
            send_line(self.sock, line)
        except Exception as e:
            self.log(f"ERR Failed to send: {e}")

    # --- פונקציות לכפתורים החדשים ---

    def cmd_start_chat(self):
        """נפתח כשלוחצים על Start Chat"""
        target = simpledialog.askstring("Start Chat", "Enter the name of the user to chat with:", parent=self.root)
        if target and target.strip():
            self._send_raw(f"/chat {target.strip()}")

    def cmd_leave_chat(self):
        """נפתח כשלוחצים על Leave Chat"""
        self._send_raw("/leave")

    def on_closing(self):
        """מטפל ביציאה מהתוכנה"""
        if messagebox.askokcancel("Quit", "Do you want to quit?", icon='warning'):
            self._send_raw("/quit")
            self.root.destroy()

# --- מסך כניסה (Login) ---

def start_app():
    def on_join(event=None):
        name = name_entry.get().strip()
        if name:
            login_window.destroy()
            root = tk.Tk()
            # הגדרת גודל התחלתי לחלון הצ'אט
            root.geometry("700x500")
            app = ChatClientGUI(root)
            if app.connect_to_server(name):
                root.mainloop()
        else:
             # שינוי צבע מסגרת לאדום אם השם ריק
             name_entry.config(highlightbackground="red", highlightcolor="red")

    # יצירת חלון כניסה מעוצב
    login_window = tk.Tk()
    login_window.title("Login")
    login_window.configure(bg=THEME["bg_main"])
    login_window.geometry("350x250")

    frame = tk.Frame(login_window, bg=THEME["bg_main"])
    frame.pack(expand=True)

    tk.Label(frame, text="Welcome! 🌸", bg=THEME["bg_main"], fg=THEME["fg_text"], font=("Helvetica", 16, "bold")).pack(pady=(0, 20))
    tk.Label(frame, text="Enter your name:", bg=THEME["bg_main"], fg=THEME["fg_text"], font=FONT_MAIN).pack(pady=5)
    
    name_entry = tk.Entry(frame, bg=THEME["bg_white"], fg=THEME["fg_text"], font=FONT_MAIN, relief=tk.FLAT, highlightthickness=2, highlightbackground=THEME["highlight"])
    name_entry.pack(pady=5, ipady=3, ipadx=5)
    name_entry.bind("<Return>", on_join)
    name_entry.focus_set()

    join_btn = tk.Button(frame, text="Join Chat", command=on_join, bg=THEME["btn_bg"], activebackground=THEME["btn_active"], fg=THEME["btn_fg"], font=FONT_BTN, relief=tk.FLAT, padx=20, pady=5, cursor="hand2")
    join_btn.pack(pady=20)

    login_window.mainloop()

if __name__ == "__main__":
    start_app()