import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from articledowloader import search_and_fetch_pubmed, create_safe_foldername, download_pdf

load_dotenv()

class PubMedDownloaderApp:
    def __init__(self, master, asyncio_bridge):
        self.master = master
        self.asyncio_bridge = asyncio_bridge
        master.title("PubMed PDF Downloader")
        master.geometry("500x300")
        master.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', padding=6, relief="flat", background="#4CAF50", foreground="white")
        self.style.map('TButton', background=[('active', '#45a049')])
        self.style.configure('TProgressbar', thickness=20, borderwidth=2, height=20, background="#4CAF50")
        self.style.configure('TEntry', padding=5)
        self.style.configure('TLabel', padding=5)

        main_frame = ttk.Frame(master, padding="20 20 20 20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Query
        ttk.Label(main_frame, text="Search Query:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.query_entry = ttk.Entry(main_frame, width=50)
        self.query_entry.grid(row=0, column=1, columnspan=2, sticky="we", pady=(0, 10))

        # Max Results
        ttk.Label(main_frame, text="Max Results:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.max_results_entry = ttk.Entry(main_frame, width=10)
        self.max_results_entry.insert(0, "5")
        self.max_results_entry.grid(row=1, column=1, sticky="w", pady=(0, 10))

        # Download Folder
        ttk.Label(main_frame, text="Download Folder:").grid(row=2, column=0, sticky="w", pady=(0, 10))
        self.folder_entry = ttk.Entry(main_frame, width=40)
        self.folder_entry.grid(row=2, column=1, sticky="we", pady=(0, 10))
        ttk.Button(main_frame, text="Browse", command=self.browse_folder, style='TButton').grid(row=2, column=2, padx=(5, 0), pady=(0, 10))

        # Search Button
        self.search_button = ttk.Button(main_frame, text="Search and Download", command=self.start_search_and_download, style='TButton')
        self.search_button.grid(row=3, column=0, columnspan=3, pady=(20, 10), sticky="we")

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky="we", pady=(10, 5))

        # Status Label
        self.status_label = ttk.Label(main_frame, text="", wraplength=460, justify="center")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(5, 10))

        # Article beeing downloaded
        self.article_label = ttk.Label(main_frame, text="", wraplength=460, justify="center")
        self.article_label.grid(row=6, column=0, columnspan=3, pady=(5, 10))

        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        for i in range(6):
            main_frame.rowconfigure(i, weight=1)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, folder_selected)

    def start_search_and_download(self):
        self.search_button.config(state='disabled')
        self.progress.start()
        self.status_label.config(text="Searching PubMed...")
        self.asyncio_bridge(self.search_and_download())

    async def search_and_download(self):
        query = self.query_entry.get()
        max_results = int(self.max_results_entry.get())
        download_folder = self.folder_entry.get() or create_safe_foldername(query)

        if not query:
            self.show_error("Please enter a search query.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                print("Searching PubMed...", query, max_results)
                articles = await search_and_fetch_pubmed(query, max_results)

                if not articles:
                    self.show_error("No articles found.")
                    return

                os.makedirs(download_folder, exist_ok=True)
                
                for i, article in enumerate(articles, 1):
                    self.update_status(f"Downloading PDF {i}/{len(articles)}")
                    self.article_label.config(text=article["MedlineCitation"]["Article"]["ArticleTitle"])
                    metadata = await download_pdf(session, article, download_folder)
                    # Create summary file
                    if metadata is not None:
                        with open(os.path.join(download_folder, "summary.txt"), "a", encoding='utf-8') as summary_file:
                            summary_file.write(f"Title: {metadata['title']}\n")
                            summary_file.write(f"Authors: {', '.join(metadata['authors'])}\n")
                            summary_file.write(f"Journal: {metadata['journal']}\n")
                            summary_file.write(f"Date: {metadata['datetime'].strftime('%Y-%m-%d')}\n")
                            summary_file.write(f"PMID: {metadata['pmid']}\n\n")
            
            self.show_success(f"Downloaded articles to {download_folder}")
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.master.after(0, self.reset_ui)

    def reset_ui(self):
        self.progress.stop()
        self.search_button.config(state='normal')
        self.status_label.config(text="")
        self.article_label.config(text="")

    def update_status(self, message):
        self.master.after(0, lambda: self.status_label.config(text=message))

    def show_error(self, message):
        self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.reset_ui()

    def show_success(self, message):
        self.master.after(0, lambda: messagebox.showinfo("Success", message))

def run_async_app():
    root = tk.Tk()
    root.configure(bg='#f0f0f0')
    # Set up asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def run_loop():
        loop.run_forever()
    
    # Run the asyncio event loop in a separate thread
    import threading
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    
    # Schedule asyncio coroutines from the main thread
    def asyncio_bridge(coroutine):
        async def wrapper():
            try:
                await coroutine
            except Exception as e:
                error = str(e)
                root.after(0, lambda: messagebox.showerror("Error", error))
        
        future = asyncio.run_coroutine_threadsafe(wrapper(), loop)
        
        def check_future():
            if not future.done():
                root.after(100, check_future)
        
        check_future()
    
    app = PubMedDownloaderApp(root, asyncio_bridge)
    root.mainloop()

if __name__ == "__main__":
    run_async_app()