#!/usr/bin/env python3
"""Conta os commits do dono do token (inclusive em repositórios privados)
e gera assets/commits.svg. Só o número vai para o card: nada de nomes de repo."""
import base64, json, os, re, sys, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GH_TOKEN")
RAIZ = Path(__file__).resolve().parent.parent
API = "https://api.github.com"


def chamar(caminho):
    req = urllib.request.Request(
        API + caminho,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "profile-card"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), r.headers.get("Link", "")
    except urllib.error.HTTPError as e:
        if e.code == 409:  # repositório vazio
            return [], ""
        raise


def contar(repo, login, desde=None):
    # per_page=1: o número da última página do Link é o total de commits
    q = f"/repos/{repo}/commits?author={login}&per_page=1"
    if desde:
        q += f"&since={desde}"
    dados, link = chamar(q)
    m = re.search(r'[?&]page=(\d+)>; rel="last"', link)
    return int(m.group(1)) if m else len(dados)


def listar_repos():
    repos, pagina = [], 1
    while True:
        dados, _ = chamar(f"/user/repos?affiliation=owner,organization_member&per_page=100&page={pagina}")
        repos += [r["full_name"] for r in dados if not r.get("archived")]
        if len(dados) < 100:
            return repos
        pagina += 1


def svg(total, ano, mes, prs, nrepos, atualizado):
    img = base64.b64encode((RAIZ / "assets/card-tayama.png").read_bytes()).decode()
    fonte = "font-family=\"'Trebuchet MS',Verdana,sans-serif\""
    mono = "font-family=\"'Courier New',monospace\""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="620" height="190" viewBox="0 0 620 190" role="img" aria-label="{total} commits feitos, contando repositórios privados">
<defs><filter id="g" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#130e13"/><stop offset="1" stop-color="#2a1426"/></linearGradient></defs>
<rect width="620" height="190" rx="14" fill="url(#f)" stroke="#3b2b33" stroke-width="2"/>
<rect x="0" y="0" width="620" height="6" rx="3" fill="#a32a40"/>
<image href="data:image/png;base64,{img}" x="22" y="26" width="128" height="128"/>
<text x="176" y="52" {mono} font-size="13" fill="#b8a7ab" letter-spacing="2">COMMITS FEITOS · PÚBLICOS E PRIVADOS</text>
<text x="176" y="112" {fonte} font-size="58" font-weight="800" fill="#f39a2b" filter="url(#g)">{total}</text>
<g {mono} font-size="12" fill="#b8a7ab"><text x="176" y="148">este ano</text><text x="270" y="148">30 dias</text><text x="366" y="148">pull requests</text><text x="506" y="148">repositórios</text></g>
<g {fonte} font-size="20" font-weight="700" fill="#f6eeec"><text x="176" y="170">{ano}</text><text x="270" y="170">{mes}</text><text x="366" y="170">{prs}</text><text x="506" y="170">{nrepos}</text></g>
<text x="598" y="180" {mono} font-size="10" fill="#76656b" text-anchor="end">atualizado em {atualizado}</text>
</svg>
'''


def main():
    if not TOKEN:
        sys.exit("falta STATS_TOKEN (ou GH_TOKEN)")
    login = chamar("/user")[0]["login"]
    agora = datetime.now(timezone.utc)
    ano = f"{agora.year}-01-01T00:00:00Z"
    mes = (agora - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    repos = listar_repos()
    t = sum(contar(r, login) for r in repos)
    a = sum(contar(r, login, ano) for r in repos)
    m = sum(contar(r, login, mes) for r in repos)
    prs = chamar(f"/search/issues?q=author:{login}+type:pr&per_page=1")[0]["total_count"]
    (RAIZ / "assets/commits.svg").write_text(svg(t, a, m, prs, len(repos), agora.strftime("%d/%m/%Y")), encoding="utf-8")
    print(f"total={t} ano={a} 30d={m} prs={prs} repos={len(repos)}")  # só números, sem nomes


if __name__ == "__main__":
    main()
