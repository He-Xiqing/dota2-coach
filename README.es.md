<!-- Idioma / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

Entrenador de Dota 2 en tiempo real como overlay externo. Usa solo el **GSI oficial de Valve** y **capturas de tu propia pantalla**:
sin leer memoria, sin inyección, sin teclas simuladas, sin mods.

<p>
  <a href="https://github.com/OWNER/REPO/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Capturas de pantalla

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Para quién es

**Para quienes empiezan en Dota 2**: no conoces todos los héroes, no sabes dónde colocarte en la línea, copias builds y te pierdes en las peleas.

Decisiones de diseño:

- **Nunca juega por ti**: una frase corta cuando importa, no un muro de datos;
- **No hace falta Dota Plus**: los héroes se reconocen desde la barra superior, sirve cualquier cuenta;
- **Sin lectura de memoria**: GSI oficial + captura de tu pantalla;
- **9 idiomas de interfaz + 9 de voz**: interfaz, consejos y voz cambian juntos;
- **Revisión tras cada partida**: 1–3 ajustes para la siguiente, ganes o pierdas.

## Qué hace

- Lee el GSI: héroe/nivel/HP/maná/habilidades/objetos/oro/KDA, tiempo, marcador;
- **Captura la pantalla de estrategia** y reconoce a los 10 héroes desde la barra superior (sin Dota Plus); 10/10 en 2560×1600;
- Escribe **nombres bajo cada retrato** de la barra (aliados en verde, enemigos en rojo, clics atraviesan);
- **Tarjeta siempre visible** semitransparente: fase y reloj, composiciones, siguiente objeto, timers de runas;
- **Coach de línea**: indica tu línea, posición y umbral de HP según amenazas (iniciación/burst/push/invisibilidad), más ward al minuto 4, noche al 5, roam al nivel 6 y aviso de last hits;
- **Sonido + voz en 9 idiomas**: runas, línea, objetos, uso de objetos y peleas se narran; la voz usa edge-tts en línea, así que funciona aunque el motor de voz de Windows esté roto; **el paquete de voz sigue el idioma de la interfaz**;
- **Biblioteca de guías (Bilibili)**: recolección periódica de guías del mismo parche (título/comentarios/danmaku, transcripción opcional), resumidas a una frase por un LLM; actualización semanal con limpieza;
- **Tres estados de interfaz**: saludo, coaching en partida y resumen final (stats, 1–3 consejos, un ánimo) que vuelve a los 30 s;
- **Tema**: imagen de fondo intercambiable (Ajustes → Tema);
- **Paquetes de voz**: 13 voces edge (5 chinas + una para zh-TW/en/fr/ru/de/pt/es/tr), más voz personalizada;
- **Alertas de pelea**: desde el minuto 10 vigila los puntos del minimapa, avisa cuando desaparecen enemigos, se agrupan aliados o empieza la pelea, con consejo según tu rol; posición/tamaño del minimapa configurables;
- **F8** muestra/oculta la tarjeta, **F9** prueba la voz; la tarjeta deja pasar los clics.

## Novedades

- **Nueve idiomas**: 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Ventana principal, ajustes, ayuda, resumen, página de build y paquetes de voz siguen el idioma; la ventana principal cambia al instante, sin reiniciar.
- **Voz en nueve idiomas**: avisos de objetos (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), consumibles de línea (Dust/Magic Stick/Stout Shield/Tango), runas y peleas se narran en el idioma actual; sin nombres de habilidades en chino en otros idiomas.
- **Página de build**: generada por idioma en `data/ingame_guide.<lang>.html`.
- **Minimapa adaptativo**: encuentra el minimapa en cualquier esquina inferior y se ajusta al tamaño; si falla, Ajustes → Asistencia → Minimapa permite posición/tamaño/X-Y; escaneo desde el minuto 10 y relocalización tras mucho tiempo sin puntos rojos.
- **Voz más limpia**: texto normalizado (`·`, `——`, `（）`, `7:00`, `6.8k`) y reproducción según la duración real del audio.
- **Resumen más justo**: los support ya no reciben "pocos last hits / GPM bajo"; saludos y ánimos son aleatorios.
- **Un objeto a la vez**: la tarjeta recomienda el objeto que comprar ahora, con motivo, uso y build, y luego pasa al siguiente.
- **Dos exe**: `Dota2Coach.exe` abre la ventana, `Dota2Coach-Card.exe` solo la tarjeta; los `*.old.exe` viejos se limpian al iniciar.

## Inicio rápido

```powershell
cd <carpeta del proyecto>

# 1) entorno + dependencias (Python 3.12)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) copiar la config GSI a la carpeta del juego
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) descargar plantillas y datos (una vez)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) opcional: voz en línea (una dependencia para los 9 idiomas)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) reinicia Dota 2 y abre el coach
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Instalación detallada y solución de problemas: [docs/install.md](docs/install.md) (en chino).

## Idioma y voz

Ajustes → Idioma: elige uno de los nueve y guarda; la ventana principal cambia al instante, sin reiniciar. El paquete de voz cambia automáticamente; una voz personalizada se mantiene.
Ajustes → Voz: activar/desactivar, velocidad/volumen y "Escuchar esta voz". Si falla, vuelve al aviso sonoro; registro en `logs\voice.log`.

## Límites de datos

| Dato | Fuente | Nota |
|---|---|---|
| Tu héroe/habilidades/objetos/oro | GSI | oficial, tiempo real |
| Reloj/marcador/torres | GSI | oficial, tiempo real |
| Composiciones | captura de la pantalla de estrategia | GSI solo entrega "tú" |
| Posiciones enemigas / peleas | captura del minimapa | segmentación por color + clustering |
| Builds | popularidad de objetos OpenDota | caché offline |
| Roles / winrates | OpenDota heroStats | parche actual |
| Consejos de guías | vídeos Bilibili + DeepSeek | guías del parche |
| Voz | edge-tts en línea (opcional) | 9 idiomas, vuelve al aviso |

**Líneas rojas**: sin lectura de memoria, sin inyección, sin entradas simuladas, sin automatización.

## Hoja de ruta

| Fase | Contenido | Estado |
|---|---|---|
| M0 | pipeline GSI, logs, scripts | hecho |
| M1 | reconocimiento de composiciones + tarjeta | 10/10 por la barra |
| M2 | base de conocimiento + consejos de draft | no iniciado |
| M3 | coach de línea | hecho |
| M4 | consejos de objetos | un objeto + motivo/uso/build |
| M5 | alertas de pelea | minimapa + consejo por rol (tras 10 min) |
| M6 | empaquetado y docs | ventana, ajustes/ayuda, dos exe |
| M7 | biblioteca de guías Bilibili | funcionando |

## Build y pruebas

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Salida: `dist\Dota2Coach\Dota2Coach.exe` (ventana) y `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (solo tarjeta).

## Descarga

- Versión portátil (Windows x64): [Releases](https://github.com/OWNER/REPO/releases/latest) — descomprime y ejecuta `Dota2Coach.exe`
- Desde el código: consulta Inicio rápido arriba

## Cumplimiento y aviso

- No es un producto oficial de Valve ni está afiliado a Valve.
- Solo lee el GSI oficial y capturas de tu propia pantalla; sin lectura de memoria, inyección ni entradas simuladas.
- Respeta los términos de Steam y Dota 2; úsalo bajo tu responsabilidad.

## Créditos

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Más

- Documentación más completa (estructura, fuentes, git): [README.zh-CN.md](README.zh-CN.md).
- Datos y scripts: [docs/data-sources.md](docs/data-sources.md).
