<!-- Dil / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

Dota 2 için harici overlay olarak çalışan gerçek zamanlı koç. Yalnızca **Valve'in resmi GSI**'sini ve **kendi ekranının görüntüsünü** kullanır:
bellek okuma yok, enjeksiyon yok, tuş simülasyonu yok, mod yok.

<p>
  <a href="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Ekran görüntüleri

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Kimler için

**Dota 2'ye yeni başlayanlar için**: tüm kahramanları bilmiyorsun, koridorda nerede duracağını bilmiyorsun, build'leri kopyalıyorsun ve takım savaşlarında ne yapacağını bilemiyorsun.

Bilinçli tercihler:

- **Senin yerine oynamaz**: gerektiğinde tek kısa cümle, veri duvarı değil;
- **Dota Plus gerekmez**: kahramanlar üst çubuktan tanınır, normal hesap yeter;
- **Bellek okuma yok**: resmi GSI + kendi ekranının görüntüsü;
- **9 arayüz dili + 9 konuşma dili**: arayüz, ipuçları ve ses birlikte değişir;
- **Her maçtan sonra özet**: kazan ya da kaybet, uygulanabilir 1–3 öneri.

## Neler yapar

- GSI okur: kahraman/seviye/HP/mana/yetenekler/eşyalar/altın/KDA, oyun süresi, skor;
- **Strateji ekranını yakalar** ve 10 kahramanı üst çubuktan tanır (Dota Plus gerekmez); 2560×1600'de 10/10;
- Üst çubuktaki portrelerin **altına isim yazar** (müttefikler yeşil, düşmanlar kırmızı, tıklamalar geçer);
- Yarı saydam **ön planda kart**: faz ve süre, dizilişler, sonraki eşya, rune sayaçları;
- **Koridor koçu**: koridorunu söyler, düşman tehditlerine göre (başlatma/patlama/push/görünmezlik) konum ve HP önerir; 4. dakika ward, 5. dakika gece, 6. seviye roam ve last-hit uyarısı;
- **Ses + 9 dilde konuşma**: rune, koridor, eşya, eşya kullanımı ve savaş önerileri okunur; ses, çevrimiçi edge-tts ile üretilir, Windows ses motoru bozuk olsa da çalışır; **ses paketi arayüz dilini takip eder**;
- **Rehber kütüphanesi (Bilibili)**: aynı yama rehberlerini düzenli toplar (başlık/yorum/danmaku, isteğe bağlı transkript), LLM tek cümleye indirir; haftalık güncelleme ve temizlik;
- **Üç arayüz durumu**: karşılama, maç içi koçluk ve maç sonu özeti (istatistik, 1–3 öneri, bir moral) 30 sn sonra başa döner;
- **Tema**: değiştirilebilir arka plan (Ayarlar → Tema);
- **Ses paketleri**: 13 edge sesi (5 Çince + zh-TW/en/fr/ru/de/pt/es/tr için birer), ayrıca özel ses;
- **Savaş uyarıları**: 10. dakikadan itibaren minimap noktalarını izler; düşmanlar kaybolunca, müttefikler toplanınca veya savaş başlayınca rolüne göre ne yapacağını söyler; minimap konumu/boyutu ayarlanabilir;
- **F8** kartı göster/gizle, **F9** sesi dene; kart tıklamaları geçirir.

## Yenilikler

- **Dokuz dil**: 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Ana pencere, ayarlar, yardım, maç sonu özeti, build sayfası ve ses paketleri dili takip eder; ana pencere yeniden başlatmadan hemen değişir.
- **Dokuz dilde konuşma**: eşya uyarıları (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), koridor tüketimleri (Dust/Magic Stick/Stout Shield/Tango), rune ve savaş önerileri geçerli dilde okunur; diğer dillerde Çince yetenek adı görünmez.
- **Build sayfası**: her dil için `data/ingame_guide.<lang>.html` üretir.
- **Uyarlanabilir minimap**: minimapı iki alt köşede bulur ve boyuta uyum sağlar; emin olamazsa Ayarlar → Yardım → Minimap ile konum/boyut/X-Y ayarlanır; tarama 10. dakikada başlar, uzun süre kırmızı nokta yoksa yeniden konumlanır.
- **Daha temiz ses**: metin normalize edilir (`·`, `——`, `（）`, `7:00`, `6.8k`), ses gerçek süresine göre oynatılır.
- **Daha akıllı özet**: destek kahramanlara artık "az last hit / düşük GPM" denmez; karşılama ve moral cümleleri rastgele.
- **Tek seferde tek eşya**: kart, şimdi alınması gereken eşyayı gerekçe, kullanım ve skill build ile önerir; alınca sonrakine geçer.
- **İki exe**: `Dota2Coach.exe` ana pencereyi, `Dota2Coach-Card.exe` yalnızca kartı açar; eski `*.old.exe` dosyaları başlangıçta silinir.

