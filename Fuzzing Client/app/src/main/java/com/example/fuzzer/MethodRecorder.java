package com.example.fuzzer;

public class MethodRecorder implements java.io.Serializable{
    String className;
    String methodName;
    Object[] parVals;
    String pars;
    String res;
    ObjectRecorder clazzObj =null;
}
