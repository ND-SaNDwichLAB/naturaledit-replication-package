import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# ===== CONFIGURATION =====
# Set to True to only download specific collections, False to download all
DOWNLOAD_SPECIFIC_ONLY = True

# If DOWNLOAD_SPECIFIC_ONLY is True, specify which collections to download
SPECIFIC_COLLECTIONS = [
    "naturaledit_interaction_2025_08_13",
    "pasta_interaction_2025_08_13",
]
# ========================

# 1. Initialize Firebase Admin SDK with your service account
cred = credentials.Certificate("naturaledit-study-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# 2. Create interactions folder if it doesn't exist
interactions_folder = "interactions"
if not os.path.exists(interactions_folder):
    os.makedirs(interactions_folder)
    print(f"Created folder: {interactions_folder}")

# 3. List all top-level collections
collections = db.collections()

for collection_ref in collections:
    collection_name = collection_ref.id

    # Skip collections that are not in the specific list if DOWNLOAD_SPECIFIC_ONLY is True
    if DOWNLOAD_SPECIFIC_ONLY:
        # Check if this collection should be downloaded
        should_download = False
        for target_collection in SPECIFIC_COLLECTIONS:
            if collection_name.startswith(target_collection):
                should_download = True
                break

        if not should_download:
            print(f"⏭️ Skipping collection: {collection_name} (not in target list)")
            continue

    print(f"Processing collection: {collection_name}")

    # 4. Download all documents in this collection
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        doc_dict = doc.to_dict()
        doc_dict["id"] = doc.id  # Keep Firestore document ID
        data.append(doc_dict)

    # 5. Sort data by timestamp if timestamp field exists
    if data and "timestamp" in data[0]:
        try:
            # Sort by timestamp in ascending order (oldest first)
            data.sort(key=lambda x: x.get("timestamp", ""), reverse=False)
            print(f"📅 Sorted {len(data)} documents by timestamp (oldest first)")
        except Exception as e:
            print(f"⚠️ Warning: Could not sort by timestamp: {e}")
    else:
        print(f"ℹ️ No timestamp field found in collection {collection_name}")

    # 6. Save each collection to a separate JSON file in the interactions folder
    output_filename = os.path.join(interactions_folder, f"{collection_name}.json")
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(data)} docs to {output_filename}")

print("All collections exported successfully to interactions folder.")
