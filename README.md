# 🎨 Bambam Converter Suite

A powerful, all-in-one media conversion tool with a beautiful dark-themed interface. Convert images, videos, audio files, and documents with ease!

## 🌐 Web App Migration Status

This repository now includes an in-progress self-hosted web application stack alongside the original desktop implementation.

### Current Web Features

- Dockerized local deployment with `[docker-compose.yml](docker-compose.yml)`
- Next.js frontend under `[frontend/](frontend)`
- FastAPI backend under `[backend/](backend)`
- Redis/RQ background job execution
- Web-based image conversion with quality slider (JPG/JPEG/WEBP only)
- Web-based sound conversion with inline waveform trim editor
- Web-based video conversion
- Single-file trim UI for both audio and video — dual-handle range selection with manual start/end inputs
- Audio trim inputs displayed in `MM:SS.s` format for precision
- Web-based document conversion through LibreOffice headless
- Job dashboard/history view
- Job dashboard now shows newly queued jobs immediately after upload starts
- Job dashboard table includes per-job download action on the right
- Manual cleanup endpoint for finished and stale jobs
- Admin panel file manager for `outputs`/`uploads` (list, view, delete, owner tracking)
- Admin storage tools: one-click `Delete All` for disk cleanup and default-collapsed `Stored Files` section
- Navbar-based fast tool switching in `[frontend/app/page.tsx](frontend/app/page.tsx)`
- Tab state persistence when switching tabs (conversion forms do not reset)
- Landing screen with centered logo, suite title, and live status cards
- Batch and zip export support for image, audio, video, and document jobs
- Conversion progress loader shown on all converter tabs during active jobs
- Per-file upload progress bars with cascade fill effect during upload phase
- Collapsible upload progress panel when more than 5 files are selected
- All file pickers filtered to supported formats only (no stray file types)
- Downloaded output files named `{originalname}_converted.{ext}`

### Current Web Limitations

- Advanced desktop-only options such as crop parity and some power-user settings are not yet fully ported
- Authentication is still intentionally lightweight for local/self-hosted usage
- Production deployment beyond local or trusted-network use still needs additional security review

### Web Support Matrix

| Module | Single File | Batch | Zip Export | Notes |
|---|---|---|---|---|
| Image | Yes | Yes | Yes | Quality slider active for JPG/JPEG/WEBP only |
| Sound | Yes | Yes | Yes | Bitrate control + waveform trim (MM:SS.s inputs) |
| Video | Yes | Yes | Yes | Format/FPS/crop + single-file trim workflow |
| Document | Yes | Yes | Yes | LibreOffice headless only |
| Batch Rename | No | No | No | Not yet ported to web |

### Web UI Snapshot

- Landing: centered Bambam logo (`@/bambam_logo.png`) + suite title + version label + quick tool buttons
- Top navbar switches screens instantly between Home, Image, Sound, Video, Document, Batch Rename, and Jobs
- Sound screen: inline waveform editor with canvas visualization, draggable cyan trim handles, `MM:SS.s` manual inputs, and Enable Trim checkbox
- Video screen: trim area with video preview, dual-handle range slider, manual start/end inputs, and draggable free-position crop overlay handles — selected region is cropped (not scaled) in output
- Admin panel: active users + stored files manager with authenticated view/delete actions
- All converter screens show an animated spinner with live job status during conversion

## 🚀 Web App Deployment (Coolify / Docker VDS)

To deploy this suite on a VPS (like Ubuntu with Coolify or raw Docker), follow these steps:

### 1. Environment Variables
In your deployment panel (Coolify, Portainer, etc.), you **must** set these environment variables:

**Backend Settings:**
```env
APP_NAME=Bambam Converter Suite Web
APP_ENV=production
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://redis:6379/0

# IMPORTANT: Replace with your VDS IP or Domain
CORS_ORIGINS=["https://bambam.zaferakkan.com"]

# File Limits
MAX_UPLOAD_SIZE_MB=250
QUEUE_DEFAULT_TIMEOUT=30m
QUEUE_VIDEO_TIMEOUT=120m
QUEUE_DOCUMENT_TIMEOUT=60m
```

