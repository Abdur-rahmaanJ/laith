package laith.runtime

import android.app.Notification
import android.app.Service
import android.content.Intent
import android.os.IBinder
import kotlinx.coroutines.*

abstract class LaithService : Service() {
    protected val serviceScope = CoroutineScope(Dispatchers.Default + Job())

    abstract suspend fun executePython()
    abstract fun createNotification(): Notification

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(1, notification)
        
        serviceScope.launch {
            executePython()
        }
        
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }
}
