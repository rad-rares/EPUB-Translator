import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ebooklib
import ollama
from bs4 import BeautifulSoup
from ebooklib import epub

MODEL = "llama3.2"

LANGUAGES = [
    "Afrikaans", "Albanian", "Arabic", "Bulgarian", "Chinese (Simplified)",
    "Chinese (Traditional)", "Croatian", "Czech", "Danish", "Dutch",
    "English", "Finnish", "French", "German", "Greek", "Hindi",
    "Hungarian", "Indonesian", "Italian", "Japanese", "Korean",
    "Norwegian", "Persian", "Polish", "Portuguese", "Romanian",
    "Russian", "Serbian", "Slovak", "Spanish", "Swedish", "Thai",
    "Turkish", "Ukrainian", "Vietnamese"
]



def translate_text(text, target_lang):
    #sends single paragraph for translation
    if not text.strip():
        return text

    prompt = (
        f"You are a professional book translator. Translate the following text to {target_lang}.\n"
        "Return EXACTLY the translated text and nothing else. No introductions, no explanations, no quotes.\n\n"
        f"Text: {text}"
    )

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        translated = response['message']['content'].strip()
        return translated
    except Exception as e:
        return text


def translate_epub(input_path, target_lang, output_path, log, update_progress, on_done):
    try:
        log("Loading EPUB file...")
        book = epub.read_epub(input_path)
        documents = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        log("Scanning book length...")
        total_lines = 0
        for item in documents:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            total_lines += len([t for t in tags if len(t.get_text(strip=True)) > 2])

        log(f"Found {total_lines} total lines/paragraphs to translate.\n")

        lines_processed = 0
        for item in documents:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            text_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])

            for tag in text_tags:
                original_text = tag.get_text(strip=True)

                if len(original_text) > 2:
                    preview = original_text[:40].replace('\n', ' ') + ("..." if len(original_text) > 40 else "")
                    log(f"Translating: {preview}")

                    translated = translate_text(original_text, target_lang)
                    tag.string = translated

                    lines_processed += 1
                    progress_val = int((lines_processed / total_lines) * 100)
                    update_progress(progress_val)

            item.set_content(soup.encode('utf-8'))

        log("\nRepackaging EPUB...")
        epub.write_epub(output_path, book)
        on_done(True, output_path)

    except Exception as e:
        on_done(False, str(e))



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPUB Book Translator")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self, bg="#2c2c2c")
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header, text="📚 EPUB Book Translator",
            font=("Segoe UI", 16, "bold"),
            bg="#2c2c2c", fg="white", pady=12
        ).pack()

        main = tk.Frame(self, bg="#f0f0f0", padx=16, pady=12)
        main.grid(row=1, column=0, sticky="nsew")

        tk.Label(main, text="Input Book (.epub)", font=("Segoe UI", 9, "bold"), bg="#f0f0f0").grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        file_frame = tk.Frame(main, bg="#f0f0f0")
        file_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.input_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.input_var, font=("Segoe UI", 10),
                 width=38, state="readonly").pack(side="left", fill="x", expand=True)
        tk.Button(file_frame, text="Browse…", command=self._browse_input,
                  bg="#e0e0e0", relief="flat", padx=8).pack(side="left", padx=(6, 0))

        tk.Label(main, text="Translate to", font=("Segoe UI", 9, "bold"), bg="#f0f0f0").grid(
            row=2, column=0, sticky="w", pady=(0, 2))
        self.lang_var = tk.StringVar(value="Romanian")
        ttk.Combobox(main, textvariable=self.lang_var, values=LANGUAGES,
                     font=("Segoe UI", 10), width=30, state="readonly").grid(
            row=3, column=0, sticky="w", pady=(0, 12))

        self.translate_btn = tk.Button(
            main, text="Translate Book ▶",
            font=("Segoe UI", 11, "bold"),
            bg="#4a90d9", fg="white", relief="flat",
            padx=16, pady=8,
            command=self._start_translation,
            cursor="hand2",
        )
        self.translate_btn.grid(row=4, column=0, pady=(0, 12))

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main, variable=self.progress_var, maximum=100, length=420)
        self.progress.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        tk.Label(main, text="Log", font=("Segoe UI", 9, "bold"), bg="#f0f0f0").grid(
            row=6, column=0, sticky="w")
        log_frame = tk.Frame(main)
        log_frame.grid(row=7, column=0, sticky="nsew", pady=(2, 0))
        self.log_text = tk.Text(log_frame, height=10, width=58,
                                font=("Consolas", 9), state="disabled",
                                bg="#1e1e1e", fg="#d4d4d4", relief="flat")
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _browse_input(self):
        filetypes = [("EPUB files", "*.epub")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.input_var.set(path)

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _update_progress(self, val):
        self.progress_var.set(val)

    def _start_translation(self):
        input_path = self.input_var.get().strip()
        target_lang = self.lang_var.get()

        if not input_path:
            messagebox.showerror("No file selected", "Please select an EPUB file.")
            return

        stem = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{stem}_translated_{target_lang.lower()}.epub")

        self.translate_btn.config(state="disabled")
        self.progress_var.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self._log(f"Starting: {Path(input_path).name} → {target_lang}")
        self._log(f"Output: {output_path}\n")

        def on_done(success, result):
            self.after(0, lambda: self._finish(success, result))

        threading.Thread(
            target=translate_epub,
            args=(
                input_path, target_lang, output_path,
                lambda msg: self.after(0, lambda m=msg: self._log(m)),
                lambda val: self.after(0, lambda v=val: self._update_progress(v)),
                on_done
            ),
            daemon=True,
        ).start()

    def _finish(self, success, result):
        self.translate_btn.config(state="normal")
        if success:
            self.progress_var.set(100)
            self._log(f"\n Done! Saved to:\n{result}")
            messagebox.showinfo("Done!", f"Translation complete!\n\nSaved to:\n{result}")
        else:
            self._log(f"\n Error: {result}")
            messagebox.showerror("Error", f"Translation failed:\n\n{result}")


if __name__ == "__main__":
    app = App()
    app.mainloop()