**Frontend Settings:**
```env
# IMPORTANT: Replace with your VDS IP or Domain (Port 8000 is for API)
NEXT_PUBLIC_API_BASE_URL=https://api-bambam.zaferakkan.com
```

**Port Mapping:**
If you need to change public ports, use these (Default: 8000 for API, 3000 for Frontend):
```env
API_PUBLIC_PORT=8000
FRONTEND_PUBLIC_PORT=3000
```

### 2. Deployment Steps
1.  **Clone/Import** the repository to Coolify.
2.  **Configure Environment Variables** as shown above.
3.  **Deploy**. Coolify will use the `docker-compose.yml` automatically.

### 3. Traefik Upload Limits & Timeout (Coolify Only)
If you are deploying via Coolify and experience `502 Bad Gateway` or `413 Payload Too Large` during video uploads, you **must** configure the Traefik proxy timeouts.

In Coolify:
1. Go to your Application -> **Proxy** (or Advanced/Traefik settings)
2. Add the following **Custom Traefik Labels**:
```ini
traefik.http.middlewares.bambam-api-bodysize.buffering.maxRequestBodyBytes=268435456
traefik.http.middlewares.bambam-api-bodysize.buffering.memRequestBodyBytes=33554432
traefik.http.serversTransports.bambam-api-transport.forwardingTimeouts.responseHeaderTimeout=600s
traefik.http.serversTransports.bambam-api-transport.forwardingTimeouts.idleConnTimeout=600s
traefik.http.serversTransports.bambam-api-transport.forwardingTimeouts.dialTimeout=60s
traefik.http.services.bambam-api.loadbalancer.serversTransport=bambam-api-transport
```
*(These labels increase the proxy upload limit to 256MB and the timeout to 10 minutes).*

### ⚠️ Troubleshooting: Port Already Allocated
If you see `Bind for 0.0.0.0:8000 failed: port is already allocated`:
1.  Check if another service is using port 8000: `lsof -i :8000`
2.  Or change `API_PUBLIC_PORT` to `8001` in your environment variables and update `NEXT_PUBLIC_API_BASE_URL` accordingly.

## 🚀 Web App Quick Start (Local)

```bash
docker compose up --build
```

### ⚡ Fast Development Loop (No Full Redeploy on Every Change)

Use the dev override file for hot-reload behavior in frontend and backend:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

After initial build, run without rebuild for normal code-only edits:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Notes:

- `api` runs with Uvicorn reload in dev override
- `frontend` uses bind mount + polling-friendly watcher env vars for Docker Desktop on Windows
- full rebuild is typically only needed after dependency changes (`requirements.txt`, `package.json`)

Docker self-host note:

- `api` and `worker` images include FFmpeg + FFprobe + LibreOffice during image build
- host machine does **not** need separate FFmpeg/FFprobe installation for web app usage

Default local endpoints:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Redis: `localhost:6379`

### Web Stack Services

- `frontend`: Next.js UI
- `api`: FastAPI routes and upload handling
- `worker`: background conversion worker
- `redis`: queue backend

### Web Environment Notes

Important backend environment options are listed in `[backend/.env.example](backend/.env.example)`:

- `MAX_UPLOAD_SIZE_MB`
- `QUEUE_DEFAULT_TIMEOUT`
- `QUEUE_VIDEO_TIMEOUT`
- `QUEUE_DOCUMENT_TIMEOUT`

These help control upload limits and long-running worker behavior for self-hosted installations.

### Web Data Directories

- `data/uploads`
- `data/outputs`
- `data/db`
- `data/temp`

### Storage and Maintenance Guidance

