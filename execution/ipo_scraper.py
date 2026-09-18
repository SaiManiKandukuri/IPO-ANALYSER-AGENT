import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

def clean_company_name(name):
    # Remove ' IPO' or trailing spaces
    return re.sub(r'(?i)\s+IPO$', '', name.strip())

def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    base_url = 'https://www.investorgain.com'
    
    # 1. Parse Dashboard
    response = requests.get(f'{base_url}/ipo-dashboard/mainline/', headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    
    # Identify tables based on headers
    ipo_list = []
    gmp_list = []
    sub_list = []
    
    for table in tables:
        th_texts = [th.text.strip().lower() for th in table.find_all('th')]
        tbody = table.find('tbody')
        if not tbody:
            continue
            
        rows = tbody.find_all('tr')
        if 'company' in th_texts and 'open' in th_texts and 'close' in th_texts:
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    name = clean_company_name(cols[0].text)
                    open_date = cols[1].text.strip()
                    close_date = cols[2].text.strip()
                    ipo_list.append({'Company': name, 'Open Date': open_date, 'Close Date': close_date})
                    
        elif 'company' in th_texts and 'ipo price' in th_texts and 'gmp' in th_texts:
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    name = clean_company_name(cols[0].text)
                    price = cols[1].text.strip()
                    gmp_text = cols[2].text.strip()
                    # Clean GMP text (e.g. "₹50 (20%)" -> 50)
                    gmp_match = re.search(r'₹?\s*(\d+)', gmp_text)
                    gmp = float(gmp_match.group(1)) if gmp_match else 0.0
                    gmp_list.append({'Company': name, 'Price Band': price, 'GMP': gmp})
                    
        elif 'company' in th_texts and 'issue size' in th_texts and 'subscription' in th_texts:
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    link_el = cols[0].find('a')
                    name = clean_company_name(cols[0].text)
                    link = link_el['href'] if link_el else None
                    size_text = cols[1].text.strip()
                    # extract numbers
                    size_text_clean = size_text.replace(',', '')
                    size_match = re.search(r'[\d\.]+', size_text_clean)
                    size = float(size_match.group()) if size_match else 0.0
                    sub_text = cols[2].text.strip()
                    sub_match = re.search(r'[\d\.]+', sub_text)
                    total_sub = float(sub_match.group()) if sub_match else 0.0
                    
                    sub_list.append({'Company': name, 'Issue Size (Cr)': size, 'Total Sub': total_sub, 'Link': link})

    df_ipo = pd.DataFrame(ipo_list)
    df_gmp = pd.DataFrame(gmp_list)
    df_sub = pd.DataFrame(sub_list)
    
    if not df_ipo.empty: df_ipo.set_index('Company', inplace=True)
    if not df_gmp.empty: df_gmp.set_index('Company', inplace=True)
    if not df_sub.empty: df_sub.set_index('Company', inplace=True)

    df_merged = df_sub.join(df_ipo, how='outer').join(df_gmp, how='outer')
    df_merged = df_merged.reset_index()

    results = []
    
    # 2. Deep-Dive Extraction
    for index, row in df_merged.iterrows():
        comp = row['Company']
        link = row.get('Link')
        
        rii = 0.0
        qib = 0.0
        nii = 0.0
        
        if pd.notna(link) and link:
            sub_url = base_url + link
            sub_resp = requests.get(sub_url, headers=headers)
            sub_soup = BeautifulSoup(sub_resp.content, 'html.parser')
            
            for table in sub_soup.find_all('table'):
                th_texts = [th.text.strip().lower() for th in table.find_all('th')]
                if any('category' in th or 'subscription' in th or 'investor' in th for th in th_texts):
                    tbody = table.find('tbody')
                    if tbody:
                        for tr in tbody.find_all('tr'):
                            tds = [td.text.strip() for td in tr.find_all('td')]
                            if len(tds) >= 2:
                                cat = tds[0].lower()
                                sub_val_str = tds[-1] # Usually the last column is subscription times
                                sub_match = re.search(r'[\d\.]+', sub_val_str)
                                sub_val = float(sub_match.group()) if sub_match else 0.0
                                
                                if 'retail' in cat or 'rii' in cat:
                                    rii = sub_val
                                elif 'qib' in cat or 'qualified' in cat:
                                    qib = sub_val
                                elif 'nii' in cat or 'non-institutional' in cat:
                                    nii = sub_val
                    # don't break immediately, might be multiple tables
                    
        # 3. Metric Calculations
        gmp = float(row.get('GMP', 0.0)) if pd.notna(row.get('GMP')) else 0.0
        price_band = str(row.get('Price Band', ''))
        
        price_val = 0.0
        if pd.notna(price_band) and price_band and price_band != 'nan':
            # E.g., "₹405.00" or "₹140 - ₹148"
            prices = re.findall(r'\d+\.?\d*', price_band.replace(',', ''))
            if prices:
                price_val = float(prices[-1]) # take upper band
                
        expected_gain = (gmp / price_val * 100) if price_val > 0 else 0.0
        total_sub = row.get('Total Sub', 0.0)
        if pd.isna(total_sub): total_sub = 0.0
        
        composite_score = expected_gain * (1 + min(total_sub, 50) / 20)
        
        verdict = 'Avoid / Skip'
        if expected_gain >= 20 and (qib > 2 or rii > 2):
            verdict = 'High Conviction Apply'
        elif expected_gain > 15:
            verdict = 'Speculative / Risky'
        elif expected_gain <= 0 or (row.get('Issue Size (Cr)', 0) > 1000 and total_sub < 1):
            verdict = 'Avoid / Skip'
            
        # Format sizes nicely
        issue_size = row.get('Issue Size (Cr)', 0.0)
        issue_size_str = f"{issue_size:.2f}" if pd.notna(issue_size) else '-'
        
        results.append({
            'Company': comp,
            'Price Band': price_band if pd.notna(price_band) and price_band != 'nan' else '-',
            'GMP': gmp,
            'Expected Gain %': round(expected_gain, 2),
            'Issue Size (Cr)': issue_size_str,
            'Retail Sub (RII)': rii,
            'Total Sub': total_sub,
            'Bidding Status': 'Closed' if 'Closed' in str(row.get('Close Date', '')) else 'Open/Upcoming',
            'Verdict': verdict,
            'Composite Score': composite_score,
            'QIB': qib
        })

    # Sort by Composite Score
    results.sort(key=lambda x: x['Composite Score'], reverse=True)
    
    # 4. Output Format
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Run Timestamp: [{timestamp}]\n")
    
    print("| Company | Price Band | GMP | Expected Gain % | Issue Size (Cr) | Retail Sub (RII) | Total Sub | Bidding Status | Verdict |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['Company']} | {r['Price Band']} | ₹{r['GMP']} | {r['Expected Gain %']}% | {r['Issue Size (Cr)']} | {r['Retail Sub (RII)']}x | {r['Total Sub']}x | {r['Bidding Status']} | {r['Verdict']} |")
        
    print("\n### Recommendations:")
    top_picks = [r for r in results if r['Verdict'] == 'High Conviction Apply'][:2]
    if not top_picks:
        top_picks = results[:2]
        
    for i, p in enumerate(top_picks, 1):
        print(f"{i}. **{p['Company']}**: Expected gain of {p['Expected Gain %']}% with a GMP of ₹{p['GMP']}. Retail subscription is at {p['Retail Sub (RII)']}x and QIB at {p['QIB']}x. Verdict: {p['Verdict']}.")

if __name__ == '__main__':
    main()
