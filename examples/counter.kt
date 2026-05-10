import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import laith.runtime.*

val v_11 = AppState().apply { __init__() }

class AppState {
    fun __init__(): Unit {
        val v_self = this
        val v_0 = 0
        val v_1 = remember { mutableStateOf(v_0) }
        v_self.count = v_1
    }
    fun increment(): Unit {
        val v_self = this
        val v_2 = v_self.count
        val v_3 = v_self.count
        val v_4 = v_3.value
        val v_5 = 1
        val v_6 = v_4 + v_5
        val v_7 = v_2.set(v_6)
    }
    fun reset(): Unit {
        val v_self = this
        val v_8 = v_self.count
        val v_9 = 0
        val v_10 = v_8.set(v_9)
    }
}

@Composable
fun main_ui(): Unit {
    val context = LocalContext.current
    Column() {
        val v_12 = "Object-Oriented Counter"
        Text(v_12)
        val v_13 = "Count: "
        val v_14 = v_11.count
        val v_15 = v_14.value
        val v_16 = v_13 + v_15
        Text(v_16)
        val v_18 = "Increment"
        Button(onClick = {
            val v_17 = v_11.increment()
        }) {
            Text(v_18)
        }
        val v_20 = "Reset"
        Button(onClick = {
            val v_19 = v_11.reset()
        }) {
            Text(v_20)
        }
    }
}

fun scheduleLaithTasks(context: Context) {
}
