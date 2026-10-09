
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR.parent / "data" / "potholes" / "dataset"

SPLITS = ["train", "valid", "test"]

print("\n========== DATASET INSPECTION ==========")
print(f"Dataset location: {DATASET_DIR}")

if not DATASET_DIR.exists():
    raise FileNotFoundError(f"Dataset folder not found: {DATASET_DIR}")

for split in SPLITS:
    images_dir = DATASET_DIR / split / "images"
    labels_dir = DATASET_DIR / split / "labels"

    print(f"\n--- {split.upper()} ---")

    if not images_dir.exists() or not labels_dir.exists():
        print("Images or labels folder is missing.")
        continue

    images = [
        p for p in images_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    ]

    empty_labels = []
    labelled_images = []
    missing_labels = []
    invalid_label_rows = []

    for image_path in images:
        label_path = labels_dir / f"{image_path.stem}.txt"

        if not label_path.exists():
            missing_labels.append(image_path.name)
            continue

        content = label_path.read_text(encoding="utf-8").strip()

        if not content:
            empty_labels.append(image_path.name)
        else:
            labelled_images.append(image_path.name)

            for line_number, line in enumerate(content.splitlines(), 1):
                parts = line.split()

                if len(parts) != 5:
                    invalid_label_rows.append(
                        f"{label_path.name}:{line_number}"
                    )
                    continue

                try:
                    class_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:])
                    if (
                        class_id != 0
                        or not all(0 <= v <= 1 for v in (x, y, w, h))
                        or w <= 0
                        or h <= 0
                    ):
                        invalid_label_rows.append(
                            f"{label_path.name}:{line_number}"
                        )
                except ValueError:
                    invalid_label_rows.append(
                        f"{label_path.name}:{line_number}"
                    )

    print(f"Images: {len(images)}")
    print(f"Images with pothole labels: {len(labelled_images)}")
    print(f"Images with empty labels: {len(empty_labels)}")
    print(f"Images missing label files: {len(missing_labels)}")
    print(f"Invalid label rows: {len(invalid_label_rows)}")

    if empty_labels:
        print("Examples of empty-label images:", empty_labels[:5])

    if missing_labels:
        print("Examples of missing-label images:", missing_labels[:5])

    if invalid_label_rows:
        print("Examples of invalid rows:", invalid_label_rows[:5])

print("\n========== INSPECTION COMPLETE ==========")