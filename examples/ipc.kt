import android.content.Context
import androidx.compose.runtime.*
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import laith.runtime.*

val v_0 = MutableSharedFlow<Any>()

class Background_syncWorker(context: Context, params: WorkerParameters) : LaithWorker(context, params) {
    override suspend fun executePython() {
        background_sync()
    }
}

suspend fun background_sync(): Any? {
    val v_1 = "new sync data"
    CoroutineScope(Dispatchers.Default).launch { v_0.emit(v_1) }
}

fun ui_observer(): Any? {
    CoroutineScope(Dispatchers.Main).launch {
        v_0.collect { v_data -> 
            val v_2 = print(v_data)
        }
    }
    Column() {
        val v_3 = "Listening for sync..."
        Text(v_3)
    }
}

fun scheduleLaithTasks(context: Context) {
    val constraints_background_sync = Constraints.Builder()
        .build()
    val workRequest_background_sync = PeriodicWorkRequestBuilder<Background_syncWorker>(10, TimeUnit.SECONDS)
        .setConstraints(constraints_background_sync)
        .build()
    WorkManager.getInstance(context).enqueueUniquePeriodicWork("background_sync", ExistingPeriodicWorkPolicy.KEEP, workRequest_background_sync)
}
