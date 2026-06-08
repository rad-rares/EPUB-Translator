# EPUB-Translator

This is a lightweight, open-source desktop application that translates EPUB e-books paragraph-by-paragraph entirely on your local machine. It uses the ollama Python library with the Llama 3.2 model to provide 100% free, private, and offline translations without requiring any API keys.    

-Local AI Powered: Runs completely offline using Ollama, saving you from cloud subscription fees and rate limits.
-Format Preservation: Uses BeautifulSoup to surgically swap translated text while perfectly maintaining the original HTML layout and chapter structures of the EPUB.
-Real-time Tracking: Features a responsive Tkinter GUI with a live progress bar and scrolling text log to monitor the exact sentence currently being translated.
-Easy Setup: Simply install Ollama (ollama pull llama3.2), install the Python dependencies (pip install EbookLib beautifulsoup4 ollama), and run the script.

To launch the application and start translating your local library, simply run python epub_translator_ui.py in your terminal.
