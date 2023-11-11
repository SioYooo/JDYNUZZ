import com.alibaba.fastjson.JSON;
import com.example.fuzzer.MethodRecorder;
import util.ApiDependency;
import util.JniClass;
import util.JniPath;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import static java.lang.System.currentTimeMillis;
import static java.lang.System.exit;
import static java.lang.Thread.sleep;

public class Engine {
    // 提取接口 生成API列表
    // 根据列表参数生成需要喂入的参数值
    // 如果是对象 则拿到对象构造方法后 再将序列发送给客户端进行处理生成（json数组序列
    // 参数数组【str，int，obj。。。】
    // 值数组【"abc"，-1，【"obj"，。。。】。。。】
    // 两组同时传给客户端

    // 设置 device ID，作为给 adb 的 指令进行传参
    //static String DEVICE = "8CFX1NP4C";
    // static String DEVICE = "emulator-5554";
    static String DEVICE = "0.0.0.0:6520";
    // PACKAGE_name 参数 用做查找 进程 ID 等作用 - 在 ADB 中进行 fuzzer engine 查找
    static String PACKAGE_NAME = "com.example.fuzzer";
//    static String adb_path = "/hci/chaoran_data/android-12.0.0_r31/out/soong/host/linux-x86/bin/adb";
    // 设置 adb 指令
    // static String adb_path = "adb";

    // static String adb_path = "C:\\Users\\au424\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe";
    static String adb_path = "/home/siyu/Android/Sdk/platform-tools/adb";
    // 进行 JNI 的 API index 计数
    static int STARTFROM = 0;
    static boolean PRINT_ADB_LOG = false;
    // 设置每个 API 的 time out 时间
    static int TIME_OUT_EVERY_API = 6 * 1000;

    static boolean KILL_BY_TIMEOUT = false;
    static String objFileName = "";
    // 遍历 API index
    static int API_INDEX = -1;
    static String pid;
    static String lastAvailablePid;
    static String identifier;
    static ArrayList<String> basicTypes = new ArrayList<String>() {};
//    static Thread testThread = null;
//    static Process testProcess= null;
    static Boolean MAIN_LOOP_WAIT_FLAG = true;
    static String record_str = "";
    static Process diedMoniterProcess=null;
//    static boolean timeout = false;
    static String testClass = "";
    static String testFun = "";
    static boolean hasSaved = false;
    static Thread logMoniterTimeOutThread = null;
    static boolean is_collecting_log = false;
    static boolean not_debug = true;
    static boolean single = false;
    // 如果没有message3 说明程序死循环了
    static boolean got_message3 = false;

    // 设置虚拟机的 Fuzzer client 保存文件路径
    static String objFileDir = "/storage/emulated/0/Android/data/com.example.fuzzer/files/DCIM";

    public static char getRandomCharacter(char ch1, char ch2) {
        return (char)(ch1 + Math.random() * (ch2 - ch1 + 1));
    }

    public static char getRandomCharacter() {
        return getRandomCharacter('\u0000', '\uFFFF');
    }

    // get save file directory, 如果当前 working dir 是在 fuzzing server 下，则返回的是 fuzzing server 的路径，否则为 root 目录下，则返回 root/fuzzing server 的路径
    public static String getSaveFileDir() {
        String saveFileDir = "";
        String workingDir = System.getProperty("user.dir");
        System.out.println("workingDir = " + workingDir);
        if(workingDir.contains("Fuzzing_Server")) {
            saveFileDir = workingDir;
        } else {
            saveFileDir = workingDir + File.separator + "Fuzzing_Server";
        }
        return saveFileDir;
    }


    public static void analyzeJNI() {
        // 通过 load() 函数对 jni12.0/jni_with_isStatic.json 文件进行读取解析得到 jniClass list
        List<JniClass> jniList = load();
        int total = jniList.size();
        int apiHasObj = 0;
        System.out.println("total = " + total);

        //遍历List<JniClass>，查找有多少个独立的class
        HashSet<String> classSet = new HashSet<String>();
        int count_static = 0;
        int count_non_static = 0;
        for (JniClass jni : jniList) {
            if(jni.getStatic_())
            {
                count_static++;
            }
            else{
                count_non_static++;
            }
            classSet.add(jni.getClass_());

            List<String> parameters = jni.getParameters();
            boolean hasObj = false;
            for(String par :parameters){
                if(par.contains(".")){
                    hasObj = true;
                    apiHasObj++;
                    break;
                }
            }
            // 参数列表没对象
            if(!hasObj){
                // API 不是静态方法
                if(!jni.getStatic_()){
                    apiHasObj++;
                }
            }
        }
        int classTotal = classSet.size();
        System.out.println("classTotal = " + classTotal);
        System.out.println("count_static = " + count_static);
        System.out.println("% static = " + Math.round((float)count_static/(float)total * 10000f)/100f + "\\%");
        System.out.println("% non-static = " + (100 - Math.round((float)count_static/(float)total * 10000f)/100f) + "\\%");
        System.out.println("有对象的API = （参数列表有对象的API" + apiHasObj + "）+（" + count_non_static + "）= " + (apiHasObj+count_non_static));


        // exit(0);
    }

