"""给九语言 README 添加徽章、截图、下载、合规与致谢（一次性维护脚本）。"""

from __future__ import annotations

from pathlib import Path

REPO = "https://github.com/OWNER/REPO"

BADGES = f"""<p>
  <a href="{REPO}/actions/workflows/tests.yml"><img alt="tests" src="{REPO}/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

<p align="center">
  <img src="docs/img/panel-roster.png" alt="DOTA2 Coach lineup" width="720">
</p>
"""

SHOTS = """<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>
"""

I18N = {
    "zh-CN": dict(
        shots="## 截图",
        down="## 下载",
        down_body=(
            "- 免安装版（Windows x64）：[Releases]({repo}/releases/latest) — 下载 zip 解压后双击 `Dota2Coach.exe`\n"
            "- 从源码运行：见下方「快速开始」"
        ),
        comp="## 合规与免责",
        comp_body=(
            "- 非 Valve 官方产品，与 Valve 无关联。\n"
            "- 只读取官方 GSI 与你自己屏幕的截图；不读内存、不注入、不模拟按键。\n"
            "- 请遵守 Steam 与 Dota 2 服务条款，使用风险自负。"
        ),
        cred="## 致谢",
        more="更多",
    ),
    "zh-TW": dict(
        shots="## 截圖",
        down="## 下載",
        down_body=(
            "- 免安裝版（Windows x64）：[Releases]({repo}/releases/latest) — 下載 zip 解壓後雙擊 `Dota2Coach.exe`\n"
            "- 從原始碼執行：見下方「快速開始」"
        ),
        comp="## 合規與免責",
        comp_body=(
            "- 非 Valve 官方產品，與 Valve 無關聯。\n"
            "- 只讀取官方 GSI 與你自己螢幕的截圖；不讀記憶體、不注入、不模擬按鍵。\n"
            "- 請遵守 Steam 與 Dota 2 服務條款，使用風險自負。"
        ),
        cred="## 致謝",
        more="更多",
    ),
    "en": dict(
        shots="## Screenshots",
        down="## Download",
        down_body=(
            "- Portable build (Windows x64): [Releases]({repo}/releases/latest) — unzip and run `Dota2Coach.exe`\n"
            "- Run from source: see Quick start below"
        ),
        comp="## Compliance & disclaimer",
        comp_body=(
            "- Not an official Valve product; not affiliated with Valve.\n"
            "- Reads only official GSI and screenshots of your own screen; no memory reading, no injection, no simulated input.\n"
            "- Follow the Steam and Dota 2 terms of service; use at your own risk."
        ),
        cred="## Credits",
        more="More",
    ),
    "fr": dict(
        shots="## Captures d'écran",
        down="## Téléchargement",
        down_body=(
            "- Version portable (Windows x64) : [Releases]({repo}/releases/latest) — décompressez et lancez `Dota2Coach.exe`\n"
            "- Depuis les sources : voir Démarrage rapide ci-dessous"
        ),
        comp="## Conformité et avertissement",
        comp_body=(
            "- Projet non officiel, sans lien avec Valve.\n"
            "- Lit uniquement le GSI officiel et des captures de votre écran ; pas de lecture mémoire, pas d'injection, pas de touches simulées.\n"
            "- Respectez les conditions d'utilisation de Steam et de Dota 2 ; utilisation à vos risques."
        ),
        cred="## Remerciements",
        more="Plus",
    ),
    "ru": dict(
        shots="## Скриншоты",
        down="## Загрузка",
        down_body=(
            "- Портативная сборка (Windows x64): [Releases]({repo}/releases/latest) — распакуйте и запустите `Dota2Coach.exe`\n"
            "- Из исходников: см. «Быстрый старт» ниже"
        ),
        comp="## Соответствие и отказ от ответственности",
        comp_body=(
            "- Это не официальный продукт Valve и он не связан с Valve.\n"
            "- Читает только официальный GSI и снимки вашего экрана; без чтения памяти, инъекций и эмуляции клавиш.\n"
            "- Соблюдайте условия Steam и Dota 2; используйте на свой риск."
        ),
        cred="## Благодарности",
        more="Подробнее",
    ),
    "de": dict(
        shots="## Screenshots",
        down="## Download",
        down_body=(
            "- Portable Version (Windows x64): [Releases]({repo}/releases/latest) — entpacken und `Dota2Coach.exe` starten\n"
            "- Aus dem Quellcode: siehe Schnellstart unten"
        ),
        comp="## Compliance und Haftungsausschluss",
        comp_body=(
            "- Kein offizielles Valve-Produkt, keine Verbindung zu Valve.\n"
            "- Liest nur offizielles GSI und Screenshots deines eigenen Bildschirms; kein Speicherlesen, keine Injektion, keine simulierten Tasten.\n"
            "- Beachte die Nutzungsbedingungen von Steam und Dota 2; Nutzung auf eigene Gefahr."
        ),
        cred="## Danksagung",
        more="Mehr",
    ),
    "pt": dict(
        shots="## Capturas de tela",
        down="## Download",
        down_body=(
            "- Versão portátil (Windows x64): [Releases]({repo}/releases/latest) — descompacte e execute `Dota2Coach.exe`\n"
            "- A partir do código: veja Início rápido abaixo"
        ),
        comp="## Conformidade e aviso",
        comp_body=(
            "- Não é um produto oficial da Valve e não tem vínculo com ela.\n"
            "- Lê apenas o GSI oficial e capturas da sua própria tela; sem leitura de memória, injeção ou entradas simuladas.\n"
            "- Respeite os termos da Steam e do Dota 2; use por sua conta e risco."
        ),
        cred="## Créditos",
        more="Mais",
    ),
    "es": dict(
        shots="## Capturas de pantalla",
        down="## Descarga",
        down_body=(
            "- Versión portátil (Windows x64): [Releases]({repo}/releases/latest) — descomprime y ejecuta `Dota2Coach.exe`\n"
            "- Desde el código: consulta Inicio rápido abajo"
        ),
        comp="## Cumplimiento y aviso",
        comp_body=(
            "- No es un producto oficial de Valve ni está afiliado a Valve.\n"
            "- Solo lee el GSI oficial y capturas de tu propia pantalla; sin lectura de memoria, inyección ni entradas simuladas.\n"
            "- Respeta los términos de Steam y Dota 2; úsalo bajo tu responsabilidad."
        ),
        cred="## Créditos",
        more="Más",
    ),
    "tr": dict(
        shots="## Ekran görüntüleri",
        down="## İndirme",
        down_body=(
            "- Taşınabilir sürüm (Windows x64): [Releases]({repo}/releases/latest) — zip'i açıp `Dota2Coach.exe` çalıştırın\n"
            "- Kaynaktan çalıştırma: aşağıdaki Hızlı başlangıç"
        ),
        comp="## Uyumluluk ve sorumluluk reddi",
        comp_body=(
            "- Resmî Valve ürünü değildir, Valve ile bağlantılı değildir.\n"
            "- Yalnızca resmî GSI ve kendi ekranınızın görüntüsünü okur; bellek okuma, enjeksiyon veya tuş simülasyonu yoktur.\n"
            "- Steam ve Dota 2 kullanım koşullarına uyun; risk size aittir."
        ),
        cred="## Teşekkürler",
        more="Daha fazla",
    ),
}

