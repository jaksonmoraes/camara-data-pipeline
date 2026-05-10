import requests

base = "https://dadosabertos.camara.leg.br/api/v2"

endpoints = [
    "/deputados",
    "/partidos",
    "/eventos",
    "/proposicoes"
]

for ep in endpoints:
    url = base + ep
    r = requests.get(url)

    print(ep, r.status_code)