import com.alibaba.fastjson.JSON;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

import static java.lang.System.currentTimeMillis;
import static java.lang.System.exit;
import static java.lang.Thread.sleep;

public class Engine {
    // DEVICE number in ADB
    static String DEVICE = "";

    // fuzzing client package name
    static String PACKAGE_NAME = "com.example.fuzzer";
    static String root_path = System.getProperty("user.dir");
    // adb path
    static String adb_path = set_adb_path();

    // operating system seperator
    static String seperator = File.separator;

    static String os = System.getProperty("os.name");



    static int StartFrom = 0;
    static boolean PRINT_ADB_LOG = false;
    static int TIME_OUT_EVERY_API = 6 * 1000;
    static boolean KILL_BY_TIMEOUT = false;
    static String objFileName = "";
    static int API_INDEX = -1;
    static String pid;
    static String lastAvailablePid;
    static String identifier;
    static ArrayList<String> basicTypes = new ArrayList<String>() {};
    static Boolean MAIN_LOOP_WAIT_FLAG = true;
    static String record_str = "";
    static Process diedMoniterProcess=null;
    static String testClass = "";
    static String testFun = "";
    static boolean hasSaved = false;
    static Thread logMoniterTimeOutThread = null;
    static boolean is_collecting_log = false;
    static boolean not_debug = true;
    static boolean single = false;
    // 如果没有message3 说明程序死循环了
    static boolean got_message3 = false;

    // 读取json文件 并且返回一个JniClass的list
    public static List<JniClass> load() {
        BufferedReader reader;
        try {
            String json_path = root_path + "/jni12.0/jni_with_isStatic.json";
            reader = new BufferedReader(new FileReader(new File(json_path)));
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

    public static void analyzeJNI(){
        // 读取json文件 并且返回一个JniClass的list
        List<JniClass> jniList = load();
        // 生成jni的测试用例
        int totalJNINo = jniList.size();
        int apiHasObj = 0;
        System.out.println("total JNI number: " + totalJNINo);

        // 遍历 jniList 并检查有多少个独立的 class
        HashSet<String> classSet = new HashSet<String>();
        int count_static = 0;
        int count_non_static = 0;

        for (JniClass jni : jniList){
            if (jni.getStatic_()){
                count_static++;
        } else {
                count_non_static++;
            }
            classSet.add(jni.getClass_());

            List<String> parameters = jni.getParameters();

            boolean hasObj = false;
            for (String p : parameters){
                if (p.contains(".")){
                    hasObj = true;
                    apiHasObj++;
                    break;
                }
            }
            // 如果参数列表中没有对象，则 API 不是静态对象？？？ TODO：问超然为什么
//            if(!hasObj){
//                // API 不是静态方法
//                if(!jni.getStatic_()){
//                    apiHasObj++;
//                }
//            }
        }
        int classNo = classSet.size();
        System.out.println("total class number: " + classNo);
        System.out.println("total static API number: " + count_static);
        System.out.println("% static = " + Math.round((float)count_static/(float)classNo * 10000f)/100f + "\\%");
        System.out.println("total non-static API number: " + count_non_static);
        System.out.println("% non-static = " + Math.round((float)count_non_static/(float)classNo * 10000f)/100f + "\\%");
        System.out.println("total API number with object: " + apiHasObj);

    }

    public static void reproduction(String objFilePath, boolean needPush) throws Exception {
        String objFile = "";

        // if need push, push the obj file to the device
        if (needPush) {
            objFile = objFilePath.substring(objFilePath.lastIndexOf("/") + 1).replace(".obj", "");
            String target = "/storage/emulated/0/Android/data/com.example.fuzzer/files/DCIM";
            String command = adb_path + " push " + objFilePath + " " + target;
            System.out.println(command);
            ProcessBuilder pb;
            if (os.contains("Windows")) {
                pb = new ProcessBuilder("cmd", "/c", command);

            } else {
                pb = new ProcessBuilder(command);
            }
            Process p = pb.start();
            int exitVal = p.waitFor();
            System.out.println("cmd result: " + exitVal);
            // 如果 push 失败，直接退出，否则, objFile = ObjFilePath
            if (exitVal != 0) {
                System.out.println("push obj file failed");
                System.exit(exitVal);
            } else {
                objFile = objFilePath;
            }
        }

        int port = 6100;

        lastAvailablePid = pid;
        System.out.println("lastAvailablePid: " + lastAvailablePid);
        record_str = "";
        hasSaved = false;
        KILL_BY_TIMEOUT = false;

        if (not_debug) {
            // TODO: 做LogMonitorThread
            logMoniterTimeOutThread = new Thread(logMoniterTimeOutRun);
            logMoniterTimeOutThread.start();
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

    // init basicTypes list
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
    }

    static String set_adb_path() {
        // read file from FuzzingServer root directory
        // read txt file and get the adb path
        String adb_path = "";
        // read file from FuzzingServer root directory
        try {
            File file = new File(root_path + "/path.txt");
            System.out.println(root_path + "/path.txt");
            if (file.isFile() && file.exists()) {
                InputStreamReader read = new InputStreamReader(Files.newInputStream(file.toPath()));
                BufferedReader bufferedReader = new BufferedReader(read);
                String lineTxt = null;
                while ((lineTxt = bufferedReader.readLine()) != null) {
                    if (lineTxt.contains("adb_path")) {
                        adb_path = lineTxt.split("=")[1];
                    }
                }
                read.close();
            } else {
                System.out.println("adb_path.txt file not found");
            }
        } catch (Exception e) {
            System.out.println("read adb_path.txt error");
            e.printStackTrace();
        }
        return adb_path;
    }

}
