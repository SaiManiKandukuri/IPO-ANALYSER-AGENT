from bs4 import BeautifulSoup

with open("after_submit.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
    print(soup.get_text(strip=True))
