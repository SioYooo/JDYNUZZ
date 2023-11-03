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
            String txt = reader.readLine();
            reader.close();
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

    static Runnable logMoniterTimeOutRun = new Runnable(){
        @Override
        public void run() {
            System.out.println(TIME_OUT_EVERY_API+"ms timeout: start");
            Process tem = null;
            try {
                sleep(TIME_OUT_EVERY_API);
                KILL_BY_TIMEOUT = true;
                tem = Runtime.getRuntime().exec("kill -9 " + pid);
                tem.waitFor();
                tem = Runtime.getRuntime().exec(adb_path + " -s " + DEVICE + " shell am force-stop " + PACKAGE_NAME);
                tem.waitFor();
                System.out.println("time out end, has kill process");
            } catch (InterruptedException e) {
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

    public static void diedMoniter(){
        String cmd=adb_path + " -s "+DEVICE+" logcat";
        BufferedReader br=null;
        diedMoniterProcess=null;
        boolean needRecorded = false;
        hasSaved = false;
        boolean HWAddressSanitizer = false;

        try {
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
                if(pid!=null && !is_collecting_log) {
                    if (tmp.contains(pid)) {
                        latest_active_time = currentTimeMillis();
                    } else if (((currentTimeMillis() - latest_active_time) > (10 * 1000)) && not_debug) {
                        System.out.println("*** diedMoniter: 3 time out, pid: " + pid);
                        System.out.println("MAIN_LOOP_WAIT_FLAG: " + MAIN_LOOP_WAIT_FLAG);
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
                if(PRINT_ADB_LOG)
                    System.out.println(".line 304 'adb logcat'|" + tmp);
                if((tmp.contains("ERROR: HWAddressSanitizer")) && !needRecorded){
                    if(!needRecorded){
                        record_str = record_str + "\n" + identifier + "\n";
                    }
                    needRecorded = true;
                    if(tmp.contains("ERROR: HWAddressSanitizer")){
                        HWAddressSanitizer = true;
                    }
                }

                if(needRecorded){
                    record_str = record_str + tmp + "\n";
                }
                if(tmp.contains("Process com.example.fuzzer") && tmp.contains("has died")){
                    System.out.println("*** diedMoniter: " + tmp);
                    tmp = tmp.substring(tmp.indexOf("ActivityManager: Process"));
                    tmp = tmp.substring(tmp.indexOf("Process com.example.fuzzer (pid ")+"Process com.example.fuzzer (pid ".length(), tmp.indexOf(") has died:"));
                    tmp = tmp.trim();
                    System.out.println("*** diedMoniter: Died PID: " + tmp);
                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    if(tmp.equals(pid)){
                        System.out.println("*** diedMoniter: exit request, if 1");
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
                else if(tmp.contains("Process") && tmp.contains("exited due to signal")){
                    System.out.println("*** diedMoniter: " + tmp);
                    String a1 = "Process";
                    String a2 = "exited due to signal";
                    tmp = tmp.substring(tmp.indexOf(a1)+a1.length(), tmp.indexOf(a2));
                    tmp = tmp.trim();
                    System.out.println("*** diedMoniter: Died PID: " + tmp);
                    System.out.println(tmp.equals(pid) + " | " + tmp + " | " + pid);
                    if(tmp.equals(pid)){
                        System.out.println("*** diedMoniter: request, if 2");
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
                else if(tmp.contains("Fatal signal 11 (SIGSEGV)") && tmp.contains(".example.fuzzer")){
                    System.out.println("*** diedMoniter: " + tmp);
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
                }
                else if(tmp.contains("Force removing") && tmp.contains("com.example.fuzzer/.MainActivity")
                        && tmp.contains("app died, no saved state")){
                    System.out.println("*** diedMoniter: " + tmp);

                    System.out.println("*** diedMoniter: request, if 4");
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

    public static void saveLog(Thread logMoniterTimeOutThread, boolean HWAddressSanitizer){
        if(logMoniterTimeOutThread!=null) {
            logMoniterTimeOutThread.interrupt();
        }
        try {
            if(HWAddressSanitizer){
                BufferedWriter out = new BufferedWriter(new FileWriter("hwasan_crash_log/" + API_INDEX + "|HWAddressSanitizer_" + identifier + ".log"));
                out.write(record_str);
                System.out.println("======= SAVE FILE FROM =======");
                System.out.println(record_str);
                System.out.println("======= SAVE FILE END  =======");
                out.close();
                System.out.println("error log is saved in file: hwasan_crash_log/" + API_INDEX + "|" + identifier + ".log");
            }else{
                BufferedWriter out = new BufferedWriter(new FileWriter("crash_log/" + API_INDEX + "|" + identifier + ".log"));
                out.write(record_str);
                System.out.println("======= SAVE FILE FROM =======");
                System.out.println(record_str);
                System.out.println("======= SAVE FILE END  =======");
                out.close();
                System.out.println("error log is saved in file: crash_log/" + API_INDEX + "|" + identifier + ".log");
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
                String path = "/sdcard/Android/data/com.example.fuzzer/files/DCIM/" + objFileName;
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
                pid = sb.toString().trim();
                System.out.println("Obtain PID: " + pid);


                if(pid.isEmpty()){
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
        String adb_path = "";
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

    public static void TCPClient(String className, String methodName, String pars, String res) throws IOException, InterruptedException {
        int port = 6100;

        lastAvailablePid = pid;
        pid = getPID();
        System.out.println("PID:" + pid);

        record_str = "";
        hasSaved = false;
        KILL_BY_TIMEOUT = false;

        // 单个api测试，需要到时间杀进程
        boolean single_api = false;
        logMoniterTimeOutThread = new Thread(logMoniterTimeOutRun);
        logMoniterTimeOutThread.start();

        Socket socket = new Socket("127.0.0.1", port);

        OutputStream output = socket.getOutputStream();
        PrintWriter writer = new PrintWriter(output, true);
        SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");//设置日期格式
        String date = df.format(new Date());// new Date()为获取当前系统时间，也可使用当前时间戳
        identifier = className + "|" + methodName + "|" + date;
        record_str = record_str + "\n" + className + "|" + methodName + "|" + pars + "|" + res + "\n";
        writer.println("MODE1|"+className + "|" + methodName + "|" + pars + "|" + res + "|" + API_INDEX);

        InputStream input = socket.getInputStream();

        BufferedReader reader = new BufferedReader(new InputStreamReader(input));
        String feedback = reader.readLine();

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

        String feedback3 = reader.readLine();
        System.out.println("msg 3 from server: " + feedback3);
        String pattern = "code:-{0,1}[0-9]+";

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
            if (dependency.getB().equals(BFullFun)) {
                As.add(dependency.getA());
            }
        }

        return As;
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
                    System.out.println("jni not found");
//                    System.out.println("jni not found");
//                    exit(1);
                }
            }
        }
        System.out.println(jniList_dependency.size());
        return jniList_dependency;
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
}
