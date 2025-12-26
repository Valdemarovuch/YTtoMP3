import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import os
from pathlib import Path
import threading
import ssl

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception as e:
    print(f"SSL setup warning: {e}")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class YouTubeToMP3Converter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.colors = {
            "bg": "#1a1a1a",
            "text_primary": "#ffffff",
            "text_secondary": "#666666",
            "button": "#8E8E93",
            "button_hover": "#6E6E73",
            "border": "#E5E5E7",
            "success": "#34C759",
            "error": "#FF3B30"
        }

        self.title("YouTube to MP3")
        self.geometry("700x550")
        self.resizable(False, False)
        
        self.configure(fg_color=self.colors["bg"])
        
        self.download_folder = str(Path.home() / "Downloads" / "YouTube_MP3")
        try:
            os.makedirs(self.download_folder, exist_ok=True)
        except Exception as e:
            print(f"Error creating download folder: {e}")
            self.download_folder = str(Path.home() / "Downloads")
        
        self.setup_ui()
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=60, pady=(50, 30), sticky="ew")
        
        icon_frame = ctk.CTkFrame(header_frame, width=80, height=80, fg_color=self.colors["button"], corner_radius=10)
        icon_frame.pack()
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame, 
            text="♪", 
            font=ctk.CTkFont(size=40),
            text_color="white"
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="YouTube to MP3", 
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(20, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame, 
            text="Конвертуйте відео в аудіо за лічені секунди", 
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        subtitle_label.pack()

        url_container = ctk.CTkFrame(self, fg_color="transparent")
        url_container.grid(row=1, column=0, padx=200, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            url_container, 
            text="URL відео з YouTube", 
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.url_entry = ctk.CTkEntry(
            url_container,
            height=50,
            font=ctk.CTkFont(size=14),
            border_width=1,
            border_color=self.colors["border"],
            corner_radius=8,
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_secondary"]
        )
        self.url_entry.pack(fill="x")
        self.url_entry.bind("<Return>", lambda e: self.start_download_thread())
        
        self.after(500, self.check_clipboard_on_start)

        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.grid(row=2, column=0, padx=200, pady=15, sticky="ew")
        
        self.download_btn = ctk.CTkButton(
            button_container, 
            text="Конвертувати в MP3", 
            font=ctk.CTkFont(size=16),
            height=50,
            corner_radius=8,
            command=self.start_download_thread,
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            border_width=0
        )
        self.download_btn.pack(fill="x")
        
        self.open_folder_btn = ctk.CTkButton(
            button_container,
            text="📁 Відкрити папку з файлами",
            font=ctk.CTkFont(size=13),
            height=35,
            corner_radius=8,
            command=self.open_download_folder,
            fg_color="transparent",
            border_width=1,
            border_color=self.colors["border"],
            text_color=self.colors["text_secondary"],
            hover_color=self.colors["border"]
        )

        progress_container = ctk.CTkFrame(self, fg_color="transparent")
        progress_container.grid(row=3, column=0, padx=200, pady=10, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=6,
            corner_radius=3,
            progress_color=self.colors["success"],
            fg_color=self.colors["border"]
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            progress_container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack()

        how_frame = ctk.CTkFrame(self, fg_color="transparent")
        how_frame.grid(row=4, column=0, padx=200, pady=(30, 20), sticky="ew")
        
        features_frame = ctk.CTkFrame(self, fg_color="transparent")
        features_frame.grid(row=5, column=0, padx=100, pady=(20, 30), sticky="ew")
        
        features_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        feat1 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat1.grid(row=0, column=0, padx=20)
        ctk.CTkLabel(feat1, text="320kbps", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat1, text="Максимальна якість", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()
        
        feat2 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat2.grid(row=0, column=1, padx=20)
        ctk.CTkLabel(feat2, text="Швидко", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat2, text="До 60 сек", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()
        
        feat3 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat3.grid(row=0, column=2, padx=20)
        ctk.CTkLabel(feat3, text="Безкоштовно", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat3, text="Без обмежень", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
    
    def open_download_folder(self):
        """Відкриває папку з завантаженими файлами"""
        try:
            import subprocess
            subprocess.run(['open', self.download_folder])
        except Exception as e:
            print(f"Error opening folder: {e}")
            messagebox.showerror("Помилка", f"Не вдалося відкрити папку: {self.download_folder}")

    def check_clipboard(self):
        pass
    
    def check_clipboard_on_start(self):
        """Перевіряє буфер обміну при запуску і показує підказку якщо є YouTube посилання"""
        try:
            if not self.winfo_exists():
                return
                
            clipboard_content = self.clipboard_get()
            if clipboard_content and ("youtube.com" in clipboard_content or "youtu.be" in clipboard_content):
                short_url = clipboard_content[:50] + "..." if len(clipboard_content) > 50 else clipboard_content
                self.url_entry.configure(placeholder_text=f"💡 Натисніть Cmd+V: {short_url}")
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Clipboard check error: {e}")
    
    def start_download_thread(self):
        thread = threading.Thread(target=self.download_mp3)
        thread.daemon = True
        thread.start()

    def update_status(self, text, color=None):
        self.status_label.configure(text=text)
        if color:
            self.status_label.configure(text_color=color)
        else:
            self.status_label.configure(text_color=self.colors["text_secondary"])

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')

                p = percent_str.replace('%','')
                try:
                    progress_val = float(p) / 100
                    self.progress_bar.set(progress_val)
                except:
                    pass
                
                self.update_status(f"Завантаження {percent_str} • {speed} • ETA: {eta}", self.colors["text_secondary"])
            except Exception as e:
                print(f"Progress error: {e}")
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.update_status("Конвертація в MP3 та додавання metadata...", self.colors["text_secondary"])
        elif d['status'] == 'processing':
            self.update_status("Обробка файлу...", self.colors["text_secondary"])

    def download_mp3(self):
        url = self.url_entry.get().strip()
        
        if not url:
            self.update_status("Будь ласка, введіть посилання YouTube", self.colors["error"])
            return
        
        self.download_btn.configure(state="disabled", text="Завантаження...")
        self.progress_bar.set(0)
        self.update_status("Підготовка до завантаження...", self.colors["text_secondary"])
        
        try:
            download_path = self.download_folder
            os.makedirs(download_path, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    },
                    {
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,
                    },
                    {
                        'key': 'EmbedThumbnail',
                        'already_have_thumbnail': False,
                    }
                ],
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'quiet': False,
                'no_warnings': False,
                'nocheckcertificate': True,
                'noplaylist': True,
                'writethumbnail': True,
                'embedthumbnail': True,
                'addmetadata': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'audio')
            
            self.progress_bar.set(1.0)
            self.update_status(f"✓ Готово! Збережено: {title[:50]}", self.colors["success"])

            self.open_folder_btn.pack(fill="x", pady=(10, 0))

            self.after(8000, lambda: [
                self.url_entry.delete(0, tk.END),
                self.update_status(""),
                self.progress_bar.set(0),
                self.open_folder_btn.pack_forget()
            ])
            
        except Exception as e:
            self.progress_bar.set(0)
            error_msg = str(e)[:60]
            self.update_status(f"Помилка: {error_msg}", self.colors["error"])
            print(e)
        
        finally:
            self.download_btn.configure(state="normal", text="⬇  Конвертувати в MP3")


if __name__ == "__main__":
    app = YouTubeToMP3Converter()
    app.mainloop()
