
import kagglehub
import shutil
from pathlib import Path

# Download the dataset
path = kagglehub.dataset_download(
    "atulyakumar98/pothole-detection-dataset"
)

source = Path(path)
destination = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "potholes"
    / "internet_source"
)

destination.mkdir(parents=True, exist_ok=True)

print("Downloaded dataset location:", source)
print("Inspecting downloaded files...")

# Copy the downloaded dataset into our project
for item in source.iterdir():
    target = destination / item.name

    if item.is_dir():
        if not target.exists():
            shutil.copytree(item, target)
    elif not target.exists():
        shutil.copy2(item, target)

print("Dataset copied to:", destination)
print("Done! Inspect the folders before using the images.")