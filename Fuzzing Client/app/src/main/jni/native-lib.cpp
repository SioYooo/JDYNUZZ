#include <jni.h>
#include <stdlib.h>
#include <android/log.h>
#include <string>
#define APPNAME "ATTACKER"

extern "C"
{
    void __llvm_profile_initialize_file(void);
    int __llvm_profile_write_file(void);
    int __llvm_profile_register_write_file_atexit(void);
//    void __llvm_gcov_flush(void);
}

//extern "C" void __llvm_gcov_flush();

extern "C"
JNIEXPORT jstring JNICALL
Java_com_example_fuzzer_HelloJNI_helloJNI(JNIEnv *env, jclass clazz) {
    // TODO: implement helloJNI()

// ----------------------------------------------------------------------
    // B    MB    GB
    // unsigned int 0 ~ 2^31-1  1024 * 1024 * 1024 * 2 = 2^31
//    int *p = (int *)malloc(1024 * 1024 * 1024 * 2 - 1);
//    __android_log_print(ANDROID_LOG_INFO, APPNAME, "指针地址为：%p\n", p);

// ----------------------------------------------------------------------
//    int *p1 = (int *)malloc(1024 * 1024 * 100);
//    if (p1 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 1);
//    }
//    int *p2 = (int *)malloc(1024 * 1024 * 100);
//    if (p2 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 2);
//    }
//    int *p3 = (int *)malloc(1024 * 1024 * 100);
//    if (p3 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 3);
//    }
//    int *p4 = (int *)malloc(1024 * 1024 * 100);
//    if (p4 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 4);
//    }
//    int *p5 = (int *)malloc(1024 * 1024 * 100);
//    if (p5 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 5);
//    }
//    int *p6 = (int *)malloc(1024 * 1024 * 100);
//    if (p6 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 6);
//    }
//    int *p7 = (int *)malloc(1024 * 1024 * 100);
//    if (p7 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 7);
//    }
//    int *p8 = (int *)malloc(1024 * 1024 * 100);
//    if (p8 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 8);
//    }
//    int *p9 = (int *)malloc(1024 * 1024 * 100);
//    if (p9 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 9);
//    }
//    int *p10 = (int *)malloc(1024 * 1024 * 100);
//    if (p10 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 10);
//    }
//    int *p11 = (int *)malloc(1024 * 1024 * 100);
//    if (p11 != NULL) {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "100M：%d\n", 11);
//    }
//    if (p == NULL){
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "内存申请失败");
//    } else {
//        __android_log_print(ANDROID_LOG_INFO, APPNAME, "内存申请成功");
//        free(p);
//        p = NULL;
//    }

// ----------------------------------------------------------------------
    // 栈溢出
//    int a [1024 * 1024 * 10 * 4];

// ----------------------------------------------------------------------

    return env->NewStringUTF("Hello From JNI!");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_example_fuzzer_HelloJNI_init(JNIEnv *env, jclass clazz) {
    setenv("LLVM_PROFILE_FILE", "/sdcard/Android/data/com.example.fuzzer/test%m.profraw", 1);
    __llvm_profile_initialize_file();
//    __llvm_profile_register_write_file_atexit();

    setenv("GCOV_PREFIX", "/sdcard/Android/data/com.example.fuzzer/gcda/", 1);
    setenv("GCOV_PREFIX_STRIP", "100", 1);
    __android_log_print(ANDROID_LOG_INFO, APPNAME, "版本标记:%s\n", "3.49");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_example_fuzzer_HelloJNI_dump(JNIEnv *env, jclass clazz) {
    __llvm_profile_write_file();
//    __llvm_gcov_flush();
}