    public static void main(String[] args) throws Exception {
        // start Fuzzing server on android phone
        Runtime.getRuntime().exec(adb_path + " shell am start -n com.example.fuzzer/.MainActivity");
//        Runtime.getRuntime().exec(adb_path + " -s " +DEVICE+ " shell input keyevent 224");
        Runtime.getRuntime().exec(adb_path + " shell input keyevent 224");
        TimeUnit.MILLISECONDS.sleep(1000);
//        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input swipe 300 1000 300 100");
        Runtime.getRuntime().exec(adb_path + " shell input swipe 300 1000 300 100");
        TimeUnit.MILLISECONDS.sleep(1000);

        // 命令行模式 ===========================================================
//        if(args.length == 2) {
//            System.out.println("args[0] = " + args[0]);
//            System.out.println("args[1] = " + args[1]);
//            if(args[1].equals("false")) {
//                not_debug = false;
//                System.out.println("disable timeout");
//            }
//
//            if(args[0].endsWith("obj")) {
//                String[] objFiles = {args[0]};
//                bench_obj(objFiles, true);
//            } else {
//                System.out.println("args[0] = " + args[0] + " is not an obj file, e.g. ./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934512875.obj");
//            }
//        }else {
//            System.out.println("please input the obj file path. eg: ./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934512875.obj");
//            System.out.println("2nd par: false, no time out; true, enable timeout");
//    }
        analyzeJNI();
        // 批量 ===========================================================
        bench();

        bench_dependency();
//        testClass = "android.graphics.RenderNode";
//        testFun = "nSetAnimationMatrix";
        benchTest();
        test();
        // is_collecting_log = false;
//        String[] objFiles = {"./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934512875.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935666129.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932895032.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933853168.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930833980.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936198348.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931812388.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934568867.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934459829.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930485152.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934849770.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649929764286.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932046904.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931318682.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931023353.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933911571.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932353444.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935530915.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936486079.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930990168.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936524044.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933781840.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932450923.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934137890.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931490509.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933207880.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930797591.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935764050.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936759185.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931390738.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930312960.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936217128.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935805918.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931386581.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935892940.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934663101.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935317776.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935406929.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933923349.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932697668.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934054670.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934338946.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933165612.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930642473.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932994270.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934770866.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936701669.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934025717.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934606461.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935770489.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931868229.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933774401.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934168675.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933889734.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935828283.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933137077.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935247278.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933127281.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932229052.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936489388.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933007087.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932317807.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932725190.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934041555.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649931234061.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935359303.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935386513.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649935678253.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649930746690.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932532756.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933106126.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936630741.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933665794.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932600087.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649932928709.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649933273694.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649936413404.obj", "./backup_old/2022.04.14-21:48:42/objFiles/DCIM/1649934450237.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952275749.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953914171.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954718020.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954793793.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953886692.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953413917.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955330539.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952360160.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953957247.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955577010.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955281546.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954516914.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954306905.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955587355.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952488865.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953923353.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951845454.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952176664.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954056394.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954685212.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951601509.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954772802.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954751378.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952128355.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953287533.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952418401.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951735228.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955011876.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955414595.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955227639.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953511519.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953097998.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954833926.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952742720.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953725520.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954959733.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954456494.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952593235.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954538392.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952987823.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954888229.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954984205.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952081619.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955123291.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953646265.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951777984.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954204643.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953805848.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952167479.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954096809.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954174267.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955464739.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952893155.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954727255.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955408266.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951439717.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952409615.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954040961.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955356300.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954459404.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955243197.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951460408.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952041812.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952999930.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952947649.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952507160.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953871159.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953094898.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952590313.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955240207.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952113062.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952314161.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954651211.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954247762.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951860416.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953012098.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953722563.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953594232.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955108031.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954645078.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953480659.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953539009.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955473960.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952657745.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952953572.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954480930.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955402346.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952794777.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955111058.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953551207.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952131292.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953152301.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955230934.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952134219.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954074275.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951799408.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953471446.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955308924.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951997370.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952883955.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954607985.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951842535.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953128019.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954015970.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951613548.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954510926.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951879421.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952284484.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954462300.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954433226.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955253485.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951486445.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952516320.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954436157.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952341293.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951516146.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952354291.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953422841.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954381259.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954405815.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953978665.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951857496.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952546798.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953960288.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953740980.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951738124.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952727728.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953637071.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955637802.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952390530.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955346044.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954654142.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952630335.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951876484.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954348021.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954940254.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954411649.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953615640.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951628961.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952185852.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951521728.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954806032.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955247283.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954554790.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953039759.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954854552.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953895839.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955630576.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951534516.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953118938.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952281509.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649954450621.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953158258.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952483046.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952788874.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649952452217.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955154275.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649951427673.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649953164137.obj", "./backup_old/2022.04.15-07:53:36/objFiles/DCIM/1649955461773.obj"};
//        String[] objFiles = {"./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432966539.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432746829.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434409882.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426346544.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431606726.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429440139.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425230875.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433594167.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430542888.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419361909.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429200944.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431763265.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434121666.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418564924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429871967.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433104062.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419384005.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433528383.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425857951.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429461264.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429506210.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425083543.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426284475.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432589623.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426730381.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425265436.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428746360.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429570030.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428495001.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418718005.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426110538.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432485439.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432005486.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419678448.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428458938.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435347180.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433348685.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431111947.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428659906.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419791912.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433761447.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431425250.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418818956.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432750966.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426758783.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432368398.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426382060.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425382662.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418713926.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425955996.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433068103.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429457239.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418772167.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426949195.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432139913.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435447745.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433647687.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419588937.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430427044.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432920304.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433690986.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426211656.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430075388.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433923965.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430270447.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426267972.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425442603.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434580808.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432560865.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431381005.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432152024.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426734381.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431953662.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428649781.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650424984122.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435507906.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435374364.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425973404.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426015373.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418131262.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435432074.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428636687.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430958386.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429176481.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425854102.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429925450.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428969099.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426664975.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419630010.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426257712.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426939993.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435336785.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432009509.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431259783.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429093025.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434353146.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425113503.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425799836.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430780076.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425889101.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429883890.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434008825.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428632727.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431341949.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433600286.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418183801.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431439388.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434493832.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430954340.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432940840.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426865632.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433765521.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432686443.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434889926.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432519912.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429412902.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430098484.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434815310.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434485702.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429172447.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650436503076.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431870823.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432216688.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429624342.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428750288.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419585061.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650424962011.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434951821.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432263286.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430764600.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425053175.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428956239.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432411481.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431333822.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429286167.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426337384.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430228580.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425969315.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425129630.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433954203.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432537225.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432816187.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430940084.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429689728.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433352722.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430816957.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432717225.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425006362.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429294208.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425207656.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431201367.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418059903.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431345948.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430243943.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430388299.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425117501.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426534195.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434865084.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430622771.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419458054.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433385822.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419645631.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418052241.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434691086.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435332684.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426816155.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434700386.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428884770.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425885097.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434427125.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432033048.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429436125.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429290224.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418037302.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435637403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418600765.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432924363.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432166725.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433497525.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418172329.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430962403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432204530.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419637816.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429163130.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430546889.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431287226.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429333685.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428447613.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426035850.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429817688.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429097009.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433309004.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426624159.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426447301.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433851582.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433514029.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435201526.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433608425.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434029385.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426526379.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426797783.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433805642.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431891266.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419607316.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429129664.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432900746.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429767212.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434516403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430218402.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435305642.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435566224.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431973729.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434112403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432495780.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426705818.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428994630.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650427022351.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431638742.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426589277.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433439943.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434161990.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432477260.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432632086.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429196924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428776469.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650417999925.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433884272.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426400264.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426511041.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435026242.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434405786.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433509983.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431003018.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428486977.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419728131.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435129032.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418465506.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435266303.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434178506.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433939984.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429053604.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433769603.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432577480.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428462680.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430186168.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426480636.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435497605.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431800318.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432148004.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432378706.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425861847.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430664154.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432678366.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429905005.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432541296.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430723403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435351571.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426581376.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431355199.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434981846.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418167995.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418496722.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433613464.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434742762.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435324501.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430494992.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434746825.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434244500.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430571646.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425250214.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434650129.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418104759.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431401586.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431478647.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434664520.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429901010.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433248047.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425034114.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431881047.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428687503.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429708025.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428880830.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435388707.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432978547.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432854521.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429875944.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426889977.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425162688.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430978960.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430318326.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433919966.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433567349.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428965156.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432779602.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432609609.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433740922.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434231142.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429192924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435088303.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434672665.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433174623.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434107385.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430089550.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418438600.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430538863.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418300246.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433736866.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434469146.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433389865.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431032863.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429262238.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429397359.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428605325.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650427000275.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419403272.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431698924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434085305.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430274431.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429393303.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431064956.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430375010.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418366721.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431759251.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425002455.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426768965.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431152693.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432533188.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434750904.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433932004.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426083012.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435096687.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434431186.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418608746.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429274200.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433827027.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431121204.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433448063.obj"};
//        String[] objFiles = {"./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614848864.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559839332.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644678942.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650553630389.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419732053.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428390839.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426455158.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429901010.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425955996.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433827027.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575775030.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650550777274.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435221943.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433448063.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426346544.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650596743445.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429368822.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650650235201.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432717225.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426730381.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433362986.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650556336274.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430940084.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433789142.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554436109.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650638037304.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419637816.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650573320011.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650632278485.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428486977.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650649701502.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432166725.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431003018.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432477260.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432378706.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431111947.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650646187661.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644296043.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650572187949.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650602347946.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419588937.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650593794106.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430546889.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650578737432.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418199044.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554247768.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559124410.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650635833183.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431706943.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650595042669.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425885097.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650549813711.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428969099.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650602752184.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614668268.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564987109.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535234812.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430664154.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431800318.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425129630.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650589892866.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431333822.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650634016162.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429925450.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650521789555.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576865287.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429461264.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432135481.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432533188.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433435722.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619698184.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433954203.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429955142.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528698737.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435336785.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587247125.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426110538.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434493832.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429129664.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650610051467.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431439388.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650525967176.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650626540952.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425113503.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558431751.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650636758206.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650642483604.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650649489421.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650536418530.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650610494505.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431642789.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433690986.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429624342.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430542888.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432216688.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645129804.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433035126.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650621960228.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432686443.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418718005.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534575392.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613598170.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650599268169.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650621037110.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650632583127.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650527265775.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429163130.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418705897.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529504599.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431638742.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650585267427.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650555911470.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650621007250.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434742762.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650501275656.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650502819323.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587443274.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433248047.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419585061.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428687503.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606845027.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429871967.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434646066.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587676487.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430318326.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426705818.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430274431.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650602577287.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430218402.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429637463.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650580656551.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434815310.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430816957.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575263006.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650506254760.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650577466517.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650589056073.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650540922352.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434353146.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433932004.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650623707908.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419645631.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625202822.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650436503076.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650616693524.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650584984808.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418300246.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644419537.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434672665.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431341949.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433805642.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430764600.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425446591.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650531724994.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650593271294.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650589325506.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534547595.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650553614810.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613990347.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428746360.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650623299603.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650516439120.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650608589411.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435305642.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650511460404.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650531574554.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650557664435.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426664975.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650524986099.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629825804.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432519912.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650648231220.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619113803.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650642214404.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650560458490.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650540353811.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575716244.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650500677019.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418082426.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590976867.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435129032.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541784613.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425053175.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435332684.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650563654810.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650633749584.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435096687.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650538178733.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431381005.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650537124474.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419384005.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650602121209.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429905005.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551210032.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650523639136.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650626184064.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434750904.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650636674082.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434700386.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428750288.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430571646.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628073019.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619307786.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435351571.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418465506.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650553560613.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650578741553.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430186168.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435201526.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428605325.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650536681452.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426581376.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425889101.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418608746.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418052241.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430954340.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434691086.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650599735151.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629700564.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431201367.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532346371.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433184945.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650626689325.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428649781.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650622616803.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619409163.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650525934457.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432978547.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650605299208.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628032648.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429290224.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650627421204.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430228580.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650631538026.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604325686.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650598342789.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571321350.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432854521.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576794809.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433174623.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650588475710.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425969315.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590221847.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650584075886.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583957147.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650650243420.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419728131.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532943956.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529988313.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541765990.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650647502101.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650633664526.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425002455.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625079346.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650578022753.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650638170802.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419458054.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650511713020.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429817688.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545798998.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434161990.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615028167.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650650270261.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650505653926.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590938907.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650570580670.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551933028.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650591330312.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625710004.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650594001011.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650544812091.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650572543368.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429412902.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650523296560.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434889926.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429196924.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545335418.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432779602.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433104062.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429200944.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628724942.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426816155.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528933332.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650616173863.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418037302.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434085305.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425034114.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650638006565.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650634044965.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650524862735.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650626009187.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435507906.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650538396917.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429172447.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432005486.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545351997.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435497605.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429192924.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583824266.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433736866.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650595076689.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650648781847.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554444339.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650524199395.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435347180.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650612367602.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431121204.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650552555949.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431401586.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650589684029.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435374364.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650507215800.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431606726.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429097009.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606479068.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590772346.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581121968.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586833847.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650649720205.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650640039047.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431152693.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587728218.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650521682336.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650611268970.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520527733.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532272073.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604099092.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558794149.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428994630.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541047411.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418183801.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541238376.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433740922.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650533118071.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650607696309.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431973729.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433613464.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554461850.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426526379.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650417999925.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434231142.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650648564048.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535543257.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429286167.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432816187.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522498052.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432152024.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434580808.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433501950.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432589623.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571499353.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650621932243.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650536677352.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429176481.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425442603.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650572601429.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615828328.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650600171607.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650533526731.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650567682078.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419403272.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428447613.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419791912.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433385822.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650560794351.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565503514.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650623913401.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650648867982.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434008825.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430538863.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619554879.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650537770935.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650637280764.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650642831141.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551638637.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434516403.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650631552466.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418438600.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650527723855.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650578557744.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650527304850.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650631275883.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434409882.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650633420043.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571385630.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650546845990.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429053604.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650594035403.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650572341193.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583504468.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432966539.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434029385.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650531766312.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581394944.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604274208.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430780076.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433919966.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650552634829.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418713926.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425006362.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554198934.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650537509613.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586984026.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433884272.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650630449783.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650574751850.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434469146.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522688913.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432632086.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628068904.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565951232.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430075388.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431345948.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650561809032.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650577304451.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429372798.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650647197380.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650502655642.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644646747.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428965156.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581306884.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418167995.obj", "./backup/2022.04.21-15:51:21/objFiles/DCIM/1650514623978.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435432074.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650552262037.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429333685.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565790689.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565217230.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650579137528.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425854102.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650599251526.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645765981.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528096960.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418564924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431355199.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650641151928.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628379904.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590814909.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434485702.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558166312.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522097614.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429689728.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575192990.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650560242573.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650642419445.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522897554.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650562933131.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650630171361.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590597166.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434405786.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432009509.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435266303.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604946811.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432263286.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650602999284.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604722564.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429875944.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432541296.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564020471.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650633777483.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432560865.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650600238302.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425265436.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433939984.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434664520.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434178506.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650577860371.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650577780925.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650585840565.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435447745.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628024384.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431870823.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650567254136.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650616475066.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432900746.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650530179272.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650589082826.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606849109.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650630628001.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541926750.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426267972.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535896652.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650563876813.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435324501.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650603064407.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592772649.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650597972545.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432368398.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576339227.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606258328.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528614097.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650600188065.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650544986693.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650531604432.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650626992084.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529098374.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650632595604.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425083543.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435168441.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650597809685.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650542265398.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434865084.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650635670701.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650594677626.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434107385.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650521249933.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535630755.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428632727.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629993204.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650524125733.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650531239014.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430089550.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551872290.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650542385129.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428776469.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650596236307.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650560721831.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425382662.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432139913.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429329657.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434951821.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628028524.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592789071.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428462680.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529637651.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615803227.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419630010.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433509983.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650624690924.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650552704273.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426889977.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426939993.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650647723204.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432148004.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583976848.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559740150.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645291988.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426382060.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432537225.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650607899843.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433352722.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431881047.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581424789.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590434866.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426035850.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650624357312.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435637403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425861847.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650605730242.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629544742.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431763265.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426480636.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429397359.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430723403.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650618690304.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529463314.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650566497490.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650555500131.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586781128.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650610133589.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650612047608.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650636056562.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418600765.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644858492.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564895973.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534886115.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650536558220.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558229312.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532751892.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650530133976.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650566252791.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431759251.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554482570.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535337178.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604653566.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613646848.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650641969979.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592509946.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586315468.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583286967.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650527867600.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650568530492.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431259783.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434746825.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430427044.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650637661863.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650637458104.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650621860124.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576519324.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650546918691.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571288412.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559722574.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558455514.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613976921.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650600564593.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650594572830.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645076904.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650588736075.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426768965.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650543101330.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650649016081.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650632604947.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426797783.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425423337.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650603136912.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650546984816.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431891266.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429436125.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430375010.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650588578028.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650612285760.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581126068.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520638316.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614530667.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433166542.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650618260382.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565700555.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431478647.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625461662.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426447301.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429093025.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534447516.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432924363.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650631017703.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650523033712.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545684673.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425857951.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565901234.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604714388.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650607281465.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650579711366.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650566792411.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650628108244.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650590042685.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434650129.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650585465373.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650601060627.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429440139.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650631492788.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650643613543.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650605015846.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650646557103.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650634847542.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433851582.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650627927141.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430098484.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650549616494.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587159166.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571933066.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650607637823.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434244500.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650539188297.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433765521.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650634876244.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650538857014.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650530101833.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650637711522.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418366721.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558570210.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650609395246.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528017136.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429274200.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592218106.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428884770.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434431186.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650617533744.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650598022988.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650591820991.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650526826472.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650546213296.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650584092229.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650427022351.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650644270227.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650546256074.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432033048.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650530616992.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650624818083.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435388707.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650571751068.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650533738089.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432200498.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431032863.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614226250.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532697453.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650627536545.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613925164.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575817667.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650555100870.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625410944.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650627615346.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534491891.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650542666313.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650568945477.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431064956.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650524695116.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545901112.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564435792.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650607717989.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433567349.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586729330.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532887337.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426083012.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551222293.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430958386.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650597850285.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625899447.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650638882083.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650639917785.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650563284851.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650599410786.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418131262.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650538688272.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425799836.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650584305570.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650635063663.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428636687.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432609609.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428880830.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433514029.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532515895.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576692993.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650568975227.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650597456288.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581009068.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650578201608.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418496722.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522105595.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650527329592.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629483541.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520924875.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645970782.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564127870.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520454830.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522051647.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425230875.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619645462.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429294208.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650550945233.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645481877.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545666012.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650535043697.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434427125.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650645770124.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426337384.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650632081025.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418104759.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650552325872.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564148331.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650612309522.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650419678448.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650522893595.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650428495001.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433497525.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575415064.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434112403.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426015373.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650643866684.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650534121252.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650562088450.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615681245.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575301291.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650583198627.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650616907465.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650596076930.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650550118296.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613435485.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429767212.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650544009992.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559061617.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558214851.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650427000275.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650529667614.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426534195.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433761447.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650523058199.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613235686.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576784435.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429393303.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650582552473.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650539130833.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650610454141.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426949195.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435088303.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650581729446.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426211656.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559794953.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650609243349.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559781592.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429457239.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650593619704.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650563721192.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650563885051.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615485960.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576668270.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650616749443.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650548499293.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650593531246.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650580636851.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587173626.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614601842.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650608079566.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650637980701.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650533948573.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650600829828.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432411481.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551004190.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650424962011.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431698924.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432577480.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430388299.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650561318728.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650526991774.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650573012807.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435566224.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650601397989.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650586598724.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650554709332.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650643286722.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433600286.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650435026242.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418172329.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418818956.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426511041.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650525146333.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650580123708.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432678366.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650559057449.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528590233.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650533130335.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650650457860.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433769603.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425250214.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650619098186.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650617962070.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429262238.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520830135.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650434981846.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650431953662.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558889232.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650642535480.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565499249.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650545629013.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650630485028.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430978960.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425356146.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430962403.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650573754008.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650572296850.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650560807673.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429506210.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432485439.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650561669489.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650615149285.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650550571112.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606320103.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426734381.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629549184.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565135210.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425973404.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650633334842.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551480552.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650565977048.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575958368.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432495780.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650574393289.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650520634375.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650650512824.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430494992.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650603157925.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425162688.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650627186978.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592853007.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650526971993.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650613664407.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650425117501.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650614451981.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650596542527.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650591470873.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650625322801.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650521629270.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650532822396.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433608425.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650542046550.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650541868934.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650540180195.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650592780855.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650418059903.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650606387068.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433439943.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433923965.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564847853.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650558372772.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576357789.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650648955987.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650526765578.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650635773085.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650548541613.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650523694632.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650528057678.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650561782169.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650432750966.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650575101747.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650580866648.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650555138976.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650629188843.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650587624827.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650567258232.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650562549007.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650576402515.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564265673.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650611175854.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650585943705.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650430270447.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650564235671.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650540387835.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650551145971.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650604415465.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650580925347.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650585356488.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650577152883.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429708025.obj", "./backup/2022.04.23-11:29:41/objFiles/DCIM/1650544521417.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426400264.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650429883890.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650433389865.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426589277.obj", "./backup/2022.04.20-16:36:59/objFiles/DCIM/1650426624159.obj"};
//        String[] objFiles = {"./907obj/1651684262090.obj", "./907obj/1651703766850.obj", "./907obj/1651701247911.obj", "./907obj/1651712920968.obj", "./907obj/1651696070326.obj", "./907obj/1651688763391.obj", "./907obj/1651691243654.obj", "./907obj/1651698267966.obj", "./907obj/1651685869971.obj", "./907obj/1651685911407.obj", "./907obj/1651693607553.obj", "./907obj/1651690099229.obj", "./907obj/1651780327452.obj", "./907obj/1651694343628.obj", "./907obj/1651689060691.obj", "./907obj/1651695161648.obj", "./907obj/1651684794551.obj", "./907obj/1651699377011.obj", "./907obj/1651711395585.obj", "./907obj/1651770234996.obj", "./907obj/1651774018292.obj", "./907obj/1651703687049.obj", "./907obj/1651701109549.obj", "./907obj/1651781755873.obj", "./907obj/1651783523231.obj", "./907obj/1651703630187.obj", "./907obj/1651697184491.obj", "./907obj/1651700406849.obj", "./907obj/1651690800266.obj", "./907obj/1651723437846.obj", "./907obj/1651651530678.obj", "./907obj/1651722368583.obj", "./907obj/1651693696297.obj", "./907obj/1651695084949.obj", "./907obj/1651702776051.obj", "./907obj/1651774518135.obj", "./907obj/1651708135804.obj", "./907obj/1651771341069.obj", "./907obj/1651699640589.obj", "./907obj/1651760694318.obj", "./907obj/1651697364351.obj", "./907obj/1651691239574.obj", "./907obj/1651789153572.obj", "./907obj/1651692996587.obj", "./907obj/1651684746191.obj", "./907obj/1651688686870.obj", "./907obj/1651690221971.obj", "./907obj/1651785212271.obj", "./907obj/1651794455870.obj", "./907obj/1651794845413.obj", "./907obj/1651761608333.obj", "./907obj/1651690796151.obj", "./907obj/1651770002994.obj", "./907obj/1651773306634.obj", "./907obj/1651689971153.obj", "./907obj/1651700606874.obj", "./907obj/1651730494287.obj", "./907obj/1651795130926.obj", "./907obj/1651686033633.obj", "./907obj/1651705493129.obj", "./907obj/1651708217433.obj", "./907obj/1651699454566.obj", "./907obj/1651697744789.obj", "./907obj/1651702212147.obj", "./907obj/1651695002186.obj", "./907obj/1651647810635.obj", "./907obj/1651700025370.obj", "./907obj/1651786547711.obj", "./907obj/1651704645135.obj", "./907obj/1651695811204.obj", "./907obj/1651688204050.obj", "./907obj/1651701366927.obj", "./907obj/1651699592192.obj", "./907obj/1651699994310.obj", "./907obj/1651671163291.obj", "./907obj/1651689726969.obj", "./907obj/1651761290054.obj", "./907obj/1651689184695.obj", "./907obj/1651693641473.obj", "./907obj/1651657087254.obj", "./907obj/1651648410412.obj", "./907obj/1651779304373.obj", "./907obj/1651695745069.obj", "./907obj/1651677136029.obj", "./907obj/1651698880331.obj", "./907obj/1651788591553.obj", "./907obj/1651779003476.obj", "./907obj/1651785471410.obj", "./907obj/1651690707315.obj", "./907obj/1651725630904.obj", "./907obj/1651764026592.obj", "./907obj/1651698761369.obj", "./907obj/1651698928671.obj", "./907obj/1651716505226.obj", "./907obj/1651708196910.obj", "./907obj/1651705258088.obj", "./907obj/1651692169836.obj", "./907obj/1651690980767.obj", "./907obj/1651697636113.obj", "./907obj/1651697818869.obj", "./907obj/1651690619653.obj", "./907obj/1651720510027.obj", "./907obj/1651696266828.obj", "./907obj/1651784983591.obj", "./907obj/1651726795167.obj", "./907obj/1651686899932.obj", "./907obj/1651670818886.obj", "./907obj/1651714624425.obj", "./907obj/1651693517793.obj", "./907obj/1651732602263.obj", "./907obj/1651670498530.obj", "./907obj/1651690468107.obj", "./907obj/1651685082989.obj", "./907obj/1651791475011.obj", "./907obj/1651793089786.obj", "./907obj/1651790405331.obj", "./907obj/1651695322068.obj", "./907obj/1651702425647.obj", "./907obj/1651675636210.obj", "./907obj/1651694485409.obj", "./907obj/1651728507647.obj", "./907obj/1651777480673.obj", "./907obj/1651698287570.obj", "./907obj/1651781657219.obj", "./907obj/1651786289968.obj", "./907obj/1651701071387.obj", "./907obj/1651696970894.obj", "./907obj/1651699293110.obj", "./907obj/1651783143451.obj", "./907obj/1651686554794.obj", "./907obj/1651685403807.obj", "./907obj/1651784647537.obj", "./907obj/1651785766714.obj", "./907obj/1651698783933.obj", "./907obj/1651642889254.obj", "./907obj/1651695689054.obj", "./907obj/1651777212954.obj", "./907obj/1651727249488.obj", "./907obj/1651688678673.obj", "./907obj/1651785418496.obj", "./907obj/1651684799608.obj", "./907obj/1651695316947.obj", "./907obj/1651792579212.obj", "./907obj/1651787854712.obj", "./907obj/1651690652790.obj", "./907obj/1651694034347.obj", "./907obj/1651761986536.obj", "./907obj/1651704653253.obj", "./907obj/1651692376448.obj", "./907obj/1651694197166.obj", "./907obj/1651761746275.obj", "./907obj/1651697488233.obj", "./907obj/1651777070892.obj", "./907obj/1651787788492.obj", "./907obj/1651777282675.obj", "./907obj/1651779437590.obj", "./907obj/1651772171394.obj", "./907obj/1651791340631.obj", "./907obj/1651699475193.obj", "./907obj/1651684946468.obj", "./907obj/1651665687512.obj", "./907obj/1651696601821.obj", "./907obj/1651692571525.obj", "./907obj/1651778054153.obj", "./907obj/1651703861186.obj", "./907obj/1651662891473.obj", "./907obj/1651647025491.obj", "./907obj/1651778272993.obj", "./907obj/1651660219173.obj", "./907obj/1651643953336.obj", "./907obj/1651693292550.obj", "./907obj/1651689564190.obj", "./907obj/1651685689049.obj", "./907obj/1651700597576.obj", "./907obj/1651730011823.obj", "./907obj/1651702165250.obj", "./907obj/1651700926052.obj", "./907obj/1651779556454.obj", "./907obj/1651769348537.obj", "./907obj/1651691074267.obj", "./907obj/1651698773627.obj", "./907obj/1651761155052.obj", "./907obj/1651684803876.obj", "./907obj/1651754064816.obj", "./907obj/1651767130575.obj", "./907obj/1651774677231.obj", "./907obj/1651697541910.obj", "./907obj/1651763683935.obj", "./907obj/1651642583913.obj", "./907obj/1651690344171.obj", "./907obj/1651697054366.obj", "./907obj/1651790542014.obj", "./907obj/1651719047706.obj", "./907obj/1651704308909.obj", "./907obj/1651699099825.obj", "./907obj/1651757820597.obj", "./907obj/1651689672009.obj", "./907obj/1651692503544.obj", "./907obj/1651725866637.obj", "./907obj/1651696201785.obj", "./907obj/1651688418290.obj", "./907obj/1651703877027.obj", "./907obj/1651654009037.obj", "./907obj/1651684969186.obj", "./907obj/1651698181010.obj", "./907obj/1651684050289.obj", "./907obj/1651697582113.obj", "./907obj/1651698213161.obj", "./907obj/1651728861202.obj", "./907obj/1651775911593.obj", "./907obj/1651787468671.obj", "./907obj/1651730759392.obj", "./907obj/1651791743690.obj", "./907obj/1651703021184.obj", "./907obj/1651699797665.obj", "./907obj/1651674365087.obj", "./907obj/1651686367526.obj", "./907obj/1651762062417.obj", "./907obj/1651689125830.obj", "./907obj/1651699636509.obj", "./907obj/1651752452794.obj", "./907obj/1651790038028.obj", "./907obj/1651698221330.obj", "./907obj/1651687262930.obj", "./907obj/1651678536753.obj", "./907obj/1651730815871.obj", "./907obj/1651767089173.obj", "./907obj/1651668286051.obj", "./907obj/1651697408629.obj", "./907obj/1651698497292.obj", "./907obj/1651702751551.obj", "./907obj/1651693945450.obj", "./907obj/1651787253313.obj", "./907obj/1651687482189.obj", "./907obj/1651666919591.obj", "./907obj/1651786160713.obj", "./907obj/1651771579653.obj", "./907obj/1651650721077.obj", "./907obj/1651790614453.obj", "./907obj/1651686835970.obj", "./907obj/1651783047152.obj", "./907obj/1651777497232.obj", "./907obj/1651693970133.obj", "./907obj/1651704245785.obj", "./907obj/1651650580534.obj", "./907obj/1651696546230.obj", "./907obj/1651789743430.obj", "./907obj/1651684340574.obj", "./907obj/1651702923185.obj", "./907obj/1651701984311.obj", "./907obj/1651689854870.obj", "./907obj/1651781359452.obj", "./907obj/1651684823612.obj", "./907obj/1651699127851.obj", "./907obj/1651695891528.obj", "./907obj/1651702375915.obj", "./907obj/1651771648053.obj", "./907obj/1651643206137.obj", "./907obj/1651703017129.obj", "./907obj/1651668661810.obj", "./907obj/1651686564329.obj", "./907obj/1651696578289.obj", "./907obj/1651699678709.obj", "./907obj/1651668323253.obj", "./907obj/1651711683107.obj", "./907obj/1651795108192.obj", "./907obj/1651698617247.obj", "./907obj/1651704460126.obj", "./907obj/1651778174953.obj", "./907obj/1651685455548.obj", "./907obj/1651776028872.obj", "./907obj/1651697046232.obj", "./907obj/1651786077356.obj", "./907obj/1651767768619.obj", "./907obj/1651764770795.obj", "./907obj/1651764732793.obj", "./907obj/1651651098195.obj", "./907obj/1651689934293.obj", "./907obj/1651694566254.obj", "./907obj/1651701871688.obj", "./907obj/1651703682947.obj", "./907obj/1651715591004.obj", "./907obj/1651692751492.obj", "./907obj/1651667807653.obj", "./907obj/1651688397650.obj", "./907obj/1651695157570.obj", "./907obj/1651730412968.obj", "./907obj/1651701793291.obj", "./907obj/1651780413535.obj", "./907obj/1651779529509.obj", "./907obj/1651708221568.obj", "./907obj/1651704572010.obj", "./907obj/1651758166614.obj", "./907obj/1651722289967.obj", "./907obj/1651699889525.obj", "./907obj/1651651722373.obj", "./907obj/1651666477711.obj", "./907obj/1651683388291.obj", "./907obj/1651788726139.obj", "./907obj/1651673983113.obj", "./907obj/1651781333531.obj", "./907obj/1651700284770.obj", "./907obj/1651675665150.obj", "./907obj/1651693065171.obj", "./907obj/1651696404354.obj", "./907obj/1651694871994.obj", "./907obj/1651703141230.obj", "./907obj/1651762849937.obj", "./907obj/1651701718667.obj", "./907obj/1651731956747.obj", "./907obj/1651700402767.obj", "./907obj/1651760494235.obj", "./907obj/1651700571689.obj", "./907obj/1651690516913.obj", "./907obj/1651704142932.obj", "./907obj/1651689301570.obj", "./907obj/1651701722766.obj", "./907obj/1651776235615.obj", "./907obj/1651684938312.obj", "./907obj/1651692857887.obj", "./907obj/1651791023638.obj", "./907obj/1651793938445.obj", "./907obj/1651792800530.obj", "./907obj/1651692343630.obj", "./907obj/1651787511210.obj", "./907obj/1651780133215.obj", "./907obj/1651710967631.obj", "./907obj/1651775827650.obj", "./907obj/1651722133787.obj", "./907obj/1651774815155.obj", "./907obj/1651696624511.obj", "./907obj/1651704134828.obj", "./907obj/1651703850889.obj", "./907obj/1651700324074.obj", "./907obj/1651759049030.obj", "./907obj/1651762643934.obj", "./907obj/1651685412009.obj", "./907obj/1651685549515.obj", "./907obj/1651704270629.obj", "./907obj/1651702844970.obj", "./907obj/1651779676479.obj", "./907obj/1651757404798.obj", "./907obj/1651684888789.obj", "./907obj/1651690750567.obj", "./907obj/1651730525250.obj", "./907obj/1651691626868.obj", "./907obj/1651694946286.obj", "./907obj/1651682749593.obj", "./907obj/1651723880545.obj", "./907obj/1651692028548.obj", "./907obj/1651683709787.obj", "./907obj/1651785954673.obj", "./907obj/1651695795632.obj", "./907obj/1651783293111.obj", "./907obj/1651701739313.obj", "./907obj/1651686998190.obj", "./907obj/1651794572235.obj", "./907obj/1651783386270.obj", "./907obj/1651778023112.obj", "./907obj/1651697787990.obj", "./907obj/1651694590868.obj", "./907obj/1651792894169.obj", "./907obj/1651695051751.obj", "./907obj/1651688460771.obj", "./907obj/1651698493227.obj", "./907obj/1651704912648.obj", "./907obj/1651713368911.obj", "./907obj/1651760683974.obj", "./907obj/1651718643625.obj", "./907obj/1651730936671.obj", "./907obj/1651684501031.obj", "./907obj/1651665352673.obj", "./907obj/1651689474309.obj", "./907obj/1651704441685.obj", "./907obj/1651737028892.obj", "./907obj/1651701816067.obj", "./907obj/1651758283680.obj", "./907obj/1651718276172.obj", "./907obj/1651682169469.obj", "./907obj/1651726598366.obj", "./907obj/1651704657366.obj", "./907obj/1651696186230.obj", "./907obj/1651691608346.obj", "./907obj/1651696860347.obj", "./907obj/1651776596041.obj", "./907obj/1651684086087.obj", "./907obj/1651666183076.obj", "./907obj/1651687786656.obj", "./907obj/1651783376953.obj", "./907obj/1651780981994.obj", "./907obj/1651690667094.obj", "./907obj/1651688549630.obj", "./907obj/1651699667375.obj", "./907obj/1651752850215.obj", "./907obj/1651693313289.obj", "./907obj/1651689574491.obj", "./907obj/1651684879512.obj", "./907obj/1651702452550.obj", "./907obj/1651684742092.obj", "./907obj/1651794213557.obj", "./907obj/1651775520537.obj", "./907obj/1651794601248.obj", "./907obj/1651693819852.obj", "./907obj/1651701083649.obj", "./907obj/1651685813209.obj", "./907obj/1651767327036.obj", "./907obj/1651703516191.obj", "./907obj/1651675310150.obj", "./907obj/1651701596891.obj", "./907obj/1651666225133.obj", "./907obj/1651692533430.obj", "./907obj/1651725126732.obj", "./907obj/1651736739323.obj", "./907obj/1651664193133.obj", "./907obj/1651698932714.obj", "./907obj/1651698452928.obj", "./907obj/1651697841528.obj", "./907obj/1651644545478.obj", "./907obj/1651715310806.obj", "./907obj/1651697284809.obj", "./907obj/1651699423472.obj", "./907obj/1651685095224.obj", "./907obj/1651791546352.obj", "./907obj/1651752339958.obj", "./907obj/1651686215309.obj", "./907obj/1651785621951.obj", "./907obj/1651759956213.obj", "./907obj/1651700223768.obj", "./907obj/1651703420189.obj", "./907obj/1651774612257.obj", "./907obj/1651704312984.obj", "./907obj/1651766385360.obj", "./907obj/1651776918151.obj", "./907obj/1651663472313.obj", "./907obj/1651687451073.obj", "./907obj/1651698663812.obj", "./907obj/1651697477929.obj", "./907obj/1651700757652.obj", "./907obj/1651682009174.obj", "./907obj/1651780361750.obj", "./907obj/1651783108151.obj", "./907obj/1651770073416.obj", "./907obj/1651689967073.obj", "./907obj/1651753767615.obj", "./907obj/1651665569654.obj", "./907obj/1651668789952.obj", "./907obj/1651642931416.obj", "./907obj/1651695438888.obj", "./907obj/1651670139634.obj", "./907obj/1651780039234.obj", "./907obj/1651702755572.obj", "./907obj/1651651841149.obj", "./907obj/1651792791373.obj", "./907obj/1651782767618.obj", "./907obj/1651651416133.obj", "./907obj/1651660486154.obj", "./907obj/1651693091951.obj", "./907obj/1651790950228.obj", "./907obj/1651701600969.obj", "./907obj/1651695493603.obj", "./907obj/1651678152574.obj", "./907obj/1651784849791.obj", "./907obj/1651651062098.obj", "./907obj/1651686840047.obj", "./907obj/1651732962927.obj", "./907obj/1651702024430.obj", "./907obj/1651699938168.obj", "./907obj/1651777766894.obj", "./907obj/1651702143566.obj", "./907obj/1651779560553.obj", "./907obj/1651649901035.obj", "./907obj/1651691002569.obj", "./907obj/1651699415251.obj", "./907obj/1651690217912.obj", "./907obj/1651641820757.obj", "./907obj/1651791107450.obj", "./907obj/1651651474793.obj", "./907obj/1651752584654.obj", "./907obj/1651792655709.obj", "./907obj/1651684908365.obj", "./907obj/1651655469371.obj", "./907obj/1651652546738.obj", "./907obj/1651699278144.obj", "./907obj/1651679792733.obj", "./907obj/1651680525968.obj", "./907obj/1651690077669.obj", "./907obj/1651689215668.obj", "./907obj/1651700207468.obj", "./907obj/1651762151795.obj", "./907obj/1651771356651.obj", "./907obj/1651793842979.obj", "./907obj/1651760470482.obj", "./907obj/1651694181614.obj", "./907obj/1651771575553.obj", "./907obj/1651684108027.obj", "./907obj/1651642036297.obj", "./907obj/1651693107507.obj", "./907obj/1651647672869.obj", "./907obj/1651761006817.obj", "./907obj/1651684517612.obj", "./907obj/1651780705372.obj", "./907obj/1651683812735.obj", "./907obj/1651646737814.obj", "./907obj/1651694910268.obj", "./907obj/1651687989547.obj", "./907obj/1651786300314.obj", "./907obj/1651782867537.obj", "./907obj/1651779764772.obj", "./907obj/1651778584310.obj", "./907obj/1651701216933.obj", "./907obj/1651775453234.obj", "./907obj/1651703619891.obj", "./907obj/1651782168712.obj", "./907obj/1651779777031.obj", "./907obj/1651727762523.obj", "./907obj/1651776444031.obj", "./907obj/1651686488549.obj", "./907obj/1651701262270.obj", "./907obj/1651776313593.obj", "./907obj/1651704880647.obj", "./907obj/1651779125753.obj", "./907obj/1651728054786.obj", "./907obj/1651660385609.obj", "./907obj/1651690073568.obj", "./907obj/1651699458649.obj", "./907obj/1651703315227.obj", "./907obj/1651760890736.obj", "./907obj/1651686287630.obj", "./907obj/1651695020672.obj", "./907obj/1651772068152.obj", "./907obj/1651686456548.obj", "./907obj/1651695967946.obj", "./907obj/1651775516440.obj", "./907obj/1651696711445.obj", "./907obj/1651756883334.obj", "./907obj/1651782297192.obj", "./907obj/1651697399310.obj", "./907obj/1651791374693.obj", "./907obj/1651692323971.obj", "./907obj/1651753261517.obj", "./907obj/1651764884396.obj", "./907obj/1651687969932.obj", "./907obj/1651694427470.obj", "./907obj/1651702241170.obj", "./907obj/1651688783473.obj", "./907obj/1651685015815.obj", "./907obj/1651768926444.obj", "./907obj/1651685122350.obj", "./907obj/1651677812892.obj", "./907obj/1651695286930.obj", "./907obj/1651686144450.obj", "./907obj/1651795219629.obj", "./907obj/1651698083770.obj", "./907obj/1651776849812.obj", "./907obj/1651655364857.obj", "./907obj/1651704456011.obj", "./907obj/1651727841283.obj", "./907obj/1651792325573.obj", "./907obj/1651735687184.obj", "./907obj/1651766324078.obj", "./907obj/1651690236384.obj", "./907obj/1651683618786.obj", "./907obj/1651679060949.obj", "./907obj/1651769126693.obj", "./907obj/1651704001112.obj", "./907obj/1651777792931.obj", "./907obj/1651757062155.obj", "./907obj/1651701516189.obj", "./907obj/1651689224987.obj", "./907obj/1651643991492.obj", "./907obj/1651695887470.obj", "./907obj/1651780643134.obj", "./907obj/1651767041761.obj", "./907obj/1651646752059.obj", "./907obj/1651791642461.obj", "./907obj/1651777096793.obj", "./907obj/1651682714349.obj", "./907obj/1651767558218.obj", "./907obj/1651642032320.obj", "./907obj/1651701565808.obj", "./907obj/1651688811268.obj", "./907obj/1651774952111.obj", "./907obj/1651735157671.obj", "./907obj/1651648518830.obj", "./907obj/1651726866227.obj", "./907obj/1651752369115.obj", "./907obj/1651686625248.obj", "./907obj/1651672517541.obj", "./907obj/1651693675629.obj", "./907obj/1651772239614.obj", "./907obj/1651777092695.obj", "./907obj/1651685087074.obj", "./907obj/1651700184753.obj", "./907obj/1651768125896.obj", "./907obj/1651732506843.obj", "./907obj/1651678353332.obj", "./907obj/1651704519069.obj", "./907obj/1651697597669.obj", "./907obj/1651778436754.obj", "./907obj/1651789947674.obj", "./907obj/1651694630087.obj", "./907obj/1651788023013.obj", "./907obj/1651693165328.obj", "./907obj/1651641607258.obj", "./907obj/1651703927827.obj", "./907obj/1651688035292.obj", "./907obj/1651643796339.obj", "./907obj/1651773796350.obj", "./907obj/1651698920571.obj", "./907obj/1651647652174.obj", "./907obj/1651694084070.obj", "./907obj/1651697492315.obj", "./907obj/1651775926016.obj", "./907obj/1651697873615.obj", "./907obj/1651693895033.obj", "./907obj/1651646290054.obj", "./907obj/1651701959609.obj", "./907obj/1651728076587.obj", "./907obj/1651683461746.obj", "./907obj/1651738109266.obj", "./907obj/1651642044231.obj", "./907obj/1651664153912.obj", "./907obj/1651659393454.obj", "./907obj/1651690855230.obj", "./907obj/1651765439258.obj", "./907obj/1651697927309.obj", "./907obj/1651703416070.obj", "./907obj/1651704548987.obj", "./907obj/1651757124819.obj", "./907obj/1651689789927.obj", "./907obj/1651684433893.obj", "./907obj/1651776706051.obj", "./907obj/1651653088850.obj", "./907obj/1651752875557.obj", "./907obj/1651771309919.obj", "./907obj/1651734583687.obj", "./907obj/1651676937271.obj", "./907obj/1651759000453.obj", "./907obj/1651736229244.obj", "./907obj/1651770458235.obj", "./907obj/1651699528164.obj", "./907obj/1651690859308.obj", "./907obj/1651670204596.obj", "./907obj/1651682310446.obj", "./907obj/1651696761107.obj", "./907obj/1651791857630.obj", "./907obj/1651688882713.obj", "./907obj/1651793167658.obj", "./907obj/1651784418152.obj", "./907obj/1651679882787.obj", "./907obj/1651701097310.obj", "./907obj/1651666396953.obj", "./907obj/1651760084955.obj", "./907obj/1651681044055.obj", "./907obj/1651695403906.obj", "./907obj/1651782609732.obj", "./907obj/1651696733266.obj", "./907obj/1651683202252.obj", "./907obj/1651667655534.obj", "./907obj/1651692853809.obj", "./907obj/1651768320972.obj", "./907obj/1651763922417.obj", "./907obj/1651793802913.obj", "./907obj/1651787907154.obj", "./907obj/1651758634576.obj", "./907obj/1651754738637.obj", "./907obj/1651780721952.obj", "./907obj/1651700211533.obj", "./907obj/1651764736835.obj", "./907obj/1651773376195.obj", "./907obj/1651673049977.obj", "./907obj/1651698116966.obj", "./907obj/1651700562387.obj", "./907obj/1651689000650.obj", "./907obj/1651780371075.obj", "./907obj/1651775108936.obj", "./907obj/1651730490189.obj", "./907obj/1651692146170.obj", "./907obj/1651696274951.obj", "./907obj/1651703111375.obj", "./907obj/1651728808390.obj", "./907obj/1651673060270.obj", "./907obj/1651697625793.obj", "./907obj/1651773629553.obj", "./907obj/1651735025402.obj", "./907obj/1651679672529.obj", "./907obj/1651700148629.obj", "./907obj/1651668468193.obj", "./907obj/1651780627614.obj", "./907obj/1651676856388.obj", "./907obj/1651675382533.obj", "./907obj/1651663172974.obj", "./907obj/1651667065393.obj", "./907obj/1651793768788.obj", "./907obj/1651790721232.obj", "./907obj/1651789394948.obj", "./907obj/1651666677094.obj", "./907obj/1651687252650.obj", "./907obj/1651701416486.obj", "./907obj/1651698291671.obj", "./907obj/1651702628215.obj", "./907obj/1651701581367.obj", "./907obj/1651790465691.obj", "./907obj/1651673786208.obj", "./907obj/1651701346329.obj", "./907obj/1651663919693.obj", "./907obj/1651684224909.obj", "./907obj/1651733991149.obj", "./907obj/1651733753404.obj", "./907obj/1651692268188.obj", "./907obj/1651664517855.obj", "./907obj/1651672669294.obj", "./907obj/1651704773907.obj", "./907obj/1651691387874.obj", "./907obj/1651729081567.obj", "./907obj/1651686568430.obj", "./907obj/1651692556013.obj", "./907obj/1651691664209.obj", "./907obj/1651685265140.obj", "./907obj/1651778509534.obj", "./907obj/1651684525750.obj", "./907obj/1651690677428.obj", "./907obj/1651663183240.obj", "./907obj/1651677504893.obj", "./907obj/1651677707333.obj", "./907obj/1651736812048.obj", "./907obj/1651703363866.obj", "./907obj/1651704508770.obj", "./907obj/1651694323027.obj", "./907obj/1651665738011.obj", "./907obj/1651692347690.obj", "./907obj/1651788882530.obj", "./907obj/1651682115591.obj", "./907obj/1651670200517.obj", "./907obj/1651764322178.obj", "./907obj/1651701231347.obj", "./907obj/1651668215476.obj", "./907obj/1651681001332.obj", "./907obj/1651773493316.obj", "./907obj/1651788240734.obj", "./907obj/1651728395423.obj", "./907obj/1651780129134.obj", "./907obj/1651676766575.obj", "./907obj/1651785720373.obj", "./907obj/1651776317671.obj", "./907obj/1651691687007.obj", "./907obj/1651666861811.obj", "./907obj/1651733263644.obj", "./907obj/1651736108242.obj", "./907obj/1651753750433.obj", "./907obj/1651663729256.obj", "./907obj/1651665957509.obj", "./907obj/1651757110476.obj", "./907obj/1651686037750.obj", "./907obj/1651673214993.obj", "./907obj/1651699731609.obj", "./907obj/1651789077092.obj", "./907obj/1651785672696.obj", "./907obj/1651736771661.obj", "./907obj/1651728302229.obj", "./907obj/1651694369415.obj", "./907obj/1651760080861.obj", "./907obj/1651737300288.obj", "./907obj/1651735568571.obj", "./907obj/1651686645988.obj", "./907obj/1651731257387.obj", "./907obj/1651699175270.obj", "./907obj/1651699207451.obj", "./907obj/1651701144688.obj", "./907obj/1651778832153.obj", "./907obj/1651771783412.obj", "./907obj/1651703905930.obj", "./907obj/1651694399328.obj", "./907obj/1651756402432.obj", "./907obj/1651685138891.obj", "./907obj/1651781499397.obj", "./907obj/1651698501348.obj", "./907obj/1651774709410.obj", "./907obj/1651685934389.obj", "./907obj/1651732299668.obj", "./907obj/1651702415311.obj", "./907obj/1651730291101.obj", "./907obj/1651685245512.obj", "./907obj/1651698403410.obj", "./907obj/1651789122431.obj", "./907obj/1651753024858.obj", "./907obj/1651702325306.obj", "./907obj/1651690008273.obj", "./907obj/1651785664512.obj", "./907obj/1651738972744.obj", "./907obj/1651697792051.obj", "./907obj/1651752568914.obj", "./907obj/1651694813211.obj", "./907obj/1651792630848.obj", "./907obj/1651792260448.obj", "./907obj/1651692089508.obj", "./907obj/1651782007296.obj", "./907obj/1651685158430.obj", "./907obj/1651768341615.obj", "./907obj/1651757332274.obj", "./907obj/1651693121850.obj", "./907obj/1651727216489.obj", "./907obj/1651763800153.obj", "./907obj/1651696795290.obj", "./907obj/1651760348206.obj", "./907obj/1651778201855.obj", "./907obj/1651769726872.obj", "./907obj/1651692156474.obj", "./907obj/1651695467753.obj", "./907obj/1651692214390.obj", "./907obj/1651698765486.obj", "./907obj/1651782668855.obj", "./907obj/1651766614795.obj", "./907obj/1651729589687.obj", "./907obj/1651688596032.obj", "./907obj/1651692047088.obj", "./907obj/1651697473829.obj", "./907obj/1651731470605.obj", "./907obj/1651790023231.obj", "./907obj/1651771741097.obj", "./907obj/1651692127751.obj", "./907obj/1651690059030.obj", "./907obj/1651791647627.obj", "./907obj/1651757451882.obj", "./907obj/1651752902175.obj", "./907obj/1651765733153.obj", "./907obj/1651728373647.obj", "./907obj/1651784407831.obj", "./907obj/1651764466573.obj", "./907obj/1651691838832.obj", "./907obj/1651691825429.obj", "./907obj/1651703615546.obj", "./907obj/1651693404689.obj", "./907obj/1651726898241.obj", "./907obj/1651794549471.obj", "./907obj/1651696241028.obj", "./907obj/1651753771574.obj", "./907obj/1651754055656.obj", "./907obj/1651690869592.obj", "./907obj/1651753674301.obj", "./907obj/1651766332234.obj", "./907obj/1651702901547.obj", "./907obj/1651768527015.obj", "./907obj/1651752496721.obj", "./907obj/1651694798657.obj", "./907obj/1651683749027.obj", "./907obj/1651785990876.obj", "./907obj/1651696653496.obj", "./907obj/1651787666653.obj", "./907obj/1651775574252.obj", "./907obj/1651703343206.obj", "./907obj/1651784297214.obj", "./907obj/1651785580519.obj", "./907obj/1651782313813.obj", "./907obj/1651779149433.obj", "./907obj/1651687137489.obj", "./907obj/1651687023952.obj", "./907obj/1651774111313.obj", "./907obj/1651793121317.obj", "./907obj/1651792078771.obj", "./907obj/1651793280611.obj", "./907obj/1651701846911.obj", "./907obj/1651695847348.obj", "./907obj/1651784967033.obj", "./907obj/1651691802809.obj", "./907obj/1651792804671.obj", "./907obj/1651785744132.obj", "./907obj/1651694333328.obj", "./907obj/1651794665230.obj", "./907obj/1651696159531.obj", "./907obj/1651690759888.obj", "./907obj/1651703008974.obj", "./907obj/1651789162929.obj", "./907obj/1651792277030.obj", "./907obj/1651791479131.obj", "./907obj/1651791739590.obj", "./907obj/1651702230848.obj", "./907obj/1651780571912.obj", "./907obj/1651696799390.obj", "./907obj/1651783434970.obj", "./907obj/1651701186053.obj", "./907obj/1651701553571.obj", "./907obj/1651693928955.obj", "./907obj/1651687446987.obj", "./907obj/1651697774675.obj", "./907obj/1651699601464.obj", "./907obj/1651694821367.obj", "./907obj/1651697832209.obj", "./907obj/1651701905847.obj", "./907obj/1651696501727.obj", "./907obj/1651703668628.obj", "./907obj/1651700558292.obj", "./907obj/1651704030986.obj", "./907obj/1651694937128.obj", "./907obj/1651693884633.obj", "./907obj/1651688261814.obj", "./907obj/1651685279690.obj", "./907obj/1651704200611.obj", "./907obj/1651691137329.obj", "./907obj/1651693611612.obj", "./907obj/1651684875410.obj", "./907obj/1651694726229.obj", "./907obj/1651691422847.obj", "./907obj/1651698217249.obj", "./907obj/1651703806246.obj", "./907obj/1651688902291.obj", "./907obj/1651688645654.obj"};
////        String[] objFiles = {"./36obj/1650446718437.obj"};
//        System.out.println("total number of obj files: " + objFiles.length);
//        bench_obj(objFiles, true);


//        String[] objFiles = {"1650497349916"};
//        bench_obj(objFiles, false);

            //1650571224306
//        String[] objFiles = {"/Users/chaoranli/Downloads/1650452923311.obj"};
//            String[] objFiles = {"/Users/chaoranli/Downloads/1650571224306.obj"};
//            bench_obj(objFiles, true);
    }

