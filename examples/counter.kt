import androidx.compose.runtime.*
import kotlinx.coroutines.*
import laith.runtime.*

fun counter_ui(): Any? {
    val v_0 = 0
    val v_1 = remember { mutableStateOf(v_0) }
    Column() {
        val v_2 = "Current count:"
        Text(v_2)
        val v_3 = v_1.value
        Text(v_3)
        val v_7 = "Increment"
        Button(onClick = {
            val v_4 = v_1.value
            val v_5 = 1
            val v_6 = v_4 + v_5
            v_1.value = v_6
        }) {
        }
    }
}
