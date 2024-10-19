import requests
from Bio import Entrez
import os
import re
from datetime import datetime
import doi2pdf
import asyncio
import aiohttp

# Set your email for Entrez
Entrez.email = os.environ.get('ENTREZ_EMAIL', 'default@example.com')

def pdf_url_from_doi(doi):
    api_res = requests.get(f"https://api.openalex.org/works/https://doi.org/{doi}")
    metadata = api_res.json()
    pdf_url = metadata["open_access"]["oa_url"]
    if pdf_url is None:
        if metadata.get("host_venue") is not None:
            pdf_url = metadata["host_venue"]["url"]
        elif metadata.get("primary_location") is not None:
            pdf_url = metadata["primary_location"]["landing_page_url"]
    else:
        print(f"No PDF found for DOI: {doi}")
    return pdf_url

def create_safe_filename(metadata):
    first_author = metadata['authors'][0].split()[0] if metadata['authors'] else 'Unknown'
    year = metadata['datetime'].year
    title_part = re.sub(r'[^\w\s-]', '', metadata['title'])[:50].strip().replace(' ', '_')
    filename = f"{first_author}_{year}_{title_part}.pdf"
    return re.sub(r'[^\w\.-]', '_', filename)

def create_safe_foldername(query):
    folder_name = re.sub(r'[^\w\-_\. ]', '_', query)
    return folder_name.replace(' ', '_')

async def search_and_fetch_pubmed(query, max_results=20, min_date="2010/01/01"):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance", mindate=min_date)
    record = Entrez.read(handle)
    ids = record["IdList"]
    
    if not ids:
        return []

    handle = Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml")
    articles = Entrez.read(handle)["PubmedArticle"]
    return articles

def fetch_article_metadata(article):
    metadata = {
        "pmid": article["MedlineCitation"]["PMID"],
        "title": article["MedlineCitation"]["Article"]["ArticleTitle"],
        "journal": article["MedlineCitation"]["Article"]["Journal"]["Title"],
        "date": article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["PubDate"],
        "authors": [author.get("LastName", "") + " " + author.get("Initials", "") for author in article["MedlineCitation"]["Article"]["AuthorList"]],
        "pubmedId": article["MedlineCitation"]["PMID"]
    }
    
    year = metadata["date"].get("Year", "1900")
    month = metadata["date"].get("Month", "1")
    day = metadata["date"].get("Day", "1")
    
    month_dict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    if month in month_dict:
        month = month_dict[month]
    
    metadata["datetime"] = datetime(int(year), int(month), int(day))
    return metadata

async def download_pdf(session, article, folder):
    try:
        metadata = fetch_article_metadata(article)
        filename = create_safe_filename(metadata)
        file_path = os.path.join(folder, filename)

        # Check if the file already exists
        if os.path.exists(file_path):
            print(f"Skipping download: {filename} already exists")
            return metadata
        
        article_id = article["PubmedData"]["ArticleIdList"]
        pmc_id = next((id for id in article_id if id.attributes["IdType"] == "pmc"), None)
        doi = next((id for id in article_id if id.attributes["IdType"] == "doi"), None)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.ncbi.nlm.nih.gov/',
        }

        print(f"PMID: {metadata['pmid']}, PMC ID: {pmc_id}, DOI: {doi}")
       
        if pmc_id:
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf"
        elif doi:
            pdf_url =  pdf_url_from_doi(doi)
        else:
            print(f"No direct PDF link available for {metadata['pmid']}")
            return None

        async with session.get(pdf_url, headers=headers, allow_redirects=True) as response:
            if response.status == 200:
                content = await response.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                print(f"Downloaded: {file_path}")
                return metadata
            else:
                print(f"Failed to download  {metadata['title']} from {pdf_url}. Status code: {response.status}")
                if doi:
                    doi2pdf.doi2pdf(doi, output=file_path)
                    if os.path.exists(file_path):
                        print(f"Downloaded: {file_path}")
                        return metadata
    except Exception as e:
        print(f"Error downloading {metadata['pmid']}: {str(e)}")
    

    return None

async def main():
    # Main execution
    search_query = "NAD Parkinson"
    max_results = 20
    min_date = "2015/01/01"  # Only articles from 2015 onwards

    download_folder = create_safe_foldername(search_query)
    os.makedirs(download_folder, exist_ok=True)

    articles = await search_and_fetch_pubmed(search_query, max_results, min_date)

    async with aiohttp.ClientSession() as session:
        tasks = [download_pdf(session, article, download_folder) for article in articles]
        results = await asyncio.gather(*tasks)


    with open(os.path.join(download_folder, "summary.txt"), "w", encoding='utf-8') as summary_file:
        for article in results:
            if article is not None:
                summary_file.write(f"Title: {article['title']}\n")
                summary_file.write(f"Authors: {', '.join(article['authors'])}\n")
                summary_file.write(f"Journal: {article['journal']}\n")
                summary_file.write(f"Date: {article['datetime'].strftime('%Y-%m-%d')}\n")
                summary_file.write(f"PMID: {article['pmid']}\n\n")

    print(f"Download complete. Check the '{download_folder}' folder.")

if __name__ == "__main__":
    asyncio.run(main())