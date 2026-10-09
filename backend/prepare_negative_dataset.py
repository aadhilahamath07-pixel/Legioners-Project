
from pathlib import Path
import shutil

# Project paths
project = Path(__file__).resolve().parent.parent
original = project / "data" / "potholes" / "dataset"
negative = project / "data" / "potholes" / "negative_dataset" / "images"
output = project / "data" / "potholes" / "dataset_with_negatives"

# Safety checks
if not original.exists():
    raise FileNotFoundError(f"Original dataset not found: {original}")

if not negative.exists():
    raise FileNotFoundError(f"Negative images not found: {negative}")

if output.exists():
    raise FileExistsError(
        f"{output} already exists. Rename it or inspect it before retrying."
    )

# Copy the original dataset, preserving validation and test splits
shutil.copytree(original, output)

# Find the original training directories
train_images = output / "train" / "images"
train_labels = output / "train" / "labels"

train_images.mkdir(parents=True, exist_ok=True)
train_labels.mkdir(parents=True, exist_ok=True)

# Copy normal images into training images and create empty labels
extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
negative_images = sorted(
    p for p in negative.iterdir()
    if p.is_file() and p.suffix.lower() in extensions
)

added = 0

for image in negative_images:
    new_name = f"negative_{image.stem}{image.suffix.lower()}"
    image_destination = train_images / new_name
    label_destination = train_labels / f"{Path(new_name).stem}.txt"

    if image_destination.exists() or label_destination.exists():
        print(f"Skipping existing filename: {new_name}")
        continue

    shutil.copy2(image, image_destination)
    label_destination.write_text("", encoding="utf-8")
    added += 1

print("\nDataset preparation complete!")
print("New dataset:", output)
print("Negative images added:", added)
print("Original dataset remains unchanged.")
print("Validation and test splits were copied without modification.")