- `data/uploads` can grow quickly if cleanup is not run periodically
- `data/outputs` and generated zip bundles can consume significant space for video and document jobs
- `data/db` should be included in backups because it stores job state and history
- periodic cleanup through `POST /admin/cleanup` is recommended for self-hosted setups

### Current Web API Overview

- `POST /image/jobs`
- `POST /audio/jobs`
- `POST /video/jobs`
  - supports optional trim query params: `trim_enabled`, `trim_start`, `trim_end` (single-file flow)
- `POST /document/jobs`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /admin/cleanup`
- `POST /auth/logout`
- `GET /admin/files`
- `GET /admin/files/view`
- `DELETE /admin/files`
- `DELETE /admin/files/all`

The desktop app remains in the repository, but ongoing migration work is focused on the self-hosted web app.

## 🤖 Telegram Bot

A Telegram bot service (`[bot/](bot/)`) provides an alternative interface to the Bambam backend via Telegram messaging. Bot configuration is managed entirely through the **Admin Panel** — no environment files needed.

### 🎯 Phase 1: Auto-Detection & Instant Conversion (Live ✅)

**Features:**
- ✅ Auto-detects file type from MIME type and file extension (image/audio/video/document)
- ✅ Shows inline keyboard with available conversion options per file type
- ✅ Polls backend job queue and returns converted file when done
- ✅ Single-worker compatible, deterministic (no AI)
- ✅ Bot configuration via frontend **Admin Panel** (no .env files)
- ✅ JWT authentication against FastAPI backend (auto-renew on token expiry)

**Supported Conversions:**
| Type | Input Formats | Output Formats |
|------|---------------|----------------|
| 🖼 Image | PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF | PNG, JPG, WEBP |
| 🎵 Audio | MP3, WAV, FLAC, OGG, M4A, AAC | MP3, WAV |
| 🎬 Video | MP4, MOV, MKV, AVI, WEBM, GIF | MP4 |
| 📄 Document | PDF, DOCX, DOC, TXT, RTF, ODT | PDF |

### 🚀 Quick Start (3 Steps)

**Step 1: Create Telegram Bot**
- Go to [@BotFather](https://t.me/BotFather)
- Send `/newbot` → follow prompts → copy your **bot token**

**Step 2: Configure via Admin Panel**
- Open web app: `http://localhost:3000`
- Login with admin credentials
- Click **"👥 Admin Panel"** (top right)
- Open **"🤖 Bot Settings"**
- Paste token → check "Bot Enabled" → **Save**

**Step 3: Test**
- Find your bot on Telegram and send `/start`
- Send any image, video, audio, or document
- Select conversion option from buttons
- ⏳ Wait for processing → 🎉 Get result back

**That's it!** No Docker restarts, no `.env` editing. Bot reads config from database at startup.

### 🔧 How It Works

```
User: sends file to bot
  ↓
Bot: detects type (image/audio/video/document)
  ↓
Bot: shows inline keyboard with options
  ↓
User: clicks button (e.g., "Convert to MP3")
  ↓
Bot: authenticates to backend (admin account)
  ↓
Bot: uploads file → creates job → polls for completion
  ↓
Backend: FFmpeg/LibreOffice processes file
  ↓
Job complete: Bot downloads → sends to user
  ↓
User: gets converted file ✅
```

**Architecture:**
- `[bot/handlers/](bot/handlers/)` — `/start`, `/help` commands + file/callback handlers
- `[bot/services/](bot/services/)` — File type detection, keyboard builder, session store (in-memory)
- `[bot/api/client.py](bot/api/client.py)` — Backend communication (login, job creation, polling, file download)

### 🔐 Security & Credentials

**Admin Panel Configuration:**
- Token stored in SQLite database (encrypted at rest optional)
- Only visible/editable by admin users
- Token is **masked** in UI (shows `12345678****`)

**Backend Authentication:**
- Bot logs in as admin (or custom user) via JWT
- Auto-renews token on expiry
- All API calls use Bearer token

