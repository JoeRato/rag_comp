import requests
import re
import os
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import io
import csv

#Scrapping ACPR website to get information on published sanctions

def get_text_info(soup):
    """retrieve infos about decisions on a specific ACPR page"""
    text_info = {'titles':[], 'links':[], 'tags':[], 'dates':[]}
    entries = soup.find_all('div', {'class': 'col-lg-9 col-md-9 col-sm-12 col-xs-12 content-info'})
    text_info['titles'].extend([entry.h3.text if entry.h3.text else "" for entry in entries])
    text_info['links'].extend([entry.a['href'] if entry.a else "" for entry in entries])
    text_info['tags'].extend([entry.find('div', {'class': 'keywords-group'}).text if entry.find('div', {'class': 'keywords-group'}) else "" for entry in entries])
    text_info['dates'].extend([entry.find('span', {'class':'date'}).text if entry.find('span', {'class':'date'}).text else "" for entry in entries])
    return text_info

def get_page_number(url):
    """Get the number of pages to be scrapped on ACPR website"""
    response = requests.get(url, params={'page': 0})
    soup = BeautifulSoup(response.text, 'html.parser')
    page_numb_text = soup.find('div', {'class': 'view-header'}).text
    total_doc = int(re.search(r'sur (\d+)', page_numb_text).group(1))
    page_numb = round(total_doc / 10) - 1
    return page_numb

def edit_links(link):
    """Edit acpr links if necessary"""
    base_url = 'https://acpr.banque-france.fr'
    return  base_url + link if link.startswith('/sites') else link

def get_acpr_decisions():
    """extract infos from ACPR decisions portal"""
    url = 'https://acpr.banque-france.fr/page-tableau-filtre/decisions'
    page_numb = get_page_number(url)
    text_info = {'titles':[], 'links':[], 'tags':[], 'dates':[]}

    for i in range(page_numb+1):
        print(f'retrieving info from page {i+1}...')
        response = requests.get(url, params={'page': i})
        soup = BeautifulSoup(response.text, 'html.parser')
        page_info = get_text_info(soup)

        text_info['titles'].extend(page_info['titles'])
        text_info['links'].extend(page_info['links'])
        text_info['tags'].extend(page_info['tags'])
        text_info['dates'].extend(page_info['dates'])

    acpr_df = pd.DataFrame(text_info)
    acpr_df['dates'] = acpr_df['dates'].apply(lambda x: pd.to_datetime(x, dayfirst=True))
    acpr_df['links'] = acpr_df['links'].apply(edit_links)

    print('done!')

    return acpr_df

def get_acpr_sanctions():
    """only get acpr published sanctions"""
    decisions = get_acpr_decisions()
    return decisions[decisions['tags'] == 'Commission des sanctions'].reset_index(drop=True)

def update_pdf_sanctions(folder_path):
    """ Check a dedicated folder and add all the missing pdf sanctions"""
    links = get_acpr_sanctions()['links']

    def update_pdf_sanction(link, folder_path):
        current_sanctions = os.listdir(Path(folder_path))
        sanction = AcprSanction(link)
        sanction_pdf_name = f'{sanction.file_name}.pdf'
        if sanction_pdf_name not in current_sanctions:
            sanction.save_pdf(folder_path)
            print(f'added {sanction_pdf_name} successfully!')

    links.apply(lambda x: update_pdf_sanction(x, folder_path))
    print('folder up to date!')
    return None

#Class processing ACPR sanctions

class ProcessPDF:

    def __init__(self, link, title=None, date=None):
        self.link = link
        self.file_name = Path(link).name.split('.')[0]
        self.title = title
        self.date = date

    def get_raw_content(self):
        """ Extract PDF text content from a http link.
        returns list of page contents """
        response = requests.get(self.link)
        remote_pdf_bytes = io.BytesIO(response.content)
        reader = PdfReader(remote_pdf_bytes)
        page_numb = len(reader.pages)
        raw_content = [reader.pages[i].extract_text() for i in range(page_numb)]
        return raw_content

    def split_text(self, raw_content):
        """split pages by paragraph
        returns a list of paragraphs"""
        content = [re.sub('\n \nAutorité de contrôle prudentiel', '\nAutorité de contrôle prudentiel', page) for page in raw_content]
        content = [page.split('\n \n') for page in content]
        return content

    def clean_content(self, pages):
        """Correct parsing mistakes of a pdf"""
        result = []
        for page in pages:
            result_page = []
            for line in page:
                line = re.sub('_','', line)
                line = re.sub('\n', ' ', line)
                line = line.replace('*','')
                line = re.sub(r' -','-', line)
                line = re.sub(r'––+','-', line)
                line = re.sub(r' ’', "'", line)
                line = re.sub(r'\s+(,)', '', line)
                line = re.sub(r'\s+\.', '.', line)
                line = re.sub(r' +',' ', line)
                result_page.append(line.strip(' -'))
            result.append([line for line in result_page if line])
        return result

    def remove_headers(self, pages):
        """Remove header - footer of each page"""
        result = []
        for page in pages:
            pattern = f".*? ({pages.index(page)+1}) "
            #match = re.match(pattern, page[0])

            page[0] = re.sub(pattern, '', page[0])
            if page[0].startswith(f'{pages.index(page)+1} '):
                page[0] = re.sub(f'{pages.index(page)+1} ', '', page[0])
            result.extend(page)
        return result

    def save_pdf(self, folder_path):
        """Save sanction as a PDF is the dedicated folder"""
        folder_path = Path(folder_path)
        file_name = Path(f'{self.file_name}.pdf')
        folder_path.mkdir(exist_ok=True, parents=True)
        response = requests.get(self.link)
        with open(folder_path/file_name, 'wb') as f:
            f.write(response.content)
        return True
