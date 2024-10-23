import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import asyncio
import aiohttp
import re
from datetime import datetime
from dotenv import load_dotenv
from articledowloader import search_and_fetch_pubmed, create_safe_foldername, download_pdf
import subprocess
import platform

load_dotenv()

class PubMedDownloaderApp:
    def __init__(self, master, asyncio_bridge):
        self.master = master
        self.asyncio_bridge = asyncio_bridge
        master.title("PubMed PDF Downloader")
        master.geometry("500x400")
        master.resizable(False, False)

        bg_color = '#4CAF50'
        master.configure(bg=bg_color)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', padding=6, relief="flat", background=bg_color, foreground="white")
        self.style.map('TButton', background=[('active', bg_color)])
        self.style.configure('TProgressbar', thickness=20, borderwidth=2, height=20, background=bg_color)
        self.style.configure('TEntry', padding=5)
        self.style.configure('TLabel', padding=5)

         # Main frame
        main_frame = ttk.Frame(self.master, padding="40 20 40 20", style='TFrame')
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        # Query
        ttk.Label(main_frame, text="Keyword:").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.keyword_query_entry = ttk.Entry(main_frame, width=50)
        self.keyword_query_entry.grid(row=0, column=1, columnspan=2, sticky="we", pady=(0, 10))

        # Author
        ttk.Label(main_frame, text="Author:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.author_query_entry = ttk.Entry(main_frame, width=50)
        self.author_query_entry.grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 10))

        # Max Results
        ttk.Label(main_frame, text="Max Results:").grid(row=2, column=0, sticky="w", pady=(0, 10))
        self.max_results_entry = ttk.Entry(main_frame, width=10)
        self.max_results_entry.insert(0, "5")
        self.max_results_entry.grid(row=2, column=1, sticky="w", pady=(0, 10))

        # Download Folder
        ttk.Label(main_frame, text="Download Folder:").grid(row=3, column=0, sticky="w", pady=(0, 10))
        self.folder_entry = ttk.Entry(main_frame, width=40)
        self.folder_entry.grid(row=3, column=1, sticky="we", pady=(0, 10))
        ttk.Button(main_frame, text="Browse", command=self.browse_folder, style='TButton').grid(row=3, column=2, padx=(5, 0), pady=(0, 10))

        # Search Button
        self.search_button = ttk.Button(main_frame, text="Search and Download", command=self.start_search_and_download, style='TButton')
        self.search_button.grid(row=4, column=0, columnspan=3, pady=(20, 10), sticky="we")

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky="we", pady=(10, 5))

        # Status Label
        self.status_label = ttk.Label(main_frame, text="", wraplength=460, justify="center")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(5, 10))

        # Article beeing downloaded
        self.article_label = ttk.Label(main_frame, text="", wraplength=460, justify="center")
        self.article_label.grid(row=7, column=0, columnspan=3, pady=(5, 10))

        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        for i in range(8):
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

    async def create_summary_file(self, summary_file_path, query, translated_query, articles, session, download_folder):
        with open(summary_file_path, "w", encoding='utf-8') as summary_file:
            summary_file.write(f"Search Query: {query}\n")
            summary_file.write(f"Translated Query: {translated_query}\n")
            summary_file.write(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary_file.write(f"Number of Results: {len(articles)}\n\n")
            summary_file.write("Articles:\n\n")

            for i, article in enumerate(articles, 1):
                self.update_status(f"Downloading PDF {i}/{len(articles)}")
                title = re.sub('<[^<]+?>', '', article["MedlineCitation"]["Article"]["ArticleTitle"])
                self.article_label.config(text=title)
                metadata = await download_pdf(session, article, download_folder)
                # Create summary file
                if metadata is not None:
                    summary_file.write(f"------------------------------------------------------------------\n\n")
                    summary_file.write(f"Title: {metadata['title']}\n")
                    summary_file.write(f"Authors: {', '.join(metadata['authors'])}\n")
                    summary_file.write(f"Journal: {metadata['journal']}\n")
                    summary_file.write(f"Date: {metadata['datetime'].strftime('%Y-%m-%d')}\n")
                    summary_file.write(f"PMID: {metadata['pmid']}\n")
                    summary_file.write(f"DOI: {metadata.get('doi', 'N/A')}\n")
                    summary_file.write(f"URL: https://pubmed.ncbi.nlm.nih.gov/{metadata['pmid']}/\n\n")
                    summary_file.write(f"MLA Citation: {self.generate_mla_citation(metadata)}\n\n")
                    summary_file.write(f"Chicago Citation: {self.generate_chicago_citation(metadata)}\n\n\n")
    
    async def search_and_download(self):
        keyword_query = self.keyword_query_entry.get()
        author_query = self.author_query_entry.get()
        max_results = int(self.max_results_entry.get())
        download_folder = self.folder_entry.get() or create_safe_foldername(keyword_query, author_query)
        query = ""

        if keyword_query:
            query += f"Keyword: {keyword_query}"
        if author_query:
            query += f"\nAuthor: {author_query}"

        if not keyword_query and not author_query:
            self.show_error("Please enter a search query.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                print(f"Searching PubMed for articles...")
                articles, translated_query = await search_and_fetch_pubmed(keyword_query, author_query, max_results)

                if not articles:
                    self.show_error("No articles found.")
                    return

                os.makedirs(download_folder, exist_ok=True)
                
                summary_file_path = os.path.join(download_folder, "summary.txt")
                await self.create_summary_file(summary_file_path, query, translated_query, articles, session, download_folder)
                
            self.open_summary_file(summary_file_path)
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
    
    def open_summary_file(self, file_path):
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', file_path))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(file_path)
        else:  # linux variants
            subprocess.call(('xdg-open', file_path))

    def generate_mla_citation(self, metadata):
        authors = " and ".join(metadata['authors'][:3])  # MLA uses up to 3 authors
        if len(metadata['authors']) > 3:
            authors += ", et al"
        
        title = f'"{metadata["title"]}"'
        journal = metadata['journal']
        date = metadata['datetime'].strftime('%d %b. %Y')
        url = f"https://pubmed.ncbi.nlm.nih.gov/{metadata['pmid']}/"
        
        citation = f"{authors}. {title}. {journal}, {date}, {url}. Accessed {datetime.now().strftime('%d %b. %Y')}."
        return citation

    def generate_chicago_citation(self, metadata):
        # Format authors for Chicago style
        authors = []
        for i, author in enumerate(metadata['authors']):
            if i == 0:
                # First author: Last, First
                names = author.split()
                if len(names) > 1:
                    authors.append(f"{names[-1]}, {' '.join(names[:-1])}")
            else:
                # Subsequent authors: First Last
                authors.append(author)
        
        author_text = ""
        if len(authors) == 1:
            author_text = authors[0]
        elif len(authors) == 2:
            author_text = f"{authors[0]} and {authors[1]}"
        elif len(authors) > 2:
            author_text = f"{authors[0]} et al."
        
        # Format date
        date = metadata['datetime'].strftime('%Y')
        
        # Create Chicago style citation
        title = f'"{metadata["title"]}"'
        journal = metadata['journal']
        doi = metadata.get('doi', '')
        
        citation = f"{author_text}. {date}. {title}. {journal}. "
        if doi:
            citation += f"https://doi.org/{doi}"
        else:
            citation += f"https://pubmed.ncbi.nlm.nih.gov/{metadata['pmid']}/"
        
        return citation

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