package laith.runtime

import android.content.Context
import android.os.*
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import kotlin.coroutines.CoroutineContext
import android.location.Location
import android.location.LocationManager
import android.location.LocationListener

object LaithContext {
    var current: Context? = null
}

object PythonRuntime : CoroutineScope {
    private val job = Job()
    override val coroutineContext: CoroutineContext = Dispatchers.Main + job

    fun initialize() {
        // Initialization logic
    }

    fun shutdown() {
        job.cancel()
    }

    fun vibrate(context: Context?, ms: Long) {
        val ctx = context ?: LaithContext.current ?: return
        val vibrator = ctx.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(ms)
        }
    }

    fun hasPermission(context: Context?, permission: String): Boolean {
        val ctx = context ?: LaithContext.current ?: return false
        return ContextCompat.checkSelfPermission(ctx, permission) == PackageManager.PERMISSION_GRANTED
    }

    fun requestLocationPermission(context: Context?, callback: (Boolean) -> Unit) {
        try {
            val ctx = context ?: LaithContext.current ?: return
            val activity = ctx as? androidx.activity.ComponentActivity
            if (activity != null) {
                val cls = activity.javaClass
                val launcherField = cls.getDeclaredField("locationPermissionLauncher")
                launcherField.isAccessible = true
                val launcher = launcherField.get(null) as? androidx.activity.result.ActivityResultLauncher<Array<String>>
                
                val callbackField = cls.getDeclaredField("onPermissionResult")
                callbackField.isAccessible = true
                callbackField.set(null, callback)
                
                launcher?.launch(arrayOf(
                    "android.permission.ACCESS_FINE_LOCATION",
                    "android.permission.ACCESS_COARSE_LOCATION"
                ))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun getLastLocation(context: Context?, callback: (Double, Double) -> Unit) {
        val ctx = context ?: LaithContext.current ?: return
        val locationManager = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        try {
            val location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER) 
                ?: locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
            
            if (location != null) {
                callback(location.latitude, location.longitude)
            } else {
                locationManager.requestSingleUpdate(LocationManager.GPS_PROVIDER, object : LocationListener {
                    override fun onLocationChanged(l: Location) {
                        callback(l.latitude, l.longitude)
                    }
                    override fun onStatusChanged(p0: String?, p1: Int, p2: Bundle?) {}
                    override fun onProviderEnabled(p0: String) {}
                    override fun onProviderDisabled(p0: String) {}
                }, null)
            }
        } catch (e: SecurityException) {
            // Permission not granted
        }
    }
}

// Basic task interface
interface PythonTask {
    suspend fun run()
}
