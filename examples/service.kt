import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import androidx.compose.runtime.*
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import laith.runtime.*


class Track_locationService : LaithService() {
    override suspend fun executePython() {
        track_location()
    }
    override fun createNotification(): Notification {
        val channelId = "track_location_channel"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "track_location Service"
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(channelId, name, importance)
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
        return NotificationCompat.Builder(this, channelId)
            .setContentTitle("Laith App")
            .setContentText("Tracking GPS")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .build()
    }
}

suspend fun track_location(): Any? {
    val v_0 = "Tracking..."
    val v_1 = print(v_0)
}
