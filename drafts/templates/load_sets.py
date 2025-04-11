# load_sets.py
from pathlib import Path

def load_sets(base_dir):
    """
    Scan the repository for keyboard sets and register them as players.
    For each set folder, load images from both the "kits_pics" and "rendering_pics"
    directories. Each player dictionary includes:
      - id: will be assigned later
      - name: display name, e.g. "DSA Alchemy"
      - images: a sorted list of image file paths (relative to base_dir)
      - score: total wins (initially 0)
      - opponents: list of opponent IDs already played
      - active: boolean indicating if the player is still in the tournament
    """
    sets = []
    base_path = Path(base_dir)
    for source in ["dsa-keycaps", "gmk-keycaps"]:
        source_path = base_path / source
        if source_path.exists() and source_path.is_dir():
            for set_dir in source_path.iterdir():
                if set_dir.is_dir():
                    display_name = f"{source.split('-')[0].upper()} {set_dir.name.capitalize()}"
                    images = []
                    # Load images from kits_pics
                    kits_dir = set_dir / "kits_pics"
                    if kits_dir.exists() and kits_dir.is_dir():
                        for p in kits_dir.iterdir():
                            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                                relative_path = p.relative_to(base_path)
                                images.append(str(relative_path))
                    # Load images from rendering_pics
                    rendering_dir = set_dir / "rendering_pics"
                    if rendering_dir.exists() and rendering_dir.is_dir():
                        for p in rendering_dir.iterdir():
                            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                                relative_path = p.relative_to(base_path)
                                images.append(str(relative_path))
                    images = sorted(images)
                    sets.append({
                        "name": display_name,
                        "images": images,
                        "score": 0,
                        "opponents": [],
                        "active": True
                    })
    # Assign unique IDs to players.
    for idx, player in enumerate(sets):
        player["id"] = idx + 1
    return sets
