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


def dias_contribuicao(desde, ate):
    """Dias com contagem (só números, sem nomes de repo). Inclui as contribuições privadas."""
    q = ('{viewer{contributionsCollection(from:"%s",to:"%s"){contributionCalendar{totalContributions '
         'weeks{contributionDays{date contributionCount}}}}}}' % (desde, ate))
    req = urllib.request.Request(
        API + "/graphql", data=json.dumps({"query": q}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
    dias = {d["date"]: d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]}
    return cal["totalContributions"], dias


def nivel(n, maximo):
    if n <= 0:
        return 0
    return min(4, 1 + int(3 * (n - 1) / max(maximo, 1)))


CORES = ["#2a1c26", "#6b2a3a", "#b8413f", "#f0802b", "#ffc15e"]
SEMANAS = 42  # janela buscada (só 30 dias aparecem)


def barras(dias, hoje):
    # um pilar por dia nos últimos 30 dias; raiz quadrada para um dia enorme não achatar os outros
    lista = [hoje - timedelta(days=29 - i) for i in range(30)]
    maximo = max([dias.get(d.isoformat(), 0) for d in lista] + [1])
    out = []
    for i, d in enumerate(lista):
        n = dias.get(d.isoformat(), 0)
        x = 32 + i * 24
        if n:
            h = max(8, round(96 * (n / maximo) ** 0.5))
            top = n == maximo
            fill = "url(#bt)" if top else "url(#bn)"
            f = ' filter="url(#g2)"' if top else ""
            out.append(f'<rect x="{x}" y="{352 - h}" width="17" height="{h}" rx="6" fill="{fill}"{f}/>')
            if top:
                out.append(f'<text x="{x + 8.5}" y="{346 - h}" {MONO} font-size="11" fill="#ffd27a" text-anchor="middle">{n}</text>')
        else:
            out.append(f'<rect x="{x}" y="348" width="17" height="4" rx="2" fill="#3a2733"/>')
        if i % 5 == 0 or i == 29:
            out.append(f'<text x="{x + 8.5}" y="370" {MONO} font-size="9" fill="#8f7780" text-anchor="middle">{d.strftime("%d/%m")}</text>')
    return "".join(out)


MONO = "font-family=\"'Courier New',monospace\""


def listar_repos():
    repos, pagina = [], 1
    while True:
        dados, _ = chamar(f"/user/repos?affiliation=owner,organization_member&per_page=100&page={pagina}")
        repos += [r["full_name"] for r in dados if not r.get("archived")]
        if len(dados) < 100:
            return repos
        pagina += 1


def svg(total, mes, prs, nrepos, seq, melhor, ativos, dias, hoje, atualizado):
    img = base64.b64encode((RAIZ / "assets/card-tayama.png").read_bytes()).decode()
    fonte = "font-family=\"'Trebuchet MS',Verdana,sans-serif\""
    mono = "font-family=\"'Courier New',monospace\""
    stats = [("30 dias", mes), ("sequência", f"{seq}d"), ("melhor dia", melhor), ("dias ativos", ativos), ("PRs", prs), ("repos", nrepos)]
    larg = 140
    cols = ""
    for i, (rot, val) in enumerate(stats):
        x = 196 + i * 92
        cols += f'<text x="{x}" y="176" {mono} font-size="10" fill="#b39aa3" letter-spacing="1">{rot.upper()}</text><text x="{x}" y="200" {fonte} font-size="22" font-weight="700" fill="#fbf1ee">{val}</text>'
        if i:
            cols += f'<line x1="{x-12}" y1="160" x2="{x-12}" y2="204" stroke="#4a3340" stroke-width="1"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="780" height="410" viewBox="0 0 780 410" role="img" aria-label="{total} contribuições em {hoje.year}, contando repositórios privados">
<defs>
<filter id="g" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="g2" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#150e14"/><stop offset="0.6" stop-color="#25121f"/><stop offset="1" stop-color="#321528"/></linearGradient>
<radialGradient id="r1" cx="0.18" cy="0.2" r="0.6"><stop offset="0" stop-color="#e0553f" stop-opacity="0.28"/><stop offset="1" stop-color="#e0553f" stop-opacity="0"/></radialGradient>
<radialGradient id="r2" cx="0.95" cy="1" r="0.7"><stop offset="0" stop-color="#b0306e" stop-opacity="0.25"/><stop offset="1" stop-color="#b0306e" stop-opacity="0"/></radialGradient>
<linearGradient id="b" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a32a40"/><stop offset="0.5" stop-color="#f39a2b"/><stop offset="1" stop-color="#d23f86"/></linearGradient>
<linearGradient id="n" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#f0802b"/></linearGradient>
<linearGradient id="bn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e0553f"/><stop offset="1" stop-color="#7a2a46"/></linearGradient>
<linearGradient id="bt" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#f0802b"/></linearGradient>
<clipPath id="c"><rect width="780" height="410" rx="20"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="780" height="410" fill="url(#f)"/><rect width="780" height="410" fill="url(#r1)"/><rect width="780" height="410" fill="url(#r2)"/>
<rect width="780" height="6" fill="url(#b)"/>
</g>
<rect x="1" y="1" width="778" height="408" rx="19" fill="none" stroke="#4a3340" stroke-width="2"/>
<image href="data:image/png;base64,{img}" x="26" y="34" width="150" height="150"/>
<text x="196" y="50" {mono} font-size="13" fill="#c2a9b1" letter-spacing="3">CONTRIBUIÇÕES · PÚBLICAS E PRIVADAS</text>
<text x="196" y="122" {fonte} font-size="68" font-weight="800" fill="url(#n)" filter="url(#g)">{total}</text>
<text x="196" y="144" {mono} font-size="12" fill="#8f7780">em {hoje.year} · só os números, sem nomes de projeto</text>
<line x1="196" y1="156" x2="750" y2="156" stroke="#4a3340" stroke-width="1"/>
{cols}
<line x1="30" y1="222" x2="750" y2="222" stroke="#4a3340" stroke-width="1"/>
<text x="30" y="240" {mono} font-size="10" fill="#b39aa3" letter-spacing="2">POR DIA · ÚLTIMOS 30 DIAS</text>
{barras(dias, hoje)}
<text x="30" y="396" {mono} font-size="10" fill="#76656b">atualizado em {atualizado}</text>
</svg>
'''


def sequencia(dias, hoje):
    d = hoje if dias.get(hoje.isoformat(), 0) else hoje - timedelta(days=1)  # hoje ainda pode estar zerado
    n = 0
    while dias.get(d.isoformat(), 0):
        n += 1
        d -= timedelta(days=1)
    return n


def main():
    if not TOKEN:
        sys.exit("falta STATS_TOKEN (ou GH_TOKEN)")
    agora = datetime.now(timezone.utc)
    hoje = agora.date()
    fim = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    t_ano, d_ano = dias_contribuicao(f"{agora.year}-01-01T00:00:00Z", fim)
    _, d_jan = dias_contribuicao((agora - timedelta(days=SEMANAS * 7)).strftime("%Y-%m-%dT%H:%M:%SZ"), fim)
    login = chamar("/user")[0]["login"]
    mes = min(t_ano, sum(n for d, n in d_jan.items() if d > (hoje - timedelta(days=30)).isoformat()))
    repos = listar_repos()
    prs = chamar(f"/search/issues?q=author:{login}+type:pr&per_page=1")[0]["total_count"]
    try:
        from zoneinfo import ZoneInfo
        local = agora.astimezone(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        local = agora - timedelta(hours=3)
    (RAIZ / "assets/commits.svg").write_text(
        svg(t_ano, mes, prs, len(repos), sequencia(d_jan, hoje), max(d_ano.values() or [0]),
            sum(1 for n in d_ano.values() if n), d_jan, hoje, local.strftime("%d/%m/%Y · %H:%M")),
        encoding="utf-8")
    print(f"ano={t_ano} 30d={mes} prs={prs} repos={len(repos)}")  # só números, sem nomes


if __name__ == "__main__":
    main()
