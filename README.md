# 🎨 Bambam Converter Suite

A powerful, all-in-one media conversion tool with a beautiful dark-themed interface. Convert images, videos, audio files, and documents with ease!

## 🌐 Web App Migration Status

This repository now includes an in-progress self-hosted web application stack alongside the original desktop implementation.

### Current Web Features

- Dockerized local deployment with `[docker-compose.yml](docker-compose.yml)`
- Next.js frontend under `[frontend/](frontend)`
- FastAPI backend under `[backend/](backend)`
- Redis/RQ background job execution
- Web-based image conversion
- Web-based sound conversion
- Web-based video conversion
- Web-based document conversion through LibreOffice headless
- Job dashboard/history view
- Manual cleanup endpoint for finished and stale jobs
- Navbar-based fast tool switching in `[frontend/app/page.tsx](frontend/app/page.tsx)`
- Landing screen with centered logo, suite title, and live status cards
- Batch and zip export support for image, audio, video, and document jobs

### Current Web Limitations

- Advanced desktop-only options such as rename patterns, crop/trim parity, and some power-user settings are not yet fully ported
- Authentication is still intentionally lightweight for local/self-hosted usage
- Production deployment beyond local or trusted-network use still needs additional security review

### Web Support Matrix

| Module | Single File | Batch | Zip Export | Notes |
|---|---|---|---|---|
| Image | Yes | Yes | Yes | Core web workflow implemented |
| Sound | Yes | Yes | Yes | Bitrate control available |
| Video | Yes | Yes | Yes | Basic format/FPS/resize workflow implemented |
| Document | Yes | Yes | Yes | LibreOffice headless only |
| Batch Rename | No | No | No | Not yet ported to web |

### Web UI Snapshot

- Landing: centered Bambam logo + `Bambam Converter Suite` + `Version 1.3.0`
- Top navbar switches screens instantly between Landing, Image, Sound, Video, Document, and Jobs
- Live cards show API health and job counters from backend endpoints

## 🚀 Web App Quick Start

```bash
docker compose up --build
```

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
- `POST /document/jobs`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /admin/cleanup`

The desktop app remains in the repository, but ongoing migration work is focused on the self-hosted web app.

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

## 📦 Release Readiness Notes

Operational and maintenance documentation for the self-hosted web app is available in:

- `[plans/operations-checklist.md](plans/operations-checklist.md)`
- `[plans/backup-restore.md](plans/backup-restore.md)`
- `[plans/web-app-master-roadmap.md](plans/web-app-master-roadmap.md)`

![Version](https://img.shields.io/badge/version-1.3.0-blue)
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

### Version 1.3.0 (Latest)
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