    public static void initList(){
        basicTypes.add("boolean");
        basicTypes.add("boolean[]");
        basicTypes.add("boolean[][]");
        basicTypes.add("byte");
        basicTypes.add("byte[]");
        basicTypes.add("byte[][]");
        basicTypes.add("short");
        basicTypes.add("short[]");
        basicTypes.add("short[][]");
        basicTypes.add("char");
        basicTypes.add("char[]");
        basicTypes.add("char[][]");
        basicTypes.add("int");
        basicTypes.add("int[]");
        basicTypes.add("int[][]");
        basicTypes.add("long");
        basicTypes.add("long[]");
        basicTypes.add("long[][]");
        basicTypes.add("float");
        basicTypes.add("float[]");
        basicTypes.add("float[][]");
        basicTypes.add("double");
        basicTypes.add("double[]");
        basicTypes.add("double[][]");

//        basicTypes.add("void");
    }

    public static void reproduction(String objFilePath, boolean needPush) throws Exception {
        String objFile = "";

        if(needPush) {
            objFile = objFilePath.substring(objFilePath.lastIndexOf("/") + 1).replace(".obj", "");
            // push objFile to android
            String target = "/sdcard/Android/data/com.example.fuzzer/files/DCIM/" + objFile + ".obj";
            String command = adb_path + " push \"" + objFilePath + "\" \"" + target + "\"";
            System.out.println(command);
//        Process p = Runtime.getRuntime().exec(command);
//        int exitVal = p.waitFor();
//        System.out.println("cmd result: " + exitVal);
            ProcessBuilder pb = new ProcessBuilder(adb_path, "push", objFilePath, target);
            Process p = pb.start();
            int exitVal = p.waitFor();
            System.out.println("cmd result: " + exitVal);
            if(exitVal != 0) {
                System.out.println("push obj file failed");
                System.exit(exitVal);
            }
        }else{
            objFile = objFilePath;
        }

        int port = 6100;


        lastAvailablePid = pid;
        pid = getPID();
        System.out.println("PID:" + pid);
//        logMoniter(pid);

        record_str = "";
        hasSaved = false;
        KILL_BY_TIMEOUT = false;

        if(not_debug) {
            logMoniterTimeOutThread = new Thread(logMoniterTimeOutRun);
            logMoniterTimeOutThread.start();
        }else{
            Scanner scanner = new Scanner(System.in);
            System.out.println("wait for debugger, please start lldb server and client. Then press any key to continue");
            String line = scanner.nextLine();
        }


        Socket socket = new Socket("127.0.0.1", port);

        OutputStream output = socket.getOutputStream();
        PrintWriter writer = new PrintWriter(output, true);
        SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");//设置日期格式
        String date = df.format(new Date());// new Date()为获取当前系统时间，也可使用当前时间戳
        identifier = objFile + "|" + date;
        record_str = record_str + "\nobjFile" + objFile + "\n";
        writer.println("MODE0|" + objFile);

//        socket.shutdownOutput();

        InputStream input = socket.getInputStream();

        BufferedReader reader = new BufferedReader(new InputStreamReader(input));
        String feedback = reader.readLine();
        System.out.println("msg 1 from server: " + feedback);
        String feedback2 = reader.readLine();
        System.out.println("msg 2 from server: " + feedback2);
        record_str = record_str + "\n" + feedback2 + "\n";
        String feedback25 = reader.readLine();
        System.out.println("msg 2.5 from server: " + feedback25);
        record_str = record_str + "\nobj" + feedback25 + "\n";

        // code if can return
        String feedback3 = reader.readLine();
        System.out.println("msg 3 from server: " + feedback3);
        String pattern = "code:-{0,1}[0-9]+";
        while(feedback3!=null && !Pattern.matches(pattern, feedback3))
        {
            record_str = record_str + "\n" + feedback3 + "\n";
            feedback3 = reader.readLine();
        }
        if(feedback3!=null) {

            int code = Integer.parseInt(feedback3.replace("code:", ""));
            switch (code) {
                case 0:
                    record_str = record_str + "code 0: success\n";
                    break;
                case -1:
                    record_str = record_str + "code -1: NoSuchMethodException\n";
                    break;
                case -2:
                    record_str = record_str + "code -2: IllegalAccessException\n";
                    break;
                case -3:
                    record_str = record_str + "code -3: InvocationTargetException\n";
                    break;
                case -4:
                    record_str = record_str + "code -4: ClassNotFoundException\n";
                    break;
                case -5:
                    record_str = record_str + "code -5: IllegalArgumentException\n";
                    break;
                case -999:
                    record_str = record_str + "code -999: should not happen\n";
                    break;
                default:
                    record_str = record_str + "code ?: enter switch branch default\n";
            }

//            if(testThread!=null){
//                testThread.interrupt();
//                testProcess.destroy();
//                System.out.println(". line 506，接收到code说明程序运行完了，要销毁监听，并保存信息");
//            }

        }else{
            record_str = record_str + "code null: crash before code was sent\n";
        }


        socket.shutdownOutput();
        socket.shutdownInput();

        writer.close();
        output.close();
        reader.close();
        input.close();
        socket.close();

        got_message3 = true;
    }

