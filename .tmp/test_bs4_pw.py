from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://www.investorgain.com/report/ipo-gmp-live/331/')
        page.wait_for_selector('table tbody tr')
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        for table in soup.find_all('table'):
            th_texts = [th.text.strip().lower() for th in table.find_all('th')]
            if 'company' in th_texts and 'gmp' in th_texts:
                print('Found GMP table with', len(table.find('tbody').find_all('tr')), 'rows')
                # print first row to check structure
                first_row = table.find('tbody').find('tr')
                print([td.text.strip() for td in first_row.find_all('td')])
                
        browser.close()

if __name__ == '__main__':
    main()
