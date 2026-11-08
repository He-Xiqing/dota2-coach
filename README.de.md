<!-- Sprache / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

Echtzeit-Coach für Dota 2 als externes Overlay. Arbeitet nur mit dem **offiziellen Valve-GSI** und **Screenshots des eigenen Bildschirms**:
kein Speicherlesen, keine Injection, keine simulierten Tasten, keine Mods.

<p>
  <a href="https://github.com/OWNER/REPO/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Screenshots

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Für wen

**Für Einsteiger in Dota 2**: du kennst nicht alle Helden, weißt nicht, wo du auf der Lane stehen sollst, kopierst Builds und weißt im Teamfight nicht, was zu tun ist.

Bewusste Kompromisse:

- **Spielt nie für dich**: eine kurze Zeile, wenn es zählt, keine Datenwand;
- **Kein Dota Plus nötig**: Helden werden über die obere Leiste erkannt, normale Accounts reichen;
- **Kein Speicherlesen**: offizielles GSI + Screenshots deines Bildschirms;
- **9 UI-Sprachen + 9 Sprechsprachen**: Oberfläche, Tipps und Sprache wechseln gemeinsam;
- **Analyse nach jedem Spiel**: 1–3 Punkte, die du sofort umsetzen kannst.

## Was es kann

- Liest GSI: Held/Level/HP/Mana/Fähigkeiten/Items/Gold/KDA, Spielzeit, Punktestand;
- **Screenshot des Strategie-Bildschirms**, erkennt alle 10 Helden aus der oberen Leiste (ohne Dota Plus); 10/10 bei 2560×1600;
- Schreibt **Namen unter die Porträts** der oberen Leiste (Verbündete grün, Gegner rot, klickdurchlässig);
- Halbtransparente **Karte im Vordergrund**: Phase und Uhr, beide Lineups, nächstes Item, Runen-Timer;
- **Lane-Coach**: erkennt deine Lane, gibt Position und HP-Grenzen je nach Gefahr (Initiation/Burst/Push/Unsichtbarkeit), dazu Ward bei 4 Min, Nacht bei 5 Min, Roam ab Level 6 und Last-Hit-Warnung;
- **Ton + Sprache in 9 Sprachen**: Runen, Lane, Items, Item-Nutzung und Fights werden gesprochen; Sprachausgabe über edge-tts online, funktioniert auch bei defekter Windows-Stimme; **das Sprachpaket folgt der UI-Sprache**;
- **Guide-Bibliothek (Bilibili)**: regelmäßiges Sammeln von Guides desselben Patches (Titel/Kommentare/Danmaku, optionale Transkription), per LLM auf einen Satz verdichtet; wöchentliche Aktualisierung mit Aufräumen;
- **Drei UI-Zustände**: Begrüßung, Coaching im Spiel, Analyse nach dem Spiel (Statistik, 1–3 Tipps, ein Mutmacher), zurück nach 30 s;
- **Theme**: austauschbares Hintergrundbild (Einstellungen → Theme);
- **Sprachpakete**: 13 edge-Stimmen (5 chinesische + je eine für zh-TW/en/fr/ru/de/pt/es/tr), plus eigene Stimme;
- **Teamfight-Warnungen**: ab Minute 10 werden Minimap-Punkte beobachtet, gewarnt wenn Gegner verschwinden, Verbündete sich sammeln oder ein Fight beginnt, mit Rollen-Tipp; Minimap-Position/-Größe einstellbar;
- **F8** Karte zeigen/verstecken, **F9** Stimme testen; Karte lässt Klicks durch.

## Neu

- **Neun Sprachen**: 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Hauptfenster, Einstellungen, Hilfe, Analyse, Build-Seite und Sprachpakete folgen der Sprache; das Hauptfenster wechselt sofort, ohne Neustart.
- **Sprachausgabe in neun Sprachen**: Item-Hinweise (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), Lane-Verbrauchsgüter (Dust/Magic Stick/Stout Shield/Tango), Runen- und Fight-Tipps laufen in der aktuellen Sprache; keine chinesischen Fähigkeitsnamen mehr in anderen Sprachen.
- **Build-Seite**: pro Sprache als `data/ingame_guide.<lang>.html` erzeugt.
- **Adaptive Minimap**: findet die Minimap in beiden unteren Ecken und passt sich der Größe an; sonst Einstellungen → Assistenz → Minimap mit Position/Größe/X-Y; Scan ab Minute 10 und Neu-Positionierung nach langer Zeit ohne rote Punkte.
- **Saubere Sprache**: Text wird normalisiert (`·`, `——`, `（）`, `7:00`, `6.8k`), Wiedergabe nach echter Audiolänge.
- **Klügere Analyse**: Supporter bekommen kein „zu wenig Last Hits / niedriges GPM“ mehr; Begrüßung und Mutmacher sind zufällig.
- **Ein Item nach dem anderen**: die Karte empfiehlt das Item, das jetzt gekauft werden sollte, mit Grund, Nutzung und Skillbuild.
- **Zwei exe**: `Dota2Coach.exe` öffnet das Hauptfenster, `Dota2Coach-Card.exe` nur die Karte; alte `*.old.exe` werden beim Start entfernt.

