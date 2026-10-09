# checks a theme folder against ECHO's own slot lists and media limits; prints problems, exit 1 if any
import json, os, re, subprocess, sys, wave
from PIL import Image
repo, theme = sys.argv[1], sys.argv[2]
kit = f"{repo}/core/theme-kit/src/main/kotlin/com/echo/themekit"
slots = set(re.findall(r'(?:catbar|item|status)\("([a-z0-9_]+)"', open(f"{kit}/IconSlots.kt").read()))
src = open(f"{kit}/CustomizableIcons.kt").read()
consoles = set(re.findall(r'"([a-z0-9_]+)"', src[src.index("SYSICON_PLATFORM_IDS"):src.index(")")]))
media = dict(re.findall(r'"([a-z_]+)" to (SOUNDS|BOOT|GAME_START)', open(f"{kit}/ThemeMedia.kt").read()))
folder_of = {"SOUNDS": "Sounds", "BOOT": "Boot", "GAME_START": "GameStart"}
limits = open(f"{kit}/UiMediaLimits.kt").read()
const = {k: int(v.replace("_", "")) for k, v in re.findall(r'const val (\w+_MS)\s*=\s*([\d_]+)L', limits)}
spec = {k: v for k, v in re.findall(r'val (\w+)\s*= ?Spec\(Kind\.\w+,\s*[\d_]+L,\s*[\d_]+L,\s*(\w+)', limits)}
slot_spec = dict(re.findall(r'\("([a-z_]+)", UiMediaKind\.\w+, "[^"]*", UiMediaLimits\.(\w+)\)', open(f"{repo}/core/core-domain/src/main/kotlin/com/echo/core/domain/model/UiMediaSlot.kt").read()))
# a sound's length: WAV through the standard library, MP3/OGG/M4A/MP4 through mutagen, anything else through
# ffprobe when it is installed; 0 when none can read it
def duration_ms(path):
    if path.lower().endswith(".wav"):
        try:
            with wave.open(path) as w: return w.getnframes() / w.getframerate() * 1000
        except Exception: return 0
    try:
        import mutagen
        info = mutagen.File(path)
        if info is not None and info.info.length: return info.info.length * 1000
    except ImportError: pass
    except Exception: return 0
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
        return float(out or 0) * 1000
    except FileNotFoundError: return 0

problems, kept = [], 0
def bad(m): problems.append(m)
m = json.load(open(f"{theme}/theme.json"))
if m.get("manifest") not in ("echo-theme", "pfptheme"): bad("theme.json: manifest is not echo-theme")
for key, allowed in [("waveDesign", {"PSP", "ECHO_RINGS", "ECHO_ARCS"}), ("gameBootStyle", {"DISC", "LENS"}), ("launchDiscStyle", {"DISC", "LENS"}), ("buttonSet", {"GENERIC", "XBOX", "NINTENDO", "PLAYSTATION"})]:
    if m.get(key) is not None and m[key] not in allowed: bad(f"theme.json: {key}={m[key]} is not one ECHO knows")
# focus style and motion: the names in FocusAndMotion.kt's two enums
fm = open(f"{kit}/FocusAndMotion.kt").read()
enums = dict(re.findall(r'enum class (\w+) \{([^}]*)\}', fm))
for key, enum in (("focusStyle", "FocusStyle"), ("motion", "MotionPreset")):
    names = {n.strip() for n in enums.get(enum, "").split(",") if n.strip()}
    if not names: bad(f"could not read {enum} from FocusAndMotion.kt")
    elif m.get(key) is not None and m[key] not in names: bad(f"theme.json: {key}={m[key]} is not one ECHO knows")
