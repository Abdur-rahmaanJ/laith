package laith.runtime

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

abstract class LaithWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {
    
    // This will be overridden by generated code to call the Python function
    abstract suspend fun executePython()

    override suspend fun doWork(): Result {
        return try {
            executePython()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
