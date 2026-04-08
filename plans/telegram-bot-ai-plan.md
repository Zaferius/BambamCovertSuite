# Telegram Bot + AI Entegrasyon Planı

## Genel Vizyon

Bambam Converter Suite web app'ini bir Telegram botuna bağlamak. Kullanıcı botla sohbet eder gibi dosya gönderir ve doğal dil ile işlem yaptırır. Yapay zeka (GPT-4o-mini) bu istekleri parse edip mevcut FastAPI backend'ine yönlendirir.

**Örnek kullanım:**
- Kullanıcı bir video atar: "ilk 5 saniyesini kes ve MP4 yap"
- Kullanıcı bir fotoğraf atar: "arka planı kaldır"
- Kullanıcı bir ses dosyası atar: "MP3'e çevir, 192kbps"

---

## Mimari

```
Telegram Kullanıcısı
        ↓
  Telegram Bot Servisi (aiogram)
        ↓
  AI Katmanı (GPT-4o-mini - Function Calling)
        ↓
  Mevcut FastAPI Backend (api-bambam.zaferakkan.com)
        ↓
  RQ Worker (Dönüşüm işlemi)
        ↓
  Telegram Kullanıcısına sonuç dosyası geri gönderilir
```

---

## Aşama 1: rembg ile Background Remover Ekleme

Telegram botu planından önce bu özelliği backend'e ekle. Her iki kanaldan (Web UI + Telegram) kullanılabilir hale gelecek.

### Backend Adımları

**1. rembg'yi bağımlılıklara ekle**
```
# backend/requirements.txt
rembg
onnxruntime
```

**2. Yeni image service fonksiyonu**
`backend/app/services/image_service.py` dosyasına `remove_background` metodu ekle:
```python
from rembg import remove
from PIL import Image

def remove_background(source_path: Path, output_dir: Path) -> Path:
    output_path = output_dir / f"{source_path.stem}_nobg.png"
    with open(source_path, "rb") as f:
        result = remove(f.read())
    with open(output_path, "wb") as f:
        f.write(result)
    return output_path
```

**3. Yeni endpoint veya mevcut endpoint'e parametre ekle**
Seçenek A: `POST /image/jobs?action=remove_background`
Seçenek B: `POST /image/remove-bg` (ayrı endpoint)

**4. Worker task güncelle**
`backend/app/tasks/image_tasks.py` dosyasına `remove_background` action'ı için dal ekle.

**5. Dockerfile güncelle**
rembg ilk çalışmada U2Net modelini indirdiğinden build sırasında model önbelleğe alınabilir:
```dockerfile
RUN python -c "from rembg import new_session; new_session('u2net')"
```

### Frontend Adımları
- Image ekranına "Remove Background" butonu/seçeneği ekle
- Seçildiğinde format seçimi gizlenir, direkt PNG çıktı üretilir

---

## Aşama 2: Telegram Bot Servisi

### Teknik Seçimler
- **Bot kütüphanesi:** `aiogram` (async, modern)
- **AI:** OpenAI `gpt-4o-mini` + Function Calling
- **Dosya limiti:** Telegram standart = 20MB indirme / 50MB yükleme. Büyük dosyalar için VDS'de Local Telegram Bot API kurulabilir (limit: 2GB)

### Yeni Docker Servisi: `bot`
`docker-compose.yml` dosyasına yeni servis:
```yaml
bot:
  build:
    context: .
    dockerfile: bot/Dockerfile
  environment:
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - API_BASE_URL=http://api:8000
  depends_on:
    - api
  restart: unless-stopped
```

### Klasör Yapısı
```
bot/
├── Dockerfile
├── requirements.txt
├── main.py           # Bot başlangıç noktası
├── handlers/
│   ├── photo.py      # Fotoğraf mesajları
│   ├── video.py      # Video mesajları
│   ├── audio.py      # Ses mesajları
│   └── document.py   # Belge mesajları
├── ai/
│   └── intent.py     # GPT-4o-mini Function Calling - niyet çıkarımı
└── api/
    └── client.py     # FastAPI backend'e istek atan HTTP client
```

### AI Function Calling Araçları (Tanımlanacak)
```json
[
  {"name": "convert_video", "parameters": {"target_format", "trim_enabled", "trim_start", "trim_end", "fps", "width", "height"}},
  {"name": "convert_image", "parameters": {"target_format", "quality", "action"}},
  {"name": "convert_audio", "parameters": {"target_format", "bitrate"}},
  {"name": "convert_document", "parameters": {"target_format"}},
  {"name": "remove_background", "parameters": {}}
]
```

### Örnek Kullanıcı Akışı
```
Kullanıcı → [video dosyası gönderir]
Bot → "Dosyanı aldım! Ne yapmamı istersin?"
Kullanıcı → "ilk 5 saniyesini kes, mp4 olarak ver"
Bot → GPT-4o-mini'ye gönderir → {trim_enabled: true, trim_start: "0", trim_end: "5", target_format: "MP4"}
Bot → POST /video/jobs ile API'ye gönderir
Bot → "İşleniyor... ⏳"
Bot → İşlem bitince videoyu Telegram'dan gönderir ✅
```

---

## Gerekli Ortam Değişkenleri (Aşama 2)

```env
TELEGRAM_BOT_TOKEN=your_token_here   # BotFather'dan alınır
OPENAI_API_KEY=your_key_here         # platform.openai.com
```

---

## Öncelik Sırası

1. ✅ SSL / Mixed Content hataları çözüldü (Tamamlandı)
2. ✅ Document convert LibreOffice profil hatası düzeltildi (Tamamlandı)
3. ⏳ **rembg background remover - backend + frontend entegrasyonu** (Sonraki)
4. ⏳ Telegram Bot servisi oluşturma (aiogram)
5. ⏳ AI intent parsing katmanı (GPT-4o-mini Function Calling)
6. ⏳ Local Telegram Bot API kurulumu (büyük dosya desteği için, opsiyonel)
