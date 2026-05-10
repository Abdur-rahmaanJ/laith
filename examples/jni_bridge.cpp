#include <jni.h>
#include <string>
extern "C" {

JNIEXPORT jlong JNICALL
Java_com_example_laithapp_NativeLib_fast_add(JNIEnv* env, jobject thiz, jlong a, jlong b) {
    // Bridge to C++ implementation
    extern jlong fast_add(jlong, jlong);
    return fast_add(a, b);
}

}