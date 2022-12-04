import requests
from bs4 import BeautifulSoup as bs

# make a session
s = requests.Session()

url = "https://annumed.sante-dz.com/detail/medecin/baka-mennouba?ref=intern-page"
api_url = "https://annumed.sante-dz.com/api/v1/phone"

# get the page
res = s.get(url)
print("1. status code: ", res.status_code)
soup = bs(res.text)
# get the x-csrf-token from the page
x_xsrf_token = soup.find("input", attrs={"name": "_token"}).attrs.get("value")
# get the data entity & place
data_entity = soup.find("a", attrs={"itemprop": "telephone"}).attrs.get("data-entity")
data_place = soup.find("a", attrs={"itemprop": "telephone"}).attrs.get("data-place")
# add all these headers to the session
s.headers.update({
    "pt": "text/html, */*; q=0.01",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6",
    "cache-control": "no-cache",
    "content-length": "75",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://annumed.sante-dz.com",
    "pragma": "no-cache",
    "referer": "https://annumed.sante-dz.com/detail/medecin/baka-mennouba?ref=intern-page",
    "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "x-csrf-token": x_xsrf_token
})
api_res = s.post(api_url, data={"entity": data_entity, "id": data_place})
print(api_res.text)
print(api_res.status_code)


