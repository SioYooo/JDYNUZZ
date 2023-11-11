package com.example.fuzzer;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Bundle;

import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.snackbar.Snackbar;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.core.app.ActivityCompat;

import android.os.Environment;
import android.system.ErrnoException;
import android.system.Os;
import android.util.Log;
import android.view.View;

import android.view.Menu;
import android.view.MenuItem;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.lang.reflect.Array;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.TreeSet;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import static android.app.PendingIntent.getActivity;
import static java.lang.System.exit;
import static java.lang.Thread.sleep;
import com.alibaba.fastjson.JSON;

public class MainActivity extends AppCompatActivity {


    private static final String TAG = "MainActivity";
    private static PrintWriter writer;
    private static boolean PROVIDE_VALUES = false;
    private static String objFileName = null;
    // private static String DCIM_PATH = "/sdcard/Android/data/com.example.fuzzer/files/DCIM";
    // DCIM_PATH for emulator
    private static String DCIM_PATH = "/storage/emulated/0/Android/data/com.example.fuzzer/files/DCIM";


    protected String handleStr() {
        return "";
    }

    protected int randomInt(Random r){
        int res = 0;
        int switcher = r.nextInt(4);
        switch (switcher) {
            case 0:
                res = r.nextInt(Integer.MAX_VALUE) - Integer.MAX_VALUE + r.nextInt(Integer.MAX_VALUE);
                break;
            case 1:
                res = r.nextInt(20) - 10;
                break;
            case 2:
                res = Integer.MAX_VALUE;
                break;
            case 3:
                res = Integer.MIN_VALUE;
                break;
        }
        return res;
    }

    protected int handleInt() {
        Random r = new Random();
        int res = randomInt(r);
        return res;
    }

