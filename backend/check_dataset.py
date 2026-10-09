
from pathlib import Path

root = Path("data/potholes/dataset")
image_exts = {".jpg", ".jpeg", ".png", ".webp"}

for split in ("train", "valid", "test"):
    image_dir = root / split / "images"
    label_dir = root / split / "labels"

    images = [p for p in image_dir.iterdir()
              if p.is_file() and p.suffix.lower() in image_exts]
    labels = list(label_dir.glob("*.txt"))

    missing = [p.name for p in images
               if not (label_dir / f"{p.stem}.txt").exists()]
    invalid = []

    for label in labels:
        for line_no, line in enumerate(
            label.read_text(encoding="utf-8").splitlines(), 1
        ):
            if not line.strip():
                continue
            try:
                values = [float(x) for x in line.split()]
                if len(values) != 5:
                    raise ValueError("expected 5 values")
                cls, x, y, w, h = values
                if cls != 0 or not (
                    0 <= x <= 1 and 0 <= y <= 1
                    and 0 < w <= 1 and 0 < h <= 1
                ):
                    raise ValueError("invalid class or coordinates")
            except ValueError as e:
                invalid.append(f"{label.name}:{line_no} ({e})")

    print(f"\n{split.upper()}: {len(images)} images, "
          f"{len(labels)} label files")
    print("Images without labels:", len(missing))
    print("Invalid annotation rows:", len(invalid))
    if missing[:3]:
        print("Examples missing:", missing[:3])
    if invalid[:3]:
        print("Examples invalid:", invalid[:3])