
from pathlib import Path
from collections import Counter
import csv
import math
import re

import cv2


# ============================================================
# PATHS — verified for Legioners-Project/backend/
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = ROOT / "data" / "potholes" / "dataset_with_negatives"
OUT_DIR = ROOT / "data" / "potholes" / "severity_workflow"
CROPS_DIR = OUT_DIR / "crops"

ANNOTATIONS_CSV = OUT_DIR / "severity_annotations.csv"
MANIFEST_CSV = OUT_DIR / "severity_manifest.csv"

SPLITS = ("train", "valid", "test")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
PADDING_RATIO = 0.10

CSV_FIELDS = [
    "crop_id",
    "split",
    "source_image",
    "source_label",
    "box_index",
    "bbox_x1",
    "bbox_y1",
    "bbox_x2",
    "bbox_y2",
    "crop_path",
    "severity_label",
    "annotation_status",
    "annotator_notes",
]


# ============================================================
# LOAD EXISTING ANNOTATIONS
# ============================================================

def load_existing_annotations():
    """
    Preserve existing severity labels and notes by crop_id.
    The annotations CSV takes priority over the manifest.
    """
    existing = {}

    for csv_path in (MANIFEST_CSV, ANNOTATIONS_CSV):
        if not csv_path.is_file():
            continue

        try:
            with csv_path.open(
                "r", newline="", encoding="utf-8-sig"
            ) as file:
                reader = csv.DictReader(file)

                for row in reader:
                    crop_id = (row.get("crop_id") or "").strip()

                    if not crop_id:
                        continue

                    # Later file has priority: annotations CSV is last.
                    existing.setdefault(crop_id, {})
                    existing[crop_id].update({
                        field: row.get(field, "") or ""
                        for field in CSV_FIELDS
                    })

        except (OSError, csv.Error) as exc:
            raise RuntimeError(
                f"Could not safely read {csv_path}: {exc}"
            ) from exc

    return existing


# ============================================================
# FIND DATASET IMAGES AND LABELS
# ============================================================

def find_images(images_dir):
    if not images_dir.is_dir():
        return []

    return sorted(
        path
        for path in images_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def find_label(labels_dir, image_path, images_dir):
    """
    Match labels using the image's relative path first,
    then fall back to a flat labels directory.
    """
    relative_path = image_path.relative_to(images_dir)
    candidate = labels_dir / relative_path.with_suffix(".txt")

    if candidate.is_file():
        return candidate

    return labels_dir / f"{image_path.stem}.txt"


def read_yolo_boxes(label_path, image_width, image_height):
    """
    Read YOLO labels:
        class_id x_center y_center width height

    Returns pixel-coordinate boxes (x1, y1, x2, y2).
    """
    boxes = []

    if not label_path.is_file():
        return boxes

    try:
        lines = label_path.read_text(
            encoding="utf-8-sig"
        ).splitlines()
    except OSError as exc:
        raise RuntimeError(
            f"Cannot read label file {label_path}: {exc}"
        ) from exc

    for line_number, line in enumerate(lines, start=1):
        parts = line.split()

        if not parts:
            continue

        if len(parts) < 5:
            print(
                f"WARNING: Invalid YOLO row at "
                f"{label_path}:{line_number}"
            )
            continue

        try:
            class_id = int(float(parts[0]))
            xc, yc, w, h = map(float, parts[1:5])
        except ValueError:
            print(
                f"WARNING: Non-numeric YOLO row at "
                f"{label_path}:{line_number}"
            )
            continue

        if not all(math.isfinite(v) for v in (xc, yc, w, h)):
            continue

        if w <= 0 or h <= 0:
            continue

        x1 = max(
            0, min(image_width - 1, int((xc - w / 2) * image_width))
        )
        y1 = max(
            0, min(image_height - 1, int((yc - h / 2) * image_height))
        )
        x2 = max(
            1, min(image_width, int((xc + w / 2) * image_width))
        )
        y2 = max(
            1, min(image_height, int((yc + h / 2) * image_height))
        )

        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))

    return boxes


def safe_stem(relative_path):
    """
    Keep crop IDs consistent with the earlier naming convention:
    split__image_stem__box000
    """
    stem = relative_path.with_suffix("").as_posix()
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)


# ============================================================
# GENERATE CROPS
# ============================================================