**Best Practices:**
1. **Local/Self-hosted:** Current setup is fine (admin credentials default)
2. **Production:**
   - Create dedicated bot user (non-admin) via admin panel
   - Use strong password
   - Rotate default admin credentials
   - Enable HTTPS / reverse proxy with SSL

### 📊 Admin Panel Integration

The bot is now fully managed via **Admin Panel** under **"🤖 Bot Settings"** section:

| Setting | Type | Notes |
|---------|------|-------|
| Telegram Bot Token | Password Input | Leave empty to keep current. Required to enable bot. |
| Bot Enabled | Toggle | Turn bot on/off without restarting services |
| Status Indicators | Display | Shows if token is set + if bot is enabled |

Changes take effect after bot container restart (automatic on deploy).

### 🐛 Troubleshooting

**Bot doesn't respond:**
- Confirm token is saved in Admin Panel
- Check bot is **enabled** (toggle ON)
- Verify backend is running: `docker logs bambam-api`
- View bot logs: `docker logs bambam-bot`

**"Failed ❌" when converting:**
- Check backend worker: `docker logs bambam-worker`
- File might be unsupported format
- Worker queue might be stuck (check Redis: `docker logs bambam-redis`)

**Bot takes too long:**
- Default timeout: 10 minutes per job
- Large videos/documents naturally take longer
- FFmpeg + LibreOffice process time depends on file size

### 🔮 Future Phases (Roadmap)

**Phase 2: Parameter Customization**
- Interactive parameter selection: bitrate, trim, resize, quality
- Inline forms via keyboard buttons

**Phase 3: Natural Language Intent Parsing** (Optional)
- Accept voice/text commands: *"convert to MP3 at 320kbps"*
- GPT-based intent parsing with function calling
- Context-aware conversation flow

**Phase 4: Advanced Features**
- Background removal (rembg integration)
- Batch file processing
- Per-user conversion history
- Usage analytics & quotas

## 🧪 Testing

Current backend smoke and test assets:

- `[backend/tests/test_health.py](backend/tests/test_health.py)`
- `[backend/tests/test_routes.py](backend/tests/test_routes.py)`
- `[backend/tests/test_services.py](backend/tests/test_services.py)`
- `[scripts/smoke-test.ps1](scripts/smoke-test.ps1)`
- `[scripts/queue-smoke-test.ps1](scripts/queue-smoke-test.ps1)`

Suggested local verification flow:

```bash
docker compose up --build
pytest backend/tests
powershell -ExecutionPolicy Bypass -File scripts/smoke-test.ps1
powershell -ExecutionPolicy Bypass -File scripts/queue-smoke-test.ps1
```

Frontend rebuild note after UI code changes:

```bash
docker compose up -d --build frontend
```

Local IDE/type-check note for frontend development:

```bash
cd frontend
npm install
npx tsc --noEmit
```

## 📦 Release Readiness Notes

Operational and maintenance documentation for the self-hosted web app is available in:

- `[plans/operations-checklist.md](plans/operations-checklist.md)`
- `[plans/backup-restore.md](plans/backup-restore.md)`
- `[plans/web-app-master-roadmap.md](plans/web-app-master-roadmap.md)`
- `[plans/coolify-vds-deployment.md](plans/coolify-vds-deployment.md)` (Coolify + Ubuntu VDS, IP-first deployment)

