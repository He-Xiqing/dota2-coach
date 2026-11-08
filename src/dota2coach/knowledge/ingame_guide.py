"""游戏内“出装顺序”说明页（九语言，随语言设置生成）。"""

from __future__ import annotations

from pathlib import Path

LANGUAGES = (
    "zh-CN",
    "zh-TW",
    "en",
    "fr",
    "ru",
    "de",
    "pt",
    "es",
    "tr",
)

_TPL = """<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<title>__TITLE__ · DOTA2 Coach</title>
<style>
  body { margin: 0; background: #f6f7f9; color: #1f2328;
         font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif; }
  main { max-width: 760px; margin: 32px auto; background: #fff; border-radius: 12px;
         padding: 28px 32px 36px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  h1 { font-size: 24px; margin: 0 0 6px; }
  .sub { color: #6b7280; font-size: 13px; margin-bottom: 22px; }
  h2 { font-size: 17px; margin: 24px 0 8px; }
  p, li { font-size: 14px; line-height: 1.9; }
  ol, ul { padding-left: 22px; }
  code { background: #f1f3f5; padding: 1px 6px; border-radius: 4px; font-size: 13px; }
  .tip { background: #eef4ff; border-left: 3px solid #2f6fed; padding: 10px 14px;
         border-radius: 6px; font-size: 13px; line-height: 1.8; margin: 16px 0; }
  .foot { color: #6b7280; font-size: 12px; margin-top: 26px; }
</style>
</head>
<body>
<main>
  <h1>__H1__</h1>
  <div class="sub">__SUB__</div>

  <h2>__S1__</h2>
  <p>__P1__</p>

  <h2>__S2__</h2>
  <ol>
    <li>__O1__</li>
    <li>__O2__</li>
    <li>__O3__</li>
  </ol>

  <div class="tip">__TIP__</div>

  <h2>__S3__</h2>
  <ul>
    <li>__U1__</li>
    <li>__U2__</li>
    <li>__U3__</li>
  </ul>

  <h2>__S4__</h2>
  <ul>
    <li>__T1__</li>
    <li>__T2__</li>
    <li>__T3__</li>
  </ul>

  <p class="foot">__FOOT__</p>
</main>
</body>
</html>
"""

