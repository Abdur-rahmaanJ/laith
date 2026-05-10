import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import laith.runtime.*


class TrackerService : LaithService() {
    override suspend fun executePython() {
        tracker()
    }
    override fun createNotification(): Notification {
        val channelId = "tracker_channel"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "tracker Service"
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(channelId, name, importance)
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
        return NotificationCompat.Builder(this, channelId)
            .setContentTitle("Laith App")
            .setContentText("Tracker")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .build()
    }
}

suspend fun tracker(): Any? {
    val v_0 = "Tracking..."
    val v_1 = print(v_0)
}

@Composable
fun ui(): Any? {
    val context = LocalContext.current
    Column() {
        val v_2 = "Start"
        Button(onClick = {
            val intent_tracker = Intent(context, TrackerService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent_tracker)
            } else {
                context.startService(intent_tracker)
            }
        }) {
            Text(v_2)
        }
        val v_3 = "Stop"
        Button(onClick = {
            val intent_tracker = Intent(context, TrackerService::class.java)
            context.stopService(intent_tracker)
        }) {
            Text(v_3)
        }
    }
}
