# PubMed PDF Downloader

PubMed PDF Downloader is a Python application that allows users to search for scientific articles on PubMed, download their PDFs, and save them locally. The application provides both a graphical user interface (GUI) and a command-line interface (CLI) for ease of use.

## Features

- Search PubMed for scientific articles based on user-defined queries
- Download PDF files of the articles (when available)
- Create a summary file with metadata for downloaded articles
- Customizable search parameters (max results, minimum date)
- User-friendly GUI for easy interaction
- Asynchronous downloads for improved performance

## Requirements

- Python 3.7+
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pubmed-pdf-downloader.git
   cd pubmed-pdf-downloader
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root and add your Entrez email:
   ```
   ENTREZ_EMAIL=your.email@example.com
   ```

## Usage

### GUI Version

To run the application with a graphical user interface:

```
   python articleDowloaderApp.py
```
