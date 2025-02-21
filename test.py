import re
import requests
from bs4 import BeautifulSoup


base = 'https://gogoanime3.co'
query = 'death note'.replace(' ', '+')
req = requests.get(f'{base}/filter.html?keyword={query}')
soup = BeautifulSoup(req.content, 'html.parser')
pages = soup.find_all("a", attrs={"data-page": re.compile(r"^ *\d[\d ]*$")})
if pages is None:
    raise Exception("No pages found")

pages = [x.get("data-page") for x in pages]
pages = int(pages[-1]) if len(pages) > 0 else 1

for i in range(pages):
    pageUrl = f'{base}/filter.html?keyword={query}&page={i + 1}'
    # print(pageUrl)
    req = requests.get(pageUrl)
    soup = BeautifulSoup(req.content, 'html.parser')
    links = soup.find_all("p", attrs={"class": "name"})
    if links is None:
        raise Exception("No links found")
    
    # print(links)
    
    for link in links:
        name = link.text.replace("\n", "")
        print(link.find("a").get("href"))