<!-- Langue / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

Coach Dota 2 en temps réel, en overlay externe. Il utilise uniquement le **GSI officiel de Valve** et la **capture de votre propre écran** :
aucune lecture mémoire, aucune injection, aucune touche simulée, aucun mod.

<p>
  <a href="https://github.com/OWNER/REPO/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Captures d'écran

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Pour qui

**Les joueurs qui débutent sur Dota 2** : vous ne connaissez pas tous les héros, vous ne savez pas où vous placer, vous copiez les builds et vous ne savez pas quoi faire en teamfight.

Choix assumés :

- **Ne joue jamais à votre place** : une phrase courte quand il faut, pas un mur de statistiques ;
- **Pas besoin de Dota Plus** : reconnaissance depuis la barre d'équipe, comptes normaux inclus ;
- **Aucune lecture mémoire** : GSI officiel + captures de votre écran ;
- **9 langues d'interface + 9 langues de voix** : interface, conseils et lecture changent ensemble ;
- **Un bilan après chaque partie** : 1–3 points à appliquer, victoire ou défaite.

## Ce qu'il fait

- Lit le GSI : héros/niveau/PV/mana/sorts/objets/or/KDA, temps de jeu, score ;
- **Capture l'écran de stratégie** et reconnaît les 10 héros depuis la barre supérieure (sans Dota Plus) ; 10/10 sur une capture 2560×1600 ;
- Écrit les **noms sous chaque portrait** de la barre (alliés en vert, ennemis en rouge, clic traversant) ;
- Une **carte toujours au premier plan** semi-transparente : phase et chrono, compositions, prochain objet, timers de runes ;
- **Coach de lane** : indique votre lane, donne placement et seuils de PV selon les menaces (initiation/burst/push/invisibilité), plus ward à 4 min, nuit à 5 min, roam au niveau 6 et alerte de last hits ;
- **Son + lecture en 9 langues** : runes, lane, objets, usage d'objets et teamfights sont lus ; la synthèse passe par edge-tts en ligne, donc fonctionne même si le moteur vocal Windows est cassé ; **le pack de voix suit la langue de l'interface** ;
- **Bibliothèque de guides (Bilibili)** : collecte périodique de guides du même patch (titre/commentaires/danmaku, transcription optionnelle), résumés en une phrase par LLM ; mise à jour hebdomadaire avec nettoyage ;
- **Trois états d'interface** : accueil, coaching en partie, puis bilan de la partie (stats, 1–3 conseils, un encouragement) qui revient à l'accueil après 30 s ;
- **Thème** : image de fond remplaçable (Réglages → Thème) ;
- **Packs de voix** : 13 voix edge (5 chinoises + une pour zh-TW/en/fr/ru/de/pt/es/tr), plus voix personnalisée ;
- **Alertes de teamfight** : dès la 10e minute, surveille les points de la minimap, prévient quand des ennemis disparaissent, que les alliés se regroupent ou qu'un combat démarre, et dit quoi faire selon votre rôle ; position/taille de la minimap configurables ;
- **F8** affiche/masque la carte, **F9** teste la voix ; la carte laisse passer les clics.

## Nouveautés récentes

- **Neuf langues** : 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Fenêtre principale, réglages, aide, bilan, page de build et packs de voix suivent la langue ; la fenêtre principale change immédiatement, sans redémarrage.
- **Lecture en neuf langues** : rappels d'objets (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), consommables de lane (Dust/Magic Stick/Stout Shield/Tango), runes et teamfights sont lus dans la langue active ; plus de noms de sorts chinois dans les autres langues.
- **Page de build** : générée par langue dans `data/ingame_guide.<lang>.html`.
- **Minimap adaptative** : trouve la minimap dans un coin bas et s'adapte à sa taille ; sinon Réglages → Assistance → Minimap pour la position, la taille et le décalage X/Y ; scan dès la 10e minute et relocalisation après une longue période sans point rouge.
- **Lecture plus propre** : textes normalisés (`·`, `——`, `（）`, `7:00`, `6.8k`) et lecture selon la durée réelle de l'audio.
- **Bilan plus juste** : les supports ne reçoivent plus « trop peu de last hits / GPM faible » ; accueil et encouragements aléatoires.
- **Un objet à la fois** : la carte conseille l'objet à acheter maintenant, avec raison, usage et build, puis passe au suivant.
- **Deux exe** : `Dota2Coach.exe` ouvre la fenêtre principale, `Dota2Coach-Card.exe` seulement la carte ; les `*.old.exe` sont nettoyés au démarrage.

## Démarrage rapide

```powershell
cd <dossier du projet>

# 1) environnement + dépendances (Python 3.12 requis)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) copier la config GSI dans le dossier du jeu
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) télécharger modèles et données (une fois)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) optionnel : lecture en ligne (une seule dépendance pour les 9 langues)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) relancer Dota 2 puis démarrer le coach
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Installation détaillée et dépannage : [docs/install.md](docs/install.md) (en chinois).

## Langue et voix

Réglages → Langue : choisissez l'une des neuf langues et enregistrez ; la fenêtre principale change immédiatement, sans redémarrage. Le pack de voix passe automatiquement à cette langue ; une voix personnalisée est conservée.
Réglages → Voix : activer/désactiver, régler vitesse/volume, « Écouter cette voix ». En cas d'échec, retour au bip ; journal dans `logs\voice.log`.

## Limites de données

| Donnée | Source | Remarque |
|---|---|---|
| Votre héros/sorts/objets/or | GSI | officiel, temps réel |
| Chrono/score/tours | GSI | officiel, temps réel |
| Compositions | capture de l'écran de stratégie | GSI ne donne que « vous » |
| Positions ennemies / combats | capture de la minimap | segmentation couleur + clustering |
| Builds | popularité OpenDota | cache hors ligne |
| Rôles / winrates | OpenDota heroStats | patch actuel |
| Conseils de guides | vidéos Bilibili + DeepSeek | guides du patch |
| Voix | edge-tts en ligne (optionnel) | 9 langues, retour au bip si échec |

**Règles** : aucune lecture mémoire, aucune injection, aucune entrée simulée, aucune automatisation.

## Feuille de route

| Étape | Contenu | État |
|---|---|---|
| M0 | pipeline GSI, logs, scripts | terminé |
| M1 | reconnaissance des compositions + carte | 10/10 via la barre |
| M2 | base de connaissances + conseils de draft | pas commencé |
| M3 | coach de lane | terminé |
| M4 | conseils d'objets | un objet + raison/usage/build |
| M5 | alertes de teamfight | minimap + conseils de rôle (après 10 min) |
| M6 | packaging et docs | fenêtre, réglages/aide, deux exe |
| M7 | bibliothèque de guides Bilibili | fonctionnel |

## Build et tests

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Sortie : `dist\Dota2Coach\Dota2Coach.exe` (fenêtre) et `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (carte seule).

## Téléchargement

- Version portable (Windows x64) : [Releases](https://github.com/OWNER/REPO/releases/latest) — décompressez et lancez `Dota2Coach.exe`
- Depuis les sources : voir Démarrage rapide ci-dessus

## Conformité et avertissement

- Projet non officiel, sans lien avec Valve.
- Lit uniquement le GSI officiel et des captures de votre écran ; pas de lecture mémoire, pas d'injection, pas de touches simulées.
- Respectez les conditions d'utilisation de Steam et de Dota 2 ; utilisation à vos risques.

## Remerciements

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Plus

- Documentation la plus complète (arborescence, sources, git) : [README.zh-CN.md](README.zh-CN.md).
- Données et scripts : [docs/data-sources.md](docs/data-sources.md).
