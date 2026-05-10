package laith.runtime

import android.content.Context
import android.os.*
import kotlinx.coroutines.*
import kotlin.coroutines.CoroutineContext

object PythonRuntime : CoroutineScope {
    private val job = Job()
    override val coroutineContext: CoroutineContext = Dispatchers.Main + job

    fun initialize() {
        // Initialization logic
    }

    fun shutdown() {
        job.cancel()
    }

    fun vibrate(context: Context, ms: Long) {
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(ms)
        }
    }
}

// Basic task interface
interface PythonTask {
    suspend fun run()
}
