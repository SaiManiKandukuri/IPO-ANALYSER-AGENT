with open("ipo_scraper_json_db.py", "r") as f:
    code = f.read()

# 1. Update SQLite CREATE TABLE query to add Open_Date and Close_Date
old_create = """
    CREATE TABLE IF NOT EXISTS ipo_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Company TEXT,
        Price_Band TEXT,
        GMP REAL,
"""
new_create = """
    CREATE TABLE IF NOT EXISTS ipo_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Company TEXT,
        Open_Date TEXT,
        Close_Date TEXT,
        Price_Band TEXT,
        GMP REAL,
"""
code = code.replace(old_create, new_create)

# 2. Update SQLite INSERT query to include the new fields
old_insert = """
        INSERT INTO ipo_analysis (
            Company, Price_Band, GMP, Expected_Gain_Pct, Issue_Size_Cr,
"""
new_insert = """
        INSERT INTO ipo_analysis (
            Company, Open_Date, Close_Date, Price_Band, GMP, Expected_Gain_Pct, Issue_Size_Cr,
"""
code = code.replace(old_insert, new_insert)

old_values_bind = """
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['Company'], str(r['Price_Band']), r['GMP'], r['Expected_Gain_Pct'], r['Issue_Size_Cr'],
"""
new_values_bind = """
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['Company'], r['Open_Date'], r['Close_Date'], str(r['Price_Band']), r['GMP'], r['Expected_Gain_Pct'], r['Issue_Size_Cr'],
"""
code = code.replace(old_values_bind, new_values_bind)

# 3. Update the data parsing block to extract dates and actual GMP
old_gmp_parse = """
        # Parse GMP and Price
        gmp = clean_num(row.get('~max_gmp1', 0))
        expected_gain = clean_num(row.get('~gmp_percent_calc', 0))
"""
new_gmp_parse = """
        # Parse Dates
        open_date = str(row.get('~Srt_Open', ''))
        close_date = str(row.get('~Srt_Close', ''))
        
        # Parse GMP and Price
        gmp_html = str(row.get('GMP_gmp') or row.get('GMP', ''))
        gmp = 0.0
        soup = BeautifulSoup(gmp_html, 'html.parser')
        b_tag = soup.find('b')
        if b_tag:
            gmp_text = b_tag.text.strip()
            if gmp_text and gmp_text != '--' and gmp_text != '-':
                match = re.search(r'[\d\.]+', gmp_text)
                if match:
                    gmp = float(match.group())
        
        expected_gain = clean_num(row.get('~gmp_percent_calc', 0))
"""
code = code.replace(old_gmp_parse, new_gmp_parse)

# 4. Update results.append
old_append = """
        results.append({
            'Company': comp,
            'Price_Band': price_band,
"""
new_append = """
        results.append({
            'Company': comp,
            'Open_Date': open_date if open_date != 'nan' else '-',
            'Close_Date': close_date if close_date != 'nan' else '-',
            'Price_Band': price_band,
"""
code = code.replace(old_append, new_append)

with open("ipo_scraper_json_db.py", "w") as f:
    f.write(code)