def generate_crops():
    rows = []
    issues = []

    for split in SPLITS:
        split_dir = DATASET_DIR / split
        images_dir = split_dir / "images"
        labels_dir = split_dir / "labels"

        if not images_dir.is_dir() or not labels_dir.is_dir():
            issues.append(
                f"{split}: missing images or labels directory: {split_dir}"
            )
            continue

        images = find_images(images_dir)
        split_count = 0

        for image_path in images:
            image = cv2.imread(str(image_path))

            if image is None:
                issues.append(f"Unreadable image: {image_path}")
                continue

            image_height, image_width = image.shape[:2]
            label_path = find_label(labels_dir, image_path, images_dir)

            boxes = read_yolo_boxes(
                label_path, image_width, image_height
            )

            relative_path = image_path.relative_to(images_dir)
            image_stem = safe_stem(relative_path)

            for box_index, (x1, y1, x2, y2) in enumerate(boxes):
                crop_id = (
                    f"{split}__{image_stem}__box{box_index:03d}"
                )

                box_width = x2 - x1
                box_height = y2 - y1

                pad_x = int(box_width * PADDING_RATIO)
                pad_y = int(box_height * PADDING_RATIO)

                cx1 = max(0, x1 - pad_x)
                cy1 = max(0, y1 - pad_y)
                cx2 = min(image_width, x2 + pad_x)
                cy2 = min(image_height, y2 + pad_y)

                crop = image[cy1:cy2, cx1:cx2]

                if crop.size == 0:
                    issues.append(f"Empty crop: {crop_id}")
                    continue

                crop_path = CROPS_DIR / f"{crop_id}.jpg"
                crop_path.parent.mkdir(parents=True, exist_ok=True)

                if not cv2.imwrite(str(crop_path), crop):
                    issues.append(f"Could not save crop: {crop_path}")
                    continue

                rows.append({
                    "crop_id": crop_id,
                    "split": split,
                    "source_image": str(image_path),
                    "source_label": str(label_path),
                    "box_index": str(box_index),
                    "bbox_x1": str(x1),
                    "bbox_y1": str(y1),
                    "bbox_x2": str(x2),
                    "bbox_y2": str(y2),
                    "crop_path": str(crop_path),
                    "severity_label": "",
                    "annotation_status": "pending",
                    "annotator_notes": "",
                })

                split_count += 1

        print(
            f"{split}: {len(images)} images, {split_count} crops"
        )

    return rows, issues


# ============================================================
# PRESERVE LABELS AND WRITE CSV SAFELY
# ============================================================

def save_csv_atomically(path, rows):
    temporary = path.with_suffix(path.suffix + ".tmp")

    try:
        with temporary.open(
            "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    field: row.get(field, "")
                    for field in CSV_FIELDS
                })

        temporary.replace(path)

    finally:
        if temporary.exists():
            temporary.unlink()


def main():
    print("UPDATED SEVERITY CROP SCRIPT RUNNING")
    print("Project root:", ROOT)
    print("Dataset:", DATASET_DIR)
    print("Output:", OUT_DIR)

    if not DATASET_DIR.is_dir():
        raise FileNotFoundError(
            f"Dataset directory does not exist: {DATASET_DIR}"
        )

    # Read the old labels before generating or writing anything.
    existing = load_existing_annotations()
    print("Existing annotation IDs loaded:", len(existing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CROPS_DIR.mkdir(parents=True, exist_ok=True)

    rows, issues = generate_crops()

    if not rows:
        print("\nERROR: Zero crops generated.")
        print("Existing annotation CSV files were not rewritten.")
        for issue in issues[:20]:
            print(" -", issue)
        return

    new_ids = {row["crop_id"] for row in rows}
    old_labelled_ids = {
        crop_id
        for crop_id, old in existing.items()
        if (old.get("severity_label") or "").strip()
    }

    unmatched_labelled = old_labelled_ids - new_ids

    # Do not overwrite annotations if any labelled crop ID was lost.
    if unmatched_labelled:
        print("\nSAFETY STOP: Existing labelled crop IDs did not match.")
        print("Annotation CSV files have NOT been rewritten.")
        print("Unmatched labelled IDs:", len(unmatched_labelled))

        for crop_id in sorted(unmatched_labelled)[:20]:
            print(" -", crop_id)

        print(
            "\nKeep the existing CSV files. We need to reconcile "
            "these crop IDs before updating the annotations."
        )
        return

    matched_count = 0

    for row in rows:
        old = existing.get(row["crop_id"])

        if old:
            matched_count += 1
            row["severity_label"] = (
                old.get("severity_label") or ""
            ).strip()
            row["annotator_notes"] = old.get("annotator_notes") or ""

            previous_status = (
                old.get("annotation_status") or ""
            ).strip()

            if row["severity_label"]:
                row["annotation_status"] = (
                    previous_status
                    if previous_status
                    and previous_status.lower() != "pending"
                    else "annotated"
                )
            else:
                row["annotation_status"] = previous_status or "pending"

    # Both files are updated only after the safety check succeeds.
    save_csv_atomically(ANNOTATIONS_CSV, rows)
    save_csv_atomically(MANIFEST_CSV, rows)

    counts = Counter(
        (row["severity_label"] or "").strip() or "UNLABELLED"
        for row in rows
    )

    print("\nSEVERITY CROP PREPARATION COMPLETE")
    print("Crops made:", len(rows))

    for split in SPLITS:
        print(
            f"  {split}: "
            f"{sum(row['split'] == split for row in rows)}"
        )

    print("Existing crop IDs matched:", matched_count)

    print("\nSeverity counts:")
    for label in ("Low", "Medium", "High", "Uncertain", "UNLABELLED"):
        print(f"  {label}: {counts[label]}")

    print("\nAnnotations:", ANNOTATIONS_CSV)
    print("Manifest:", MANIFEST_CSV)

    if issues:
        print("\nIssues:", len(issues))
        for issue in issues[:20]:
            print(" -", issue)


if __name__ == "__main__":
    main()
