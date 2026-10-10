
from pathlib import Path
import shutil
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = (
    PROJECT_ROOT / "data" / "potholes" / "severity_workflow"
)
CSV_PATH = WORKFLOW_DIR / "severity_annotations.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "potholes" / "severity_dataset"

CLASSES = {"Low", "Medium", "High"}
SPLITS = {"train", "valid", "test"}


def main():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Annotation CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    required = {"split", "crop_path", "severity_label"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")

    labelled = df[
        df["severity_label"].astype(str).str.strip().isin(CLASSES)
    ].copy()

    if labelled.empty:
        raise ValueError("No Low, Medium, or High labels found.")

    # Validate every crop before copying anything.
    labelled["resolved_crop"] = labelled["crop_path"].map(
        lambda p: WORKFLOW_DIR / str(p)
    )

    missing_files = labelled[
        ~labelled["resolved_crop"].map(Path.is_file)
    ]

    if not missing_files.empty:
        raise FileNotFoundError(
            f"{len(missing_files)} labelled crop files are missing. "
            "Check the paths in severity_annotations.csv."
        )

    invalid_splits = set(labelled["split"].dropna()) - SPLITS
    if invalid_splits:
        raise ValueError(f"Unexpected split names: {invalid_splits}")

    # Avoid accidentally mixing new and old output files.
    if OUTPUT_DIR.exists():
        raise FileExistsError(
            f"{OUTPUT_DIR} already exists. Rename or remove it "
            "after checking its contents before rerunning."
        )

    try:
        for split in sorted(SPLITS):
            split_df = labelled[labelled["split"] == split]

            for label in sorted(CLASSES):
                (OUTPUT_DIR / split / label).mkdir(
                    parents=True, exist_ok=True
                )

                for _, row in split_df[
                    split_df["severity_label"] == label
                ].iterrows():
                    source = Path(row["resolved_crop"])
                    destination = OUTPUT_DIR / split / label / source.name
                    shutil.copy2(source, destination)

        print("Severity dataset prepared successfully.")
        print(f"Output: {OUTPUT_DIR}")
        print("\nLabel counts by split:")
        print(
            labelled.groupby(["split", "severity_label"])
            .size()
            .unstack(fill_value=0)
            .to_string()
        )
        print(f"\nTotal labelled crops: {len(labelled)}")
        print("Uncertain and unlabelled crops were excluded.")

    except Exception:
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