    public static void bench_obj(String[] objFiles, boolean needPush) throws Exception {
        initList();

        Thread diedMoniterhread = new Thread(diedMoniterRun);
        diedMoniterhread.start();

        ADBForward();
        int count = 0;
        int index = 0;
        for (String objFile:objFiles) {
            System.out.println("\n\n=============== NEW =================");
            index++;
            System.out.println(index + "/" + objFiles.length);

            count++;
            reproduction(objFile, needPush);

            while (MAIN_LOOP_WAIT_FLAG) {
                TimeUnit.MILLISECONDS.sleep(1000);
            }

            if(count>40) {
                count = 0;
                collect_log();
                is_collecting_log = false;
            }
            MAIN_LOOP_WAIT_FLAG = true;
        }

        collect_log();
        is_collecting_log = false;

        TimeUnit.MILLISECONDS.sleep(3000);
        System.out.println("1111111");
        diedMoniterhread.interrupt();
        diedMoniterProcess.destroy();
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input keyevent 223");
        System.out.println("2222222");
    }

    public static void collect_log() throws Exception {
        is_collecting_log = true;
        ProcessBuilder pb = new ProcessBuilder("python", "py/check_tombstones.py");
        Process p = pb.start();
        InputStream in = p.getInputStream();
        byte[] sb = readStream(in);
        String str = new String(sb, "UTF-8");
        in.close();

        int exitVal = p.waitFor();
        System.out.println("cmd result: " + exitVal);
    }

