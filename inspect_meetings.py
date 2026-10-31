from meeting_store import collection

for meeting_id in [
    "0eb179c9-bfc1-4010-af4f-5a0aa77a915f",
    "8730103d-21c4-47cd-b492-afb2287d17e0",
    "e3b434e0-4679-4a63-a7e8-7042465726e3",
]:
    result = collection.get(
        ids=[meeting_id],
        include=["documents", "metadatas"],
    )

    if result["ids"]:
        print("\n" + "=" * 60)
        print("ID:", result["ids"][0])
        print("TITLE:", result["metadatas"][0].get("title"))
        print(result["documents"][0][:1200])
