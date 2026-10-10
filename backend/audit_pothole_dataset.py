"""
Read-only audit of the Legioners pothole dataset.
Does not modify images, labels, YAML, model weights, or database.
Run from the project root:
    python backend\audit_pothole_dataset.py
"""
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "potholes" / "dataset_with_negatives"
DEFAULT_YAML = PROJECT_ROOT / "backend" / "pothole_data_with_negatives.yaml"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def read_yaml_names(yaml_path):
    """Read common YOLO `names:` formats without requiring PyYAML."""
    if not yaml_path.exists():
        return {}
    text = yaml_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    names = {}
    in_names = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^names\s*:", stripped):
            in_names = True
            inline = stripped.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                vals = [x.strip().strip("'\"") for x in inline[1:-1].split(",")]
                return {i: name for i, name in enumerate(vals) if name}
            continue
        if in_names:
            match = re.match(r"^\s*(\d+)\s*:\s*(.*?)\s*$", line)
            if match:
                names[int(match.group(1))] = match.group(2).strip("'\"")
            elif not line.startswith((" ", "\t")):
                break
    return names


def image_stems(directory):
    if not directory.exists():
        return set()
    return {p.stem for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS}


def label_stems(directory):
    if not directory.exists():
        return set()
    return {p.stem for p in directory.rglob("*.txt") if p.is_file()}


def audit_split(split_name, split_dir, class_names):
    image_dir = split_dir / "images"
    label_dir = split_dir / "labels"
    images = image_stems(image_dir)
    labels = label_stems(label_dir)
    print(f"\n[{split_name}]")
    print(f"  images directory: {image_dir} {'(found)' if image_dir.exists() else '(MISSING)'}")
    print(f"  labels directory: {label_dir} {'(found)' if label_dir.exists() else '(MISSING)'}")
    print(f"  image files: {len(images)}")
    print(f"  label files: {len(labels)}")

    missing_label = sorted(images - labels)
    orphan_label = sorted(labels - images)
    if missing_label:
        print(f"  images with no matching .txt label: {len(missing_label)}")
        print("    examples:", ", ".join(missing_label[:8]))
        print("    Note: no-label images are not necessarily wrong; confirm whether these are intended negatives.")
    if orphan_label:
        print(f"  label files with no matching image: {len(orphan_label)}")
        print("    examples:", ", ".join(orphan_label[:8]))

    class_counts = {}
    invalid_lines = 0
    empty_label_files = 0
    total_boxes = 0
    if label_dir.exists():
        for label_file in label_dir.rglob("*.txt"):
            content = label_file.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                empty_label_files += 1
                continue
            for line_number, line in enumerate(content.splitlines(), 1):
                parts = line.split()
                if len(parts) < 5:
                    invalid_lines += 1
                    continue
                try:
                    class_id = int(float(parts[0]))
                    coords = [float(x) for x in parts[1:5]]
                    if not all(0.0 <= x <= 1.0 for x in coords):
                        # YOLO box center/width/height should normally be normalized.
                        invalid_lines += 1
                    class_counts[class_id] = class_counts.get(class_id, 0) + 1
                    total_boxes += 1
                except ValueError:
                    invalid_lines += 1

    print(f"  labelled bounding boxes: {total_boxes}")
    print(f"  empty label files (often negative examples): {empty_label_files}")
    print(f"  malformed/unusual label lines: {invalid_lines}")
    if class_counts:
        print("  class counts:")
        for class_id in sorted(class_counts):
            name = class_names.get(class_id, "UNKNOWN_CLASS_ID")
            print(f"    class {class_id} ({name}): {class_counts[class_id]} boxes")
    else:
        print("  class counts: no labelled boxes found")

    return {
        "images": len(images),
        "labels": len(labels),
        "class_ids": set(class_counts),
        "class_counts": class_counts,
        "empty_label_files": empty_label_files,
        "invalid_lines": invalid_lines,
    }


def main():
    dataset_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_DATASET
    yaml_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_YAML
    class_names = read_yaml_names(yaml_path)

    print("LEGIONERS DATASET AUDIT (READ-ONLY)")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Dataset:      {dataset_dir}")
    print(f"YOLO YAML:    {yaml_path}")
    print("\nConfigured class names:")
    if class_names:
        for class_id, name in sorted(class_names.items()):
            print(f"  {class_id}: {name}")
    else:
        print("  Could not parse class names (check YAML manually).")

    if not dataset_dir.exists():
        print("\nERROR: Dataset folder not found.")
        print("Pass the correct dataset path as the first argument, for example:")
        print(r'  python backend\audit_pothole_dataset.py "C:\path\to\dataset"')
        sys.exit(2)

    split_results = {}
    found_splits = 0
    for split in ("train", "valid", "val", "test"):
        split_dir = dataset_dir / split
        if (split_dir / "images").exists() or (split_dir / "labels").exists():
            found_splits += 1
            split_results[split] = audit_split(split, split_dir, class_names)

    if found_splits == 0:
        print("\nERROR: No train/valid/val/test split folders containing images/ or labels/ were found.")
        print("Expected layout: dataset/train/images, dataset/train/labels, dataset/valid/images, dataset/valid/labels.")
        sys.exit(2)

    all_class_ids = set().union(*(r["class_ids"] for r in split_results.values()))
    print("\n" + "=" * 58)
    print("SEVERITY-LABEL READINESS")
    print("=" * 58)
    if not all_class_ids:
        print("No YOLO object classes were found in the scanned label files.")
        print("Severity training readiness cannot be inferred from these labels.")
    elif len(all_class_ids) == 1:
        only_id = next(iter(all_class_ids))
        print(f"Only one detection class was found: {only_id} ({class_names.get(only_id, 'unknown')}).")
        print("This dataset can train pothole detection, but it does NOT by itself provide Low/Medium/High severity labels.")
        print("Next step: obtain severity annotations or create a separate image-level severity dataset.")
    else:
        print(f"Found {len(all_class_ids)} object classes: {sorted(all_class_ids)}.")
        print("Multiple detection classes were found, but they are severity labels only if the class names explicitly encode severity.")
        severity_names = [name.lower() for name in class_names.values()]
        has_severity_names = any(any(term in name for term in ("low", "medium", "moderate", "high", "severe")) for name in severity_names)
        if has_severity_names:
            print("The YAML names include severity-like terms; manually confirm their annotation meaning before training.")
        else:
            print("The YAML class names do not clearly identify severity labels; verify annotation definitions.")
    if any(r["invalid_lines"] for r in split_results.values()):
        print("\nWARNING: Some label lines may be malformed or use a non-standard format. Inspect these before training.")
    print("\nAudit complete. No files were changed.")


if __name__ == "__main__":
    main()
