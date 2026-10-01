from bs4 import BeautifulSoup

with open("kfin_state.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

inputs = soup.find_all("input")
for inp in inputs:
    print(f"INPUT: id={inp.get('id')}, type={inp.get('type')}, value={inp.get('value')}, name={inp.get('name')}")