    public static List<ApiDependency> loadApiDependency(){
        BufferedReader reader;
        try {
            reader = new BufferedReader(new FileReader(new File("jni12.0/dependency_api_call_sequence.json")));
            String txt = reader.readLine();
            reader.close();
            List<ApiDependency> apiDependency = JSON.parseArray(txt, ApiDependency.class);

            return apiDependency;

        }catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            System.out.println("read data file error.\n" + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.out.println(e.getMessage());
            e.printStackTrace();
        }
        return null;

    }

    // fullName 转变成JniClass
    public static JniClass getJniClass(String fullName, List<JniClass> jniList){
        System.out.println("要找的JNI: " + fullName);
        for (JniClass tem : jniList) {
            if(tem.fullName().equals(fullName)){
                return tem;
            }
        }

        return null;
    }

    public static ArrayList<String> get_pre_dependency(List<ApiDependency> apiDependency, JniClass b){
        ArrayList<String> As = new ArrayList<String>();
        String BFullFun = b.fullName();
        for (ApiDependency dependency:apiDependency) {
//            System.out.println(dependency.getB());
//            System.out.println(BFullFun);
             if (dependency.getB().equals(BFullFun)) {
                 As.add(dependency.getA());
             }
        }

        return As;
    }

    // jniList 所有java jni；apiDependency 所有api依赖关系；b 所要找的jni
    public static ArrayList<JniClass> addDependency(List<JniClass> jniList, List<ApiDependency> apiDependency){
        ArrayList<JniClass> jniList_dependency = new ArrayList<JniClass>();
        for (JniClass jni : jniList) {
            ArrayList<String> As = get_pre_dependency(apiDependency, jni);
            for (String A:As) {
                // 确认是jni方法
                JniClass temm = getJniClass(A, jniList);
                if(temm!=null){
                    jniList_dependency.add(temm);
                    jniList_dependency.add(jni);
                }else{
//                    System.out.println("jni not found");
//                    exit(1);
                }
            }
        }
        System.out.println(jniList_dependency.size());
        return jniList_dependency;
    }

