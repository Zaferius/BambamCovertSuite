# Simple localization (i18n) helper for Bambam Converter Suite

from typing import Dict

# Supported languages metadata
LANG_META: Dict[str, Dict[str, str]] = {
    "en": {"name": "English"},
    "tr": {"name": "Türkçe"},
}

# Flat key dictionaries
STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app.title": "Bambam Converter Suite",

        "home.title": "Bambam Converter Suite",
        "home.version": "Version {version}",
        "home.product": "Bambam Product 2025",
        "home.language_label": "Language:",
        "home.btn.image": "Image Converter",
        "home.btn.sound": "Sound Converter",
        "home.btn.video": "Video Converter",
        "home.btn.document": "Document Converter",
        "home.btn.rename": "Batch Rename",

        "tabs.home": "Home",
        "tabs.image": "Image",
        "tabs.sound": "Sound",
        "tabs.video": "Video",
        "tabs.document": "Document",
        "tabs.rename": "Batch Rename",
        "tabs.settings": "Settings",

        "image.title": "Bambam Image Converter",
        "image.header.presets": "Presets",
        "image.section.select": "1) Select Images / Folders",
        "image.btn.browse_files": "Browse Images...",
        "image.btn.add_folder": "Add Folder...",
        "image.btn.clear_selected": "Clear Selected",
        "image.files.count": "Selected files: {file_count} | Selected folders: {folder_count}",
        "image.hint.dragdrop": "You can also drag & drop files or folders onto this area (recursive).",

        "image.section.output": "2) Output Location",
        "image.output.radio.mirror": "Same folder as source (mirror)",
        "image.output.radio.folder": "Use selected output folder",
        "image.output.btn.browse": "Browse Folder...",
        "image.output.label.not_selected": "Not selected",
        "image.output.label.using_source": "Using source folders",
        "image.output.btn.clear": "Clear Output Folder",
        "image.output.delete_originals": "Delete originals after successful conversion",

        "image.section.format": "3) Target Format",
        "image.format.label": "Format:",
        "image.quality.label": "JPEG Quality:",

        "image.section.resize": "4) Resize (optional)",
        "image.resize.enable": "Enable resize",
        "image.resize.width": "Width (px):",
        "image.resize.height": "Height (px):",
        "image.resize.mode.fit_pad": "Keep aspect, add white bars",
        "image.resize.mode.stretch": "Stretch to fill",

        "image.section.rename": "5) Batch Rename (optional)",
        "image.rename.enable": "Enable batch renaming",
        "image.rename.pattern": "Pattern:",
        "image.rename.hint": "Placeholders: {name} = original name, {index} = 1,2,3...",

        "image.section.progress": "Progress",
        "image.progress.initial": "0 / 0",
        "image.status.idle": "Idle.",
        "image.btn.start": "Start Conversion",

        "image.warning.title": "Warning",
        "image.warning.no_selection": "Please select at least one image or folder.",
        "image.warning.no_output": "Please select an output folder or choose 'Same folder as source'.",

        "image.info.title": "Info",
        "image.info.no_images": "No images found.",

        "image.status.processing": "Processing…",
        "image.result.errors_status": "Completed with errors.",
        "image.result.errors_title": "Completed with errors",
        "image.result.errors_message": "Conversion finished with errors.\n\n{failed} of {total} item(s) failed.\n\nFirst error:\n{path}\n{error}",
        "image.result.done_status": "Completed.",
        "image.result.done_title": "Done",
        "image.result.done_message": "All {total} image(s) converted successfully!",

        "image.clear_output.info_no_folder": "Output folder is not set.",
        "image.clear_output.confirm_title": "Confirm",
        "image.clear_output.confirm_message": "Delete ALL files in output folder?",
        "image.clear_output.done_title": "Cleared",
        "image.clear_output.done_message": "Deleted {count} file(s).",

        "image.presets.window_title": "Image Presets",
        "image.presets.label_list": "Presets:",
        "image.presets.label_name": "Name:",
        "image.presets.btn.apply": "Apply",
        "image.presets.btn.delete": "- Delete",
        "image.presets.btn.add": "+ Add",
        "image.presets.warning.no_name": "Please enter a preset name.",
        "image.presets.warning.title": "Warning",
        "image.presets.confirm.delete_title": "Confirm",
        "image.presets.confirm.delete_message": "Delete preset '{name}'?",
        "image.presets.warning.save_failed": "Failed to save presets file.",

        # ---- Sound tab ----
        "sound.title": "Bambam Sound Converter",
        "sound.section.select": "1) Select Audio Files",
        "sound.btn.browse_files": "Browse Audio...",
        "sound.btn.add_folders": "Add Folders...",
        "sound.btn.clear_selected": "Clear Selected",
        "sound.files.count": "Selected files: {file_count}",
        "sound.hint.dragdrop": "You can also drag & drop audio files onto this area.",

        "sound.section.output": "2) Output Location",
        "sound.output.btn.browse": "Browse Folder...",
        "sound.output.label.not_selected": "Not selected",
        "sound.output.btn.clear": "Clear Output Folder",

        "sound.section.format": "3) Target Format & Bitrate",
        "sound.format.label": "Format:",
        "sound.bitrate.label": "Bitrate:",

        "sound.section.progress": "Progress",
        "sound.progress.initial": "0 / 0",
        "sound.status.idle": "Idle.",
        "sound.status.processing": "Processing…",
        "sound.btn.start": "Start Conversion",

        "sound.warning.title": "Warning",
        "sound.warning.no_files": "Please select at least one audio file.",
        "sound.warning.no_output": "Please select an output folder.",

        "sound.info.title": "Info",
        "sound.info.output_not_set": "Output folder is not set.",

        "sound.result.errors_status": "Completed with errors.",
        "sound.result.errors_title": "Completed with errors",
        "sound.result.errors_message": "Audio conversion finished with errors.\n\n{failed} of {total} file(s) failed.\n\nFirst error:\n{path}\n{error}",
        "sound.result.done_status": "Completed.",
        "sound.result.done_title": "Done",
        "sound.result.done_message": "All audio conversions finished.",

        "sound.clear_output.confirm_title": "Confirm",
        "sound.clear_output.confirm_message": "Delete ALL files in output folder?",
        "sound.clear_output.done_title": "Cleared",
        "sound.clear_output.done_message": "Deleted {count} file(s).",

        "sound.ffmpeg.missing_title": "FFmpeg not found",
        "sound.ffmpeg.missing_message": "FFmpeg is required for Sound features.",

        # ---- Video tab ----
        "video.title": "Bambam Video Converter",
        "video.section.select": "1) Select Videos",
        "video.btn.browse_files": "Browse Videos...",
        "video.btn.add_folder": "Add Folder...",
        "video.btn.clear_selected": "Clear Selected",
        "video.files.count": "Selected files: {file_count}",
        "video.hint.dragdrop": "You can also drag & drop video files or folders onto this area (recursive).",

        "video.section.output": "2) Output Location",
        "video.output.btn.browse": "Browse Folder...",
        "video.output.label.not_selected": "Not selected",
        "video.output.btn.clear": "Clear Output Folder",

        "video.section.format": "3) Target Format & Settings",
        "video.format.label": "Format:",
        "video.resize.enable": "Resize",
        "video.resize.width_short": "W:",
        "video.resize.height_short": "H:",
        "video.resize.keep_aspect": "Keep aspect",
        "video.fps.label": "FPS (0=keep):",
        "video.gif.btn_settings": "GIF Settings...",

        "video.section.progress": "Progress",
        "video.progress.initial": "0 / 0",
        "video.status.idle": "Idle.",
        "video.status.processing": "Processing…",
        "video.status.cancelling": "Cancelling…",
        "video.status.cancelled": "Cancelled.",
        "video.status.completed": "Completed.",
        "video.status.completed_errors": "Completed with errors.",
        "video.btn.start": "Start Conversion",

        "video.warning.title": "Warning",
        "video.warning.no_files": "Please select at least one video.",
        "video.warning.no_output": "Please select an output folder.",

        "video.info.title": "Info",
        "video.info.output_not_set": "Output folder is not set.",

        "video.result.errors_title": "Completed with errors",
        "video.result.errors_message": "Conversion finished with errors.\n\n{failed} of {total} item(s) failed.\n\nFirst error:\n{path}\n{error}",
        "video.result.done_title": "Done",
        "video.result.done_message": "All {total} video(s) converted successfully!",

        "video.clear_output.confirm_title": "Confirm",
        "video.clear_output.confirm_message": "Delete ALL files in output folder?",
        "video.clear_output.done_title": "Cleared",
        "video.clear_output.done_message": "Deleted {count} file(s).",

        "video.ffmpeg.missing_title": "FFmpeg not found",
        "video.ffmpeg.missing_message": "FFmpeg is required for Video features.",

        "video.gif.window_title": "GIF Settings",
        "video.gif.width": "Width (px):",
        "video.gif.height": "Height (px):",
        "video.gif.fps": "FPS:",
        "video.gif.btn.save": "Save",
        "video.gif.btn.cancel": "Cancel",
        "video.gif.warning.title": "Invalid values",
        "video.gif.warning.message": "Please enter valid numeric values for GIF settings.",

        "video.crop.section": "Crop / Trim",
        "video.crop.btn_open": "Open Crop Tool",
        "video.crop.note.single_only": "(Available for single selection)",
        "video.crop.note.disabled": "Select exactly one video to configure crop.",
        "video.crop.status.off": "Crop disabled",
        "video.crop.status.on": "Crop enabled: {area}",
        "video.crop.window.title": "Crop / Trim",
        "video.crop.window.enable": "Enable crop",
        "video.crop.slider.left": "Left %",
        "video.crop.slider.right": "Right %",
        "video.crop.slider.top": "Top %",
        "video.crop.slider.bottom": "Bottom %",
        "video.crop.preview.error": "Failed to load preview frame for cropping.",
        "video.crop.btn.apply": "Apply",
        "video.crop.btn.reset": "Reset",
        "video.crop.warning.original_title": "Crop requires re-encode",
        "video.crop.warning.original_message": "Please choose a target format other than 'Original' when crop is enabled.",
        "video.trim.section": "Trim Timeline",
        "video.trim.enable": "Enable trim",
        "video.trim.slider.start": "Start (s)",
        "video.trim.slider.end": "End (s)",
        "video.trim.warning.order": "Start time must be earlier than end time.",
        "video.trim.status.off": "Trim disabled",
        "video.trim.status.on": "Trim: {start} → {end}",
        "video.trim.note.single_only": "(Available for single selection)",
        "video.trim.note.disabled": "Select exactly one video to configure trim.",
        "video.trim.note.ready": "Duration: {duration}",
        "video.trim.note.error": "Could not read video duration for trimming.",
        "video.trim.warning.original_title": "Trim requires re-encode",
        "video.trim.warning.original_message": "Please choose a target format other than 'Original' when trim is enabled.",

        # ---- Batch Rename tab ----
        "rename.title": "Bambam Batch Rename",
        "rename.section.select": "1) Select Files",
        "rename.btn.browse_files": "Browse Files...",
        "rename.btn.clear_selected": "Clear Selected",
        "rename.files.count": "Selected files: {file_count}",

        "rename.section.dest": "2) Destination",
        "rename.dest.in_place": "Rename in place",
        "rename.dest.btn_output": "Output Folder...",
        "rename.dest.label.not_selected": "Not selected",
        "rename.dest.label.in_place": "(in-place rename)",
        "rename.dest.btn_clear_output": "Clear Output",

        "rename.section.pattern": "3) Pattern",
        "rename.pattern.label": "Pattern:",
        "rename.pattern.start_index": "Start #:",
        "rename.pattern.hint": "Placeholders: {name}, {ext}, {index}, {date}",

        "rename.section.preview": "Preview",
        "rename.preview.column_new": "New Name",

        "rename.actions.btn.refresh": "Refresh Preview",
        "rename.actions.btn.apply": "Apply Rename",

        "rename.warning.title": "Warning",
        "rename.warning.no_files": "No files selected.",
        "rename.warning.no_output": "Please select an output folder or enable in-place rename.",
        "rename.error.title": "Error",
        "rename.error.message": "Failed: {name}\n{error}",
        "rename.done.title": "Done",
        "rename.done.message": "Batch rename finished.",

        "settings.title": "Global Settings",
        "settings.section.behavior": "Conversion Behavior",
        "settings.auto_open": "Open the output folder automatically after conversions finish",
        "settings.auto_open.hint": "When enabled, Bambam Converter Suite will open the folder that holds your converted files right after a successful conversion.",
        
        "settings.section.updates": "Updates",
        "settings.current_version": "Current Version:",
        "settings.btn.check_updates": "Check for Updates",
        "settings.btn.download_update": "Download Latest Version",
        "settings.checking_updates": "Checking for updates...",
        "settings.update_available": "🎉 New version available: {version}",
        "settings.up_to_date": "✓ You are using the latest version!",
        "settings.dev_version": "You are using a development version ({current}). Latest stable: {latest}",
        "settings.update_check_failed": "Failed to check for updates: {error}",
    },
    "tr": {
        "app.title": "Bambam Converter Suite",

        "home.title": "Bambam Dönüştürücü Paketi",
        "home.version": "Sürüm {version}",
        "home.product": "Bambam Ürün 2025",
        "home.language_label": "Dil:",
        "home.btn.image": "Resim Dönüştürücü",
        "home.btn.sound": "Ses Dönüştürücü",
        "home.btn.video": "Video Dönüştürücü",
        "home.btn.document": "Doküman Dönüştürücü",
        "home.btn.rename": "Toplu Yeniden Adlandırma",

        "tabs.home": "Ana Sayfa",
        "tabs.image": "Resim",
        "tabs.sound": "Ses",
        "tabs.video": "Video",
        "tabs.document": "Doküman",
        "tabs.rename": "Toplu Yeniden Adlandırma",
        "tabs.settings": "Ayarlar",

        "image.title": "Bambam Resim Dönüştürücü",
        "image.header.presets": "Presets",
        "image.section.select": "1) Resim / Klasör Seç",
        "image.btn.browse_files": "Resim Seç...",
        "image.btn.add_folder": "Klasör Ekle...",
        "image.btn.clear_selected": "Seçileni Temizle",
        "image.files.count": "Seçilen dosya: {file_count} | Seçilen klasör: {folder_count}",
        "image.hint.dragdrop": "Bu alana dosya veya klasörleri sürükleyip bırakabilirsiniz (alt klasörler dahil).",

        "image.section.output": "2) Çıkış Konumu",
        "image.output.radio.mirror": "Kaynak klasör ile aynı (yansıma)",
        "image.output.radio.folder": "Seçilen çıkış klasörünü kullan",
        "image.output.btn.browse": "Klasör Seç...",
        "image.output.label.not_selected": "Seçilmedi",
        "image.output.label.using_source": "Kaynak klasörler kullanılıyor",
        "image.output.btn.clear": "Çıkış Klasörünü Temizle",
        "image.output.delete_originals": "Başarılı dönüşümden sonra orijinalleri sil",

        "image.section.format": "3) Hedef Format",
        "image.format.label": "Format:",
        "image.quality.label": "JPEG Kalitesi:",

        "image.section.resize": "4) Yeniden Boyutlandır (opsiyonel)",
        "image.resize.enable": "Yeniden boyutlandırmayı etkinleştir",
        "image.resize.width": "Genişlik (px):",
        "image.resize.height": "Yükseklik (px):",
        "image.resize.mode.fit_pad": "Oranı koru, beyaz boşluk ekle",
        "image.resize.mode.stretch": "Esnet ve doldur",

        "image.section.rename": "5) Toplu Yeniden Adlandırma (opsiyonel)",
        "image.rename.enable": "Toplu yeniden adlandırmayı etkinleştir",
        "image.rename.pattern": "Desen:",
        "image.rename.hint": "Yer tutucular: {name} = orijinal ad, {index} = 1,2,3...",

        "image.section.progress": "İlerleme",
        "image.progress.initial": "0 / 0",
        "image.status.idle": "Beklemede.",
        "image.btn.start": "Dönüştürmeyi Başlat",

        "image.warning.title": "Uyarı",
        "image.warning.no_selection": "Lütfen en az bir resim veya klasör seçin.",
        "image.warning.no_output": "Lütfen bir çıkış klasörü seçin veya 'Kaynak klasör ile aynı' seçeneğini kullanın.",

        "image.info.title": "Bilgi",
        "image.info.no_images": "Herhangi bir resim bulunamadı.",

        "image.status.processing": "İşleniyor…",
        "image.result.errors_status": "Hatalarla tamamlandı.",
        "image.result.errors_title": "Hatalarla tamamlandı",
        "image.result.errors_message": "Dönüşüm hatalarla tamamlandı.\n\nToplam {total} öğeden {failed} tanesi başarısız oldu.\n\nİlk hata:\n{path}\n{error}",
        "image.result.done_status": "Tamamlandı.",
        "image.result.done_title": "Bitti",
        "image.result.done_message": "Toplam {total} resim başarıyla dönüştürüldü!",

        "image.clear_output.info_no_folder": "Çıkış klasörü ayarlanmadı.",
        "image.clear_output.confirm_title": "Onayla",
        "image.clear_output.confirm_message": "Çıkış klasöründeki TÜM dosyalar silinsin mi?",
        "image.clear_output.done_title": "Temizlendi",
        "image.clear_output.done_message": "{count} dosya silindi.",

        "image.presets.window_title": "Resim Preset'leri",
        "image.presets.label_list": "Preset'ler:",
        "image.presets.label_name": "Ad:",
        "image.presets.btn.apply": "Uygula",
        "image.presets.btn.delete": "- Sil",
        "image.presets.btn.add": "+ Ekle",
        "image.presets.warning.no_name": "Lütfen bir preset adı girin.",
        "image.presets.warning.title": "Uyarı",
        "image.presets.confirm.delete_title": "Onayla",
        "image.presets.confirm.delete_message": "'{name}' preset'i silinsin mi?",
        "image.presets.warning.save_failed": "Preset dosyası kaydedilemedi.",

        # ---- Sound tab ----
        "sound.title": "Bambam Ses Dönüştürücü",
        "sound.section.select": "1) Ses Dosyalarını Seç",
        "sound.btn.browse_files": "Ses Dosyası Seç...",
        "sound.btn.add_folders": "Klasörler Ekle...",
        "sound.btn.clear_selected": "Seçileni Temizle",
        "sound.files.count": "Seçilen dosya: {file_count}",
        "sound.hint.dragdrop": "Bu alana ses dosyalarını sürükleyip bırakabilirsiniz.",

        "sound.section.output": "2) Çıkış Konumu",
        "sound.output.btn.browse": "Klasör Seç...",
        "sound.output.label.not_selected": "Seçilmedi",
        "sound.output.btn.clear": "Çıkış Klasörünü Temizle",

        "sound.section.format": "3) Hedef Format ve Bitrate",
        "sound.format.label": "Format:",
        "sound.bitrate.label": "Bitrate:",

        "sound.section.progress": "İlerleme",
        "sound.progress.initial": "0 / 0",
        "sound.status.idle": "Beklemede.",
        "sound.status.processing": "İşleniyor…",
        "sound.btn.start": "Dönüştürmeyi Başlat",

        "sound.warning.title": "Uyarı",
        "sound.warning.no_files": "Lütfen en az bir ses dosyası seçin.",
        "sound.warning.no_output": "Lütfen bir çıkış klasörü seçin.",

        "sound.info.title": "Bilgi",
        "sound.info.output_not_set": "Çıkış klasörü ayarlanmadı.",

        "sound.result.errors_status": "Hatalarla tamamlandı.",
        "sound.result.errors_title": "Hatalarla tamamlandı",
        "sound.result.errors_message": "Ses dönüştürme hatalarla tamamlandı.\n\nToplam {total} dosyadan {failed} tanesi başarısız oldu.\n\nİlk hata:\n{path}\n{error}",
        "sound.result.done_status": "Tamamlandı.",
        "sound.result.done_title": "Bitti",
        "sound.result.done_message": "Tüm ses dönüştürme işlemleri tamamlandı.",

        "sound.clear_output.confirm_title": "Onayla",
        "sound.clear_output.confirm_message": "Çıkış klasöründeki TÜM dosyalar silinsin mi?",
        "sound.clear_output.done_title": "Temizlendi",
        "sound.clear_output.done_message": "{count} dosya silindi.",

        "sound.ffmpeg.missing_title": "FFmpeg bulunamadı",
        "sound.ffmpeg.missing_message": "Ses özellikleri için FFmpeg gereklidir.",

        # ---- Video tab ----
        "video.title": "Bambam Video Dönüştürücü",
        "video.section.select": "1) Videoları Seç",
        "video.btn.browse_files": "Video Seç...",
        "video.btn.add_folder": "Klasör Ekle...",
        "video.btn.clear_selected": "Seçileni Temizle",
        "video.files.count": "Seçilen dosya: {file_count}",
        "video.hint.dragdrop": "Bu alana video dosyalarını veya klasörleri sürükleyip bırakabilirsiniz (alt klasörler dahil).",

        "video.section.output": "2) Çıkış Konumu",
        "video.output.btn.browse": "Klasör Seç...",
        "video.output.label.not_selected": "Seçilmedi",
        "video.output.btn.clear": "Çıkış Klasörünü Temizle",

        "video.section.format": "3) Hedef Format ve Ayarlar",
        "video.format.label": "Format:",
        "video.resize.enable": "Yeniden boyutlandır",
        "video.resize.width_short": "G:",
        "video.resize.height_short": "Y:",
        "video.resize.keep_aspect": "Oranı koru",
        "video.fps.label": "FPS (0=koru):",
        "video.gif.btn_settings": "GIF Ayarları...",

        "video.section.progress": "İlerleme",
        "video.progress.initial": "0 / 0",
        "video.status.idle": "Beklemede.",
        "video.status.processing": "İşleniyor…",
        "video.status.cancelling": "İptal ediliyor…",
        "video.status.cancelled": "İptal edildi.",
        "video.status.completed": "Tamamlandı.",
        "video.status.completed_errors": "Hatalarla tamamlandı.",
        "video.btn.start": "Dönüştürmeyi Başlat",

        "video.warning.title": "Uyarı",
        "video.warning.no_files": "Lütfen en az bir video seçin.",
        "video.warning.no_output": "Lütfen bir çıkış klasörü seçin.",

        "video.info.title": "Bilgi",
        "video.info.output_not_set": "Çıkış klasörü ayarlanmadı.",

        "video.result.errors_title": "Hatalarla tamamlandı",
        "video.result.errors_message": "Dönüşüm hatalarla tamamlandı.\n\nToplam {total} öğeden {failed} tanesi başarısız oldu.\n\nİlk hata:\n{path}\n{error}",
        "video.result.done_title": "Bitti",
        "video.result.done_message": "Toplam {total} video başarıyla dönüştürüldü!",

        "video.clear_output.confirm_title": "Onayla",
        "video.clear_output.confirm_message": "Çıkış klasöründeki TÜM dosyalar silinsin mi?",
        "video.clear_output.done_title": "Temizlendi",
        "video.clear_output.done_message": "{count} dosya silindi.",

        "video.ffmpeg.missing_title": "FFmpeg bulunamadı",
        "video.ffmpeg.missing_message": "Video özellikleri için FFmpeg gereklidir.",

        "video.gif.window_title": "GIF Ayarları",
        "video.gif.width": "Genişlik (px):",
        "video.gif.height": "Yükseklik (px):",
        "video.gif.fps": "FPS:",
        "video.gif.btn.save": "Kaydet",
        "video.gif.btn.cancel": "İptal",
        "video.gif.warning.title": "Geçersiz değerler",
        "video.gif.warning.message": "Lütfen GIF ayarları için geçerli sayısal değerler girin.",

        "video.crop.section": "Kırp / Trim",
        "video.crop.btn_open": "Kırpma Aracını Aç",
        "video.crop.note.single_only": "(Sadece tekli seçimlerde geçerli)",
        "video.crop.note.disabled": "Kırpma için tam olarak bir video seçmelisiniz.",
        "video.crop.status.off": "Kırpma kapalı",
        "video.crop.status.on": "Kırpma açık: {area}",
        "video.crop.window.title": "Kırp / Trim",
        "video.crop.window.enable": "Kırpmayı etkinleştir",
        "video.crop.slider.left": "Sol %",
        "video.crop.slider.right": "Sağ %",
        "video.crop.slider.top": "Üst %",
        "video.crop.slider.bottom": "Alt %",
        "video.crop.preview.error": "Kırpma önizlemesi yüklenemedi.",
        "video.crop.btn.apply": "Uygula",
        "video.crop.btn.reset": "Sıfırla",
        "video.crop.warning.original_title": "Kırpma yeniden kodlama gerektirir",
        "video.crop.warning.original_message": "Kırpma açıksa 'Orijinal' yerine başka bir hedef format seçin.",
        "video.trim.section": "Kesme Zaman Çizelgesi",
        "video.trim.enable": "Kesmeyi etkinleştir",
        "video.trim.slider.start": "Başlangıç (sn)",
        "video.trim.slider.end": "Bitiş (sn)",
        "video.trim.warning.order": "Başlangıç süresi bitişten küçük olmalıdır.",
        "video.trim.status.off": "Kesme devre dışı",
        "video.trim.status.on": "Kesme: {start} → {end}",
        "video.trim.note.single_only": "(Sadece tekli seçimde kullanılabilir)",
        "video.trim.note.disabled": "Kesme ayarı için tek bir video seçin.",
        "video.trim.note.ready": "Süre: {duration}",
        "video.trim.note.error": "Videonun süresi okunamadı.",
        "video.trim.warning.original_title": "Kesme yeniden kodlama gerektirir",
        "video.trim.warning.original_message": "Kesme açıksa 'Orijinal' yerine başka bir hedef format seçin.",

        # ---- Batch Rename tab ----
        "rename.title": "Bambam Toplu Yeniden Adlandırma",
        "rename.section.select": "1) Dosyaları Seç",
        "rename.btn.browse_files": "Dosya Seç...",
        "rename.btn.clear_selected": "Seçileni Temizle",
        "rename.files.count": "Seçilen dosya: {file_count}",

        "rename.section.dest": "2) Hedef",
        "rename.dest.in_place": "Yerinde yeniden adlandır",
        "rename.dest.btn_output": "Çıkış Klasörü...",
        "rename.dest.label.not_selected": "Seçilmedi",
        "rename.dest.label.in_place": "(yerinde yeniden adlandır)",
        "rename.dest.btn_clear_output": "Çıkış Seçimini Temizle",

        "rename.section.pattern": "3) Desen",
        "rename.pattern.label": "Desen:",
        "rename.pattern.start_index": "Başlangıç #:",
        "rename.pattern.hint": "Yer tutucular: {name}, {ext}, {index}, {date}",

        "rename.section.preview": "Önizleme",
        "rename.preview.column_new": "Yeni Ad",

        "rename.actions.btn.refresh": "Önizlemeyi Yenile",
        "rename.actions.btn.apply": "Yeniden Adlandırmayı Uygula",

        "rename.warning.title": "Uyarı",
        "rename.warning.no_files": "Hiç dosya seçilmedi.",
        "rename.warning.no_output": "Lütfen bir çıkış klasörü seçin veya yerinde yeniden adlandırmayı etkinleştirin.",
        "rename.error.title": "Hata",
        "rename.error.message": "Başarısız: {name}\n{error}",
        "rename.done.title": "Bitti",
        "rename.done.message": "Toplu yeniden adlandırma tamamlandı.",

        "settings.title": "Genel Ayarlar",
        "settings.section.behavior": "Dönüştürme Davranışı",
        "settings.auto_open": "İşlem bittiğinde çıktının bulunduğu klasörü otomatik aç",
        "settings.auto_open.hint": "Bu seçenek açıkken, başarılı bir dönüştürme tamamlandıktan sonra Bambam Converter Suite dosyaların kaydedildiği klasörü otomatik olarak açar.",
        
        "settings.section.updates": "Güncellemeler",
        "settings.current_version": "Mevcut Sürüm:",
        "settings.btn.check_updates": "Güncellemeleri Kontrol Et",
        "settings.btn.download_update": "Son Sürümü İndir",
        "settings.checking_updates": "Güncellemeler kontrol ediliyor...",
        "settings.update_available": "🎉 Yeni sürüm mevcut: {version}",
        "settings.up_to_date": "✓ En son sürümü kullanıyorsunuz!",
        "settings.dev_version": "Geliştirme sürümü kullanıyorsunuz ({current}). Son kararlı sürüm: {latest}",
        "settings.update_check_failed": "Güncelleme kontrolü başarısız: {error}",
    },
}

DEFAULT_LANG = "en"
_current_lang = DEFAULT_LANG


def set_language(code: str) -> None:
    global _current_lang
    if code not in STRINGS:
        code = DEFAULT_LANG
    _current_lang = code


def get_language() -> str:
    return _current_lang


def get_available_languages():
    return list(LANG_META.keys())


def get_language_name(code: str) -> str:
    meta = LANG_META.get(code, {})
    return meta.get("name", code)


def get_language_code(name: str) -> str:
    for code, meta in LANG_META.items():
        if meta.get("name") == name:
            return code
    return DEFAULT_LANG


def t(key: str, **kwargs) -> str:
    """Translate key for current language.

    Falls back to English, then to the key itself if missing.
    """
    lang = _current_lang
    text = STRINGS.get(lang, {}).get(key)
    if text is None:
        text = STRINGS.get(DEFAULT_LANG, {}).get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text
