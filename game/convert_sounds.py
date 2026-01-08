import subprocess
from pathlib import Path
import shutil

"""
Batch converter for sound assets.
- Converts all .ogg/.mp3 to .wav (22050 Hz, mono) using ffmpeg.
- Skips files that already have a .wav sibling.
Usage (run from project root):
    python -m game.convert_sounds
Requires: ffmpeg available in PATH.
"""

TARGET_RATE = 22050
TARGET_CHANNELS = 1

def has_ffmpeg() -> bool:
    ffmpeg_path = Path(r"C:\ffmpeg\bin\ffmpeg.exe")
    return ffmpeg_path.exists()

def convert_file(src: Path, dst: Path) -> bool:
    cmd = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "-y", "-i", str(src),
        "-ar", str(TARGET_RATE),
        "-ac", str(TARGET_CHANNELS),
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as ex:
        #print(f"[fail] {src.name} -> {dst.name}: {ex.stderr.decode(errors='ignore')[:200]}")
        return False

def main():
    base_dir = Path(__file__).resolve().parent / "assets" / "sounds"
    #print(f"[info] sounds dir: {base_dir}")

    if not has_ffmpeg():
        #print("[error] ffmpeg not found in PATH. Install ffmpeg and retry.")
        return

    converted = []
    skipped = []
    failed = []

    for src in base_dir.iterdir():
        if src.suffix.lower() not in {".ogg", ".mp3"}:
            continue
        dst = src.with_suffix(".wav")
        if dst.exists():
            skipped.append(src.name)
            continue
        ok = convert_file(src, dst)
        if ok:
            converted.append(dst.name)
        else:
            failed.append(src.name)

    #print("\n=== Summary ===")
    #print(f"Converted: {len(converted)}")
    for n in converted:
        #print(f"  - {n}")
    #print(f"Skipped (wav already present): {len(skipped)}")
    for n in skipped:
        #print(f"  - {n}")
    if failed:
        #print(f"Failed: {len(failed)}")
        for n in failed:
            #print(f"  - {n}")
    else:
        #print("Failed: 0")

if __name__ == "__main__":
    main()
