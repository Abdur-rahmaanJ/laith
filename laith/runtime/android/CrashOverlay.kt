package laith.runtime

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.activity.ComponentActivity
import java.io.PrintWriter
import java.io.StringWriter

@Composable
fun CrashOverlay(content: @Composable () -> Unit) {
    var crash by remember { mutableStateOf<Throwable?>(null) }

    if (crash != null) {
        val context = LocalContext.current
        val activity = context as? ComponentActivity

        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF1A1A2E))
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.Top
        ) {
            Text(
                text = "CRASH",
                color = Color(0xFFFF4444),
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = crash!!.message ?: "Unknown error",
                color = Color(0xFFCCCCCC),
                fontSize = 16.sp
            )
            Spacer(modifier = Modifier.height(16.dp))
            val stackText = stackTraceToString(crash!!)
            Text(
                text = stackText,
                color = Color(0xFFAAAAAA),
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(24.dp))
            Button(
                onClick = {
                    crash = null
                    activity?.recreate()
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFFFF4444)
                )
            ) {
                Text("Reload App", fontSize = 18.sp)
            }
        }
    } else {
        Box(modifier = Modifier.fillMaxSize()) {
            try {
                content()
            } catch (e: Throwable) {
                crash = e
            }
        }
    }
}

private fun stackTraceToString(t: Throwable): String {
    val sw = StringWriter()
    val pw = PrintWriter(sw)
    t.printStackTrace(pw)
    pw.flush()
    return sw.toString()
}
