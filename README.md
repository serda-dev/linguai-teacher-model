# LinguAI Teacher GPU Service

Vast.ai GPU sunucusunda Qwen3-30B-A3B çalıştırır; mevcut LinguAI VPS projesine
OpenAI uyumlu, doğrulanan kalite etiketi API’si sunar. Varsayılan: **resmî Qwen
Q8_0 GGUF + kaynaktan derlenen llama.cpp**. vLLM veya Ollama kurulumu gerekmez.

**Durum:** uygulama ve CPU/mock testleri hazır. Docker/CUDA build, gerçek GPU’da
model yükleme, VPS bağlantısı, hız ve A–H kalite kalibrasyonu henüz doğrulanmadı.
Bu repo bir image tarifi içerir; registry’ye yayınlanmış image varmış gibi
varsaymayın. İlk dağıtımdan önce aşağıdaki build/publish adımı gerekir.

## Seçilen profil

- Model: `Qwen/Qwen3-30B-A3B-GGUF`, orijinal Qwen3; Instruct-2507 veya Qwen3.5 değil.
- Q8_0 dosyası yaklaşık 32.5 GB. Revision ve SHA-256: [profil](profiles/qwen3-30b-a3b-q8.json).
- llama.cpp v0.5.0, sabit source commit; CUDA 12.8.1, Ampere/Ada/Hopper build hedefleri.
- 8192 bağlam tokenı, en çok 1024 çıktı tokenı, 32 güvenlik tokenı, tek üretim.
- Thinking template ayarıyla kapalı. Yetkili teacher prompt’u birebir korunur.
- Tam mesaj şablonu gerçek tokenizer ile sayılır; sığmayan istek kesilmeden reddedilir.
- 48 GB VRAM hedefidir; kullanılabilir VRAM/driver ve gerçek yükleme ölçülmelidir.

## Image oluşturma ve yayınlama

Docker Buildx bulunan Linux/amd64 geliştirme veya build makinesinde:

```bash
git clone https://github.com/serda-dev/linguai-teacher-model.git
cd linguai-teacher-model
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
# Registry hesabınıza docker login ile giriş yaptıktan sonra:
export TEACHER_REGISTRY_IMAGE=ghcr.io/serda-dev/linguai-teacher-model
bash scripts/publish.sh
```

Script commit SHA etiketiyle image yayınlar ve `image@sha256:...` adresini yazdırır.
Vast’a **bu digest adresini** girin. Private GHCR paketleri için Vast registry
kimlik bilgileri gerekir; repo/paket görünürlüğünü script değiştirmez. Build sırasında
CUDA kaynak derlemesi zaman alır; GPU gerekmez, yeterli CPU/RAM/disk gerekir.
GitHub Actions veya ücretli runner otomatik tetiklenmez.

## Vast.ai başlangıcı

1. Desteklenen NVIDIA GPU/driver, en az 48 GB **kullanılabilir VRAM hedefi**, tercihen
   64 GB host RAM ve image/model/cache için en az 60 GB boş disk planlayın.
2. Image alanına yayınlanan digest’i yazın. **Entrypoint mode** kullanın; image’ın
   başlangıç komutu download → checksum → model load → API adımlarını yürütür.
3. `TEACHER_API_KEY` olarak en az 32 karakterlik rastgele bir değer verin. VPS’de de
   aynı değer kullanılır. Model otomatik indirilir; `/workspace/models` kalıcı cache’idir.
4. API container içinde **8000** portundadır. Vast’ın atadığı dış portu panelden alın;
   dış portun 8000 olduğunu varsaymayın. **8081’i açmayın.**
5. TLS sertifikası + anahtarı mount edip `TEACHER_TLS_CERT` / `TEACHER_TLS_KEY` verin
   veya SSH tüneli kullanın. Jupyter adresi API adresi değildir.

SSH/Jupyter mode image ENTRYPOINT’ini değiştirebilir. Bu modu seçerseniz
[runbook](docs/deployment/vast.md) içindeki açık başlatma komutunu kullanın.
İlk model indirmesi sürerken API henüz cevap vermeyebilir; `phase=serving` beklenir.

## VPS tarafı

Mevcut projede yalnız bağlantı/profil ayarları:

```dotenv
TEACHER_BASE_URL=https://gpu-api.example.com:EXTERNAL_PORT/v1
TEACHER_API_KEY=SAME_RANDOM_KEY_AS_GPU
TEACHER_MODEL=Qwen/Qwen3-30B-A3B-GGUF
TEACHER_PROFILE=qwen3-30b-a3b-q8-llamacpp-v1
```

VPS üzerinde bu repodaki bağımlılıklarla, aynı environment altında:

```bash
python scripts/check_connection.py
```

Bu kontrol **etiket üretmez**. Onaylı tek bir request dosyasıyla gerçek testi ayrıca
`python scripts/check_connection.py --request /secure/approved-request.json`
çalıştırır; dosya exact system/user mesajlarını içermeli. Yanıt/anahtar/metin loglanmaz.

Mevcut VPS client timeout’u 20 saniye; servis bütçesi 18 saniyedir. Gerçek p95 bu
sınırı aşarsa yalnız `.env` değişikliği yeterli değildir: client timeout’u, 60 saniyelik
lease ve 30 saniyelik heartbeat birlikte ele alınmalıdır. Küçük kalibrasyon geçmeden
büyük corpus işi başlatmayın.

## API ve geliştirme

| Yol | Davranış |
| --- | --- |
| `GET /health` | Anonim liveness; inference yok |
| `GET /ready` | Bearer auth; backend + profil kontrolü; inference yok |
| `GET /v1/models` | Bearer auth; tek model |
| `POST /v1/chat/completions` | Exact iki mesaj; `temperature: 0`; schema + ID doğrulaması |

Hatalar: 400 yanlış sözleşme/token bütçesi, 401 auth, 413 boyut, 429 meşgul,
502 geçersiz/eksik model yanıtı, 503 model hazır değil, 504 timeout.
Başarılı label yalnız `choices[0].message.content` JSON string’idir. GPU tarafında
veritabanı, corpus kaynağı, routing, repair veya kalıcı etiket deposu bulunmaz.

Yerel NVIDIA Docker testi için `.env.example` → `.env`, anahtar ayarı ve
`docker compose up --build -d`. Port yalnız host loopback’te yayınlanır.

Agent akışı: [AGENTS.md](AGENTS.md) → [requirements](docs/requirements/runtime-v1.md)
→ [ADR](docs/architecture/decisions/0002-qwen-llamacpp.md)
→ [tests](docs/tests/test-plan.md) → [audit](docs/audit/2026-09-28-runtime.md).
