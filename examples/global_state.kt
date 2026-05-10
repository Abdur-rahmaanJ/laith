import android.content.Context
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.flow.MutableStateFlow
import laith.runtime.*

val v_0 = 0
val v_1 = MutableStateFlow(v_0)

class Auto_incWorker(context: Context, params: WorkerParameters) : LaithWorker(context, params) {
    override suspend fun executePython() {
        auto_inc()
    }
}

suspend fun auto_inc(): Any? {
    val v_2 = v_1.value
    val v_3 = 1
    val v_4 = v_2 + v_3
    v_1.value = v_4
}

@Composable
fun counter_ui(): Any? {
    val context = LocalContext.current
    Column() {
        val v_5 = "Global Count:"
        Text(v_5)
        val v_6 = v_1.collectAsState().value
        Text(v_6)
        val v_8 = "Reset"
        Button(onClick = {
            val v_7 = 0
            v_1.value = v_7
        }) {
            Text(v_8)
        }
    }
}

fun scheduleLaithTasks(context: Context) {
    val constraints_auto_inc = Constraints.Builder()
        .build()
    val workRequest_auto_inc = PeriodicWorkRequestBuilder<Auto_incWorker>(5, TimeUnit.SECONDS)
        .setConstraints(constraints_auto_inc)
        .build()
    WorkManager.getInstance(context).enqueueUniquePeriodicWork("auto_inc", ExistingPeriodicWorkPolicy.KEEP, workRequest_auto_inc)
}
