import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import os
from pathlib import Path
import threading
import ssl
import urllib.request
import socket

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception as e:
    print(f"SSL setup warning: {e}")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def check_internet_connection():
    """Check internet connection"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

class YouTubeToMP3Converter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.colors = {
            "bg": "#1a1a1a",
            "text_primary": "#ffffff",
            "text_secondary": "#666666",
            "button": "#8E8E93",
            "button_hover": "#ffffff",
            "border": "#E5E5E7",
            "success": "#34C759",
            "error": "#FF3B30"
        }

        self.title("YouTube to MP3")
        self.geometry("900x600")
        self.resizable(False, False)
        
        self.update_idletasks()
        width = 900
        height = 750
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.configure(fg_color=self.colors["bg"])
        
        self.selected_quality = "320"
        
        self.is_downloading = False
        
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
            text="Convert videos to audio in seconds", 
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        subtitle_label.pack()

        url_container = ctk.CTkFrame(self, fg_color="transparent")
        url_container.grid(row=1, column=0, padx=200, pady=20, sticky="ew")
        
        ctk.CTkLabel(
            url_container, 
            text="YouTube Video URL", 
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
        self.url_entry.bind("<KeyRelease>", lambda e: self.validate_url())
        
        self.preview_frame = ctk.CTkFrame(url_container, fg_color="transparent")
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        self.preview_label.pack(fill="x", pady=(5, 0))
        
        self.after(500, self.check_clipboard_on_start)

        quality_container = ctk.CTkFrame(self, fg_color="transparent")
        quality_container.grid(row=2, column=0, padx=200, pady=(15, 0), sticky="ew")
        
        ctk.CTkLabel(
            quality_container,
            text="Select Quality",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        quality_buttons_frame = ctk.CTkFrame(quality_container, fg_color="transparent")
        quality_buttons_frame.pack(fill="x")
        quality_buttons_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.quality_buttons = {}
        qualities = ["320", "256", "192", "128", "64"]
        
        for idx, quality in enumerate(qualities):
            btn = ctk.CTkButton(
                quality_buttons_frame,
                text=f"{quality} kbps",
                font=ctk.CTkFont(size=13),
                height=38,
                corner_radius=8,
                command=lambda q=quality: self.select_quality(q),
                fg_color=self.colors["button"] if quality == "320" else "transparent",
                hover_color=self.colors["button_hover"],
                border_width=1,
                border_color=self.colors["border"],
                text_color="white" if quality == "320" else self.colors["text_secondary"]
            )
            btn.grid(row=0, column=idx, padx=3, sticky="ew")
            self.quality_buttons[quality] = btn

        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.grid(row=3, column=0, padx=200, pady=15, sticky="ew")
        
        self.download_btn = ctk.CTkButton(
            button_container, 
            text="⬇  Convert to MP3", 
            font=ctk.CTkFont(size=16),
            height=50,
            corner_radius=8,
            command=self.start_download_thread,
            fg_color=self.colors["button"],
            hover_color=self.colors["button_hover"],
            border_width=0
        )
        self.download_btn.pack(fill="x")
        
        self.folder_btn = ctk.CTkButton(
            button_container,
            text="📁 Change Folder",
            font=ctk.CTkFont(size=12),
            height=30,
            corner_radius=8,
            command=self.browse_folder,
            fg_color="transparent",
            border_width=1,
            border_color=self.colors["border"],
            text_color=self.colors["text_secondary"],
            hover_color=self.colors["border"]
        )
        self.folder_btn.pack(fill="x", pady=(8, 0))
        
        self.open_folder_btn = ctk.CTkButton(
            button_container,
            text="📁 Open Download Folder",
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

        self.progress_container = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_container,
            height=6,
            corner_radius=3,
            progress_color=self.colors["success"],
            fg_color=self.colors["border"]
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            self.progress_container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack()

        features_frame = ctk.CTkFrame(self, fg_color="transparent")
        features_frame.grid(row=5, column=0, padx=100, pady=(20, 30), sticky="ew")
        
        features_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        feat1 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat1.grid(row=0, column=0, padx=20)
        ctk.CTkLabel(feat1, text="320kbps", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat1, text="Maximum Quality", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()
        
        feat2 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat2.grid(row=0, column=1, padx=20)
        ctk.CTkLabel(feat2, text="Fast", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat2, text="Up to 60 sec", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()
        
        feat3 = ctk.CTkFrame(features_frame, fg_color="transparent")
        feat3.grid(row=0, column=2, padx=20)
        ctk.CTkLabel(feat3, text="Free", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=self.colors["text_primary"]).pack()
        ctk.CTkLabel(feat3, text="No Limits", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_secondary"]).pack()
        
        statusbar_frame = ctk.CTkFrame(self, fg_color=self.colors["bg"], height=30)
        statusbar_frame.grid(row=6, column=0, sticky="ew", padx=0, pady=0)
        statusbar_frame.grid_columnconfigure(0, weight=1)
        
        self.folder_path_label = ctk.CTkLabel(
            statusbar_frame,
            text=f"📂 Folder: {self.download_folder}",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        self.folder_path_label.grid(row=0, column=0, sticky="w", padx=15, pady=5)

    def browse_folder(self):
        """Select download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_path_label.configure(text=f"📂 Folder: {self.download_folder}")
            self.update_status("Folder changed", self.colors["success"])
            self.after(2000, lambda: self.update_status(""))
    
    def validate_url(self):
        """Validate YouTube URL"""
        url = self.url_entry.get().strip()
        if not url:
            self.url_entry.configure(border_color=self.colors["border"])
            self.preview_frame.pack_forget()
            return
        
        if "youtube.com" in url or "youtu.be" in url:
            self.url_entry.configure(border_color=self.colors["success"])
            threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()
        else:
            self.url_entry.configure(border_color=self.colors["error"])
            self.preview_frame.pack_forget()
    
    def fetch_video_info(self, url):
        """Fetch video information"""
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown title')
                duration = info.get('duration', 0)
                author = info.get('uploader', 'Unknown author')
                
                minutes = duration // 60
                seconds = duration % 60
                
                preview_text = f"📹 {title[:40]}... | 👤 {author} | ⏱ {minutes}:{seconds:02d}"
                self.preview_label.configure(text=preview_text)
                self.preview_frame.pack(fill="x", pady=(5, 0))
        except:
            self.preview_frame.pack_forget()
    
    def select_quality(self, quality):
        """Select MP3 quality"""
        self.selected_quality = quality
        
        for q, btn in self.quality_buttons.items():
            if q == quality:
                btn.configure(
                    fg_color=self.colors["button"],
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.colors["text_secondary"]
                )
    
    def open_download_folder(self):
        """Opens download folder"""
        try:
            import subprocess
            subprocess.run(['open', self.download_folder])
        except Exception as e:
            print(f"Error opening folder: {e}")
            messagebox.showerror("Error", f"Failed to open folder: {self.download_folder}")
    
    def check_clipboard_on_start(self):
        """Check clipboard for YouTube links on startup"""
        try:
            if not self.winfo_exists():
                return
                
            clipboard_content = self.clipboard_get()
            if clipboard_content and ("youtube.com" in clipboard_content or "youtu.be" in clipboard_content):
                short_url = clipboard_content[:50] + "..." if len(clipboard_content) > 50 else clipboard_content
                self.url_entry.configure(placeholder_text=f"💡 Press Cmd+V: {short_url}")
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Clipboard check error: {e}")
    
    def start_download_thread(self):
        if self.is_downloading:
            return
        
        url = self.url_entry.get().strip()
        if not url or ("youtube.com" not in url and "youtu.be" not in url):
            self.update_status("Invalid YouTube URL", self.colors["error"])
            self.url_entry.configure(border_color=self.colors["error"])
            return
        
        if not check_internet_connection():
            self.update_status("❌ No internet connection. Check your connection", self.colors["error"])
            messagebox.showerror(
                "No Internet", 
                "Failed to connect to the internet.\n\nCheck:\n• Wi-Fi or Ethernet connection\n• Network settings\n• Firewall"
            )
            return
        
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
                
                self.update_status(f"Downloading {percent_str} • {speed} • ETA: {eta}", self.colors["text_secondary"])
            except Exception as e:
                print(f"Progress error: {e}")
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1.0)
            self.update_status("Converting to MP3 and adding metadata...", self.colors["text_secondary"])
        elif d['status'] == 'processing':
            self.update_status("Processing file...", self.colors["text_secondary"])

    def download_mp3(self):
        url = self.url_entry.get().strip()
        
        if not url:
            self.update_status("Please enter a YouTube URL", self.colors["error"])
            return
        
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ Downloading...")
        
        self.progress_container.grid(row=4, column=0, padx=200, pady=10, sticky="ew")
        self.progress_bar.set(0)
        self.update_status("Preparing download...", self.colors["text_secondary"])
        
        try:
            download_path = self.download_folder
            os.makedirs(download_path, exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': self.selected_quality,
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
            self.update_status(f"✓ Done! Saved: {title[:50]}", self.colors["success"])

            self.open_folder_btn.pack(fill="x", pady=(10, 0))

            self.after(8000, lambda: [
                self.url_entry.delete(0, tk.END),
                self.update_status(""),
                self.progress_bar.set(0),
                self.progress_container.grid_forget(),
                self.open_folder_btn.pack_forget()
            ])
            
        except Exception as e:
            self.progress_bar.set(0)
            error_str = str(e).lower()
            
            if "private" in error_str or "unavailable" in error_str:
                error_msg = "Video unavailable or private"
            elif "copyright" in error_str:
                error_msg = "Video is copyrighted"
            elif "nodename" in error_str or "network" in error_str or "connection" in error_str or "errno 8" in error_str:
                error_msg = "❌ Connection problem"
                self.update_status(error_msg, self.colors["error"])
                retry = messagebox.askyesno(
                    "Connection Error",
                    "Failed to connect to YouTube.\n\nPossible causes:\n• No internet connection\n• DNS problems\n• YouTube unavailable\n\nTry again?",
                    icon='warning'
                )
                if retry:
                    self.after(500, self.start_download_thread)
                return
            elif "age" in error_str:
                error_msg = "Authorization required (age restrictions)"
            else:
                error_msg = str(e)[:60]
            
            self.update_status(f"❌ Error: {error_msg}", self.colors["error"])
            print(f"Download error: {e}")
            self.after(5000, lambda: [
                self.progress_container.grid_forget(),
                self.update_status("")
            ])
        finally:
            self.is_downloading = False
            self.download_btn.configure(state="normal", text="⬇  Convert to MP3")


if __name__ == "__main__":
    app = YouTubeToMP3Converter()
    app.mainloop()