# look settings: only the keys ThemeSettings.kt lists, true/false or a name as it says, or null
setting_kinds = dict(re.findall(r'"([a-z0-9_]+)" to Kind\.(BOOL|TEXT)', open(f"{kit}/ThemeSettings.kt").read()))
if not setting_kinds: bad("could not read ThemeSettings.kt from the echo-launcher checkout")
settings = m.get("settings") or {}
if not isinstance(settings, dict): bad("theme.json: settings is not an object"); settings = {}
for key, value in settings.items():
    kind = setting_kinds.get(key)
    if kind is None: bad(f"theme.json: settings.{key} is not a setting a theme can carry")
    elif value is not None and not (isinstance(value, bool) if kind == "BOOL" else isinstance(value, str)):
        bad(f"theme.json: settings.{key} must be {'true or false' if kind == 'BOOL' else 'a name'}")
# a font: the extensions and size EchoThemeCodec takes, one file, with a TrueType or OpenType signature
codec = open(f"{kit}/EchoThemeCodec.kt").read()
font_exts = set(re.findall(r'"(\w+)"', re.search(r'FONT_EXTENSIONS = setOf\(([^)]*)\)', codec).group(1)))
font_mb = int(re.search(r'MAX_FONT_BYTES = (\d+) \* 1024 \* 1024', codec).group(1))
fonts = 0
for root, _, files in os.walk(theme):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), theme); parts = rel.split(os.sep); stem, ext = os.path.splitext(f); ext = ext[1:].lower()
        if rel in ("theme.json", "README.md"): kept += 1; continue
        if parts[0] == "Icons":
            ok = (len(parts) == 2 and stem in slots) or (len(parts) == 3 and parts[1] == "Consoles" and stem in consoles)
            if not ok or ext not in ("png", "gif"): bad(f"{rel}: not an icon slot ECHO has"); continue
            if os.path.getsize(os.path.join(root, f)) > 8 << 20: bad(f"{rel}: over 8 MB")
        elif parts[0] == "Wallpaper":
            if f not in ("wallpaper.png", "preview.png") and not re.fullmatch(r"motion\.(mp4|webm|gif)", f): bad(f"{rel}: not a wallpaper file ECHO reads"); continue
        elif parts[0] in folder_of.values():
            if media.get(stem) is None or folder_of[media[stem]] != parts[0] or ext not in ("mp3", "wav", "ogg", "m4a", "mp4", "webm"): bad(f"{rel}: not a media slot of {parts[0]}"); continue
            ms = duration_ms(os.path.join(root, f))
            hard = const[spec[slot_spec[stem]]]
            if ms <= 0: bad(f"{rel}: no duration")
            elif ms > hard: bad(f"{rel}: {ms:.0f} ms, over the {hard} ms limit")
        elif parts[0] == "Fonts":
            if len(parts) != 2 or ext not in font_exts: bad(f"{rel}: not a font ECHO reads ({', '.join(sorted(font_exts))})"); continue
            fonts += 1
            if fonts > 1: bad(f"{rel}: a theme carries one font; ECHO keeps only one of them")
            path = os.path.join(root, f)
            if os.path.getsize(path) > font_mb << 20: bad(f"{rel}: over {font_mb} MB")
            elif open(path, "rb").read(4) not in (b"\x00\x01\x00\x00", b"OTTO", b"true"): bad(f"{rel}: not a TrueType or OpenType font")
        elif parts[0] == "Preview":
            if not ((len(parts) == 2 and stem == "hero") or (len(parts) == 3 and parts[1] == "Screenshots")) or ext not in ("jpg", "jpeg", "png", "webp"): bad(f"{rel}: not a hero or screenshot"); continue
        else:
            bad(f"{rel}: has no place in a theme"); continue
        if ext in ("png", "jpg", "jpeg", "webp", "gif"):
            try: Image.open(os.path.join(root, f)).verify()
            except Exception as e: bad(f"{rel}: not a readable picture ({e})"); continue
        kept += 1
print(f"{os.path.basename(os.path.normpath(theme))}: {kept} files kept, {len(problems)} problems")
for p in problems: print("  ", p)
sys.exit(1 if problems else 0)