    //
    public static void bench() throws Exception {
        System.out.println("Start bench");
        initList();
        System.out.println("initList complete");

        //监控程序执行
        Thread diedMoniterhread = new Thread(diedMoniterRun);
        System.out.println("diedMoniterhread complete");
        diedMoniterhread.start();

        ADBForward();

        List<JniClass> jniList = load();
        // below code is to enable D3G or not
//        List<JniClass> jniList_dependency = addDependency(jniList, apiDependency);
//        System.out.println("dependency 数量：" + jniList_dependency.size());
//        jniList = jniList_dependency;
//        exit(0);



        // for test only
//        jniList = jniList.subList(0,10);
        int total = jniList.size();

        int times_max = 10;
        int time = 0;
        API_INDEX = -1;
        while(time < times_max) {
            time++;
            //List顺序打乱
//            Collections.shuffle(jniList);

            for (JniClass jni : jniList) {
                API_INDEX = API_INDEX + 1;
                if (API_INDEX < STARTFROM) {
                    continue;
                }
                System.out.println("\n\nFrom here, new call!!!(" + API_INDEX + "/" + total + ")");
                jni.print();

                String className = jni.getClass_();
                String methodName = jni.getFun();
                String pars = jni.getParameters().toString();
                pars = pars.substring(1, pars.length() - 1);
                // [return_type] 去括号
                String res = jni.getReturn_().get(0);
                // 检查是否支持
                System.out.println("pars: " + pars);
                System.out.println("res: " + res);
                // single的时候，无参数暂时不测试；非single，可以测试
                if(single && pars.isEmpty())
                    continue;
//                if (!isSupportJNI(className, methodName, pars, res)) {
////                System.out.println("上面的方法不支持，跳过");
//                    continue;
//                }
                System.out.println("input:" + className + " " + res + " " + methodName + "(" + pars + ")");
                TCPClient(className, methodName, pars, res);
                while (MAIN_LOOP_WAIT_FLAG) {
                    TimeUnit.MILLISECONDS.sleep(1000);
                }
                MAIN_LOOP_WAIT_FLAG = true;
//                System.exit(0);
            }
            collect_log();
            is_collecting_log = false;
        }

        TimeUnit.MILLISECONDS.sleep(3000);
        System.out.println("1111111");
        diedMoniterhread.interrupt();
        diedMoniterProcess.destroy();
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input keyevent 223");
        System.out.println("2222222");

    }