## Schnellstart

```powershell
cd <Projektordner>

# 1) Umgebung + Abhängigkeiten (Python 3.12 nötig)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) GSI-Konfiguration ins Spielverzeichnis kopieren
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) Vorlagen und Daten laden (einmalig)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) optional: Online-Sprachausgabe (eine Abhängigkeit für 9 Sprachen)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) Dota 2 neu starten, dann den Coach starten
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Ausführliche Installation und Fehlersuche: [docs/install.md](docs/install.md) (chinesisch).

## Sprache und Stimme

Einstellungen → Sprache: eine der neun Sprachen wählen und speichern; das Hauptfenster wechselt sofort, ohne Neustart. Das Sprachpaket wechselt automatisch, eine eigene Stimme bleibt.
Einstellungen → Stimme: Sprachausgabe ein/aus, Tempo/Lautstärke, „Stimme testen“. Bei Fehlern ertönt der Signalton weiter; Log in `logs\voice.log`.

## Datengrenzen

| Daten | Quelle | Hinweis |
|---|---|---|
| Dein Held/Fähigkeiten/Items/Gold | GSI | offiziell, Echtzeit |
| Uhr/Punktestand/Türme | GSI | offiziell, Echtzeit |
| Beide Lineups | Screenshot Strategiebildschirm | GSI liefert nur „dich“ |
| Gegnerpositionen / Fights | Minimap-Screenshot | Farbsegmentierung + Clustering |
| Builds | OpenDota Item-Popularität | Offline-Cache |
| Rollen / Winrates | OpenDota heroStats | aktueller Patch |
| Guide-Tipps | Bilibili-Videos + DeepSeek | Guides des Patches |
| Sprache | edge-tts online (optional) | 9 Sprachen, Rückfall auf Ton |

**Rote Linien**: kein Speicherlesen, keine Injection, keine simulierten Eingaben, keine Automatisierung.

## Roadmap

| Phase | Inhalt | Status |
|---|---|---|
| M0 | GSI-Pipeline, Logs, Setup-Skripte | fertig |
| M1 | Lineup-Erkennung + Karte | 10/10 über die obere Leiste |
| M2 | Wissensbasis + Draft-Tipps | nicht begonnen |
| M3 | Lane-Coach | fertig |
| M4 | Item-Tipps | ein Item + Grund/Nutzung/Build |
| M5 | Teamfight-Warnungen | Minimap + Rollen-Tipps (ab 10 Min) |
| M6 | Packaging und Doku | Fenster, Einstellungen/Hilfe, zwei exe |
| M7 | Bilibili-Guide-Bibliothek | läuft |

## Build und Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Ergebnis: `dist\Dota2Coach\Dota2Coach.exe` (Fenster) und `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (nur Karte).

## Download

- Portable Version (Windows x64): [Releases](https://github.com/OWNER/REPO/releases/latest) — entpacken und `Dota2Coach.exe` starten
- Aus dem Quellcode: siehe Schnellstart oben

## Compliance und Haftungsausschluss

- Kein offizielles Valve-Produkt, keine Verbindung zu Valve.
- Liest nur offizielles GSI und Screenshots deines eigenen Bildschirms; kein Speicherlesen, keine Injektion, keine simulierten Tasten.
- Beachte die Nutzungsbedingungen von Steam und Dota 2; Nutzung auf eigene Gefahr.

## Danksagung

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Mehr

- Ausführlichste Doku (Struktur, Datenquellen, Git): [README.zh-CN.md](README.zh-CN.md).
- Daten und Skripte: [docs/data-sources.md](docs/data-sources.md).
