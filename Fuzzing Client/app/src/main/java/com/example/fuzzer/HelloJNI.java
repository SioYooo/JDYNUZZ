package com.example.fuzzer;

public class HelloJNI {

    static {
        System.loadLibrary("native-lib");
    }

    public static native String helloJNI();

    public static native void init();

    public static native void dump();

}