![Version](https://img.shields.io/badge/version-1.3.7-blue)
![Python](https://img.shields.io/badge/python-3.13-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### 🖼️ Image Converter
- **Supported Formats**: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP, ICO, SVG
- **Batch Processing**: Convert multiple images at once
- **Quality Control**: Adjust output quality (1-100)
- **Resize Options**: Width, height, and percentage-based scaling
- **Output Modes**: 
  - Custom output folder
  - Mirror source folder structure
  - Delete originals after conversion

### 🎬 Video Converter
- **Supported Formats**: MP4, AVI, MKV, MOV, WMV, FLV, WEBM, GIF
- **Advanced Features**:
  - Resolution control (width, height, FPS)
  - Video trimming with timeline preview
  - Crop tool with visual preview
  - GIF conversion with custom settings
  - Quality presets (ultrafast to veryslow)
- **Codec Support**: H.264, H.265, VP9, and more
- **Folder Scanning**: Recursively scan folders for videos

### 🎵 Sound Converter
- **Supported Formats**: MP3, WAV, OGG, FLAC, AAC, M4A, WMA
- **Audio Settings**:
  - Bitrate control (64-320 kbps)
  - Sample rate adjustment
  - Channel configuration (mono/stereo)
- **Batch Processing**: Convert entire music libraries
- **Folder Support**: Recursive folder scanning

### 📄 Document Converter
- **Supported Formats**: PDF, DOCX, DOC, TXT, RTF, ODT
- **Conversion Engines**:
  - LibreOffice (recommended)
  - Microsoft Word (if installed)
- **Features**:
  - Batch document conversion
  - Folder scanning support
  - Mirror mode for organized output

### 🔄 Bambam Batch Rename
- **Powerful Renaming**: Rename multiple files with custom patterns
- **Preview**: See changes before applying
- **Flexible Options**: Support for various file types

## 🚀 Installation

### Option 1: Pre-built Executable (Recommended)

**Download the latest release from [GitHub Releases](https://github.com/Zaferius/BambamCovertSuite/releases)**

✅ **No installation required!**
✅ **All dependencies bundled** (FFmpeg, FFprobe included)
✅ **Single executable file**

Simply download `BambamConverter.exe` and run it!

### Option 2: Run from Source

#### Prerequisites
- **Python 3.13** or higher
- **FFmpeg & FFprobe** (download from [ffmpeg.org](https://ffmpeg.org/download.html))
- **LibreOffice** (optional, for document conversion)

> This prerequisite list is for desktop/source execution path.
> For Dockerized web self-host, conversion dependencies are bundled inside the backend images.

#### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/Zaferius/BambamCovertSuite.git
cd BambamCovertSuite
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Place FFmpeg binaries**
- Download FFmpeg and FFprobe
- Place `ffmpeg.exe` and `ffprobe.exe` in the project root folder

4. **Run the application**
```bash
python bambam_converter_suite.py
```

## 📦 Building from Source

### Create Standalone Executable

```bash
# Make sure ffmpeg.exe and ffprobe.exe are in the project folder
pyinstaller BambamConverter.spec
```

The executable will be created in the `dist/` folder with all dependencies bundled.

## 🎯 Usage

### Quick Start

1. **Launch the application**
2. **Select a tab** (Image, Video, Sound, Document, or Batch Rename)
3. **Add files** by:
   - Clicking "Select Files" or "Add Folder"
   - Dragging and dropping files/folders
4. **Configure settings** (format, quality, resolution, etc.)
5. **Choose output location**:
   - Select a custom folder
   - Use mirror mode to maintain folder structure
6. **Click Start** to begin conversion

### Output Modes

- **Custom Folder**: All converted files go to selected folder
- **Mirror Mode**: Maintains source folder structure in output location
- **Delete Originals**: Automatically removes source files after successful conversion

### Language Support

- 🇬🇧 English
- 🇹🇷 Turkish

Change language from the home screen dropdown menu.

## 🔧 Configuration

### Settings Tab

- **Auto-open Output**: Automatically open output folder after conversion
- **Update Checker**: Check for new versions from GitHub
- **Language Selection**: Switch between supported languages

## 📋 Requirements

### For Pre-built Executable
✅ **Nothing!** All dependencies are bundled in the .exe file.

### For Running from Source

#### Python Packages
```
Pillow>=10.0.0
opencv-python>=4.8.0
numpy>=1.24.0
tkinterdnd2>=0.3.0
pywin32>=306
packaging>=23.0
requests>=2.31.0
```

#### External Tools
- **FFmpeg**: Required for video and audio conversion (bundled in .exe)
- **FFprobe**: Required for video analysis (bundled in .exe)
- **LibreOffice**: Optional, for document conversion (not bundled)

## 🛠️ Development

### Project Structure
```
BambamImageConvert/
├── bambam_converter_suite.py  # Main application
├── image_tab.py               # Image conversion module
├── video_tab.py               # Video conversion module
├── sound_tab.py               # Audio conversion module
├── document_tab.py            # Document conversion module
├── batch_rename_tab.py        # Batch rename module
├── settings_tab.py            # Settings and preferences
├── landing_tab.py             # Home screen
├── localization.py            # Multi-language support
├── update_checker.py          # GitHub update checker
├── BambamConverter.spec       # PyInstaller configuration
├── ffmpeg.exe                 # FFmpeg binary (bundled)
├── ffprobe.exe                # FFprobe binary (bundled)
├── bambam_logo.ico            # Application icon
└── bambam_logo.png            # Logo image
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Known Issues

- Document conversion requires LibreOffice or Microsoft Word (not bundled)
- Some video codecs may require additional FFmpeg builds
- Large video files may take significant time to process

## 📝 Changelog

### Version 1.3.7 (Latest)
- ✨ Telegram bot service added (`bot/`) — send files to the bot for conversion via inline keyboard
- ✨ Bot auto-detects file type (image/audio/video/document) from MIME type and extension  
- ✨ Bot configuration moved to **Admin Panel** — no `.env` files needed (token + enabled toggle)
- ✨ `BotSettings` database table stores token + enabled flag (singleton row)
- ✨ Backend `/admin/bot-settings` + `/admin/bot-settings/token` endpoints (admin-only)
- ✨ Frontend Admin Panel new "🤖 Bot Settings" section with token input + enable/disable toggle
- ✨ Bot reads config from database at startup (env var fallback for retrograde compat)
- ✨ Phase 1: deterministic, AI-less flow; supports PNG/JPG/WEBP, MP3/WAV, MP4, PDF
- 🐛 Fixed bot Dockerfile COPY path and module imports (`bot/` subdirectory structure)
- 🐛 Fixed httpx GET request parameter handling (files param only on POST)

### Version 1.3.6
- ✨ Video crop overlay now performs a true FFmpeg crop instead of scaling — the dragged region is cropped out of the original frame
- ✨ Crop overlay label now shows both dimensions and pixel offset (e.g. `960 × 540px @ 480,270`)
- 🐛 Removed standalone width/height inputs that were misleading without positional context; crop area is set exclusively via the visual overlay handles
- ✨ Backend `crop_x` / `crop_y` query parameters added to `/video/jobs` for precise crop offset control

### Version 1.3.5
- ✨ Video resize now automatically normalizes odd dimensions (e.g., 471x323) to even numbers to ensure codec compatibility
- 🐛 Fixed FFmpeg "reset_sar" option error by switching to standardized "setsar=1" filter for better version compatibility
- ✨ Jobs dashboard now shows newly queued jobs immediately during upload flow
- ✨ Jobs table now includes a right-side per-job `Download` action
- ✨ Admin storage section now supports one-click `Delete All` for `uploads` + `outputs`
- ✨ Admin `Stored Files` area is now collapsible and closed by default to save panel space
- ✨ Video resize editor upgraded with draggable edge/corner handles directly on preview
- ✨ Admin online users panel now refreshes immediately on user logout
- ✨ Admin file manager added (list/view/delete on `outputs` and `uploads` + owner username display)
- 🐛 Fixed protected file view in admin panel by switching to authenticated fetch-based preview
- 🐛 Fixed tab-switch reset issue by keeping converter components mounted across navigation
- 🐛 Improved video resize interaction: video pauses, controls hide, and all handles drag in correct direction

### Version 1.3.4
- ✨ Implemented secure JWT-based authentication system for the web app
- ✨ First registered user is automatically granted admin privileges on fresh database
- ✨ Frontend registration disabled for public; admin-only user creation supported
- 🐛 Fixed SQLAlchemy circular import issues preventing backend startup
- 🐛 Resolved Coolify Traefik 503 deployment errors caused by undefined transport labels
- 🐛 Fixed `passlib` and `bcrypt` version incompatibility causing worker and API crashes

### Version 1.3.3
- ✨ Per-file upload progress bars on all converter tabs — files cascade-fill left to right as upload progresses
- ✨ Collapsible upload progress panel for batches larger than 5 files — shows overall % and expand/collapse toggle
- ✨ Upload phase and job processing phase are visually separated: progress bars during upload, spinner during queue/processing

### Version 1.3.2
- ✨ Added waveform trim editor to Sound tab — canvas-based waveform visualization using Web Audio API, draggable cyan handles, dark region masks, and `Enable Trim` checkbox
- ✨ Audio trim backend support added (`trim_enabled`, `trim_start`, `trim_end`) mirroring video trim implementation
- ✨ Manual trim time inputs in Sound tab now use `MM:SS.s` format (e.g. `02:15.0`) instead of raw seconds
- ✨ Conversion progress loader added to all converter tabs — animated spinner with live job status (`queued`, `processing`) that resolves on completion
- ✨ Image converter Quality slider now only appears when target format supports it (JPG, JPEG, WEBP); hidden for PNG, TIFF, BMP, GIF
- ✨ All file pickers now restrict selection to supported formats per tab (no stray file types in dialog)
- ✨ Downloaded output files renamed to `{originalname}_converted.{ext}` across all converters

### Version 1.3.1
- ✨ Home landing updated to centered hero layout with larger Bambam logo and quick tool buttons
- ✨ Navbar labels simplified (removed `Converter` suffix in top navigation)
- ✨ Added minimal video trim UX in web app with dual-handle range slider + manual start/end fields
- ✨ Added backend video trim query support (`trim_enabled`, `trim_start`, `trim_end`) for single video jobs
- ⚡ Added documented fast dev loop with compose override and hot-reload flow

### Version 1.3.0
- ✨ Reworked web frontend into a navbar-driven experience
- ✨ Added centered landing screen with Bambam branding and version label
- ✨ Replaced static roadmap text with live API and job status cards
- ✨ Improved batch conversion UX by fixing batch status/download endpoint wiring
- 🐛 Updated worker startup command in `[docker-compose.yml](docker-compose.yml)` to `python -m app.worker`

### Version 1.2.9
- ✨ Improved Settings UI layout
- ✨ Update checker status now appears next to button
- ✨ Fixed version display across all tabs
- ✨ Added custom icons to all popup windows
- ✨ Improved taskbar icon handling
- ✨ Added ffprobe.exe bundling support
- 🐛 Fixed .gitignore to exclude build artifacts
- 🐛 Cleaned up repository structure

### Version 1.2.8
- ✨ Added GitHub update checker
- ✨ Implemented folder scanning for video and document tabs
- ✨ Added mirror mode for all conversion tabs
- ✨ Improved output location UI
- 🐛 Various bug fixes and improvements

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Zaferius**
- GitHub: [@Zaferius](https://github.com/Zaferius)
- Repository: [BambamCovertSuite](https://github.com/Zaferius/BambamCovertSuite)

## 🙏 Acknowledgments

- FFmpeg team for the amazing media processing library
- Pillow contributors for image processing capabilities
- LibreOffice team for document conversion support
- All open-source contributors who made this project possible

## 💬 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/Zaferius/BambamCovertSuite/issues) page
2. Create a new issue with detailed information
3. Star ⭐ the repository if you find it useful!

---

Made by Zaferius