_TEXT: dict[str, dict[str, str]] = {
    "zh-CN": {
        "title": "游戏内“出装顺序”怎么用",
        "h1": "游戏内“出装顺序”怎么用",
        "sub": "对应软件卡片里的「下一件 / 后续」；这里讲游戏里怎么看、怎么按顺序买。",
        "s1": "1. 打开商店",
        "p1": "游戏内按 <code>F3</code>（或点右下角商店图标）打开商店。商店上方有「<strong>攻略</strong>」「<strong>推荐</strong>」两个标签。",
        "s2": "2. 看推荐出装顺序",
        "o1": "点「<strong>攻略</strong>」标签，左侧会列出当前版本的热门出装路线。",
        "o2": "部分路线会带 <strong>1 → 2 → 3</strong> 的先后标记：按顺序买，优先把第一件做出来。",
        "o3": "没有顺序标记时，看「<strong>推荐</strong>」标签的装备格子，从左到右通常就是优先级。",
        "tip": "本软件的卡片每次只推<strong>一件</strong>（附理由/用法/加点）。你买完这件后，下次刷新会自动换下一件——和游戏内攻略的长路线是同一个思路，只是拆成了单步。",
        "s3": "3. 我们推荐的顺序从哪来",
        "u1": "优先用 B 站攻略里提炼的出装序列（设置→辅助可看攻略库条数与更新时间）。",
        "u2": "没有攻略数据时，退回 OpenDota 的当前版本热门出装（按英雄热度排序）。",
        "u3": "会结合你自己的英雄特性过滤：自带驱散的英雄不再被推荐分身斧，已有黑皇杖就不再重复推控制装。",
        "s4": "4. 小技巧",
        "t1": "<code>Ctrl</code> + 左键点装备可以快速购买并送到英雄身上。",
        "t2": "出门装阶段先买「消耗品」里的吃树/大药，再按推荐做第一个小件。",
        "t3": "买错方向时，按卡片「理由」里的威胁提示换一件针对性装备（如对面沉默多 → 黑皇/分身）。",
        "foot": "说明会随版本调整；如与游戏内不一致，以客户端内「攻略/推荐」为准。",
    },
    "zh-TW": {
        "title": "遊戲內「出裝順序」怎麼用",
        "h1": "遊戲內「出裝順序」怎麼用",
        "sub": "對應軟體卡片裡的「下一件 / 後續」；這裡講遊戲裡怎麼看、怎麼按順序買。",
        "s1": "1. 打開商店",
        "p1": "遊戲內按 <code>F3</code>（或點右下角商店圖示）打開商店。商店上方有「<strong>攻略</strong>」「<strong>推薦</strong>」兩個標籤。",
        "s2": "2. 看推薦出裝順序",
        "o1": "點「<strong>攻略</strong>」標籤，左側會列出目前版本的熱門出裝路線。",
        "o2": "部分路線會帶 <strong>1 → 2 → 3</strong> 的先後標記：按順序買，優先做出第一件。",
        "o3": "沒有順序標記時，看「<strong>推薦</strong>」標籤的裝備格子，從左到右通常就是優先級。",
        "tip": "本軟體的卡片每次只推<strong>一件</strong>（附理由/用法/加點）。買完這件後，下次刷新會自動換下一件——和遊戲內攻略的長路線是同一個思路，只是拆成單步。",
        "s3": "3. 我們推薦的順序從哪來",
        "u1": "優先採用 B 站攻略裡提煉的出裝序列（設定→輔助可看攻略庫條數與更新時間）。",
        "u2": "沒有攻略資料時，退回 OpenDota 目前版本的熱門出裝（按英雄熱度排序）。",
        "u3": "會結合你的英雄特性過濾：自帶驅散的英雄不再推薦分身斧，已有黑皇杖就不再重複推控制裝。",
        "s4": "4. 小技巧",
        "t1": "<code>Ctrl</code> + 左鍵點裝備可以快速購買並送到英雄身上。",
        "t2": "出門裝階段先買「消耗品」裡的吃樹/大藥，再按推薦做第一個小件。",
        "t3": "買錯方向時，按卡片「理由」裡的威脅提示換一件針對性裝備（如對面沉默多 → 黑皇/分身）。",
        "foot": "說明會隨版本調整；如與遊戲內不一致，以客戶端內「攻略/推薦」為準。",
    },
    "en": {
        "title": "Using the in-game build order",
        "h1": "Using the in-game “build order”",
        "sub": "This matches “Next item / After that” on the card; here is how to read it and buy in order in game.",
        "s1": "1. Open the shop",
        "p1": "Press <code>F3</code> in game (or click the shop icon at the bottom-right). The shop has <strong>Guide</strong> and <strong>Recommended</strong> tabs at the top.",
        "s2": "2. Read the recommended build",
        "o1": "Open the <strong>Guide</strong> tab: popular builds for the current patch are listed on the left.",
        "o2": "Some builds show <strong>1 → 2 → 3</strong>: buy in that order and finish the first item first.",
        "o3": "Without numbers, the <strong>Recommended</strong> grid reads left to right by priority.",
        "tip": "The card recommends <strong>one</strong> item at a time (with reason, usage and skill build). After you buy it, the next refresh moves to the next item — the same idea as a long in-game build, split into single steps.",
        "s3": "3. Where our order comes from",
        "u1": "Build sequences extracted from Bilibili guides come first (Settings → Assist shows the count and update time).",
        "u2": "Without guide data we fall back to OpenDota’s popular items for the current patch.",
        "u3": "We filter by your hero’s kit: heroes with a built-in dispel are not told to buy Manta, and if you already own BKB we stop pushing more control items.",
        "s4": "4. Tips",
        "t1": "<code>Ctrl</code> + left-click an item to quick-buy and deliver it to your hero.",
        "t2": "In the starting-items phase buy tangos/salve from Consumables first, then your first small item.",
        "t3": "If the threat changes, use the reason on the card to swap in a counter item (e.g. lots of silence → BKB/Manta).",
        "foot": "This page may change between patches; if it differs from the client, trust the in-game Guide/Recommended tabs.",
    },
    "fr": {
        "title": "Utiliser l’ordre d’achat en jeu",
        "h1": "Utiliser l’« ordre d’achat » en jeu",
        "sub": "Correspond à « Prochain objet / Ensuite » sur la carte ; voici comment le lire et acheter dans l’ordre en jeu.",
        "s1": "1. Ouvrir la boutique",
        "p1": "Appuyez sur <code>F3</code> en jeu (ou cliquez sur l’icône boutique en bas à droite). La boutique a les onglets <strong>Guide</strong> et <strong>Recommandé</strong> en haut.",
        "s2": "2. Lire l’ordre recommandé",
        "o1": "Ouvrez l’onglet <strong>Guide</strong> : les builds populaires du patch sont listés à gauche.",
        "o2": "Certains builds affichent <strong>1 → 2 → 3</strong> : achetez dans cet ordre et terminez d’abord le premier objet.",
        "o3": "Sans numéros, la grille <strong>Recommandé</strong> se lit de gauche à droite par priorité.",
        "tip": "La carte ne propose qu’<strong>un</strong> objet à la fois (avec raison, usage et ordre des sorts). Après l’achat, le prochain rafraîchissement passe à l’objet suivant — même logique qu’un build long, découpé en étapes.",
        "s3": "3. D’où vient notre ordre",
        "u1": "D’abord les séquences extraites des guides Bilibili (Réglages → Assistance affiche le nombre et la date).",
        "u2": "Sans données de guide, on retombe sur les objets populaires OpenDota du patch.",
        "u3": "On filtre selon ton héros : pas de Manta pour un héros avec dispel intégré, et si tu as déjà la BKB on arrête de proposer des objets de contrôle.",
        "s4": "4. Astuces",
        "t1": "<code>Ctrl</code> + clic gauche sur un objet pour l’acheter et le livrer à ton héros.",
        "t2": "Au départ, achète d’abord tango/salve dans Consommables, puis ton premier petit objet.",
        "t3": "Si la menace change, utilise la raison sur la carte pour prendre un objet de contre (ex. beaucoup de silence → BKB/Manta).",
        "foot": "Cette page peut changer selon le patch ; en cas de différence, fie-toi aux onglets Guide/Recommandé du client.",
    },
    "ru": {
        "title": "Как пользоваться порядком закупки в игре",
        "h1": "Как пользоваться «порядком закупки» в игре",
        "sub": "Соответствует «Следующий предмет / Далее» на карточке; здесь — как смотреть и покупать по порядку в игре.",
        "s1": "1. Откройте магазин",
        "p1": "Нажмите <code>F3</code> в игре (или кликните по иконке магазина справа снизу). Сверху у магазина есть вкладки <strong>Гайд</strong> и <strong>Рекомендованные</strong>.",
        "s2": "2. Смотрите рекомендованный порядок",
        "o1": "Откройте вкладку <strong>Гайд</strong>: слева показаны популярные сборки текущего патча.",
        "o2": "У части сборок есть <strong>1 → 2 → 3</strong>: покупайте по порядку и сначала завершите первый предмет.",
        "o3": "Без номеров сетка <strong>Рекомендованные</strong> читается слева направо по приоритету.",
        "tip": "Карточка предлагает только <strong>один</strong> предмет (с причиной, применением и прокачкой). После покупки следующее обновление покажет следующий — та же длинная сборка, но разбитая на шаги.",
        "s3": "3. Откуда берётся наш порядок",
        "u1": "Сначала последовательности из гайдов Bilibili (Настройки → Подсказки показывают число и дату обновления).",
        "u2": "Без данных гайдов — популярные предметы OpenDota для текущего патча.",
        "u3": "Учитываем особенности героя: героям со своим диспелом не предлагаем Manta, а при уже купленной BKB не повторяем предметы контроля.",
        "s4": "4. Советы",
        "t1": "<code>Ctrl</code> + левый клик по предмету — быстрая покупка с доставкой герою.",
        "t2": "На старте сначала купите танго/зелья в «Расходниках», затем первый малый предмет.",
        "t3": "Если угроза сменилась, используйте причину на карточке и возьмите контр-предмет (например, много молчания → BKB/Manta).",
        "foot": "Страница может меняться между патчами; при расхождении ориентируйтесь на вкладки Гайд/Рекомендованные в клиенте.",
    },
    "de": {
        "title": "Die Build-Reihenfolge im Spiel nutzen",
        "h1": "Die „Build-Reihenfolge“ im Spiel nutzen",
        "sub": "Entspricht „Nächstes Item / Danach“ auf der Karte; hier steht, wie du sie im Spiel liest und in Reihenfolge kaufst.",
        "s1": "1. Shop öffnen",
        "p1": "Drücke im Spiel <code>F3</code> (oder klicke unten rechts auf das Shop-Symbol). Oben im Shop gibt es die Tabs <strong>Guide</strong> und <strong>Empfohlen</strong>.",
        "s2": "2. Empfohlene Reihenfolge lesen",
        "o1": "Öffne den <strong>Guide</strong>-Tab: links stehen populäre Builds des aktuellen Patches.",
        "o2": "Manche Builds zeigen <strong>1 → 2 → 3</strong>: kaufe in dieser Reihenfolge und schließe zuerst das erste Item ab.",
        "o3": "Ohne Nummern gilt im <strong>Empfohlen</strong>-Raster die Reihenfolge von links nach rechts.",
        "tip": "Die Karte empfiehlt immer nur <strong>ein</strong> Item (mit Grund, Nutzung und Skill-Build). Nach dem Kauf rückt die nächste Aktualisierung zum nächsten Item vor — dieselbe lange Build, nur in Einzelschritte zerlegt.",
        "s3": "3. Woher unsere Reihenfolge kommt",
        "u1": "Zuerst Build-Sequenzen aus Bilibili-Guides (Einstellungen → Assistenz zeigt Anzahl und Datum).",
        "u2": "Ohne Guide-Daten greifen wir auf OpenDota-Popularität des Patches zurück.",
        "u3": "Wir filtern nach deinem Helden: Helden mit eigenem Dispel bekommen kein Manta, und mit vorhandener BKB werden keine weiteren Kontroll-Items mehr vorgeschlagen.",
        "s4": "4. Tipps",
        "t1": "<code>Ctrl</code> + Linksklick auf ein Item kauft es schnell und liefert es zum Helden.",
        "t2": "Kaufe am Start zuerst Tango/Salve unter Verbrauchsgüter, dann das erste kleine Item.",
        "t3": "Ändert sich die Bedrohung, nutze den Grund auf der Karte für ein Konter-Item (z. B. viel Silence → BKB/Manta).",
        "foot": "Diese Seite kann sich mit Patches ändern; bei Abweichungen gelten die Tabs Guide/Empfohlen im Client.",
    },
    "pt": {
        "title": "Como usar a ordem de itens no jogo",
        "h1": "Como usar a “ordem de itens” no jogo",
        "sub": "Corresponde a “Próximo item / Depois” no cartão; aqui mostra como ler e comprar em ordem no jogo.",
        "s1": "1. Abra a loja",
        "p1": "Pressione <code>F3</code> no jogo (ou clique no ícone da loja no canto inferior direito). A loja tem as abas <strong>Guia</strong> e <strong>Recomendado</strong> no topo.",
        "s2": "2. Leia a ordem recomendada",
        "o1": "Abra a aba <strong>Guia</strong>: builds populares do patch atual aparecem à esquerda.",
        "o2": "Algumas builds mostram <strong>1 → 2 → 3</strong>: compre nessa ordem e termine o primeiro item primeiro.",
        "o3": "Sem números, a grade <strong>Recomendado</strong> segue da esquerda para a direita por prioridade.",
        "tip": "O cartão recomenda <strong>um</strong> item por vez (com motivo, uso e ordem de habilidades). Depois de comprar, a próxima atualização passa ao seguinte — a mesma build longa, dividida em passos.",
        "s3": "3. De onde vem nossa ordem",
        "u1": "Primeiro as sequências extraídas de guias do Bilibili (Configurações → Assistência mostra quantidade e data).",
        "u2": "Sem dados de guia, usamos os itens populares da OpenDota para o patch.",
        "u3": "Filtramos pelo herói: heróis com dispel próprio não recebem Manta, e com BKB já comprada paramos de sugerir itens de controle.",
        "s4": "4. Dicas",
        "t1": "<code>Ctrl</code> + clique esquerdo compra rápido e entrega ao herói.",
        "t2": "No início, compre tango/salve em Consumíveis e depois o primeiro item pequeno.",
        "t3": "Se a ameaça mudar, use o motivo no cartão para trocar por um item de contra (ex.: muito silêncio → BKB/Manta).",
        "foot": "Esta página pode mudar entre patches; se divergir, siga as abas Guia/Recomendado do cliente.",
    },
    "es": {
        "title": "Cómo usar el orden de objetos en partida",
        "h1": "Cómo usar el “orden de objetos” en partida",
        "sub": "Corresponde a “Siguiente objeto / Después” en la tarjeta; aquí se explica cómo leerlo y comprar en orden en el juego.",
        "s1": "1. Abre la tienda",
        "p1": "Pulsa <code>F3</code> en partida (o haz clic en el icono de la tienda abajo a la derecha). La tienda tiene las pestañas <strong>Guía</strong> y <strong>Recomendado</strong> arriba.",
        "s2": "2. Lee el orden recomendado",
        "o1": "Abre la pestaña <strong>Guía</strong>: a la izquierda aparecen las builds populares del parche.",
        "o2": "Algunas builds muestran <strong>1 → 2 → 3</strong>: compra en ese orden y termina primero el primer objeto.",
        "o3": "Sin números, la cuadrícula <strong>Recomendado</strong> se lee de izquierda a derecha por prioridad.",
        "tip": "La tarjeta recomienda <strong>un</strong> objeto a la vez (con motivo, uso y orden de habilidades). Tras comprarlo, la siguiente actualización pasa al siguiente — la misma build larga, dividida en pasos.",
        "s3": "3. De dónde sale nuestro orden",
        "u1": "Primero las secuencias extraídas de guías de Bilibili (Ajustes → Asistencia muestra cantidad y fecha).",
        "u2": "Sin datos de guía, usamos los objetos populares de OpenDota del parche.",
        "u3": "Filtramos por tu héroe: los que tienen dispel propio no reciben Manta, y con BKB ya comprada dejamos de sugerir objetos de control.",
        "s4": "4. Consejos",
        "t1": "<code>Ctrl</code> + clic izquierdo compra rápido y entrega al héroe.",
        "t2": "Al inicio compra tango/salve en Consumibles y luego tu primer objeto pequeño.",
        "t3": "Si cambia la amenaza, usa el motivo de la tarjeta para cambiar a un objeto de contra (p. ej. mucho silencio → BKB/Manta).",
        "foot": "Esta página puede cambiar entre parches; si difiere, haz caso a las pestañas Guía/Recomendado del cliente.",
    },
    "tr": {
        "title": "Oyun içi item sırası nasıl kullanılır",
        "h1": "Oyun içi “item sırası” nasıl kullanılır",
        "sub": "Karttaki “Sıradaki item / Sonrası” ile eşleşir; burada oyunda nasıl okunacağı ve sırayla nasıl alınacağı anlatılır.",
        "s1": "1. Mağazayı aç",
        "p1": "Oyunda <code>F3</code> tuşuna bas (veya sağ alttaki mağaza simgesine tıkla). Mağazanın üstünde <strong>Rehber</strong> ve <strong>Önerilen</strong> sekmeleri var.",
        "s2": "2. Önerilen sırayı oku",
        "o1": "<strong>Rehber</strong> sekmesini aç: solda güncel yamanın popüler dizilişleri listelenir.",
        "o2": "Bazı dizilişlerde <strong>1 → 2 → 3</strong> vardır: bu sırayla al ve önce ilk itemi tamamla.",
        "o3": "Numara yoksa <strong>Önerilen</strong> sekmesindeki ızgara soldan sağa öncelik sırasıdır.",
        "tip": "Kart her seferinde yalnızca <strong>bir</strong> item önerir (gerekçe, kullanım ve yetenek sırası ile). Aldıktan sonra bir sonraki yenilemede sıradaki iteme geçer — uzun dizilişin adımlara bölünmüş hali.",
        "s3": "3. Sıralamamız nereden geliyor",
        "u1": "Önce Bilibili rehberlerinden çıkarılan dizilişler (Ayarlar → Yardımcı, sayı ve güncelleme tarihini gösterir).",
        "u2": "Rehber verisi yoksa OpenDota’nın güncel popüler itemlerine döneriz.",
        "u3": "Kahramanına göre filtreleriz: kendi dispeli olan kahramana Manta önerilmez, BKB varsa kontrol itemi önerileri kesilir.",
        "s4": "4. İpuçları",
        "t1": "<code>Ctrl</code> + sol tık ile itemi hızlıca alıp kahramana gönderirsin.",
        "t2": "Başlangıçta önce Sarf Malzemeleri’nden tango/salve al, sonra ilk küçük itemi yap.",
        "t3": "Tehdit değişirse karttaki gerekçeyle karşı iteme geç (ör. çok sessizleştirme → BKB/Manta).",
        "foot": "Bu sayfa yamalar arasında değişebilir; farklıysa istemcideki Rehber/Önerilen sekmelerini esas al.",
    },
}


def normalize_language(language: str) -> str:
    code = (language or "").strip()
    if code in _TEXT:
        return code
    if code.startswith("zh"):
        return "zh-CN"
    return "en"


def render(language: str) -> str:
    code = normalize_language(language)
    text = dict(_TEXT[code])
    text["lang"] = code
    html = _TPL
    for key, value in text.items():
        html = html.replace(f"__{key.upper()}__", value)
    return html


def guide_path(data_dir: Path | str, language: str) -> Path:
    code = normalize_language(language)
    return Path(data_dir) / f"ingame_guide.{code}.html"


def ensure_guide(data_dir: Path | str, language: str) -> Path:
    """按当前语言写出一份说明页，返回路径。"""
    code = normalize_language(language)
    target = guide_path(data_dir, code)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(code), encoding="utf-8")
        if code == "zh-CN":
            legacy = Path(data_dir) / "ingame_guide.html"
            legacy.write_text(render(code), encoding="utf-8")
    except OSError:
        pass
    return target
