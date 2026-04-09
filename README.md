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
- **Unified Settings Panel** (⚙️ button, left-sliding sidebar):
  - Admin users see: Account info, Active Users monitor, **Workers monitor + scaling**, File Storage manager (all files), System & Personal Bot Settings
  - Admin Users sub-panel now offers an **Admin-only Users** view with real-time active users, a member creation form, and full registered user listing + delete controls
  - Admin users now also get a **Workers** monitor: live worker list (online/offline, idle/busy, current job), queue size, API/Redis health, and admin scale control
  - Workers scale input now preserves typed value during auto-refresh
  - Workers health color mapping normalized so `healthy` always renders green
  - Workers scaling semantics are exact-count based (set final total, not additive)
  - Workers target count now reconciles against actual running compose worker replicas so `1 → 3` results in a final total of `3`, not `4`
  - Worker list includes quick `×` control to decrement desired total by 1
  - Worker quick-remove (`×`) control can now decrement reliably down to the minimum worker count
  - Regular users see: Account info, Personal Storage (own jobs only), Personal Bot Settings
  - File Storage: admins can view/delete all files with owner tracking; users can download their completed jobs
  - One-click Delete All button for admins to cleanup disk space
- **Video crop overlay**: Drag handles to resize, or drag the box interior to reposition — full mouse & touch support
- Navbar-based fast tool switching between Home, Image, Sound, Video, Document, Batch Rename, Jobs
- Removed completed-job notification badge indicators (`!`) from landing buttons and navbar tabs
- Tab state persistence when switching tabs (conversion forms do not reset)
- Landing screen with centered logo, suite title, version badge, and balanced 2-column quick tool layout (Jobs now matches other button sizes and sits in the right-column gap under Document Converter)
- Batch and zip export support for image, audio, video, and document jobs
- Conversion progress loader shown on all converter tabs during active jobs
- Per-file upload progress bars with cascade fill effect during upload phase
- Collapsible upload progress panel when more than 5 files are selected
- All file pickers filtered to supported formats only (no stray file types)
- Downloaded output files named `{originalname}_converted.{ext}`
- Mobile-optimized UI: horizontal-scrolling navbar (no button overflow), full touch support for all controls, and improved portrait spacing so settings/logout controls do not overlap navbar tabs
- Fixed settings gear icon (⚙️) accessible on all screens for all users

### Current Web Limitations

- Advanced desktop-only options such as crop parity and some power-user settings are not yet fully ported
- Authentication is still intentionally lightweight for local/self-hosted usage
- Production deployment beyond local or trusted-network use still needs additional security review

### Web Support Matrix

| Module | Single File | Batch | Zip Export | Notes |
|---|---|---|---|---|
| Image | Yes | Yes | Yes | Quality slider active for JPG/JPEG/WEBP only |
| Sound | Yes | Yes | Yes | Bitrate control + waveform trim (MM:SS.s inputs); full touch support |
| Video | Yes | Yes | Yes | Format/FPS/crop + single-file trim workflow; mobile touch support for crop & trim handles |
| Document | Yes | Yes | Yes | LibreOffice headless only |
| Batch Rename | No | No | No | Not yet ported to web |

### Web UI Snapshot

- **Landing Screen**: centered Bambam logo + suite title + `v{version}` badge + tagline + 2-column grid of quick-access tool buttons; Jobs uses the same button size as others and is placed in the right-column slot beneath Document Converter
- **Top Navbar** (all tool screens): horizontally scrollable tabs for Home, Image, Sound, Video, Document, Batch Rename, Jobs — fits portrait mobile without overflow
- Fixed ⚙️ **Settings FAB button** (top-left corner): opens unified settings panel for all users on all screens, with portrait-mobile-safe spacing from navbar and logout controls
- **Unified Settings Panel** (left sidebar, both admin & users):
  - Account section: username, role indicator (👑 for admin), logout button
  - **Admin-only sections**:
    - Users: real-time list of active users with status (idle/processing), 3s refresh
    - Workers: real-time worker telemetry + scale control (exact worker count, health summary, queue pressure)
    - Storage: browse uploads/outputs with owner tracking, view/delete individual files, one-click Delete All
    - Telegram Bot Settings: list of active user bots + system-wide bot config (legacy)
  - **User sections**:
    - Storage: list of user's completed jobs with download button
    - Telegram Bot Settings: personal Telegram bot token + enable/disable toggle
  - Responsive: 320px desktop sidebar, full-width mobile, sub-menu navigation with back button
