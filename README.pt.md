<!-- Idioma / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

Coach de Dota 2 em tempo real, como overlay externo. Usa apenas o **GSI oficial da Valve** e **capturas da sua própria tela**:
sem leitura de memória, sem injeção, sem teclas simuladas, sem mods.

<p>
  <a href="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Capturas de tela

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Para quem é

**Para quem está começando no Dota 2**: não conhece todos os heróis, não sabe onde ficar na lane, copia builds e se perde nas lutas em equipe.

Escolhas conscientes:

- **Nunca joga por você**: uma frase curta quando importa, não uma parede de números;
- **Não precisa de Dota Plus**: os heróis são reconhecidos pela barra superior, conta normal serve;
- **Sem leitura de memória**: GSI oficial + captura da sua tela;
- **9 idiomas de interface + 9 de fala**: interface, dicas e voz mudam juntas;
- **Revisão após cada partida**: 1–3 ajustes para a próxima, ganhando ou perdendo.

## O que faz

- Lê o GSI: herói/nível/HP/mana/habilidades/itens/ouro/KDA, tempo, placar;
- **Captura a tela de estratégia** e reconhece os 10 heróis pela barra superior (sem Dota Plus); 10/10 em 2560×1600;
- Escreve **nomes sob cada retrato** da barra (aliados em verde, inimigos em vermelho, cliques passam);
- **Cartão sempre visível** semitransparente: fase e relógio, composições, próximo item, timers de runas;
- **Coach de lane**: indica sua lane, posicionamento e limite de HP conforme ameaças (iniciação/burst/push/invisibilidade), além de ward aos 4 min, noite aos 5 min, roam no nível 6 e aviso de last hits;
- **Som + fala em 9 idiomas**: runas, lane, itens, uso de itens e lutas são falados; a voz usa edge-tts online, então funciona mesmo com o motor de voz do Windows quebrado; **o pacote de voz segue o idioma da interface**;
- **Biblioteca de guias (Bilibili)**: coleta periódica de guias do mesmo patch (título/comentários/danmaku, transcrição opcional), resumidos em uma frase por LLM; atualização semanal com limpeza;
- **Três estados de interface**: saudação, coaching na partida e resumo final (stats, 1–3 dicas, um incentivo) que volta em 30 s;
- **Tema**: imagem de fundo trocável (Configurações → Tema);
- **Pacotes de voz**: 13 vozes edge (5 chinesas + uma para zh-TW/en/fr/ru/de/pt/es/tr), além de voz personalizada;
- **Alertas de luta**: a partir dos 10 min observa os pontos do minimapa, avisa quando inimigos somem, aliados se juntam ou a luta começa, com dica por função; posição/tamanho do minimapa configuráveis;
- **F8** mostra/oculta o cartão, **F9** testa a voz; o cartão deixa os cliques passarem.

## Novidades

- **Nove idiomas**: 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Janela principal, configurações, ajuda, resumo, página de build e pacotes de voz seguem o idioma; a janela principal muda na hora, sem reiniciar.
- **Fala em nove idiomas**: avisos de itens (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), consumíveis de lane (Dust/Magic Stick/Stout Shield/Tango), runas e lutas são falados no idioma atual; sem nomes de habilidades em chinês nos outros idiomas.
- **Página de build**: gerada por idioma em `data/ingame_guide.<lang>.html`.
- **Minimapa adaptativo**: encontra o minimapa em qualquer canto inferior e se ajusta ao tamanho; se errar, Configurações → Assistência → Minimapa define posição/tamanho/X-Y; varredura a partir dos 10 min e reposicionamento após muito tempo sem pontos vermelhos.
- **Fala mais limpa**: texto normalizado (`·`, `——`, `（）`, `7:00`, `6.8k`) e reprodução pela duração real do áudio.
- **Resumo mais justo**: suportes não recebem mais "poucos last hits / GPM baixo"; saudações e incentivos são aleatórios.
- **Um item por vez**: o cartão recomenda o item a comprar agora, com motivo, uso e build, depois passa ao próximo.
- **Dois exe**: `Dota2Coach.exe` abre a janela, `Dota2Coach-Card.exe` só o cartão; `*.old.exe` antigos são limpos ao iniciar.

## Início rápido

```powershell
cd <pasta do projeto>

# 1) ambiente + dependências (Python 3.12)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) copiar a config GSI para a pasta do jogo
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) baixar modelos e dados (uma vez)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) opcional: fala online (uma dependência para os 9 idiomas)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) reinicie o Dota 2 e abra o coach
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Instalação detalhada e solução de problemas: [docs/install.md](docs/install.md) (em chinês).

## Idioma e voz

Configurações → Idioma: escolha um dos nove e salve; a janela principal muda na hora, sem reiniciar. O pacote de voz troca automaticamente; uma voz personalizada é mantida.
Configurações → Voz: ligar/desligar, velocidade/volume e "Ouvir esta voz". Se falhar, volta ao som de aviso; log em `logs\voice.log`.

## Limites de dados

| Dado | Fonte | Observação |
|---|---|---|
| Seu herói/habilidades/itens/ouro | GSI | oficial, tempo real |
| Relógio/placar/torres | GSI | oficial, tempo real |
| Composições | captura da tela de estratégia | GSI só entrega "você" |
| Posições inimigas / lutas | captura do minimapa | segmentação por cor + cluster |
| Builds | popularidade de itens OpenDota | cache offline |
| Funções / winrates | OpenDota heroStats | patch atual |
| Dicas de guias | vídeos Bilibili + DeepSeek | guias do patch |
| Fala | edge-tts online (opcional) | 9 idiomas, volta ao som |

**Linhas vermelhas**: sem leitura de memória, sem injeção, sem entradas simuladas, sem automação.

## Roteiro

| Fase | Conteúdo | Status |
|---|---|---|
| M0 | pipeline GSI, logs, scripts | concluído |
| M1 | reconhecimento das composições + cartão | 10/10 pela barra |
| M2 | base de conhecimento + dicas de draft | não iniciado |
| M3 | coach de lane | concluído |
| M4 | dicas de itens | um item + motivo/uso/build |
| M5 | alertas de luta | minimapa + dica por função (após 10 min) |
| M6 | empacotamento e docs | janela, config/ajuda, dois exe |
| M7 | biblioteca de guias Bilibili | funcionando |

## Build e testes

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Saída: `dist\Dota2Coach\Dota2Coach.exe` (janela) e `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (só cartão).

## Download

- Versão portátil (Windows x64): [Releases](https://github.com/He-Xiqing/dota2-coach/releases/latest) — descompacte e execute `Dota2Coach.exe`
- A partir do código: veja Início rápido acima

## Conformidade e aviso

- Não é um produto oficial da Valve e não tem vínculo com ela.
- Lê apenas o GSI oficial e capturas da sua própria tela; sem leitura de memória, injeção ou entradas simuladas.
- Respeite os termos da Steam e do Dota 2; use por sua conta e risco.

## Créditos

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Mais

- Documentação mais completa (estrutura, fontes, git): [README.zh-CN.md](README.zh-CN.md).
- Dados e scripts: [docs/data-sources.md](docs/data-sources.md).
