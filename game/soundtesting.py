import pygame
from pathlib import Path

"""Quick sound support tester.
Loads and briefly plays each sound effect to verify decoder support.
Run from project root:  python -m game.soundtesting
"""

# Per-sound candidate list; tries in order until one loads
SOUND_CANDIDATES = {
    "badankh": ["badankh.ogg", "badankh.mp3", "badankh.wav"],
    "block": ["block.ogg", "block.mp3", "block.wav"],
    "click": ["click.ogg", "click.mp3", "click.wav"],
    "expwalk15a": ["expwalk15a.ogg", "expwalk15a.mp3", "expwalk15a.wav"],
    "expwalk15b": ["expwalk15b.ogg", "expwalk15b.mp3", "expwalk15b.wav"],
    "expwalk30a": ["expwalk30a.ogg", "expwalk30a.mp3", "expwalk30a.wav"],
    "expwalk30b": ["expwalk30b.ogg", "expwalk30b.mp3", "expwalk30b.wav"],
    "expwalk60a": ["expwalk60a.ogg", "expwalk60a.mp3", "expwalk60a.wav"],
    "expwalk60b": ["expwalk60b.ogg", "expwalk60b.mp3", "expwalk60b.wav"],
    "finishedlevel": ["finishedlevel.ogg", "finishedlevel.mp3", "finishedlevel.wav"],
    "gate": ["gate.ogg", "gate.mp3", "gate.wav"],
    "mummyhowl": ["mummyhowl.ogg", "mummyhowl.mp3", "mummyhowl.wav"],
    "mumwalk15a": ["mumwalk15a.ogg", "mumwalk15a.mp3", "mumwalk15a.wav"],
    "mumwalk15b": ["mumwalk15b.ogg", "mumwalk15b.mp3", "mumwalk15b.wav"],
    "mumwalk30a": ["mumwalk30a.ogg", "mumwalk30a.mp3", "mumwalk30a.wav"],
    "mumwalk30b": ["mumwalk30b.ogg", "mumwalk30b.mp3", "mumwalk30b.wav"],
    "mumwalk60a": ["mumwalk60a.ogg", "mumwalk60a.mp3", "mumwalk60a.wav"],
    "mumwalk60b": ["mumwalk60b.ogg", "mumwalk60b.mp3", "mumwalk60b.wav"],
    "opentreasure": ["opentreasure.ogg", "opentreasure.mp3", "opentreasure.wav"],
    "pit": ["pit.ogg", "pit.mp3", "pit.wav"],
    "poison": ["poison.ogg", "poison.mp3", "poison.wav"],
    "pummel": ["pummel.mp3", "pummel.ogg", "pummel.wav"],
    "scorpwalk1": ["scorpwalk1.ogg", "scorpwalk1.mp3", "scorpwalk1.wav"],
    "scorpwalk2": ["scorpwalk2.ogg", "scorpwalk2.mp3", "scorpwalk2.wav"],
    "tombslide": ["tombslide.ogg", "tombslide.mp3", "tombslide.wav"],
}

def main():
    base_dir = Path(__file__).resolve().parent
    sounds_dir = base_dir / "assets" / "sounds"

    #print(f"[info] sounds dir: {sounds_dir}")

    # Initialize mixer with multiple channels
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=8, buffer=512)
    pygame.mixer.init()

    failed = []
    for name, variants in SOUND_CANDIDATES.items():
        loaded = False
        for fname in variants:
            path = sounds_dir / fname
            if not path.exists():
                continue
            try:
                snd = pygame.mixer.Sound(str(path))
                length = snd.get_length()
                #print(f"[ok] {name} using {fname} length={length:.2f}s")
                snd.play()
                pygame.time.delay(int(min(length, 0.5) * 1000))
                snd.stop()
                loaded = True
                break
            except Exception as ex:
                #print(f"[fail] {name} ({fname}): {ex}")
        if not loaded:
            #print(f"[missing/unsupported] {name}")
            failed.append(name)

    if failed:
        #print("\nFailed/unsupported (convert these to wav or mp3 and rerun):")
        for f in failed:
            #print(f" - {f}")
    else:
        #print("\nAll sounds loaded and played successfully.")

    pygame.mixer.quit()


if __name__ == "__main__":
    main()
