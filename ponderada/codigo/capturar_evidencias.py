"""Captura em PNG as saídas reais de A4 e o relatório de caches via Chromium.

Utilitário opcional de evidência, sem dependências Python externas. Não executa
novamente medições nem altera seus valores; renderiza os arquivos .txt salvos.
"""

from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile


IMAGENS = Path(__file__).resolve().parents[1] / "img"


def pagina(titulo, comando, conteudo):
    """Recebe título, comando e saída em texto; retorna HTML com conteúdo escapado."""
    return f"""<!doctype html>
<html lang="pt-BR"><meta charset="utf-8">
<title>{escape(titulo)}</title>
<style>
* {{box-sizing:border-box}} body {{margin:0;padding:28px;background:#eef2f6;
color:#17243b;font:16px Arial,sans-serif}} h1 {{font-size:25px;margin:0 0 10px}}
p {{margin:8px 0 18px}} pre {{margin:0;background:#111b2c;color:#f4f7fc;
padding:24px;border-radius:10px;font:16px/1.55 monospace;white-space:pre-wrap;
overflow-wrap:anywhere}} .nota {{color:#43566f;font-size:14px}}
</style>
<h1>{escape(titulo)}</h1>
<p>Luiz Felipe Paravatti Maciel Hinuy · D1 = 4 · D2 = 0 · N = 3</p>
<pre>$ {escape(comando)}\n\n{escape(conteudo.rstrip())}</pre>
<p class="nota">Captura de página local com a saída real preservada em TXT.
Data das medições: 05/11/2026. Os valores não foram editados.</p></html>"""


def principal():
    """Sem parâmetros/retorno; lê quatro TXT e salva seus prints PNG em img.

    Requer chromium ou chromium-browser no PATH. HTML e perfil ficam em pasta
    temporária. Erros do navegador interrompem a captura com código não zero.
    """
    navegador = shutil.which("chromium") or shutil.which("chromium-browser")
    if not navegador:
        raise SystemExit("Instale Chromium para reproduzir os prints; A4 não depende dele.")
    capturas = []
    for versao in (1, 2, 3):
        nome = f"versao{versao}"
        conteudo = (IMAGENS / f"{nome}.txt").read_text(encoding="utf-8")
        capturas.append((nome, f"A4 · Versão {versao} · 3 execuções reais",
                         f"python3 ponderada/codigo/{nome}.py --repeticoes 3 "
                         f"--saida ponderada/img/{nome}.json", conteudo, 1000))
    linhas = (IMAGENS / "lscpu.txt").read_text(encoding="utf-8").splitlines()
    selecionadas = [linha for linha in linhas if any(
        linha.startswith(prefixo) for prefixo in (
            "Architecture:", "CPU(s):", "Model name:", "L1d cache:",
            "L1i cache:", "L2 cache:", "L3 cache:"))]
    capturas.append(("caches", "A1 · Caches reportadas pela máquina", "lscpu",
                     "\n".join(selecionadas)
                     + "\n\nRecorte da saída completa preservada em lscpu.txt.", 600))
    with tempfile.TemporaryDirectory(prefix="tato-prints-") as temporario:
        pasta = Path(temporario)
        for nome, titulo, comando, conteudo, altura in capturas:
            documento = pasta / f"{nome}.html"
            documento.write_text(pagina(titulo, comando, conteudo), encoding="utf-8")
            subprocess.run([
                navegador, "--headless", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--disable-background-networking",
                "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
                f"--user-data-dir={pasta / 'perfil'}",
                f"--window-size=1280,{altura}",
                f"--screenshot={IMAGENS / (nome + '.png')}", documento.as_uri(),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
            print(f"Captura salva: {nome}.png")


if __name__ == "__main__":
    principal()