    public static List<JniPath> get_dependency_api_call_sequence_paths(){
        BufferedReader reader;
        try {
            reader = new BufferedReader(new FileReader(new File("jni12.0/dependency_api_call_sequence_paths.json")));
            String txt = reader.readLine();
            reader.close();

            List<JniPath> JniPathList = JSON.parseArray(txt, JniPath.class);
            return JniPathList;
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;

    }

    public static List<JniClass> transform_JniPathList2JniClassList(List<JniPath> JniPathList, List<JniClass> jniList){
        List<JniClass> jniClassList = new ArrayList<JniClass>();
        for (JniPath jniPath : JniPathList) {
            for(String jniName: jniPath.getPath()) {
                JniClass jniClass = getJniClass(jniName, jniList);
                if(jniClass!=null){
                    jniClassList.add(jniClass);
                }else {
                    System.out.println("jni not found");
                    exit(1);
                }
            }

        }
        return jniClassList;
    }



    public static void bench_dependency() throws Exception {
        collect_log();

        initList();


        //监控程序执行
        Thread diedMoniterhread = new Thread(diedMoniterRun);
        diedMoniterhread.start();

        ADBForward();

        List<JniClass> jniList = load();
        List<JniPath> jniPathList = get_dependency_api_call_sequence_paths();
        System.out.println("jniPathList size " + jniPathList.size());

        List<JniClass> jniPathCLassList = transform_JniPathList2JniClassList(jniPathList, jniList);
        jniList = jniPathCLassList;



        // for test only
//        jniList = jniList.subList(0,10);

        int times_max = 10;
        int time = 0;
        int total = jniList.size() * times_max;

        API_INDEX = -1;
        while(time < times_max) {
            time++;
            //List顺序打乱
//            Collections.shuffle(jniList);

            for (JniClass jni : jniList) {
                API_INDEX = API_INDEX + 1;
                if (API_INDEX < STARTFROM) {
                    continue;
                }
                System.out.println("\n\nFrom here, new call!!!(" + API_INDEX + "/" + total + ")");
                jni.print();

                String className = jni.getClass_();
                String methodName = jni.getFun();
                String pars = jni.getParameters().toString();
                pars = pars.substring(1, pars.length() - 1);
                // [return_type] 去括号
                String res = jni.getReturn_().get(0);
                // 检查是否支持
                System.out.println("pars: " + pars);
                System.out.println("res: " + res);
                // single的时候，无参数暂时不测试；非single，可以测试
                if(single && pars.isEmpty())
                    continue;
//                if (!isSupportJNI(className, methodName, pars, res)) {
////                System.out.println("上面的方法不支持，跳过");
//                    continue;
//                }
                System.out.println("input:" + className + " " + res + " " + methodName + "(" + pars + ")");
                TCPClient(className, methodName, pars, res);
                while (MAIN_LOOP_WAIT_FLAG) {
                    TimeUnit.MILLISECONDS.sleep(1000);
                }
                MAIN_LOOP_WAIT_FLAG = true;
//                System.exit(0);
            }
            collect_log();
            is_collecting_log = false;
        }

        TimeUnit.MILLISECONDS.sleep(3000);
        System.out.println("1111111");
        diedMoniterhread.interrupt();
        diedMoniterProcess.destroy();
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input keyevent 223");
        System.out.println("2222222");

    }

    public static void benchTest() throws Exception {
        initList();

        Thread diedMoniterhread = new Thread(diedMoniterRun);
        diedMoniterhread.start();

        ADBForward();

        List<JniClass> jniList = load();
        //        System.out.println("jniList.subList(0,2).size()"+jniList.subList(0,2).size());
        int total = jniList.size();
        int index = -1;
//        List<JniClass> jniListShort = new ArrayList<>();
//        for (JniClass jni: jniList) {
//            index = index + 1;
//            System.out.print(index+" | ");
//            jni.print();
//        }

//        jniListShort.add(jniList.get(2893));
        boolean got = false;
        index = -1;
        for (JniClass jni: jniList) {
            if(got)break;
            index = index + 1;
//            if (index>2)break;
            System.out.println("\n\nFrom here, new call!!!(" + index + "/" + total + ")");
            jni.print();
            String className = jni.getClass_();
            String methodName = jni.getFun();
            String pars = jni.getParameters().toString();
            pars = pars.substring(1, pars.length()-1);
            // [return_type] 去括号
            String res = jni.getReturn_().get(0);
            // 检查是否支持
//            System.out.println("pars: " + pars);
//            System.out.println("res: " + res);
//            if(isSupportJNI(className, methodName, pars, res)){
//                System.out.println("上面的方法不支持，跳过");
//                continue;
//            }
//            System.out.println("跳过"+methodName);
            // android.os.HwBlob|putInt8Array
            // com.android.org.conscrypt.NativeCrypto|get_EVP_CIPHER_CTX_final_used
            // android.os.HwBlob|putString
            if(!className.equals(testClass) || !methodName.equals(testFun)){
//                System.out.println("跳过");
                continue;
            }
            got =true;
            System.out.println("actual input:" + className + " " + res + " " + methodName + "(" + pars + ")");
            TCPClient(className, methodName, pars, res);
            while (MAIN_LOOP_WAIT_FLAG){
                System.out.println("still in loop");
                TimeUnit.MILLISECONDS.sleep(100 * 1000);
            }
            System.out.println("jump out of loop");
            MAIN_LOOP_WAIT_FLAG = true;
        }

        TimeUnit.MILLISECONDS.sleep(3000);
        System.out.println("1111111");
        diedMoniterhread.interrupt();
        diedMoniterProcess.destroy();
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input keyevent 223");
        System.out.println("2222222");

    }

    public static void test() throws Exception{
        initList();

        Thread diedMoniterhread = new Thread(diedMoniterRun);
        diedMoniterhread.start();

        ADBForward();

        // for test
        System.out.println("ADB forwarding complete");
//        String className = "android.net.NetworkUtils";
//        String methodName = "testFun"; // 没这个方法
//        String methodName = "heapUseAfterFree"; // 只有这个能触发HWAsan
//        String methodName = "heapBufferOverflow"; // 不触发 正常运行
//        String methodName = "oriError"; // 原生搞错
//        String pars = "int";
//        String res = "int";
//        TCPClient("android.net.NetworkUtils", "heapUseAfterFree", "int", "int");
//        TCPClient("android.net.NetworkUtils", "oriError", "int", "int");
        TCPClient("android.net.NetworkUtils", "testFun", "int", "int");
//        TCPClient("android.graphics.drawable.VectorDrawable", "nAddChild", "long, long", "void");
//        TCPClient("android.database.CursorWindow", "nativePutBlob", "long, byte[], int, int", "boolean");
        TimeUnit.MILLISECONDS.sleep(3000);
        System.out.println("1111111");
        diedMoniterhread.interrupt();
        diedMoniterProcess.destroy();
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell input keyevent 223");
        System.out.println("2222222");
    }

    public static Boolean isSupportJNI(String className, String methodName, String pars, String res){
//        if(!basicTypes.contains(res)){
//            return false;
//        }
        if(pars.isEmpty()){
            return true;
        }
        String[] parArray = pars.split(",");
        for (String tem : parArray) {
            tem = tem.trim();
            if(!basicTypes.contains(tem)){
                return false;
            }
        }

        return true;
    }

    // 读取JNI files
    public static List<JniClass> load() {
        BufferedReader reader;
        try {
            reader = new BufferedReader(new FileReader(new File("jni12.0/jni_with_isStatic.json")));
//            JSONObject data = (JSONObject) JSON.parse(reader.readLine());
            String txt = reader.readLine();
            reader.close();

//            List<JniClass> JniClasses = JSON.parseArray(data.getJSONArray("array").toJSONString(), JniClass.class);
            List<JniClass> JniClasses = JSON.parseArray(txt, JniClass.class);


            return JniClasses;

        }catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            System.out.println("read data file error.\n" + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.out.println(e.getMessage());
            e.printStackTrace();
        }
        return null;
    }

    public static void ADBForward() throws Exception {
        String localPort = "6100";
        String serverPort = "7100";
        Boolean mForwardSuccess = false;


        //转发，
        System.out.println(adb_path + " -s "+DEVICE+" forward tcp:" + localPort + " tcp:" + serverPort);
        Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" forward tcp:" + localPort + " tcp:" + serverPort);

        while(!mForwardSuccess) {
            // 可以再执行adb forward --list解析一下结果判断是否转发成功
            Process process = Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" forward --list");
            DataInputStream dis = new DataInputStream(process.getInputStream());
            byte[] buf = new byte[8];
            int len = -1;
            StringBuilder sb = new StringBuilder();
            while ((len = dis.read(buf)) != -1) {
                String str = new String(buf, 0, len);
                sb.append(str);
            }
            String adbList = sb.toString().toString();
            System.out.println(adb_path + " -s "+DEVICE+" forward list=" + adbList);
            String[] forwardArr = adbList.split("\n");
            for (String forward : forwardArr) {
                System.out.println("forward=" + forward);
                if (forward.contains(localPort) && forward.contains(serverPort)) {
                    mForwardSuccess = true;
                }
            }
            TimeUnit.MILLISECONDS.sleep(1000);
        }
    }

    public static void TCPServer() {
        int port = 6100;

        try (ServerSocket serverSocket = new ServerSocket(port)) {

            System.out.println("Server is listening on port " + port);
            Socket socket;
            InputStream input;
            BufferedReader reader;
            String message_row;
            OutputStream output;
            PrintWriter writer;

            while (true) {
                socket = serverSocket.accept();

                System.out.println("New client connected, and say:");

                input = socket.getInputStream();
                reader = new BufferedReader(new InputStreamReader(input));
                message_row = reader.readLine();
                System.out.println(message_row);

                socket.shutdownInput();

                output = socket.getOutputStream();
                writer = new PrintWriter(output, true);
                writer.println("copy that");

                socket.shutdownOutput();


            }

        } catch (IOException ex) {
            System.out.println("Server exception: " + ex.getMessage());
            ex.printStackTrace();
        }

    }

    public static String getPID(){
        String activity = "MainActivity";

        Process process = null;
        String pid = "";
        try {
            while(pid.isEmpty()){
                process = Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell pidof "+PACKAGE_NAME);

                DataInputStream dis = new DataInputStream(process.getInputStream());
                byte[] buf = new byte[8];
                int len = -1;
                StringBuilder sb = new StringBuilder();
                while ((len = dis.read(buf)) != -1) {
                    String str = new String(buf, 0, len);
                    sb.append(str);
                }
//                if(!sb.toString().trim().isEmpty()){
                    pid = sb.toString().trim();
                    System.out.println("Obtain PID: " + pid);
//                }


                if(pid.isEmpty()){
//                    System.out.println("kill -9 lastAvailablePid:" + lastAvailablePid);
//                    Runtime.getRuntime().exec("kill -9 "+lastAvailablePid);
//                    lastAvailablePid
                    System.out.println(adb_path + " -s " + DEVICE + " shell am force-stop " + PACKAGE_NAME);
                    Runtime.getRuntime().exec(adb_path + " -s " + DEVICE + " shell am force-stop " + PACKAGE_NAME);
                    TimeUnit.MILLISECONDS.sleep(1000);
                    Runtime.getRuntime().exec(adb_path + " -s "+DEVICE+" shell am start "+PACKAGE_NAME+"/."+activity);
                    TimeUnit.MILLISECONDS.sleep(1000);
                }
            }
            return pid;
        } catch (IOException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static byte[] readStream(InputStream inStream) throws Exception {
        ByteArrayOutputStream outSteam = new ByteArrayOutputStream();

        byte[] buffer = new byte[1024];
        int len = -1;

        while ((len = inStream.read(buffer)) != -1) {
            outSteam.write(buffer, 0, len);
        }

        outSteam.close();
        return outSteam.toByteArray();

    }

    public static void saveLog(Thread logMoniterTimeOutThread, boolean HWAddressSanitizer){
        if(logMoniterTimeOutThread!=null) {
            logMoniterTimeOutThread.interrupt();
        }
        try {
            if(HWAddressSanitizer){
                // BufferedWriter out = new BufferedWriter(new FileWriter("hwasan_crash_log/" + API_INDEX + "|HWAddressSanitizer_" + identifier + ".log"));
                String crash_log_path = "hwasan_crash_log/" + API_INDEX + "|HWAddressSanitizer_" + identifier + ".log";
                crash_log_path = buildPathWithSystemSeparator(crash_log_path);
                BufferedWriter out = new BufferedWriter(new FileWriter(crash_log_path));
                out.write(record_str);
                System.out.println("======= SAVE FILE FROM =======");
                System.out.println(record_str);
                System.out.println("======= SAVE FILE END  =======");
                out.close();
                System.out.println("error log is saved in file: " + crash_log_path );
                // System.out.println("error log is saved in file: hwasan_crash_log/" + API_INDEX + "|" + identifier + ".log");
            }else{
//                BufferedWriter out = new BufferedWriter(new FileWriter("crash_log/" + API_INDEX + "|" + identifier + ".log"));
                String crash_log_path = "crash_log/" + API_INDEX + "|" + identifier + ".log";
                crash_log_path = buildPathWithSystemSeparator(crash_log_path);
                BufferedWriter out = new BufferedWriter(new FileWriter(crash_log_path));
                out.write(record_str);
                System.out.println("======= SAVE FILE FROM =======");
                System.out.println(record_str);
                System.out.println("======= SAVE FILE END  =======");
                out.close();
                System.out.println("error log is saved in file: " + crash_log_path );
                // System.out.println("error log is saved in file: crash_log/" + API_INDEX + "|" + identifier + ".log");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }

        boolean hasSaved = false;
        int retry_time = 0;
        while(!hasSaved && retry_time < 3 && !KILL_BY_TIMEOUT){
            try {
                retry_time++;
                TimeUnit.MILLISECONDS.sleep(1000);
                // String path = "/sdcard/Android/data/com.example.fuzzer/files/DCIM/" + objFileName;
                String path = objFileDir + "/" + objFileName;
                System.out.println(adb_path + " shell ls " + path);
                ProcessBuilder pb = new ProcessBuilder(adb_path, "shell", "ls", path);
                Process p = pb.start();
                InputStream in = p.getInputStream();
                byte[] sb = readStream(in);
                String str = new String(sb, "UTF-8");
                in.close();

                int exitVal = p.waitFor();
                System.out.println("cmd result: " + exitVal);
//                System.out.println("cmd output: " + str);
                if (exitVal == 0) {
                    hasSaved = true;
//                    System.exit(exitVal);
                }else{
                    System.out.println("cmd failed, tetry time: " + retry_time);
                }
//                if (str.contains("No such file or directory")) {
//                    System.out.println(str);
////                    System.exit(exitVal);
//                }else{
//                    hasSaved = true;
//                }
            } catch (IOException | InterruptedException e) {
                e.printStackTrace();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        if(retry_time>=3){
            System.out.println("save log fail: " + objFileName);
//            System.exit(0);
        }
//        String cmd="adb -s "+DEVICE+" logcat";
//        Process temProcess = null;
    }

    public static void diedMoniter(){
        // 2022-04-04 20:59:52.750 1722-4180/? I/ActivityManager: Process com.example.fuzzer (pid 5619) has died: fg  TOP
        // ActivityTaskManager:   Force finishing activity com.example.fuzzer/.MainActivity
        // Process 23969 exited due to signal 11 (Segmentation fault)
        String cmd=adb_path + " -s "+DEVICE+" logcat";
        BufferedReader br=null;
        diedMoniterProcess=null;
        boolean needRecorded = false;
        hasSaved = false;
        boolean HWAddressSanitizer = false;
//        Thread currentThread = Thread.currentThread();

        try {
            //先清空log
            Process temProcess = Runtime.getRuntime().exec(cmd + " --clear");
            temProcess.waitFor();
            diedMoniterProcess = Runtime.getRuntime().exec(cmd);
            //获取cmd命令的输出结果
            br=new BufferedReader(new InputStreamReader(diedMoniterProcess.getInputStream()));
            String tmp;
            // 获取时间戳
            long latest_active_time = currentTimeMillis();
            long first_time = currentTimeMillis();
            while ((tmp= br.readLine())!=null)
            {
                // 更新apk活跃时间
                if(pid!=null && !is_collecting_log) {
                    if (tmp.contains(pid)) {
                        latest_active_time = currentTimeMillis();
//                        System.out.println("有log输出，更新活跃时间");
                    } else if (((currentTimeMillis() - latest_active_time) > (10 * 1000)) && not_debug) {
                        // 10 秒无消息 认为程序退出了 应该输出log
                        System.out.println("*** diedMoniter: 3 time out, pid: " + pid);
                        System.out.println("MAIN_LOOP_WAIT_FLAG: " + MAIN_LOOP_WAIT_FLAG);
                        // 保存
                        if (!hasSaved) {
                            hasSaved = true;
                            saveLog(logMoniterTimeOutThread, HWAddressSanitizer);
                            System.out.println("1 exit request and save log file");
                            needRecorded = false;
                            HWAddressSanitizer = false;
                            MAIN_LOOP_WAIT_FLAG = false;
                        }
                    }
                }
                // 打印所有adb log
                if(PRINT_ADB_LOG)
                    System.out.println(".line 304 'adb logcat'|" + tmp);



                // 开始记录
                if((tmp.contains("ERROR: HWAddressSanitizer")) && !needRecorded){
//                if((tmp.contains("ERROR: HWAddressSanitizer") || tmp.contains("--------- beginning of crash") || tmp.contains("Exception:")) && !needRecorded){
                    if(!needRecorded){
                        record_str = record_str + "\n" + identifier + "\n";
                    }
                    needRecorded = true;
                    if(tmp.contains("ERROR: HWAddressSanitizer")){
                        HWAddressSanitizer = true;
                    }
                }

                // 持续记录
                if(needRecorded){
//                    System.out.println(tmp);
                    record_str = record_str + tmp + "\n";
                }

                // 判断是否结束1
                if(tmp.contains("Process com.example.fuzzer") && tmp.contains("has died")){
                    System.out.println("*** diedMoniter: " + tmp);
                    tmp = tmp.substring(tmp.indexOf("ActivityManager: Process"));
                    tmp = tmp.substring(tmp.indexOf("Process com.example.fuzzer (pid ")+"Process com.example.fuzzer (pid ".length(), tmp.indexOf(") has died:"));
                    tmp = tmp.trim();
                    System.out.println("*** diedMoniter: Died PID: " + tmp);
                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    if(tmp.equals(pid)){
                        System.out.println("*** diedMoniter: exit request, if 1");
                        // 保存
                        if(!hasSaved) {
                            hasSaved = true;
                            saveLog(logMoniterTimeOutThread, HWAddressSanitizer);
                            System.out.println("save log file");
                            needRecorded = false;
                            HWAddressSanitizer = false;
                            MAIN_LOOP_WAIT_FLAG = false;

                        }
                    }
                }
                // 判断是否结束2
                else if(tmp.contains("Process") && tmp.contains("exited due to signal")){
                    System.out.println("*** diedMoniter: " + tmp);
//                    tmp = tmp.substring(tmp.indexOf("Process"));
                    String a1 = "Process";
                    String a2 = "exited due to signal";
                    tmp = tmp.substring(tmp.indexOf(a1)+a1.length(), tmp.indexOf(a2));
                    tmp = tmp.trim();
                    System.out.println("*** diedMoniter: Died PID: " + tmp);
                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    if(tmp.equals(pid)){
                        System.out.println("*** diedMoniter: request, if 2");
                        // 保存
                        if(!hasSaved) {
                            hasSaved = true;
                            saveLog(logMoniterTimeOutThread, HWAddressSanitizer);
                            System.out.println("save log file");
                            needRecorded = false;
                            HWAddressSanitizer = false;
                            MAIN_LOOP_WAIT_FLAG = false;
                        }
                    }
                }
                // 判断是否结束3
                else if(tmp.contains("Fatal signal 11 (SIGSEGV)") && tmp.contains(".example.fuzzer")){
                    System.out.println("*** diedMoniter: " + tmp);
//                    tmp = tmp.substring(tmp.indexOf("Process"));
                    String a1 = "pid";
                    String a2 = "(.example.fuzzer)";
                    tmp = tmp.substring(tmp.indexOf(a1)+a1.length(), tmp.indexOf(a2));
                    tmp = tmp.trim();
                    System.out.println("*** diedMoniter: Died PID: " + tmp);
                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    if(tmp.equals(pid)){
                        System.out.println("*** diedMoniter: request, if 3");
                        // 保存
                        if(!hasSaved) {
                            hasSaved = true;
                            saveLog(logMoniterTimeOutThread, HWAddressSanitizer);
                            System.out.println("save log file");
                            needRecorded = false;
                            HWAddressSanitizer = false;
                            MAIN_LOOP_WAIT_FLAG = false;
                        }
                    }
                }// 判断是否结束4
                else if(tmp.contains("Force removing") && tmp.contains("com.example.fuzzer/.MainActivity")
                        && tmp.contains("app died, no saved state")){
                    System.out.println("*** diedMoniter: " + tmp);
//                    tmp = tmp.substring(tmp.indexOf("Process"));
//                    String a1 = "pid";
//                    String a2 = "(.example.fuzzer)";
//                    tmp = tmp.substring(tmp.indexOf(a1)+a1.length(), tmp.indexOf(a2));
//                    tmp = tmp.trim();
//                    System.out.println("*** diedMoniter: Died PID: " + tmp);
//                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    System.out.println("*** diedMoniter: request, if 4");
                    // 保存
                    if(!hasSaved) {
                        hasSaved = true;
                        saveLog(logMoniterTimeOutThread, HWAddressSanitizer);
                        System.out.println("save log file");
                        needRecorded = false;
                        HWAddressSanitizer = false;
                        MAIN_LOOP_WAIT_FLAG = false;
                    }

                }

            }

            diedMoniterProcess.waitFor();
        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }finally {
            if (br!=null){
                try {
                    br.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
            if (diedMoniterProcess != null) {
                diedMoniterProcess.destroy();
            }

        }
    }

//    public static void logMoniter(String port){
//        // TODO: crash 后要关闭记录 并保存
////        String cmd="adb -s "+DEVICE+" logcat --pid=" + port;
//        String[] cmd = new String[]{"adb", "-s", "DEVICE", "logcat", "--pid=" + port};
//        BufferedReader br=null;
//        boolean print = false;
//        boolean HWAddressSanitizer = false;
//        Thread currentThread = Thread.currentThread();
//        Thread logMoniterTimeOutThread = new Thread(logMoniterTimeOutRun);
//        try {
//            //logMoniterTimeOutRun
//            logMoniterTimeOutThread.start();
//
//            ProcessBuilder pb = new ProcessBuilder(cmd);
//            testProcess = pb.start();
//
//            //执行cmd命令
////            testProcess = Runtime.getRuntime().exec(cmd);
//            //获取cmd命令的输出结果
//            br = new BufferedReader(new InputStreamReader(testProcess.getInputStream()));
//
//            String tmp;
//            while (!currentThread.isInterrupted() && (tmp= br.readLine())!=null){
////                str.append(tmp).append("\n");
//                if((tmp.contains("ERROR: HWAddressSanitizer") || tmp.contains("--------- beginning of crash") || tmp.contains("Exception:")) && !print){
//                    print = true;
//                    if(tmp.contains("ERROR: HWAddressSanitizer")){
//                        HWAddressSanitizer = true;
//                    }
//                    record_str = record_str + "\n" + identifier + "\n";
//                }
//                if(print){
//                    System.out.println(tmp);
//                    record_str = record_str + tmp + "\n";
//                }
//
//            }
////            System.out.println("*** .line 279 ***");
//
//            testProcess.waitFor();
//
//        } catch (IOException e) {
//            e.printStackTrace();
//        } catch (InterruptedException e) {
//            currentThread.interrupt();
////            e.printStackTrace();
//            System.out.println("test进程被阻断2");
//        }finally {
//            System.out.println("API_INDEX: " + API_INDEX);
//            System.out.println("test进程被阻断3");
//            logMoniterTimeOutThread.interrupt();
//            try {
//                if(HWAddressSanitizer){
//                    BufferedWriter out = new BufferedWriter(new FileWriter("hwasan_crash_log/" + API_INDEX + "|HWAddressSanitizer_" + identifier + ".txt"));
//                    out.write(record_str);
//                    System.out.println("======= SAVE FILE FROM =======");
//                    System.out.println(record_str);
//                    System.out.println("======= SAVE FILE END  =======");
//                    out.close();
//                    System.out.println("error log is saved in file: crash_log/" + API_INDEX + "|" + identifier + ".txt");
//                }else{
//                    BufferedWriter out = new BufferedWriter(new FileWriter("crash_log/" + API_INDEX + "|" + identifier + ".txt"));
//                    out.write(record_str);
//                    System.out.println("======= SAVE FILE FROM =======");
//                    System.out.println(record_str);
//                    System.out.println("======= SAVE FILE END  =======");
//                    out.close();
//                    System.out.println("error log is saved in file: crash_log/" + API_INDEX + "|" + identifier + ".txt");
//                }
//
//            } catch (IOException e) {
//                e.printStackTrace();
//            }
//
//            if (br!=null){
//                try {
//                    br.close();
//                } catch (IOException e) {
//                    e.printStackTrace();
//                }
//            }
//            if (testProcess != null) {
//                testProcess.destroy();
//            }
//            System.out.println(".line 544 MAIN_LOOP_WAIT_FLAG = false");
//            MAIN_LOOP_WAIT_FLAG = false;
//
//        }// final end
//    }

//    static Runnable logMoniterRun = new Runnable(){
//        @Override
//        public void run() {
//            logMoniter(pid);
//        }
//    };

    static Runnable logMoniterTimeOutRun = new Runnable(){
        @Override
        public void run() {
            System.out.println(TIME_OUT_EVERY_API+"ms timeout: start");
            Process tem = null;
            try {
                sleep(TIME_OUT_EVERY_API);
                // kill -9 关掉进程
                KILL_BY_TIMEOUT = true;
                tem = Runtime.getRuntime().exec("kill -9 " + pid);
                tem.waitFor();
                tem = Runtime.getRuntime().exec(adb_path + " -s " + DEVICE + " shell am force-stop " + PACKAGE_NAME);
                tem.waitFor();
//                timeout = true;
                System.out.println("time out end, has kill process");
            } catch (InterruptedException e) {
//                e.printStackTrace();
                if(tem!=null)
                    tem.destroy();
            } catch (IOException e) {
                e.printStackTrace();
            } finally {
                System.out.println("timeout: finally");
            }

        }
    };

    static Runnable diedMoniterRun = new Runnable(){
        @Override
        public void run() {
            diedMoniter();
        }
    };


    public static void TCPClient(String className, String methodName, String pars, String res) throws IOException, InterruptedException {
        int port = 6100;

//        if(testThread!=null){
//            System.out.println("上一个线程状态: " + testThread.isAlive());
//            testThread.interrupt();
//            testProcess.destroy();
//            System.out.println("处理完后，上一个线程状态: " + testThread.isAlive());
//        }

        lastAvailablePid = pid;
        pid = getPID();
        System.out.println("PID:" + pid);
//        logMoniter(pid);

        record_str = "";
        hasSaved = false;
        KILL_BY_TIMEOUT = false;

        // 单个api测试，需要到时间杀进程
        boolean single_api = false;
        logMoniterTimeOutThread = new Thread(logMoniterTimeOutRun);
        logMoniterTimeOutThread.start();

//        testThread = new Thread(logMoniterRun);
//        testThread.start();

        Socket socket = new Socket("127.0.0.1", port);

        OutputStream output = socket.getOutputStream();
        PrintWriter writer = new PrintWriter(output, true);
        SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");//设置日期格式
        String date = df.format(new Date());// new Date()为获取当前系统时间，也可使用当前时间戳
        identifier = className + "|" + methodName + "|" + date;
        record_str = record_str + "\n" + className + "|" + methodName + "|" + pars + "|" + res + "\n";
        writer.println("MODE1|"+className + "|" + methodName + "|" + pars + "|" + res + "|" + API_INDEX);

//        socket.shutdownOutput();

        InputStream input = socket.getInputStream();

        BufferedReader reader = new BufferedReader(new InputStreamReader(input));
        String feedback = reader.readLine();
//        while(feedback==null){
//            feedback = reader.readLine();
//        }
        System.out.println("msg 1 from server: " + feedback);
        record_str = record_str + "\nobj" + feedback + "\n";
        if(feedback==null){
            System.out.println("1013 obj feedback is null");
//            System.exit(0);
        }
        objFileName = feedback.replace("fileName: ","").trim();

        String feedback2 = reader.readLine();
        System.out.println("msg 2 from server: " + feedback2);
        record_str = record_str + "\n" + feedback2 + "\n";
//        String feedback25 = reader.readLine();
//        System.out.println("msg 2.5 from server: " + feedback25);

//        try {
//            ObjectInputStream in = new ObjectInputStream(input);
//            MethodRecorder e = (MethodRecorder) in.readObject();
//            FileOutputStream fileOut =
//                    new FileOutputStream("test.obj");
//            ObjectOutputStream out = new ObjectOutputStream(fileOut);
//            out.writeObject(e);
//            out.close();
//            fileOut.close();
//        } catch (ClassNotFoundException e) {
//            e.printStackTrace();
//        }

        // code if can return
        String feedback3 = reader.readLine();
        System.out.println("msg 3 from server: " + feedback3);
        String pattern = "code:-{0,1}[0-9]+";

//        while(feedback3!=null && !Pattern.matches(pattern, feedback3))
//        {
//            record_str = record_str + "\n" + feedback3 + "\n";
////            feedback3 = reader.readLine();
//        }

        if(feedback3!=null) {

            int code = Integer.parseInt(feedback3.replace("code:", ""));
            switch (code) {
                case 0:
                    record_str = record_str + "code 0: success\n";
                    break;
                case -1:
                    record_str = record_str + "code -1: NoSuchMethodException\n";
                    break;
                case -2:
                    record_str = record_str + "code -2: IllegalAccessException\n";
                    break;
                case -3:
                    record_str = record_str + "code -3: InvocationTargetException\n";
                    break;
                case -4:
                    record_str = record_str + "code -4: ClassNotFoundException\n";
                    break;
                case -5:
                    record_str = record_str + "code -5: IllegalArgumentException\n";
                    break;
                case -999:
                    record_str = record_str + "code -999: should not happen\n";
                    break;
                default:
                    record_str = record_str + "code ?: enter switch branch default\n";
            }

//            MAIN_LOOP_WAIT_FLAG = false;
//            if(testThread!=null){
//                testThread.interrupt();
//                testProcess.destroy();
//                System.out.println(". line 506，接收到code说明程序运行完了，要销毁监听，并保存信息");
//            }

        }else{
            record_str = record_str + "code null: crash before code was sent\n";
        }


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

//        socket.shutdownOutput();
    }

    public static String buildPathWithSystemSeparator(String... paths){
        StringBuilder sb = new StringBuilder();
        for (String path : paths){
            // 如果构建器最后一个字符不是分隔符，并且路径不是空的，添加分隔符
            if (sb.length() > 0 && !path.endsWith(File.separator)) {
                sb.append(File.separator);
            }
            // 替换掉所有的 / 为系统分隔符
            sb.append(path.replace("/", File.separator));
        }
        String result = sb.toString().replace("|", "_").replace(" ", "_" ).replace(":", "_");
        result = getSaveFileDir() + File.separator + result;
        return result;
    }

    public static String buildPathwithSystemSeperator(String path) {
        String result = path.replace("/", File.separator).replace("|", "_").replace(" ", "_" ).replace(":", "_");
        result = getSaveFileDir() + File.separator + result;
        return result;
    }
}



