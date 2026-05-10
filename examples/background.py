@periodic_task(interval="1h")
async def sync_data():
    print("Syncing data...")
