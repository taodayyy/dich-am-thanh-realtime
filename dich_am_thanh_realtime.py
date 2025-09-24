import openai
import sounddevice as sd
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
from deep_translator import GoogleTranslator

# ⚠️ Đặt API key của bạn ở đây
openai.api_key = "YOUR_OPENAI_API_KEY"

# Hàng đợi audio
audio_q = queue.Queue()

# Cấu hình ghi âm
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000  # mẫu mỗi block (tương đương ~0.25 giây)

running = True

def audio_callback(indata, frames, time, status):
    """Callback ghi âm -> đưa dữ liệu vào queue"""
    if status:
        print(status)
    audio_q.put(bytes(indata))

def transcribe_and_translate():
    """Luồng xử lý: lấy audio từ queue -> Whisper -> dịch -> hiện"""
    global running
    buffer = b""
    while running:
        try:
            buffer += audio_q.get(timeout=1)
        except queue.Empty:
            continue

        if len(buffer) > SAMPLE_RATE * 2 * 3:  # ~3 giây audio (16kHz * 2 bytes * 3s)
            # Gửi lên OpenAI Whisper API
            try:
                result = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", buffer)
                )
                jp_text = result.text.strip()

                # Dịch sang tiếng Việt
                vi_text = GoogleTranslator(source='ja', target='vi').translate(jp_text)

                # Hiện trên GUI
                text_box.insert(tk.END, f"🇯🇵 {jp_text}\n🇻🇳 {vi_text}\n\n")
                text_box.see(tk.END)

            except Exception as e:
                print("Lỗi:", e)

            buffer = b""  # reset bộ nhớ

# GUI
root = tk.Tk()
root.title("Dịch âm thanh Nhật → Việt (Realtime)")

text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, font=("Arial", 12))
text_box.pack(padx=10, pady=10)

# Nút thoát
def on_close():
    global running
    running = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Bắt đầu ghi âm
stream = sd.InputStream(callback=audio_callback, channels=CHANNELS, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE)
stream.start()

threading.Thread(target=transcribe_and_translate, daemon=True).start()

root.mainloop()