CREDITS = (
    "[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · "
    "[edge-tts](https://github.com/rany2/edge-tts) · "
    "[faster-whisper](https://github.com/SYSTRAN/faster-whisper) · "
    "[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)"
)


def patch(path: Path) -> None:
    code = path.name[len("README") : -len(".md")].strip(".")
    if path.name == "README.md":
        return
    t = I18N[code]
    lines = path.read_text(encoding="utf-8").splitlines()

    # 1) 徽章 + 主图：插在第一个 "## " 之前
    first = next(i for i, line in enumerate(lines) if line.startswith("## "))
    head = BADGES.splitlines() + SHOTS.splitlines() + [
        t["shots"],
        "",
    ]
    lines[first:first] = head

    tail = [
        "",
        t["down"],
        "",
        t["down_body"].format(repo=REPO),
        "",
        t["comp"],
        "",
        t["comp_body"],
        "",
        t["cred"],
        "",
        CREDITS,
        "",
    ]

    more = t["more"]
    idx = max(
        (i for i, line in enumerate(lines) if line.startswith("## ") and more in line),
        default=None,
    )
    if idx is None:
        lines.extend(tail)
    else:
        lines[idx:idx] = tail

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("patched", path.name)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for code in I18N:
        patch(root / f"README.{code}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
