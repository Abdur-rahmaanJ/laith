# Global channel for IPC
sync_channel = Channel()

@periodic_task(interval="10s")
async def background_sync():
    data = "new sync data"
    sync_channel.publish(data)

def ui_observer():
    # Collect updates from the background channel
    sync_channel.collect(lambda data: print(data))
    
    Column(
        Text("Listening for sync...")
    )
