import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from IPython.display import display, HTML

PAGE_URL = 'https://sexpositions.club/'
HEADERS = { "User-Agent": "Mozilla/5.0" }

def mostrar_todas():
    response = requests.get(PAGE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img')

    html = ""
    for i, img in enumerate(images):
        src = img.get('src')
        if src:
            url = urljoin(PAGE_URL, src)
            html += f"<div style='margin:10px'><b>{i}</b><br><img src='{url}' width='200'/><br>{url}</div>"

    display(HTML(f"<div style='display:flex; flex-wrap:wrap'>{html}</div>"))

mostrar_todas()

