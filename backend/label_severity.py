
from pathlib import Path
import csv
import shutil
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

WORKFLOW_DIR = ROOT / "data" / "potholes" / "severity_workflow"
CROPS_DIR = WORKFLOW_DIR / "crops"

ANNOTATIONS_CSV = WORKFLOW_DIR / "severity_annotations.csv"
MANIFEST_CSV = WORKFLOW_DIR / "severity_manifest.csv"
BACKUP_CSV = WORKFLOW_DIR / "severity_annotations_backup.csv"

SEVERITY_LABELS = ["Low", "Medium", "High", "Uncertain"]

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

WINDOW_TITLE = "Legioners - Pothole Severity Annotation"
PREVIEW_SIZE = (800, 560)


# ============================================================
# CSV HELPERS
# ============================================================

def load_csv(path):
    if not path.exists():
        return []

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error) as exc:
        raise RuntimeError(f"Cannot read {path}:\n{exc}") from exc


def save_csv(path, rows):
    """
    Save annotations with a backup of the original CSV.
    Try an atomic replacement first, then fall back to a direct
    write if Windows denies the replacement operation.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    # Preserve the original file before the first modification.
    if path.exists() and not BACKUP_CSV.exists():
        shutil.copy2(path, BACKUP_CSV)

    try:
        # Write the complete CSV to a temporary file.
        with temporary.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    field: row.get(field, "")
                    for field in CSV_FIELDS
                })

        try:
            # Preferred method: replace the destination atomically.
            temporary.replace(path)

        except PermissionError:
            # Fallback: write directly to the destination.
            # If another program has locked the CSV, this will also
            # fail and the error will be shown to the user.
            with path.open("w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writeheader()

                for row in rows:
                    writer.writerow({
                        field: row.get(field, "")
                        for field in CSV_FIELDS
                    })

    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass


def resolve_crop_path(row):
    """Find a crop using its stored path or crop ID."""
    raw_path = (row.get("crop_path") or "").strip()
    candidates = []

    if raw_path:
        supplied = Path(raw_path)

        if supplied.is_absolute():
            candidates.append(supplied)
        else:
            candidates.extend([
                ROOT / supplied,
                WORKFLOW_DIR / supplied,
                CROPS_DIR / supplied.name,
            ])

    crop_id = (row.get("crop_id") or "").strip()

    if crop_id:
        candidates.extend(
            CROPS_DIR / f"{crop_id}{extension}"
            for extension in (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


# ============================================================
# LOAD AND VALIDATE ANNOTATIONS
# ============================================================

def prepare_rows():
    if not CROPS_DIR.is_dir():
        raise FileNotFoundError(
            f"Crop directory not found:\n{CROPS_DIR}\n\n"
            "Run prepare_severity_crops.py first."
        )

    if ANNOTATIONS_CSV.is_file():
        rows = load_csv(ANNOTATIONS_CSV)
    elif MANIFEST_CSV.is_file():
        rows = load_csv(MANIFEST_CSV)
    else:
        raise FileNotFoundError(
            "Neither severity_annotations.csv nor "
            f"severity_manifest.csv was found in:\n{WORKFLOW_DIR}"
        )

    if not rows:
        raise RuntimeError(f"No annotation rows found in:\n{WORKFLOW_DIR}")

    usable_rows = []
    missing_count = 0

    for row in rows:
        crop_path = resolve_crop_path(row)

        if crop_path is None:
            missing_count += 1
            continue

        row["crop_path"] = str(crop_path)
        row.setdefault("severity_label", "")
        row.setdefault("annotation_status", "pending")
        row.setdefault("annotator_notes", "")

        usable_rows.append(row)

    print("Project root:", ROOT)
    print("Crop directory:", CROPS_DIR)
    print("Annotation CSV:", ANNOTATIONS_CSV)
    print("Rows in CSV:", len(rows))
    print("Crops found:", len(usable_rows))
    print("Missing crops:", missing_count)

    if not usable_rows:
        raise RuntimeError(
            "No usable crops found. Check crop_path values and filenames."
        )

    return usable_rows


# ============================================================
# ANNOTATION GUI
# ============================================================

class SeverityAnnotator:

    def __init__(self, root, rows):
        self.root = root
        self.rows = rows
        self.index = self.find_first_unlabelled()
        self.current_photo = None
        self.busy = False

        self.root.title(WINDOW_TITLE)
        self.root.geometry("1000x850")
        self.root.minsize(760, 650)

        self.label_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.build_ui()
        self.show_current()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def find_first_unlabelled(self):
        for index, row in enumerate(self.rows):
            label = (row.get("severity_label") or "").strip()
            status = (row.get("annotation_status") or "").strip().lower()

            if label not in SEVERITY_LABELS or status == "pending":
                return index

        # All crops are labelled: start at the first crop.
        return 0

    def build_ui(self):
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Pothole Severity Annotation",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(0, 8))

        self.progress_label = ttk.Label(
            container,
            text="",
            font=("Segoe UI", 10),
        )
        self.progress_label.pack(pady=(0, 8))

        self.image_label = ttk.Label(
            container,
            text="Loading crop...",
            anchor="center",
        )
        self.image_label.pack(fill="both", expand=True, pady=8)

        self.info_label = ttk.Label(
            container,
            text="",
            justify="left",
            wraplength=900,
        )
        self.info_label.pack(fill="x", pady=5)

        severity_frame = ttk.LabelFrame(
            container,
            text="Choose severity — click to save and move to next crop",
            padding=10,
        )
        severity_frame.pack(fill="x", pady=8)

        self.label_var.set("")

        for label in SEVERITY_LABELS:
            ttk.Radiobutton(
                severity_frame,
                text=label,
                value=label,
                variable=self.label_var,
                command=self.on_severity_selected,
            ).pack(side="left", padx=12)

        notes_frame = ttk.Frame(container)
        notes_frame.pack(fill="x", pady=5)

        ttk.Label(notes_frame, text="Notes:").pack(side="left")

        self.notes_entry = ttk.Entry(
            notes_frame,
            textvariable=self.notes_var,
        )
        self.notes_entry.pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=10)

        ttk.Button(
            buttons,
            text="Previous",
            command=self.previous,
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Skip",
            command=self.skip,
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Save Label",
            command=self.save_current,
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Next",
            command=self.next,
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons,
            text="Save & Close",
            command=self.close,
        ).pack(side="right", padx=4)

        ttk.Label(
            container,
            text=(
                "Automatic mode: click Low, Medium, High, or Uncertain "
                "to save and advance. Previous and Skip do not save "
                "a new selection."
            ),
            foreground="gray",
            wraplength=900,
        ).pack(pady=(0, 3))

        self.status_label = ttk.Label(
            container,
            textvariable=self.status_var,
        )
        self.status_label.pack()

    def labelled_count(self):
        return sum(
            1 for row in self.rows
            if (row.get("severity_label") or "").strip() in SEVERITY_LABELS
        )

    def show_current(self):
        if not self.rows:
            return

        self.index = max(0, min(self.index, len(self.rows) - 1))
        row = self.rows[self.index]
        crop_path = Path(row["crop_path"])

        self.label_var.set(row.get("severity_label", ""))
        self.notes_var.set(row.get("annotator_notes", ""))

        try:
            with Image.open(crop_path) as image:
                image = image.convert("RGB")
                image.thumbnail(PREVIEW_SIZE)
                self.current_photo = ImageTk.PhotoImage(image)

            self.image_label.configure(
                image=self.current_photo,
                text="",
            )

        except Exception as exc:
            self.current_photo = None
            self.image_label.configure(
                image="",
                text=f"Could not load image:\n{crop_path}\n{exc}",
            )

        crop_id = row.get("crop_id", crop_path.stem)
        split = row.get("split", "unknown")
        current_label = row.get("severity_label", "") or "Unlabelled"

        self.info_label.configure(
            text=(
                f"Crop ID: {crop_id}\n"
                f"Split: {split}    |    Current label: {current_label}\n"
                f"Source image: {row.get('source_image', 'Unknown')}"
            )
        )

        self.progress_label.configure(
            text=(
                f"Crop {self.index + 1} of {len(self.rows)}"
                f"    |    Saved labels: {self.labelled_count()}"
                f"    |    Remaining: {len(self.rows) - self.labelled_count()}"
            )
        )

        self.status_var.set(f"Showing: {crop_id}")

    def save_current(self, show_message=True):
        row = self.rows[self.index]
        selected = self.label_var.get().strip()

        if selected not in SEVERITY_LABELS:
            messagebox.showwarning(
                "Choose a severity",
                "Select Low, Medium, High, or Uncertain before saving.",
                parent=self.root,
            )
            return False

        # Keep the previous values so they can be restored if saving fails.
        old_label = row.get("severity_label", "")
        old_status = row.get("annotation_status", "")
        old_notes = row.get("annotator_notes", "")

        row["severity_label"] = selected
        row["annotation_status"] = "annotated"
        row["annotator_notes"] = self.notes_var.get().strip()

        try:
            save_csv(ANNOTATIONS_CSV, self.rows)

        except (OSError, csv.Error, shutil.Error) as exc:
            row["severity_label"] = old_label
            row["annotation_status"] = old_status
            row["annotator_notes"] = old_notes

            messagebox.showerror(
                "Save failed",
                "Could not save your annotations:\n\n"
                f"{exc}\n\n"
                "Close Excel or any program using the CSV, then try again.",
                parent=self.root,
            )
            self.status_var.set("SAVE FAILED — still on this crop")
            return False

        self.progress_label.configure(
            text=(
                f"Crop {self.index + 1} of {len(self.rows)}"
                f"    |    Saved labels: {self.labelled_count()}"
                f"    |    Remaining: {len(self.rows) - self.labelled_count()}"
            )
        )

        self.status_var.set(f"Saved {selected}: {row['crop_id']}")

        if show_message:
            self.root.bell()

        return True

    def on_severity_selected(self):
        """Save the selected class and advance only after a successful save."""
        if self.busy:
            return

        self.busy = True
        try:
            if self.save_current(show_message=False):
                self.next()
        finally:
            self.busy = False

    def next(self):
        if self.index < len(self.rows) - 1:
            self.index += 1
            self.show_current()
        else:
            self.status_var.set("All crops reached — you are at the final crop.")
            messagebox.showinfo(
                "End reached",
                "You are at the final crop.",
                parent=self.root,
            )

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self.show_current()
        else:
            messagebox.showinfo(
                "Beginning",
                "You are at the first crop.",
                parent=self.root,
            )

    def skip(self):
        # Skip advances without assigning a new label.
        self.next()

    def close(self):
        try:
            save_csv(ANNOTATIONS_CSV, self.rows)
        except (OSError, csv.Error, shutil.Error) as exc:
            if not messagebox.askyesno(
                "Save failed",
                f"Could not save the CSV:\n{exc}\n\nClose anyway?",
                parent=self.root,
            ):
                return

        self.root.destroy()


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    try:
        rows = prepare_rows()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror("Annotation error", str(exc))
            error_root.destroy()
        except Exception:
            pass
        raise SystemExit(1)

    app_root = tk.Tk()
    SeverityAnnotator(app_root, rows)
    app_root.mainloop()


if __name__ == "__main__":
    main()