- **Sound Screen**: inline waveform editor with canvas visualization, draggable cyan trim handles, `MM:SS.s` manual inputs, Enable Trim checkbox — **full touch support on mobile**
- **Video Screen**: 
  - Trim editor: video preview + dual-handle range slider + manual start/end inputs
  - **New**: Crop overlay with 8 resize handles (corners & edges) + grab-cursor center to reposition the box
  - Selected crop region is cropped (not scaled) in output
  - **Full touch support**: all handles + box drag work on mobile
- **Job monitoring**: animated spinner with live job status during conversion on all converter screens

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

# Worker Monitor & Scaling
WORKER_HEARTBEAT_INTERVAL_SECONDS=5
WORKER_OFFLINE_THRESHOLD_SECONDS=15
WORKER_SCALE_ENABLED=true
WORKER_SCALE_COMMAND=docker-compose
WORKER_COMPOSE_FILE=/workspace/docker-compose.yml
WORKER_COMPOSE_PROJECT_DIR=/workspace
WORKER_SCALE_TIMEOUT_SECONDS=120
WORKER_MIN_COUNT=1
WORKER_MAX_COUNT=8
WORKER_TARGET_DEFAULT=1
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
- `WORKER_HEARTBEAT_INTERVAL_SECONDS`
- `WORKER_OFFLINE_THRESHOLD_SECONDS`
- `WORKER_SCALE_ENABLED`
- `WORKER_MIN_COUNT`
- `WORKER_MAX_COUNT`

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

**Conversion Jobs:**
- `POST /image/jobs`
- `POST /audio/jobs`
- `POST /video/jobs` — supports optional trim query params: `trim_enabled`, `trim_start`, `trim_end`
- `POST /document/jobs`
- `GET /jobs`
- `GET /jobs/{job_id}`

**User Bot Settings (Per-User):**
- `GET /auth/user/bot-settings` — get current user's bot configuration
- `PUT /auth/user/bot-settings` — update current user's bot token/enabled status

**Admin Functions:**
- `GET /admin/bot-settings/active` — list all active bots with owner information ✨ NEW
- `GET /admin/bot-settings` — legacy system-wide bot settings (backward compatible)
- `PUT /admin/bot-settings` — update system-wide bot settings
- `GET /admin/files`
- `GET /admin/files/view`
- `DELETE /admin/files`
- `DELETE /admin/files/all`
- `POST /admin/cleanup`
- `GET /admin/workers` — worker list + summary (online/offline, busy/idle, queue, health)
- `POST /admin/workers/scale` — update worker replica target via Docker Compose (admin-only)

**Auth:**
- `POST /auth/login`
- `POST /auth/register` (admin-only)
- `POST /auth/logout`
- `GET /auth/online-users` (admin-only)

The desktop app remains in the repository, but ongoing migration work is focused on the self-hosted web app.

## 🤖 Telegram Bot

A Telegram bot service (`[bot/](bot/)`) provides an alternative interface to the Bambam backend via Telegram messaging. Each user can manage their own bot token through the **Bot Settings** tab, and admins can see all active bots in the **Admin Panel**. No environment files needed.

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
| 🖼 Image | PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF, ICO | PNG, JPG, WEBP, TIFF, BMP, GIF, ICO |
| 🎵 Audio | MP3, WAV, FLAC, OGG, M4A, AAC, WMA, OPUS, AIFF | MP3, WAV, FLAC, OGG, M4A, AAC, WMA, OPUS, AIFF |
| 🎬 Video | MP4, MOV, MKV, AVI, WEBM, GIF, WMV, FLV | MP4, MOV, MKV, AVI, WEBM, GIF, WMV, FLV |
| 📄 Document | PDF, DOCX, DOC, TXT, RTF, ODT | PDF |

### 🚀 Quick Start (3 Steps)

