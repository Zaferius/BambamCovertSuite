# 🎨 Bambam Converter Suite

A powerful, all-in-one media conversion tool with a beautiful dark-themed interface. Convert images, videos, audio files, and documents with ease!

![Version](https://img.shields.io/badge/version-1.2.9-blue)
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

### Version 1.2.9 (Latest)
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

Made with ❤️ by Zaferius
