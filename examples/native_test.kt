import android.content.Context
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import laith.runtime.*


fun fast_add(v_a: Int, v_b: Int): Int {
    val v_0 = v_a + v_b
    return v_0
}

@Composable
fun ui_entry(): Any? {
    val context = LocalContext.current
    val v_1 = 10
    val v_2 = 20
    val v_3 = NativeLib.fast_add(v_1, v_2)
    Column() {
        val v_4 = "Native result is 30"
        Text(v_4)
    }
}

fun scheduleLaithTasks(context: Context) {
}

object NativeLib {
    init {
        System.loadLibrary("laith-native")
    }

    external fun fast_add(a: Int, b: Int): Int
}