    protected int[] handleIntA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int[] res = new int[x];
        for (int i = 0; i < x; i++) {
            res[i] = randomInt(r);
        }
        return res;
    }

    protected int[][] handleIntAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        int[][] res = new int[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = randomInt(r);
            }
        }
        return res;
    }

    protected boolean handleBoolean() {
        Random r = new Random();
        int res = r.nextInt(2);
        return res != 0;
    }

    protected boolean[] handleBooleanA() {
        Random r = new Random();
        int x = r.nextInt(6);
        boolean[] res = new boolean[x];
        for (int i = 0; i < x; i++) {
            res[i] = (r.nextInt(2) != 0);
        }
        return res;
    }

    protected boolean[][] handleBooleanAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        boolean[][] res = new boolean[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = (r.nextInt(2) != 0);
            }
        }
        return res;
    }

    protected byte handleByte() {
        Random r = new Random();
        byte[] arr = new byte[2];
        r.nextBytes(arr);
        return arr[0];
    }

    protected byte[] handleByteA() {
        Random r = new Random();
        int x = r.nextInt(6);
        byte[] arr = new byte[x];
        r.nextBytes(arr);
        return arr;
    }

    protected byte[][] handleByteAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        byte[][] res = new byte[x][y];
        for (int i = 0; i < x; i++) {
            r.nextBytes(res[i]);
        }
        return res;
    }

    public static String getRandomString(int length){
        String str="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        Random random=new Random();
        StringBuffer sb=new StringBuffer();
        for(int i=0;i<length;i++){
            int number=random.nextInt(62);
            sb.append(str.charAt(number));
        }
        return sb.toString();
    }

    protected String handleString() {
        Random r = new Random();
        String res = getRandomString(r.nextInt(2) + 1);
        return res;
    }

    protected String[] handleStringA() {
        Random r = new Random();
        int x = r.nextInt(6);
        String[] res = new String[x];
        for (int i = 0; i < x; i++) {
            res[i] = getRandomString(r.nextInt(2) + 1);
        }
        return res;
    }

    protected String[][] handleStringAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        String[][] res = new String[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = getRandomString(r.nextInt(2) + 1);
            }
        }
        return res;
    }

    protected void handleParameter(String tem, MethodRecorder methRec4Save, int i_par, Object[] valArr, Object[] valArrRecord) throws ClassNotFoundException {
//        System.out.println("* 14 Arrays.toString(valArrRecord): " + Arrays.toString(valArrRecord));
        tem = tem.replace("class ","");
        String pattern = "\\[{0,2}[ZBSCIJFD]";
        if(Pattern.matches(pattern, tem))
            tem = transformType(tem);
        Object res = null;
        switch (tem) {
            case "boolean":

                if (!PROVIDE_VALUES){
                    res =  handleBoolean();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }

                break;
            case "boolean[]":

                if (!PROVIDE_VALUES){
                    res =  handleBooleanA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "boolean[][]":
                if (!PROVIDE_VALUES){
                    res =  handleBooleanAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "byte":
                if (!PROVIDE_VALUES){
                    res =  handleByte();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "byte[]":

                if (!PROVIDE_VALUES){
                    res =  handleByteA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "byte[][]":

                if (!PROVIDE_VALUES){
                    res =  handleByteAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "short":

                if (!PROVIDE_VALUES){
                    res =  handleShort();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }
                break;
            case "short[]":
                if (!PROVIDE_VALUES){
                    res =  handleShortA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "short[][]":
                if (!PROVIDE_VALUES){
                    res =  handleShortAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "char":

                if (!PROVIDE_VALUES){
                    res =  handleChar();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "char[]":

                if (!PROVIDE_VALUES){
                    res =  handleCharA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "char[][]":

                if (!PROVIDE_VALUES){
                    res =  handleCharAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "int":

                if (!PROVIDE_VALUES){
                    res =  handleInt();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "int[]":

                if (!PROVIDE_VALUES){
                    res =  handleIntA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "int[][]":

                if (!PROVIDE_VALUES){
                    res =  handleIntAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "long":

                if (!PROVIDE_VALUES){
                    res =  handleLong();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "long[]":

                if (!PROVIDE_VALUES){
                    res =  handleLongA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "long[][]":

                if (!PROVIDE_VALUES){
                    res =  handleLongAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "float":

                if (!PROVIDE_VALUES){
                    res =  handleFloat();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "float[]":

                if (!PROVIDE_VALUES){
                    res =  handleFloatA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "float[][]":

                if (!PROVIDE_VALUES){
                    res =  handleFloatAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "double":

                if (!PROVIDE_VALUES){
                    res =  handleDouble();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "double[]":
                if (!PROVIDE_VALUES){
                    res =  handleDoubleA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "double[][]":

                if (!PROVIDE_VALUES){
                    res =  handleDoubleAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "java.lang.String":

                if (!PROVIDE_VALUES){
                    res =  handleString();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "java.lang.String[]":

                if (!PROVIDE_VALUES){
                    res =  handleStringA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            case "java.lang.String[][]":

                if (!PROVIDE_VALUES){
                    res =  handleStringAA();
                    valArr[i_par] = res;
                    valArrRecord[i_par] = res;
                }else{
                    valArr[i_par] = valArrRecord[i_par];
                }                break;
            default:

                res = null;
                if (!PROVIDE_VALUES) {
                    valArrRecord[i_par] = new ObjectRecorder();
                }
                System.out.println("475 valArrRecord[i_par]==null: " + (valArrRecord[i_par]==null));
                while(res==null) {
//                    obj_num_attempts++;
                    System.out.println(".line 268 obj is null");
                    System.out.println("invoke handleObject in line 311");
                    res = handleObject(tem, (ObjectRecorder) valArrRecord[i_par], methRec4Save);
                    System.out.println("478 valArrRecord[i_par]==null: " + (valArrRecord[i_par]==null));
                }
                if(res instanceof String && res.equals("NoConstructor")){
                    res = null;
                }

                valArr[i_par] = res;

                if(tem.endsWith("[][]")){
                    int x = -1;
                    int y = -1;
                    if (!PROVIDE_VALUES){
                        Random r = new Random();
                        x = r.nextInt(5) + 1 ;
                        y = r.nextInt(5) + 1 ;
                        ((ObjectRecorder)valArrRecord[i_par]).x=x;
                        ((ObjectRecorder)valArrRecord[i_par]).y=y;
                    }else{
                        x = ((ObjectRecorder)valArrRecord[i_par]).x;
                        y = ((ObjectRecorder)valArrRecord[i_par]).y;
                    }
                    Class theClassX = Class.forName(tem);
                    Class theClassY = Class.forName("[L"+tem+";");
//                    Object[][] resArr = new Object[x][y];
                    Object resArrX = Array.newInstance(theClassX, x);
                    Object resArrY = Array.newInstance(theClassY, y);
                    for (int i = 0; i < x; i++) {
                        Array.set(resArrX, i, res);
                    }
                    for (int j = 0; j < y; j++) {
                        Array.set(resArrY, j, resArrX);
                    }

                    res = resArrY;
                    valArr[i_par] = res;
                }else if(tem.endsWith("[]")){
                    int x = -1;
                    if (!PROVIDE_VALUES) {
                        Random r = new Random();
                        x = r.nextInt(5) + 1;
                        ((ObjectRecorder)valArrRecord[i_par]).x=x;
                    }else{
                        x = ((ObjectRecorder)valArrRecord[i_par]).x;
                    }
                    Class theClass = Class.forName(tem);
                    Object resArr = Array.newInstance(theClass, x);
//                    Object[] resArr = new Object[x];
                    for (int i = 0; i < x; i++) {
                        Array.set(resArr, i, res);
//                        resArr[i] = res;
                    }

                    res = resArr;
                    valArr[i_par] = res;
                }
        }

    }

    protected Object handleObject(String tem, ObjectRecorder objRec, MethodRecorder methRec4Save) throws ClassNotFoundException {
        Object res = null;
        System.out.println("| 可能是对象类型: " + tem);
        Class sClass = Class.forName(tem);
        if (!PROVIDE_VALUES)objRec.objName = tem;
        System.out.println("| sClass: " + sClass);
        Constructor<?>[] cons = sClass.getDeclaredConstructors();
        System.out.println("| cons.length: " + cons.length);
        if(cons.length!=0) {
            Constructor con = null;
            if (!PROVIDE_VALUES){
                int MIN = 0;
                int MAX = cons.length - 1;
                int randIndex = new Random().nextInt(MAX - MIN + 1) + MIN;
                objRec.constructorIndex = randIndex;
                System.out.println("552 存储的constructorIndex: " + objRec.constructorIndex);
                con = cons[randIndex];
            }else{
                System.out.println("561 提取到的constructorIndex: " + objRec.constructorIndex);
                con = cons[objRec.constructorIndex];
            }

            try {
                con.setAccessible(true);
            }catch(SecurityException e){
                e.printStackTrace();
            }

            Class[] pars = con.getParameterTypes();
//            System.out.println("| " + con.getName() + "'s pars: " + Arrays.deepToString(pars));
            System.out.println("| ========= ");
            Object[] valArr = new Object[pars.length];
            if (!PROVIDE_VALUES) objRec.valArrRecord = new Object[pars.length];
            int i = -1;
            for (Class par : pars) {
                i++;
                System.out.println("| par: " + par.getName());
                handleParameter(par.getName(), methRec4Save, i, valArr, objRec.valArrRecord);
            }

            try {
//                System.out.println("使用 构造函数 " + con + " 和参数 " + Arrays.deepToString(valArr) + " 创建了对象 " + tem);
                if(!PROVIDE_VALUES){
                    System.out.println("invoke saveMethodRecorder in line 424");
                    saveMethodRecorder(methRec4Save);
                }
                res = con.newInstance(valArr);
                System.out.println("创建完成");
            } catch (IllegalAccessException e) {
                e.printStackTrace();
            } catch (InstantiationException e) {
                e.printStackTrace();
            } catch (InvocationTargetException e) {
                e.printStackTrace();
            }
        }else{
            return "NoConstructor";
        }
        return res;
    }

    protected String transformType(String input) {
        System.out.println("转换前: " + input);
        int array = 0;
        String res = "";
        while(input.length() > 0) {
            if(input.startsWith("[")){
                array++;
                input = input.substring(1, input.length());
            }else if(input.startsWith("Z")){
                res = "boolean";
                if(array==1){
                    res = "boolean[]";
                    array = 0;
                }else if (array==2){
                    res = "boolean[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("B")){
                res = "byte";
                if(array==1){
                    res = "byte[]";
                    array = 0;
                }else if (array==2){
                    res = "byte[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("S")){
                res = "short";
                if(array==1){
                    res = "short[]";
                    array = 0;
                }else if (array==2){
                    res = "short[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("C")){
                res = "char";
                if(array==1){
                    res = "char[]";
                    array = 0;
                }else if (array==2){
                    res = "char[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("I")){
                res = "int";
                if(array==1){
                    res = "int[]";
                    array = 0;
                }else if (array==2){
                    res = "boolean[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("J")){
                res = "long";
                if(array==1){
                    res = "long[]";
                    array = 0;
                }else if (array==2){
                    res = "long[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("F")){
                res = "float";
                if(array==1){
                    res = "float[]";
                    array = 0;
                }else if (array==2){
                    res = "float[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }else if(input.startsWith("D")){
                res = "double";
                if(array==1){
                    res = "double[]";
                    array = 0;
                }else if (array==2){
                    res = "double[][]";
                    array = 0;
                }
                input = input.substring(1, input.length());
            }
        }
        System.out.println("转换后: " + res);
        return res;
    }

    protected short randomShort(Random r){
        short res = 0;
        int switcher = r.nextInt(4);
        switch (switcher) {
            case 0:
                res = (short)(r.nextInt(Short.MAX_VALUE) - Short.MAX_VALUE + r.nextInt(Short.MAX_VALUE));
                break;
            case 1:
                res = (short)(r.nextInt(20) - 10);
                break;
            case 2:
                res = Short.MAX_VALUE;
                break;
            case 3:
                res = Short.MIN_VALUE;
                break;
        }
        return res;
    }

    protected short handleShort() {
        return randomShort(new Random());
    }

    protected short[] handleShortA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        short[] res = new short[x];
        for (int i = 0; i < x; i++) {
            res[i] = randomShort(r);
        }
        return res;
    }

    protected short[][] handleShortAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        short[][] res = new short[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = randomShort(r);
            }
        }
        return res;
    }

    public static char getRandomCharacter(char ch1, char ch2) {
        return (char)(ch1 + Math.random() * (ch2 - ch1 + 1));
    }

    public static char getRandomCharacter() {
        return getRandomCharacter('\u0000', '\uFFFF');
    }

    protected char handleChar() {
        Random r = new Random();
        char res = getRandomCharacter();
        return res;
    }

    protected char[] handleCharA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        char[] res = new char[x];
        for (int i = 0; i < x; i++) {
            res[i] = getRandomCharacter();
        }
        return res;
    }

    protected char[][] handleCharAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        char[][] res = new char[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = getRandomCharacter();
            }
        }
        return res;
    }

    protected long randromLong(Random r){
        long res = 0;
        int switcher = r.nextInt(4);
        switch (switcher) {
            case 0:
                res = r.nextLong();
                break;
            case 1:
                res = (long)(r.nextInt(20) - 10);
                break;
            case 2:
                res = Long.MAX_VALUE;
                break;
            case 3:
                res = Long.MIN_VALUE;
                break;
        }
        return res;
    }

    protected long handleLong() {
        Random r = new Random();
        long res = randromLong(r);
        return res;
    }

    protected long[] handleLongA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        long[] res = new long[x];
        for (int i = 0; i < x; i++) {
            res[i] = randromLong(r);
        }
        return res;
    }

    protected long[][] handleLongAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        long[][] res = new long[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = randromLong(r);
            }
        }
        return res;
    }


    protected float handleFloat() {
        Random r = new Random();
        float res = r.nextFloat();
        return res;
    }

    protected float[] handleFloatA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        float[] res = new float[x];
        for (int i = 0; i < x; i++) {
            res[i] = r.nextFloat();
        }
        return res;
    }

    protected float[][] handleFloatAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        float[][] res = new float[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = r.nextFloat();
            }
        }
        return res;
    }

    protected double handleDouble() {
        Random r = new Random();
        double res = r.nextDouble();
        return res;
    }

    protected double[] handleDoubleA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        double[] res = new double[x];
        for (int i = 0; i < x; i++) {
            res[i] = r.nextDouble();
        }
        return res;
    }

    protected double[][] handleDoubleAA() {
        Random r = new Random();
        int x = r.nextInt(5) + 1 ;
        int y = r.nextInt(5) + 1 ;
        double[][] res = new double[x][y];
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                res[i][j] = r.nextDouble();
            }
        }
        return res;
    }

    protected int[] object4ana(String tem) {
//        System.out.println("转换前：" + tem);
        // Lpackage/name/ObjectName
//        tem = "L" + tem.replace(".", "/");
//        System.out.println("转换后：" + tem);
        int[] res = new int[]{0,0,0}; // # constructor, # constructors that have object, # no object
        Class sClass = null;
        try {
            sClass = Class.forName(tem);
            Constructor<?>[] cons = sClass.getDeclaredConstructors();
            res[0] = cons.length;
            if (cons.length != 0) {
                Constructor con = null;
                int MAX = cons.length;
                for (int i = 0; i < MAX; i++) {
                    con = cons[i];

                    Class[] pars = con.getParameterTypes();
                    boolean hasObj = false;
                    for (Class par : pars) {
                        String parName = par.getName();
                        if (isObject(parName)) {
                            hasObj = true;
                        }
                    }
                    if (hasObj) {
                        res[1]++;
                    } else {
                        res[2]++;
                    }
                }
            }
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }

        return res;
    }

    protected boolean isObject(String tem) {
        switch (tem) {
            case "boolean":

                break;
            case "boolean[]":

                break;
            case "boolean[][]":

                break;
            case "byte":

                break;
            case "byte[]":

                break;
            case "byte[][]":

                break;
            case "short":

                break;
            case "short[]":

                break;
            case "short[][]":

                break;
            case "char":

                break;
            case "char[]":

                break;
            case "char[][]":

                break;
            case "int":

                break;
            case "int[]":

                break;
            case "int[][]":

                break;
            case "long":

                break;
            case "long[]":

                break;
            case "long[][]":

                break;
            case "float":

                break;
            case "float[]":

                break;
            case "float[][]":

                break;
            case "double":

                break;
            case "double[]":

                break;
            case "double[][]":

                break;
//                    case "java.lang.String":
//
//                        break;
//                    case "java.lang.String[]":
//
//                        break;
//                    case "java.lang.String[][]":
//
//                        break;
            default:
//                        System.out.println("non-basic-var");
                return true;
        }
        return false;
    }
    protected String calPercen(int a, int b){
        return Math.round((float)a/(float)b * 10000f)/100f + "\\%";
    }
    protected void forAnalysis() throws IOException {
        InputStreamReader inputReader = new InputStreamReader(getResources().getAssets().open("jni_with_isStatic.json"));
        BufferedReader bufReader = new BufferedReader(inputReader);
        String txt = bufReader.readLine();
        bufReader.close();

        List<JniClass> JniClasses = JSON.parseArray(txt, JniClass.class);

        int total = JniClasses.size() - 3;

        Map<String, Integer> api_freq_in_class = new HashMap();
        Map<String, Integer> obj_freq = new HashMap();

        TreeSet<String> objs = new TreeSet<>();
        ArrayList<String> objs_all = new ArrayList<>();
        ArrayList<JniClass> api_has_obj = new ArrayList<>();
        ArrayList<JniClass> api_no_obj = new ArrayList<>();

        for (JniClass jni : JniClasses) {
            List<String> parameters = jni.getParameters();
            String class_ = jni.getClass_();
            if(api_freq_in_class.containsKey(class_)) {
                api_freq_in_class.replace(class_, api_freq_in_class.get(class_) + 1);
            }else{
                api_freq_in_class.put(class_, 1);
            }

            boolean hasObj = false;
            for (String tem_ : parameters) {
                String tem = tem_.trim();
                if(tem.isEmpty())
                    continue;
                if(isObject(tem)){
                    tem = tem.replace("[]","");
                    objs.add(tem);
                    objs_all.add(tem);
                    hasObj = true;

                    if(obj_freq.containsKey(tem)) {
                        obj_freq.replace(tem, obj_freq.get(tem) + 1);
                    }else{
                        obj_freq.put(tem, 1);
                    }
                }
            }
            if(hasObj){
                api_has_obj.add(jni);
            }else{
                api_no_obj.add(jni);
            }
        }

        List<Map.Entry<String, Integer>> list = new ArrayList<>(api_freq_in_class.entrySet());
        list.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        // 前10
        list = list.subList(0, 10);
        System.out.println("===== class中API个数前十 =====");
        list.forEach(System.out::println);

        List<Map.Entry<String, Integer>> list2 = new ArrayList<>(obj_freq.entrySet());
        list2.sort(Collections.reverseOrder(Map.Entry.comparingByValue()));
        // 前10
        list2 = list2.subList(0, 10);
        System.out.println("===== 对象出现频率前十 =====");
        list2.forEach(System.out::println);

        System.out.println("总对象个数：" + objs_all.size());
        System.out.println("去重后，对象个数：" + objs.size());
        System.out.println("总API = " + total);
        System.out.println("有对象的API：" + api_has_obj.size());
        System.out.println("无对象的API：" + api_no_obj.size());

        int t_n_constor = 0;
        int t_n_constor_obj = 0;
        int t_n_constor_no_obj = 0;

        for (String obj : objs){
            int[] res = object4ana(obj);
            // # constructor, # constructors that have object, # no object
            int n_constor = res[0];
            int n_constor_obj = res[1];
            int n_constor_no_obj = res[2];
            t_n_constor = t_n_constor + n_constor;
            t_n_constor_obj = t_n_constor_obj + n_constor_obj;
            t_n_constor_no_obj = t_n_constor_no_obj + n_constor_no_obj;
        }


        System.out.println("平均每个对象的构造函数个数" + (float)t_n_constor / (float)objs.size());
        System.out.println("平均每个对象的构造函数个数（有对象）" + (float)t_n_constor_obj / (float)objs.size());
        System.out.println("平均每个对象的构造函数个数（无对象）" + (float)t_n_constor_no_obj / (float)objs.size());

        System.out.println("构造函数个数/百分比（有对象）" + t_n_constor_obj + "/" + calPercen(t_n_constor_obj, t_n_constor));
        System.out.println("构造函数个数/百分比（无对象）" + t_n_constor_no_obj + "/" + calPercen(t_n_constor_no_obj, t_n_constor));
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        FloatingActionButton fab = findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
                        .setAction("Action", null).show();
            }
        });

        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(getApplicationContext(),"没有权限,请手动开启存储权限",Toast.LENGTH_SHORT).show();
            ActivityCompat.requestPermissions(MainActivity.this,new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 100);
        }

        String string = HelloJNI.helloJNI();
        try {
            Os.setenv("GCOV_PREFIX", "/sdcard/Android/data/com.example.fuzzer/gcda/", true);
            Os.setenv("GCOV_PREFIX_STRIP", "10", true);
        } catch (ErrnoException e) {
            e.printStackTrace();
        }
        Log.e("JNI_OUT_PUT", string);
        // 输出完整的 DCIM 路径
        //Log.e("Path", Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM).getAbsolutePath());
        Log.e("DCIM_PATH", getApplicationContext().getExternalFilesDir(Environment.DIRECTORY_DCIM).getAbsolutePath());

        // run server, normal mode
        new Thread(serverRun).start();

        // debug mode, get info
//        try {
//            forAnalysis();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }


    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            new Thread(clientRun).start();
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    public Object[] list2Arr(List<Object> parRecList){
        Object[] parRecArr = new Object[parRecList.size()];
            int index = -1;
            for (Object tem : parRecList) {
                index = index + 1;
                parRecArr[index] = tem;
            }
        return parRecArr;
    }

    public int process(String className, String methodName, String pars, String res, MethodRecorder methRec) throws ClassNotFoundException, InstantiationException, IllegalAccessException {
        objFileName = System.currentTimeMillis() + "";
        // message 1
        writer.println("fileName: "+objFileName +".obj");

        if(!pars.isEmpty()) {
            Object[] parRecList = null;


            // init
            String[] list = pars.split(",");

            Class[] parList = new Class[list.length];
            Object[] valList = new Object[list.length];

            if(PROVIDE_VALUES) {
                parRecList = methRec.parVals;
                System.out.println(" * 948 parVals.length: " + parRecList.length);
            }else{
                parRecList = new Object[list.length];
                methRec.className = className;
                methRec.methodName = methodName;
                methRec.parVals = parRecList;
                methRec.pars = pars;
                methRec.res = res;
            }



            int i_par = -1;
            // for to handle
            for (String tem_ : list) {
                i_par++;
                String tem = tem_.trim();
                System.out.println("972 第" + i_par + "个参数:" + parRecList[i_par]);
                System.out.println("973 parVals[i_par]==null: " + (parRecList[i_par]==null));
                switch (tem) {
                    case "boolean":
                        parList[i_par] = boolean.class;
                        if (!PROVIDE_VALUES){
                            boolean temValueBoolean = handleBoolean();
                            valList[i_par] = temValueBoolean;
                            parRecList[i_par] = temValueBoolean;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "boolean[]":
                        parList[i_par] = boolean[].class;


                        if (!PROVIDE_VALUES){
                            boolean[] temValueBooleanA = handleBooleanA();
                            valList[i_par] = temValueBooleanA;
                            parRecList[i_par] = temValueBooleanA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "boolean[][]":
                        parList[i_par] = boolean[][].class;


                        if (!PROVIDE_VALUES){
                            boolean[][] temValueBooleanAA = handleBooleanAA();
                            valList[i_par] = temValueBooleanAA;
                            parRecList[i_par] = temValueBooleanAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "byte":
                        parList[i_par] = byte.class;


                        if (!PROVIDE_VALUES){
                            byte handleByte = handleByte();
                            valList[i_par] = handleByte;
                            parRecList[i_par] = handleByte;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "byte[]":
                        parList[i_par] = byte[].class;


                        if (!PROVIDE_VALUES){
                            byte[] handleByteA = handleByteA();
                            valList[i_par] = handleByteA;
                            parRecList[i_par] = handleByteA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "byte[][]":
                        parList[i_par] = byte[][].class;


                        if (!PROVIDE_VALUES){
                            byte[][] handleByteAA = handleByteAA();
                            valList[i_par] = handleByteAA;
                            parRecList[i_par] = handleByteAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "short":
                        parList[i_par] = short.class;


                        if (!PROVIDE_VALUES){
                            int handleShort = handleShort();
                            valList[i_par] = handleShort;
                            parRecList[i_par] = handleShort;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "short[]":
                        parList[i_par] = short[].class;


                        if (!PROVIDE_VALUES){
                            short[] handleShortA = handleShortA();
                            valList[i_par] = handleShortA;
                            parRecList[i_par] = handleShortA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "short[][]":
                        parList[i_par] = short[][].class;


                        if (!PROVIDE_VALUES){
                            short[][] handleShortAA = handleShortAA();
                            valList[i_par] = handleShortAA;
                            parRecList[i_par] = handleShortAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "char":
                        parList[i_par] = char.class;


                        if (!PROVIDE_VALUES){
                            char handleChar = handleChar();
                            valList[i_par] = handleChar;
                            parRecList[i_par] = handleChar;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "char[]":
                        parList[i_par] = char[].class;


                        if (!PROVIDE_VALUES){
                            char[] handleCharA = handleCharA();
                            valList[i_par] = handleCharA;
                            parRecList[i_par] = handleCharA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "char[][]":
                        parList[i_par] = char[][].class;


                        if (!PROVIDE_VALUES){
                            char[][] handleCharAA = handleCharAA();
                            valList[i_par] = handleCharAA;
                            parRecList[i_par] = handleCharAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "int":
                        parList[i_par] = int.class;


                        if (!PROVIDE_VALUES){
                            int handleInt = handleInt();
                            valList[i_par] = handleInt;
                            parRecList[i_par] = handleInt;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "int[]":
                        parList[i_par] = int[].class;


                        if (!PROVIDE_VALUES){
                            int[] handleIntA = handleIntA();
                            valList[i_par] = handleIntA;
                            parRecList[i_par] = handleIntA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "int[][]":
                        parList[i_par] = int[][].class;


                        if (!PROVIDE_VALUES){
                            int[][] handleIntAA = handleIntAA();
                            valList[i_par] = handleIntAA;
                            parRecList[i_par] = handleIntAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "long":
                        parList[i_par] = long.class;


                        if (!PROVIDE_VALUES){
                            long handleLong = handleLong();
                            valList[i_par] = handleLong;
                            parRecList[i_par] = handleLong;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "long[]":
                        parList[i_par] = long[].class;


                        if (!PROVIDE_VALUES){
                            long[] handleLongA = handleLongA();
                            valList[i_par] = handleLongA;
                            parRecList[i_par] = handleLongA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "long[][]":
                        parList[i_par] = long[][].class;


                        if (!PROVIDE_VALUES){
                            long[][] handleLongAA = handleLongAA();
                            valList[i_par] = handleLongAA;
                            parRecList[i_par] = handleLongAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "float":
                        parList[i_par] = float.class;


                        if (!PROVIDE_VALUES){
                            float handleFloat = handleFloat();
                            valList[i_par] = handleFloat;
                            parRecList[i_par] = handleFloat;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "float[]":
                        parList[i_par] = float[].class;


                        if (!PROVIDE_VALUES){
                            float[] handleFloatA = handleFloatA();
                            valList[i_par] = handleFloatA;
                            parRecList[i_par] = handleFloatA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "float[][]":
                        parList[i_par] = float[][].class;


                        if (!PROVIDE_VALUES){
                            float[][] handleFloatAA = handleFloatAA();
                            valList[i_par] = handleFloatAA;
                            parRecList[i_par] = handleFloatAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "double":
                        parList[i_par] = double.class;


                        if (!PROVIDE_VALUES){
                            double handleDouble = handleDouble();
                            valList[i_par] = handleDouble;
                            parRecList[i_par] = handleDouble;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "double[]":
                        parList[i_par] = double[].class;


                        if (!PROVIDE_VALUES){
                            double[] handleDoubleA = handleDoubleA();
                            valList[i_par] = handleDoubleA;
                            parRecList[i_par] = handleDoubleA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "double[][]":
                        parList[i_par] = double[][].class;


                        if (!PROVIDE_VALUES){
                            double[][] handleDoubleAA = handleDoubleAA();
                            valList[i_par] = handleDoubleAA;
                            parRecList[i_par] = handleDoubleAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "java.lang.String":
                        parList[i_par] = String.class;


                        if (!PROVIDE_VALUES){
                            String handleString = handleString();
                            valList[i_par] = handleString;
                            parRecList[i_par] = handleString;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "java.lang.String[]":
                        parList[i_par] = String[].class;


                        if (!PROVIDE_VALUES){
                            String[] handleStringA = handleStringA();
                            valList[i_par] = handleStringA;
                            parRecList[i_par] = handleStringA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    case "java.lang.String[][]":
                        parList[i_par] = String[][].class;


                        if (!PROVIDE_VALUES){
                            String[][] handleStringAA = handleStringAA();
                            valList[i_par] = handleStringAA;
                            parRecList[i_par] = handleStringAA;
                        }else{
                            valList[i_par] = parRecList[i_par];
                        }
                        break;
                    default:
                        Object obj = null;

                        if(tem.endsWith("[][]")){
                            tem = tem.replace("[][]", "");
                            if (!PROVIDE_VALUES) {
                                parRecList[i_par] = new ObjectRecorder();
                            }


                            while(obj==null) {
                                System.out.println(".line 799 obj is null");
                                System.out.println("invoke handleObject in line 1160");
                                obj = handleObject(tem, (ObjectRecorder)parRecList[i_par], methRec);

                            }
                            if(obj instanceof String && obj.equals("NoConstructor")){
                                obj = null;

                            }


                            Class theClassX = Class.forName(tem);
                            Class theClassY = Class.forName("[L"+tem+";");
                            Class sClass = Class.forName("[[L"+tem+";");
                            parList[i_par] = sClass;
//                            if (obj == null) {
//                                System.out.println("731, obj为空");
//                                System.exit(0);
//                            }

                            Random r = new Random();
                            int x = r.nextInt(5) + 1 ;
                            int y = r.nextInt(5) + 1 ;
                            if(PROVIDE_VALUES) x = ((ObjectRecorder)parRecList[i_par]).x;
                            if(PROVIDE_VALUES) y = ((ObjectRecorder)parRecList[i_par]).y;

                            Object resArrX = Array.newInstance(theClassX, x);
                            for (int i = 0; i < x; i++) {
                                Array.set(resArrX, i, obj);
                            }
                            Object resArrY = Array.newInstance(theClassY, y);
                            for (int j = 0; j < y; j++) {
                                Array.set(resArrY, j, resArrX);
                            }
                            if (!PROVIDE_VALUES)((ObjectRecorder)parRecList[i_par]).x = x;
                            if (!PROVIDE_VALUES)((ObjectRecorder)parRecList[i_par]).y = y;

                            valList[i_par] = resArrY;

                        }else if(tem.endsWith("[]")){
                            tem = tem.replace("[]", "");
                            if (!PROVIDE_VALUES) {
                                parRecList[i_par] = new ObjectRecorder();
                            }

                            while (obj == null) {
//                                if(!PROVIDE_VALUES) methRec.parVals = parRecList;
                                System.out.println(".line 829 obj is null");
                                System.out.println("invoke handleObject in line 1213");
                                obj = handleObject(tem, (ObjectRecorder)parRecList[i_par], methRec);
                            }
                            if (obj instanceof String && obj.equals("NoConstructor")) {
                                obj = null;
                            }

                            Class theClass = Class.forName(tem);
                            Class sClass = Class.forName("[L"+tem+";");
                            parList[i_par] = sClass;
//                            if (obj == null) {
//                                System.out.println("753, obj为空");
//                                System.exit(0);
//                            }

                            Random r = new Random();
                            int x = r.nextInt(5) + 1 ;
                            if(PROVIDE_VALUES) x = ((ObjectRecorder)parRecList[i_par]).x;

//                            Object[] resArr = new Object[x];
                            Object resArr = Array.newInstance(theClass, x);
                            for (int i = 0; i < x; i++) {
                                Array.set(resArr, i, obj);
//                                resArr[i] = obj;
                            }
                            if (!PROVIDE_VALUES)((ObjectRecorder)parRecList[i_par]).x = x;
                            valList[i_par] = resArr;

                        }else{
                            if (!PROVIDE_VALUES) {
                                parRecList[i_par] = new ObjectRecorder();
//                                methRec.parVals = parRecList;

                            }

//                            Class sClass = Class.forName("L"+tem+";");
                            Class sClass = Class.forName(tem);
//                            System.out.println(sClass);
//                            Class<?> sClass2 = Class.forName(tem);
//                            System.out.println(".line 764");
//                            System.out.println(sClass2);
//                            System.exit(0);
                            parList[i_par] = sClass;
                            while (obj == null) {
//                                if(!PROVIDE_VALUES) methRec.parVals = parRecList;
                                System.out.println("invoke handleObject in line 1263");
                                System.out.println("1405 parRecList[i_par]==null: " + (parRecList[i_par]==null));
                                obj = handleObject(tem, (ObjectRecorder)parRecList[i_par], methRec);
                            }
                            if (obj instanceof String && obj.equals("NoConstructor")) {
                                obj = null;
                            }

//                            if (obj == null) {
//                                System.out.println("764, obj为空");
//                                System.exit(0);
//                            }
                            valList[i_par] = obj;

                        }
                }
            }


            System.out.println("final parArr: " + parList);

            for (Class tem : parList) {
                System.out.println(tem);
            }



            System.out.println("1297 parRecList.size(): "+parRecList.length);
            Object[] parRecArr = new Object[parRecList.length];


            System.out.println("final valArr: " + valList);
//            System.out.println("Arrays.toString(parArr) : " + Arrays.toString(parList));
//            System.out.println("Arrays.toString(valArr) : " + Arrays.toString(valList));


            for (Object tem : valList) {
                System.out.println(tem);
            }

            // message 2
            writer.println(className + "|" + methodName);
            System.out.println("message 2 sent .line 641");

//            System.out.println("方法 " + className + " " + res + " " + methodName + " " + Arrays.toString(parList));
//            System.out.println("被使用下列参数创建: " + Arrays.toString(parList));
//            System.out.println("被使用下列值创建: " + Arrays.toString(valList));

            System.out.println("1324 methRec4save.parVals.length: "+methRec.parVals.length);
            if (!PROVIDE_VALUES) {
//                methRec.className = className;
//                methRec.methodName = methodName;
//                methRec.parVals = parRecArr;
//                methRec.pars = pars;
//                methRec.res = res;
                System.out.println("invoke saveMethodRecorder in line 1332");
                saveMethodRecorder(methRec);
                System.out.println("1345 parRecArr.length: " + parRecArr.length);
                System.out.println("1346 methRec4save.parVals.length: " + methRec.parVals.length);
            }

//            // message 3
//            ObjectOutputStream out = null;
//            try {
//                out = new ObjectOutputStream(output);
//                out.writeObject(methRec);
//            } catch (IOException e) {
//                e.printStackTrace();
//            }

            try {
                Class<?> sClass = Class.forName(className);
                Method privateMethod = sClass.getDeclaredMethod(methodName, parList);
                privateMethod.setAccessible(true);
                System.out.println("1358 invoke fun");
                System.out.println("invoke funtion indecator 2");
                privateMethod.invoke(sClass, valList);

                Log.i(TAG, "==========call success!!========");

            } catch (NoSuchMethodException e) {
                e.printStackTrace();
                return -1;
            } catch (IllegalAccessException e) {
                e.printStackTrace();
                return -2;
            } catch (InvocationTargetException e) {
                e.printStackTrace();
                return -3;
            } catch (ClassNotFoundException e) {
                e.printStackTrace();
                return -4;
            } catch (IllegalArgumentException e) {
                System.out.println("1376 methRec4save.parVals.length: " + methRec.parVals.length);
//                e.printStackTrace();
                System.out.println("处理第一次IllegalArgumentException，尝试构建对象");
                // https://stackoverflow.com/questions/19740885/android-reflection-method-error
                try {
                    System.out.println("926 | Class sClass = Class.forName(className);");
                    Class sClass = Class.forName(className);
                    System.out.println("928 | Method privateMethod  = sClass.getDeclaredMethod(methodName, parArr);");
                    Method privateMethod  = sClass.getDeclaredMethod(methodName, parList);
                    privateMethod.setAccessible(true);
                    System.out.println("931 | Object clazzObj = handleObject(className);");
                    Object clazzObj = null;
                    if (!PROVIDE_VALUES){
                        methRec.clazzObj = new ObjectRecorder();
                    }

                    System.out.println("1535 objRec==null: " + (methRec.clazzObj == null));
                    System.out.println("1384 methRec4save.parVals.length: " + methRec.parVals.length);
                    System.out.println("1391 parRecArr.length: " + parRecArr.length);
                    System.out.println("1392 parRecList.size(): " + parRecList.length);

                    while (clazzObj == null) {
                        System.out.println(".line 949 obj is null");
                        System.out.println("invoke handleObject in line 1396");
                        clazzObj = handleObject(className, methRec.clazzObj, methRec);
                    }

                    if (clazzObj instanceof String && clazzObj.equals("NoConstructor")) {
                        clazzObj = null;
                    }


                    System.out.println("933 | privateMethod.invoke(clazzObj, valArr);");

                    if (!PROVIDE_VALUES) {
                        System.out.println("invoke saveMethodRecorder in line 1402");
                        saveMethodRecorder(methRec);
                    }
                    System.out.println("invoke funtion indecator 1");
                    System.out.println("clazzObj: " + (clazzObj==null));
//                    System.out.println("被使用下列值创建: " + Arrays.toString(valList));
                    privateMethod.invoke(clazzObj, valList);

                    Log.i(TAG, "==========call success!!========");
                } catch (NoSuchMethodException ex) {
                    ex.printStackTrace();
                    return -1;
                } catch (IllegalAccessException ex) {
                    ex.printStackTrace();
                    return -2;
                } catch (InvocationTargetException ex) {
                    ex.printStackTrace();
                    return -3;
                } catch (ClassNotFoundException ex) {
                    ex.printStackTrace();
                    return -4;
                } catch (IllegalArgumentException ex) {
                    ex.printStackTrace();
                    return -5;
                }
                return 0;
            }
            return 0;
        }else{
            // message 2
            writer.println(className + "|" + methodName + "|" + "|");
            System.out.println("message 2 sent .line 641");

            try {
                // 获取类
                Class sClass = Class.forName(className);
                // 是否可访问
//            Method privateMethod = sClass.getDeclaredMethod(methodName, new Class<?>[]{String.class,Integer.class});
                // 获取方法

                Method privateMethod = sClass.getDeclaredMethod(methodName);
//            Method publicMethod = null;
//            publicMethod = sClass.getMethod("publicMethod");
                privateMethod.setAccessible(true);
//            String r_txt1 = (String) privateMethod.invoke(sClass);
                // 是否有返回值
//            privateMethod.invoke(sClass, new Class<?>[]{String.class,Integer.class});
                System.out.println("invoke funtion indecator 3");
                // 实际调用
                privateMethod.invoke(sClass);

//            Class<?> sClass = Class.forName("android.view.SurfaceControl");
//            Method method = sClass.getMethod("screenshot",int.class,int.class);
//            Method method2 = sClass.getDeclaredMethod("screenshot",int.class,int.class);
//            method.setAccessible(true);
//            bitmap = (Bitmap) method.invoke(sClass,widht,height);

                Log.i(TAG, "==========call success!!========");

            } catch (NoSuchMethodException e) {
                e.printStackTrace();
                return -1;
            } catch (IllegalAccessException e) {
                e.printStackTrace();
                return -2;
            } catch (InvocationTargetException e) {
                e.printStackTrace();
                return -3;
            } catch (ClassNotFoundException e) {
                e.printStackTrace();
                return -4;
            } catch (IllegalArgumentException e) {
                e.printStackTrace();
                return -5;
            }
            return 0;
        }
    }

    private void printObjectRecorder(ObjectRecorder o, int deep){
        String space = String.format("%" + deep + "s", " ");
        System.out.println(space + "| objName: " + o.objName);
        System.out.println(space + "| constructorIndex: " + o.constructorIndex);
        System.out.println(space + "| x: " + o.x);
        System.out.println(space + "| y: " + o.y);
        System.out.println(space + "| valArrRecord: " + o.valArrRecord);
        if (o.valArrRecord !=null) {
            for (Object tem : o.valArrRecord) {
                if (tem instanceof ObjectRecorder) {
                    printObjectRecorder((ObjectRecorder) tem, deep + 1);
                } else {
                    System.out.println(space + "| : " + tem);
                }
            }
        }
    }

    private void saveMethodRecorder(MethodRecorder methRec) {
        System.out.println("====== saveMethodRecorder ======");
        System.out.println("| objFileName: " + objFileName);
//        System.out.println("| methodName: " + methRec.methodName);
//        System.out.println("| pars: " + methRec.pars);
//        System.out.println("| res: " + methRec.res);

        System.out.println("| clazzObj: ");
        if(methRec.clazzObj != null)
            printObjectRecorder(methRec.clazzObj, 1);
        else
            System.out.println(" | null");

        System.out.println("| parVals: " + methRec.parVals);
        for(Object tem : methRec.parVals){
            if (tem instanceof ObjectRecorder){
                printObjectRecorder((ObjectRecorder)tem, 1);
            }else{
                System.out.println(" | : " + tem);
            }
        }



        File folder = getApplicationContext().getExternalFilesDir(Environment.DIRECTORY_DCIM);
        if (folder.exists() ||folder.mkdir()) {
            // 使用 debug 打印出 folder 的路径

            File file = new File(folder, objFileName + ".obj");
            FileOutputStream fileOut = null;
            try {
                fileOut = new FileOutputStream(file);
                ObjectOutputStream out = new ObjectOutputStream(fileOut);
                out.writeObject(methRec);
                out.close();
                fileOut.close();
                System.out.println("====== COMPLETE saveMethodRecorder ======");
                System.out.println(" - ");
                System.out.println(" - ");
                // message 3
//                writer.println("fileName: "+fileName +".obj");
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            }

        }

    }

    private MethodRecorder loadMethodRecorder(String fileName) {
        System.out.println("====== loadMethodRecorder ======");
        MethodRecorder methRec = null;
        File folder = getApplicationContext().getExternalFilesDir(Environment.DIRECTORY_DCIM);

        File file = new File(folder, fileName + ".obj");
        FileInputStream fileIn = null;
        try {
            fileIn = new FileInputStream(file);
            ObjectInputStream in = new ObjectInputStream(fileIn);
            methRec = (MethodRecorder) in.readObject();

            System.out.println("| clazzObj: ");
            if(methRec.clazzObj != null)
                printObjectRecorder(methRec.clazzObj, 1);
            else
                System.out.println(" | null");

            System.out.println("| parVals: " + methRec.parVals);
            if(methRec.parVals != null) {
                for (Object tem : methRec.parVals) {
                    if (tem instanceof ObjectRecorder) {
                        printObjectRecorder((ObjectRecorder) tem, 1);
                    } else {
                        System.out.println(" | : " + tem);
                    }
                }
            }

            in.close();
            fileIn.close();

            System.out.println("====== COMPLETE loadMethodRecorder ======");
            System.out.println(" - ");
            System.out.println(" - ");


            return methRec;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        } finally{
            return methRec;
        }
    }



    public void showMethods(String className){
        try {
            // "android.net.NetworkUtils"
            Class activityClass = Class.forName(className);
            Method[] m = activityClass.getDeclaredMethods();
            for (Method t : m) {
                System.out.print(Modifier.toString(t.getModifiers()));    //获取方法的修饰符
                System.out.print(" ");
                System.out.print(t.getReturnType().getName());    //带包名的
                //    System.out.println(t.getReturnType().getSimpleName());    //带包名的
                System.out.print(" ");
                System.out.print(t.getName());    //获取方法名

                Class[] type = t.getParameterTypes();        //获取方法的所有参数类型(返回Clss[])
                System.out.print("(");
                for (Class temp : type) {
                    System.out.print(temp.getSimpleName() + ",");        //打印方法的参数类型(不带包名)
                    //System.out.println(temp.getName());        //打印方法的参数类型(带包名)
                }
                System.out.println(")");
            }
        } catch (Throwable e) {
            Log.e(TAG, "error:", e);
        }
    }


    Runnable serverRun = new Runnable(){
        @Override
        public void run() {
            TCPServer();
        }
    };

    Runnable clientRun = new Runnable(){
        @Override
        public void run() {
            TCPClient();
        }
    };

    public void TCPServer() {
        int port = 7100;

        try (ServerSocket serverSocket = new ServerSocket(port)) {

            System.out.println("Server is listening on port " + port);
            Socket socket;
            InputStream input;
            BufferedReader reader;
            String message_row;
            OutputStream output;


            while (true) {
                socket = serverSocket.accept();

                System.out.println("New client connected, and say:");

                input = socket.getInputStream();
                reader = new BufferedReader(new InputStreamReader(input));
                message_row = reader.readLine();
                System.out.println(message_row);

//                socket.shutdownInput();

                output = socket.getOutputStream();
                writer = new PrintWriter(output,true);

                ////                socket.shutdownOutput();
////                output = socket.getOutputStream();
////                writer = new PrintWriter(output, true);
////                writer.flush();
//
//                writer.println("copy that22");

                String[] tem = message_row.split("\\|");


                String className;
                String methodName;
                String pars;
                String res;
                String objFile = null;
                MethodRecorder methRec = null;

                if(message_row.startsWith("MODE0|")){
                    PROVIDE_VALUES = true;
                    objFile = tem[1];
                    methRec = loadMethodRecorder(objFile);
                    className = methRec.className;
                    methodName = methRec.methodName;
                    pars = methRec.pars;
//                    Object[] parVals = methRec.parVals;
                    res = methRec.res;
//                    Object clazzObj = methRec.clazzObj;

                }else {
                    methRec = new MethodRecorder();
                    className = tem[1];
                    methodName = tem[2];
                    pars = tem[3];
                    res = tem[4];
                }

                System.out.println("className: " + className);
                System.out.println("methodName: " + methodName);
                System.out.println("pars: " + pars);
                System.out.println("res(return): " + res);

                int code = -999;
                try {
                    HelloJNI.init();
                    code = process(className, methodName, pars, res, methRec);
                } catch (IllegalArgumentException e) {
                    e.printStackTrace();
                } catch (ClassNotFoundException e) {
                    e.printStackTrace();
                } catch (IllegalAccessException e) {
                    e.printStackTrace();
                } catch (InstantiationException e) {
                    e.printStackTrace();
                } finally {
                    System.out.println("程序到这里了！");
                    writer.println("code:" + code);
                    socket.shutdownOutput();

                    HelloJNI.dump();
                    System.out.println("保存好了");
                }

            }

        } catch (IOException ex) {
            System.out.println("Server exception: " + ex.getMessage());
            ex.printStackTrace();
        }

    }

    public void TCPClient() {
        int port = 7100;

        Socket socket = null;
        try {
            socket = new Socket("127.0.0.1", port);


            OutputStream output = socket.getOutputStream();
            PrintWriter writer = new PrintWriter(output, true);
            writer.println("wo shi client");

//        socket.shutdownOutput();

            InputStream input = socket.getInputStream();
            BufferedReader reader = new BufferedReader(new InputStreamReader(input));
            String feedback = reader.readLine();
            System.out.println(feedback);

//        if(feedback==null){
//            Runtime.getRuntime().exec("adb shell am start "+pkg+"/."+activity);
//            TimeUnit.MILLISECONDS.sleep(1000);
//            TCPClient();
//        }


            socket.shutdownOutput();
            socket.shutdownInput();

            writer.close();
            output.close();
            reader.close();
            input.close();
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

//        socket.shutdownOutput();
    }
}