**Step 1: Create Telegram Bot**
- Go to [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot` → follow prompts → copy your **bot token**

**Step 2: Configure via Bot Settings (User)**
- Open web app: `http://localhost:3000`
- Login with your account
- Click **"Bot Settings"** in the top navbar
- Paste your bot token in the input field
- Check **"Enable my Telegram bot"** checkbox
- Click **"Save Bot Settings"** → ✓ Done!

**Step 3: Test**
- Find your bot on Telegram and send `/start`
- Send any image, video, audio, or document
- Select conversion option from buttons
- ⏳ Wait for processing → 🎉 Get result back

**That's it!** No Docker restarts, no `.env` editing. Bot reads config from database at startup.

**Note for Admins:**
- Go to **Admin Panel** (👥 button in navbar) to see:
  - 🤖 **Active Bots** — shows all enabled bots with owner usernames
  - 🤖 **Bot Settings (Legacy)** — system-wide bot configuration (backward compatible)

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

**Bot Token Storage:**
- Tokens stored in SQLite database per-user
- Token is **masked** in UI (shows `12345678****`)
- Only the token owner and admins can see their configuration status

**Backend Authentication:**
- Each bot authenticates with its owner's credentials via JWT
- Auto-renews token on expiry
- All API calls use Bearer token
- Bot operates under the user's privilege level

**Best Practices:**
1. **Local/Self-hosted:** Current setup is fine (default admin credentials acceptable)
2. **Production:**
   - Use strong passwords for all user accounts
   - Rotate default admin credentials immediately
   - Enable HTTPS / reverse proxy with SSL
   - Consider encrypted storage for bot tokens in database
   - Monitor active bots through Admin Panel regularly
3. **Per-User Setup:**
   - Each user creates their own Telegram bot via @BotFather
   - Each bot runs under that user's account
   - Users have full autonomy over their bot configuration

### 📊 Admin Panel Integration

**Left Sidebar Admin Panel** (click 👥 Admin button in navbar):

**For All Users - Bot Settings Tab:**
| Setting | Type | Notes |
|---------|------|-------|
| Bot Token | Password Input | Paste token from @BotFather. Leave empty to keep current. |
| Bot Enabled | Toggle | Turn your bot on/off without restarting services |
| Status | Display | Shows if token is configured + if bot is enabled |

**For Admins Only - Active Bots Section:**
| Info | Display | Notes |
|------|---------|-------|
| Active Bots List | Display | All enabled bots with owner username |
| Token Status | Indicator | ✓ configured or ✗ missing |
| Last Updated | Timestamp | When bot settings were last changed |

**For Admins Only - Bot Settings (Legacy):**
- System-wide singleton bot configuration (backward compatible)
- Only used if no per-user bots are configured

### 🐛 Troubleshooting

**Bot doesn't respond:**
- Go to **Bot Settings** tab in navbar
- Confirm token is pasted and valid (from @BotFather)
- Check **"Enable my Telegram bot"** is checked
- Verify backend is running: `docker logs bambam-api`
- View bot logs: `docker logs bambam-bot`
- Admins: Check **Admin Panel** → **Active Bots** to see bot status

**"Failed ❌" when converting:**
- Check backend worker: `docker logs bambam-worker`
- File might be unsupported format (check supported formats above)
- Worker queue might be stuck: `docker logs bambam-redis`
- Verify your user account is active (not suspended)

**Bot takes too long:**
- Default timeout: 10 minutes per job
- Large videos/documents naturally take longer
- FFmpeg + LibreOffice process time depends on file size
- Check job status in **Jobs** dashboard tab

**Multiple users, only one bot works:**
- Make sure each user has their own bot token from @BotFather
- Each user must set their token in their **Bot Settings** tab
- Admins can see all active bots in the **Admin Panel** → **Active Bots**

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

![Version](https://img.shields.io/badge/version-1.4.1-blue)
![Python](https://img.shields.io/badge/python-3.13-green)
![License](https://img.shields.io/badge/license-MIT-orange)

> **📌 Version Management**: Update the version in `[frontend/lib/version.ts](frontend/lib/version.ts)` (the single source of truth). It will automatically reflect on the landing page. Also update the badge version number above and add a changelog entry when releasing.

## ✨ Features

### 🖼️ Image Converter
- **Supported Formats**: PNG, JPG, JPEG, BMP, GIF, TIFF, WEBP, ICO
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
- **Supported Formats**: MP3, WAV, OGG, FLAC, AAC, M4A, WMA, OPUS, AIFF
- **Audio Settings**:
  - Bitrate control (64-320 kbps)
  - Sample rate adjustment
  - Channel configuration (mono/stereo)
- **Batch Processing**: Convert entire music libraries
- **Folder Support**: Recursive folder scanning

### 📄 Document Converter
- **Supported Input Formats**: PDF, DOCX, DOC, TXT, RTF, ODT, XLS, XLSX, PPT, PPTX
- **Supported Output Formats**: PDF, DOCX, ODT, TXT
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

### Version 1.4.2 (Latest)
- ✨ Workers panel scale control now applies **exact final worker count** behavior (non-additive)
- ✨ Workers target display now reconciles against actual running Docker Compose worker replicas for more accurate scaling telemetry
- ✨ Added per-worker quick `×` action to reduce desired worker total by 1
- 🐛 Fixed worker decrement edge case where quick-remove could stop working before reaching minimum worker count
- 🐛 Fixed quick-remove `×` button alignment so the icon sits centered within the button hit area
- 🐛 Fixed portrait mobile navbar/header overlap so settings gear and logout controls no longer cover tool tabs
- 🐛 Fixed worker count input reset during periodic telemetry refresh
- 🐛 Fixed workers health badge color mismatch by normalizing health status text
- ✨ Admin Users view now offers account creation plus full registered user listing with delete actions, and the Workers scale control uses the landing-style slider

### Version 1.4.1
- ✨ Removed completed-job notification `!` badges from both landing quick buttons and top navbar tabs
- ✨ Refined landing quick-tool grid so **Jobs** uses standard button size and is positioned in the right-column slot under **Document Converter**
- ✨ Added **Workers** admin monitor in unified settings: online/offline workers, busy/idle state, current job info, queue size, API/Redis health cards
- ✨ Added admin worker scaling endpoint and UI control backed by Docker Compose (`worker` replicas)

### Version 1.4.0
- ✨ **Unified Settings Panel** — Single ⚙️ button opens all settings for both admins and users
  - Admin users: Account, Users (real-time monitor), Storage (all files), Bot Settings (active bots + system bot)
  - Regular users: Account, Storage (own jobs only with download), Bot Settings (personal bot only)
- ✨ **Removed Admin Panel button** from navbar and landing page — now only unified settings ⚙️ button
- ✨ **Per-user Storage** — normal users see only their completed jobs with download buttons
- ✨ **Admin Storage** — toggle between Uploads/Outputs, view/delete files with owner tracking, one-click Delete All
- ✨ **Sub-menu navigation** in settings: Account → Users/Storage/Bot Settings with back button
- ✨ **Video crop drag-to-move**: hold and drag the crop box center to reposition; handles still resize
- ✨ **Mobile navbar optimization**: buttons scroll horizontally (no wrap), stays readable on portrait
- ✨ **Improved landing page**: cleaner 2-column grid layout with user info row
- 🐛 Fixed navbar buttons from wrapping on mobile portrait — now horizontally scrollable
- 🐛 Removed "Bot Settings" tab from navbar (accessible only from unified settings panel)

### Version 1.3.9
- ✨ **Settings Panel** — New left-sliding settings panel accessible to all users via ⚙️ FAB button (top-left)
- ✨ Settings Panel includes user account info and personal Telegram bot configuration
- ✨ Responsive Settings Panel design: 320px desktop, full-width on mobile (same pattern as Admin Panel)
- ✨ **Mobile touch support** for video crop and trim controls — drag handles now work with finger touches
- ✨ Crop overlay handles respond to touch events on mobile devices
- ✨ Trim waveform handles respond to touch events on mobile devices (both start and end)
- 🐛 **Fixed mobile portrait mode blur bug** — overlay no longer covers entire screen when panels are closed
- 🐛 Removed forced `display: block` CSS rule that was blocking all interaction on mobile

### Version 1.3.8
- ✨ **Per-User Bot Management** — Each user can now manage their own Telegram bot token in "Bot Settings" tab
- ✨ Admin panel refactored to **left-sliding sidebar** (320px desktop, full-width mobile)
- ✨ Admin Panel now shows **Active Bots** section with owner usernames and token status
- ✨ New endpoint `/admin/bot-settings/active` — lists all active bots with user information
- ✨ New user endpoints `/auth/user/bot-settings` (GET/PUT) — users manage their own bot configuration
- ✨ BotSettings model updated with `user_id` field for per-user support (backward compatible)
- ✨ Bot Settings tab in navbar visible to all authenticated users
- ✨ Responsive design: mobile hamburger sidebar, touch-friendly UI
- ✨ Updated documentation with per-user bot setup instructions
- 🐛 Improved admin panel organization with collapsible sections

### Version 1.3.7
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
