
from pathlib import Path
import requests
import time
import re

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "potholes" / "negative_collection"

CATEGORIES = {
    "clean_roads": ["smooth asphalt road", "normal paved road"],
    "rural_gravel": ["rural gravel road", "dirt road landscape"],
    "wet_roads": ["wet asphalt road", "rain wet road reflections"],
    "shadows_patches": ["road tree shadows", "asphalt road sunlight shadows"],
}

API_URL = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": (
        "LegionersPotholeResearch/1.0 "
        "(educational pothole detection project; contact: developer@example.com)"
    )
}

def safe_name(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text)[:80]

def download_category(category, queries, target=25):
    folder = OUTPUT_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    existing = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
    count = len(existing)
    print(f"\n--- {category}: {count}/{target} images already present ---")

    if count >= target:
        print("Target reached; skipping.")
        return

    seen_titles = set()
    log_path = OUTPUT_DIR / "sources.tsv"

    for search_term in queries:
        if count >= target:
            break

        print(f"Searching: {search_term}")

        try:
            response = requests.get(
                API_URL,
                headers=HEADERS,
                params={
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srnamespace": 6,
                    "srsearch": search_term + " filetype:bitmap",
                    "srlimit": 50,
                },
                timeout=30,
            )
            response.raise_for_status()
            results = response.json().get("query", {}).get("search", [])
        except Exception as error:
            print("Search failed:", error)
            continue

        for result in results:
            if count >= target:
                break

            title = result.get("title", "")
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            try:
                detail = requests.get(
                    API_URL,
                    headers=HEADERS,
                    params={
                        "action": "query",
                        "format": "json",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url|mime|extmetadata",
                    },
                    timeout=30,
                )
                detail.raise_for_status()
                pages = detail.json().get("query", {}).get("pages", {})

                page = next(iter(pages.values()), {})
                info = page.get("imageinfo", [{}])[0]
                url = info.get("url", "")
                mime = info.get("mime", "")
                metadata = info.get("extmetadata", {})

                if mime not in ("image/jpeg", "image/png"):
                    continue
                if not url:
                    continue

                image_response = requests.get(url, headers=HEADERS, timeout=30)
                image_response.raise_for_status()

                if not image_response.headers.get("Content-Type", "").startswith("image/"):
                    continue

                extension = ".png" if mime == "image/png" else ".jpg"
                filename = folder / f"{category}_{count + 1:03d}{extension}"

                with open(filename, "wb") as file:
                    file.write(image_response.content)

                license_name = metadata.get("LicenseShortName", {}).get("value", "Unknown")
                author = metadata.get("Artist", {}).get("value", "Unknown")
                source_page = "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_")

                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(
                        f"{filename}\t{title}\t{source_page}\t"
                        f"{license_name}\t{author}\n"
                    )

                count += 1
                print(f"Saved {filename.name} | licence: {license_name}")
                time.sleep(0.4)

            except Exception as error:
                print(f"Skipped {title}: {error}")

    print(f"Finished {category}: {count}/{target} downloaded.")
    if count < target:
        print("More search terms or another source may be needed.")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for category, queries in CATEGORIES.items():
        download_category(category, queries)

    print("\nDownload attempt complete.")
    print("Inspect every image before using it as a negative training example.")
    print("No YOLO labels were created.")

if __name__ == "__main__":
    main()