import tkinter as tk
from tkinter import messagebox
from PIL import Image
import pystray
import pytesseract
import pyautogui
import pyttsx3
import os
from threading import Lock

class OCRScreenshotApp:
    def __init__(self):
        self.icon = None
        self.root = None
        self.lock = Lock()
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.engine = pyttsx3.init()
        tesseract_path = os.environ.get('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        if not os.path.exists(tesseract_path):
            raise FileNotFoundError(f"Tesseract実行ファイルが見つかりません: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def safe_start_capture(self):
        if self.lock.acquire(blocking=False):
            try:
                self.create_screenshot_window()
            finally:
                self.lock.release()

    def create_screenshot_window(self):
        try:
            if self.root is not None:
                self.root.destroy()
                self.root = None
            
            self.root = tk.Tk()
            self.root.attributes('-alpha', 0.3, '-fullscreen', True, '-topmost', True)
            self.canvas = tk.Canvas(self.root)
            self.canvas.pack(fill='both', expand=True)
            
            self.start_x = None
            self.start_y = None
            self.current_rect = None
            
            self.canvas.bind('<Button-1>', self.start_selection)
            self.canvas.bind('<B1-Motion>', self.update_selection)
            self.canvas.bind('<ButtonRelease-1>', self.end_selection)
            self.canvas.bind('<Escape>', lambda e: self.on_closing())
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("エラー", f"ウィンドウ作成中にエラーが発生しました: {str(e)}")
            self.on_closing()

    def on_closing(self):
        if self.root:
            self.root.destroy()
            self.root = None

    def start_selection(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def update_selection(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, outline='red')

    def end_selection(self, event):
        try:

            self.root.withdraw()
            

            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            

            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            

            temp_image_path = "temp_screenshot.png"
            screenshot.save(temp_image_path)
            

            text = self.perform_ocr(temp_image_path)
            


            

            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            

            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}")
            self.root.quit()

    def perform_ocr(self, image_path):
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='jpn')
            self.engine.say(text)
            image.close()
            self.engine.runAndWait()
            return text.strip()
        except Exception as e:
            raise Exception(f"OCR処理中にエラーが発生しました: {str(e)}")

    def exit_app(self):
        if self.root:
            self.root.destroy()
            self.root = None
        if self.icon:
            self.icon.stop()

    def setup_tray(self):
        image = Image.new('RGB', (64, 64), color='blue')
        menu = pystray.Menu(
            pystray.MenuItem("スクリーンショット取得", self.safe_start_capture),
            pystray.MenuItem("終了", self.exit_app)
        )
        self.icon = pystray.Icon("OCRスクリーンショット", image, "OCRスクリーンショット", menu)
        self.icon.run()

if __name__ == '__main__':
    app = OCRScreenshotApp()
    app.setup_tray()