## Hızlı başlangıç

```powershell
cd <proje klasörü>

# 1) ortam + bağımlılıklar (Python 3.12 gerekir)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) GSI yapılandırmasını oyun klasörüne kopyala
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) şablonları ve verileri indir (bir kez)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) isteğe bağlı: çevrimiçi konuşma (9 dil için tek bağımlılık)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) Dota 2'yi yeniden başlat, sonra koçu aç
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Ayrıntılı kurulum ve sorun giderme: [docs/install.md](docs/install.md) (Çince).

## Dil ve ses

Ayarlar → Dil: dokuz dilden birini seç ve kaydet; ana pencere yeniden başlatmadan hemen değişir. Ses paketi otomatik olarak o dile geçer; özel ses korunur.
Ayarlar → Ses: konuşmayı aç/kapat, hız/ses düzeyi, "Bu sesi dinle". Başarısız olursa uyarı sesine döner; günlük `logs\voice.log`.

## Veri sınırları

| Veri | Kaynak | Not |
|---|---|---|
| Kahramanın/yeteneklerin/eşyaların/altının | GSI | resmi, gerçek zamanlı |
| Süre/skor/kuleler | GSI | resmi, gerçek zamanlı |
| Dizilişler | strateji ekranı görüntüsü | GSI yalnızca "seni" verir |
| Düşman konumları / savaşlar | minimap görüntüsü | renk ayrımı + kümeleme |
| Build'ler | OpenDota eşya popülerliği | çevrimdışı önbellek |
| Roller / kazanma oranları | OpenDota heroStats | güncel yama |
| Rehber önerileri | Bilibili videoları + DeepSeek | yama rehberleri |
| Ses | çevrimiçi edge-tts (isteğe bağlı) | 9 dil, uyarı sesine döner |

**Kırmızı çizgiler**: bellek okuma yok, enjeksiyon yok, girdi simülasyonu yok, otomasyon yok.

## Yol haritası

| Aşama | İçerik | Durum |
|---|---|---|
| M0 | GSI hattı, günlükler, kurulum betikleri | tamam |
| M1 | diziliş tanıma + kart | üst çubuktan 10/10 |
| M2 | bilgi tabanı + draft önerisi | başlanmadı |
| M3 | koridor koçu | tamam |
| M4 | eşya önerisi | tek eşya + gerekçe/kullanım/build |
| M5 | savaş uyarıları | minimap + rol önerisi (10 dk sonra) |
| M6 | paketleme ve doküman | pencere, ayarlar/yardım, iki exe |
| M7 | Bilibili rehber kütüphanesi | çalışıyor |

## Derleme ve testler

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Çıktı: `dist\Dota2Coach\Dota2Coach.exe` (pencere) ve `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (yalnızca kart).

## İndirme

- Taşınabilir sürüm (Windows x64): [Releases](https://github.com/He-Xiqing/dota2-coach/releases/latest) — zip'i açıp `Dota2Coach.exe` çalıştırın
- Kaynaktan çalıştırma: yukarıdaki Hızlı başlangıç

## Uyumluluk ve sorumluluk reddi

- Resmî Valve ürünü değildir, Valve ile bağlantılı değildir.
- Yalnızca resmî GSI ve kendi ekranınızın görüntüsünü okur; bellek okuma, enjeksiyon veya tuş simülasyonu yoktur.
- Steam ve Dota 2 kullanım koşullarına uyun; risk size aittir.

## Teşekkürler

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Daha fazla

- En ayrıntılı doküman (klasörler, veri kaynakları, git): [README.zh-CN.md](README.zh-CN.md).
- Veriler ve betikler: [docs/data-sources.md](docs/data-sources.md).
