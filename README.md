# PubMed PDF Downloader

## Description

PubMed PDF Downloader is a user-friendly desktop application that allows researchers and medical professionals to easily search and download scientific articles from PubMed. This tool streamlines the process of literature review by automating the search and download of PDF articles based on user-specified criteria.

## Features

- Simple and intuitive graphical user interface
- Search PubMed database using custom queries
- Specify maximum number of results and minimum publication date
- Automatically download PDF versions of articles when available
- Save downloaded articles in a user-specified or automatically created folder
- Display real-time progress and status updates
- Handle errors gracefully and provide user feedback

## Installation

1. Ensure you have Python 3.7 or later installed on your system.
2. Clone this repository or download the source code.
3. Navigate to the project directory in your terminal or command prompt.
4. Create a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python doidownloader.py
   ```
2. Enter your search query in the "Search Query" field.
3. Specify the maximum number of results you want to retrieve (default is 20).
4. Set the minimum publication date in the format YYYY/MM/DD (default is 2015/01/01).
5. (Optional) Choose a specific download folder,