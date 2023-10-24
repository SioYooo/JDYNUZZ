package javaLink;/////////////////////////////////////////////////////////////////////////////////////////////////
// 倒叙 从permission check 函数开始去找所有调用过的函数
// permission check提取传入的string (e.g. android.permission.bluetooth)
//
//
/////////////////////////////////////////////////////////////////////////////////////////////////


import soot.*;
import soot.jimple.StringConstant;
import soot.jimple.internal.JAssignStmt;
import soot.jimple.internal.JInvokeStmt;
import soot.jimple.spark.SparkTransformer;
import soot.jimple.toolkits.callgraph.CHATransformer;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;
import soot.jimple.toolkits.callgraph.Sources;
import soot.options.Options;
import util.config;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class JavaLink extends SceneTransformer {

    public static boolean RUN_ON_MAC = true;
    public static ArrayList<String> uniqueMethodList = new ArrayList();

    static LinkedList<String> excludeList;
    //    //第一张组测试
//    static String mainClassStrLast = "LocationManagerService";
//    static String mainClassStr = "com.android.server." + mainClassStrLast;
//    //第二张组测试
//    static String mainClassStrLast = "ActivityRecognitionHardware";
//    static String mainClassStr = "android.hardware.location." + mainClassStrLast;
    //第二张组测试
//    static String mainClassStrLast = "LocationManagerService";
//    static String mainClassStr = "com.android.server." + mainClassStrLast;

    static String mainClassStrLast = "ICameraService$Stub$Proxy";
    static String mainClassStr = "android.hardware." + mainClassStrLast;
    static ArrayList<String> starts_call = new ArrayList<String>();
    //    static String mainClassStr = "android.content.Context";
    static SootClass mainClass = null;

    public static void run(String mainClassStrLast, String mainClassStr, int mode, ArrayList<String> starts_call) throws IOException {
        ArrayList<String> supportClassList = new ArrayList<String>();
        run(mainClassStrLast, mainClassStr, mode, starts_call, supportClassList);
    }

    public static void run(String mainClassStrLast, String mainClassStr, int mode, ArrayList<String> starts_call, ArrayList<String> supportClassList) throws IOException {
        String mode1 = "wjtp.parent_call";
        String mode2 = "wjtp.permission_finder";
        String transform_str = mode1;
        if (mode ==1) {
            transform_str = mode1;
        }else if(mode ==2) {
            transform_str = mode2;
        }
        JavaLink.mainClassStrLast = mainClassStrLast;
        JavaLink.mainClassStr = mainClassStr;
        JavaLink.starts_call = starts_call;
        System.out.println("mainClassStr: " + mainClassStr);
        System.out.println("mainClassStrLast: " + mainClassStrLast);
        //遍历打印JavaLink.starts_call
        for (int i = 0; i < JavaLink.starts_call.size(); i++) {
            System.out.println("starts_call: " + JavaLink.starts_call.get(i));
        }
//        String[] classesDir = {"E:\\AndroidSdk\\sources\\android-26", "C:/Program Files/Java/jre1.8.0_191/lib/rt.jar"};
//        String classesDir = "E:/AndroidSdk/sources/android-26";

//        String classesDir = "test/testCallGraph";
//        String mainClass = "testers.CallGraphs";

//		//set classpath
//        String javapath = System.getProperty("java.class.path");
        String javapath = "";
//        String jreDir = "C:/Program Files/Java/jre1.8.0_191/lib/rt.jar";
//        String jceDir = "C:/Program Files/Java/jre1.8.0_191/lib/jce.jar";

//        String jreDir = "C:/Program Files/Java/jre-9/lib/jrt-fs.jar";
//        String jceDir = "";
//        String path = classesDir+File.pathSeparator+jredir;
//        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + "E:/AndroidSdk/platforms/android-26/android.jar";
        String path = config.loadJarPath();

//        System.out.println(path);

//        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + "E:/android-hidden-api-master/android-26/services.jar";
//        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + classesDir;
//        Options.v().set_prepend_classpath(true);
        Scene.v().setSootClassPath(path);
//        ArrayList<String> listtt = new ArrayList<String>();
//        Options.v().set_src_prec(Options.src_prec_java);
//        listtt.add("/Volumes/android/android-8.0.0_r34/frameworks/base/services/core/java/com/android/server/display/WifiDisplayAdapter.java");
//        Options.v().set_process_dir(listtt);
//        Options.v().set_soot_classpath(path);
//        Scene.v().setSootClassPath(jredir+File.pathSeparator+"C:/Program Files/Java/jre1.8.0_191/lib/rt.jar");
//        Scene.v().setSootClassPath("E:/AndroidSdk/sources/android-26"+File.pathSeparator+jredir);

        //add an intra-procedural analysis phase to Soot
        JavaLink analysis = new JavaLink();
        Transform temTransform = PackManager.v().getPack("wjtp").get(transform_str);
        if(temTransform == null) {
            PackManager.v().getPack("wjtp").add(new Transform(transform_str, analysis));
        }
//        PackManager.v().getPack("wjtp").add(new Transform("wjtp.parent_call", analysis));
//        PackManager.v().getPack("wjtp").add(new Transform("wjtp.permission_finder", analysis));


        excludeJDKLibrary();

//        Options.v().set_process_dir(Arrays.asList(classesDir));

        Options.v().set_whole_program(true);
        Options.v().set_app(true);
        Options.v().set_validate(true);



//        Scene.v().loadNecessaryClasses();
        SootClass c = Scene.v().forceResolve(mainClassStr, SootClass.BODIES);
        for(String classTem : supportClassList){
            Scene.v().forceResolve(classTem, SootClass.BODIES);
        }

        //        SootClass c = Scene.v().loadClassAndSupport(mainClass);
        c.setApplicationClass();
//        Scene.v().addBasicClass("com.android.server.LocationManagerService");
        Scene.v().loadNecessaryClasses();

//        String tem222 = c.getFilePath();
//        List<SootMethod> tem2 = c.getMethods();

//        SootMethod method = c.getMethodByName("ignoreNetwork");
//        List entryPoints = new ArrayList();
//        entryPoints.add(method);
//        Scene.v().setEntryPoints(entryPoints);

        //全部设置entrypoint 并找到mainclass
        List<SootMethod> entryPoints = new ArrayList<SootMethod>();
        for(SootClass sc : Scene.v().getApplicationClasses()) {
            if(!sc.getName().contains("jdk.")){
                //输出所有加载的class名称
//                System.err.println(sc);

                if(sc.getName().equals(mainClassStr)){
                    mainClass = sc;
                }
//                else if(sc.getName().contains("com.android.server")){
//                    System.err.println("Find server class:" + sc);
//                }

                for (SootMethod m : sc.getMethods()) {
                    entryPoints.add(m);
                }
            }
        }

        if(mainClass==null){
            System.err.println("未找到指定的mainClass");
            System.exit(0);
        }
//        System.exit(0);
//        SootMethod aaaa = entryPoints.get(entryPoints.size()-1);
        Scene.v().setEntryPoints(entryPoints);
//        SootClass bbb = Scene.v().getMainClass();


//        Options.v().set_app(true);
//        SootClass appclass = Scene.v().loadClassAndSupport(mainClass);
//        Scene.v().setMainClass(appclass);
//        Scene.v().loadNecessaryClasses();


        //enable call graph
        enableCHACallGraph();
//        enableSparkCallGraph();

        PackManager.v().runPacks();

        //打开txt文件输入流
        String outputDir = "jni_warpper";
        BufferedWriter out = new BufferedWriter(new FileWriter(outputDir + "/" + mainClassStr + ".txt")); //创建文件缓冲输出流
        System.out.println("=============");
        System.out.println("=============");
        System.out.println("=============");
        for(String tem: uniqueMethodList){
            // 不输出内部类的函数
            Pattern p = Pattern.compile("\\$[0-9]+");
            Matcher m = p.matcher(tem);
            if(!m.find()){
                System.out.println(tem);
                out.write(tem + "\n");
            }

        }
        out.close();
    }

    private static void excludeJDKLibrary()
    {
        Options.v().set_exclude(excludeList());
        Options.v().set_no_bodies_for_excluded(true);
        Options.v().set_allow_phantom_refs(true);
    }

    private static void enableSparkCallGraph() {
        /*
        - verbose. (设定SPARK在分析过程中，打印多种信息【提示信息】)
        - propagator SPARK. (包含两个传播算法，原生迭代算法，基于worklist的算法)
        - simple-edges-bidirectional. (如果设置为真，则所有的边都为双向的)
        - on-fly-cg.（通过设置此选项，进行更加精确的points-to分析，得到精确的call graph）
        - set-impl. (描述points-to集合的实现。可能的值为hash,bit,hybrid,array,double)
        - double-set-old以及double-set-new.
         */
        //Enable Spark
        HashMap<String,String> opt = new HashMap<String,String>();
        opt.put("propagator","worklist");
        opt.put("simple-edges-bidirectional","false");
        opt.put("on-fly-cg","true");
        opt.put("set-impl","double");
        opt.put("double-set-old","hybrid");
        opt.put("double-set-new","hybrid");
        opt.put("pre_jimplify", "true");
        SparkTransformer.v().transform("",opt);
        PhaseOptions.v().setPhaseOption("cg.spark", "enabled:true");
    }

    private static void enableCHACallGraph() {
        CHATransformer.v().transform();
    }

    private static LinkedList<String> excludeList()
    {
        if(excludeList==null)
        {
            excludeList = new LinkedList<String> ();

            excludeList.add("java.");
            excludeList.add("javax.");
            excludeList.add("sun.");
            excludeList.add("sunw.");
            excludeList.add("com.sun.");
            excludeList.add("com.ibm.");
            excludeList.add("com.apple.");
            excludeList.add("apple.awt.");

            excludeList.add("android.os.Message");
            excludeList.add("android.os.Handler");

//            excludeList.add("android.os.Handler");
        }
        return excludeList;
    }

    public List<SootClass> getSUbclasses(SootClass c){
        List<SootClass> subclasses= new ArrayList<SootClass>();
        for (SootClass sc : Scene.v().getApplicationClasses()) {
            if(sc.hasSuperclass()){
                SootClass superClass = sc.getSuperclass();
                if(superClass.getName().equals(c.getName())){
                    subclasses.add(sc);
                }
            }
        }
        return subclasses;
    }


    public List<SootClass> getInnerClass(SootClass c){
        List<SootClass> innerClass= new ArrayList<SootClass>();
        for (SootClass sc : Scene.v().getApplicationClasses()) {
            if(sc.getName().contains(c.getName())){
                innerClass.add(sc);
            }
        }
        return innerClass;
    }

    public SootClass getInnerClass(SootClass c, String className){
        for (SootClass sc : Scene.v().getApplicationClasses()) {
            if(sc.getName().contains("$Proxy")){
                int u=0;
                boolean aaaaaaa = sc.getName().contains(c.getName()+"$"+className);
            }
            if(sc.getName().contains(c.getName()+"$"+className)){
                return sc;
            }
        }
        return null;
    }

    public SootClass getClass(String className){
        for (SootClass sc : Scene.v().getApplicationClasses()) {
            if(sc.getName().contains(className)){
                return sc;
            }
        }
        return null;
    }

    protected void pre_visit(SootMethod m, SootMethod p, CallGraph callGraph, CallGraph bigCallGraph, List<String> permissionStrs, List<String> visitedMethodSig){
        //有问题不能继续分析下去

        //防止重复走死循环
        if(!visitedMethodSig.contains(m.getSignature())) {
            if(!m.getSignature().contains("$Stub: boolean onTransact(")){
                visitedMethodSig.add(m.getSignature());
            }
        }else{
            return;
        }

        //AIDL相关分析
        if(m.getSignature().contains("$Stub: boolean onTransact(")){
            //stub -> interface, interface -> Proxy
            SootClass classProxy = getInnerClass(m.getDeclaringClass(),"Proxy");
            SootMethod mthodInterface = classProxy.getMethod(p.getName(),p.getParameterTypes());
            System.out.println("===FROM=====" + m.toString() + "========");
            System.out.println("===TO=====" + mthodInterface.toString() + "========");
            m = mthodInterface;

//            System.exit(2);
//            Iterator<Edge> temEdgesIterator = callGraph.edgesInto(mthodInterface);
//            Iterator<MethodOrMethodContext> parents = new Sources(temEdgesIterator);

            //            if(m.getDeclaringClass().getName().contains("com.android.server.")) {

//            List<SootClass> AIDLclasses= new ArrayList<SootClass>();
//            for (SootClass sc : Scene.v().getApplicationClasses()) {
//                try{
//                    if(sc.getName().contains("android.location.LocationManager")){
//                        int a =0;
//                    }
//                    List<Type> types = sc.getMethods().get(0).getParameterTypes();
//                    for (Type t : types) {
//                        if(m.getDeclaringClass().getName().contains(t.toString())){
//                            AIDLclasses.add(sc);
//                            break;
//                        }
//                    }
//                }catch (Exception e){
//
//                }
//            }
//
//            if(AIDLclasses.size()==1){
//                SootMethod aidlParent =AIDLclasses.get(0).getMethod(p.getName(),p.getParameterTypes());
//                pre_visit(aidlParent, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);
//                return;
//            }


//                String[] classArr = m.getDeclaringClass().getName().split("\\.");
//                String classLast = classArr[classArr.length - 1].replace("Service", "");
//                String func = m.getName();
//                SootMethod aidlParent = null;
//                for (SootClass sc : Scene.v().getApplicationClasses()) {
//                    if (sc.getName().contains("." + classLast) && !sc.getName().contains("Service")) {
//                        try {
//                            aidlParent = sc.getMethodByName(func);
//                        } catch (Exception e) {          //()里为接收try{}代码块中出现异常的类型
////                                    System.err.println("这个Service在Manager无对应函数");
//                        }
//                        break;
//                    }
//                }
//                if (aidlParent != null) {
//                    pre_visit(aidlParent, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);
//                }
        }

        // CFG逆向回溯终止API 前兩個涉及handler處理
        // onReceive onChange都是listener无法向上追溯
        if(m.getDeclaringClass().getName().contains("android.os.Handler") || m.getSignature().contains("handleMessage(android.os.Message)")){
            return;
//                    System.out.println(old.PrintColor.ANSI_RESET + m + old.PrintColor.ANSI_GREEN + " <=== " + parent + old.PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
//                    int i =0;
        }else if(m.getDeclaringClass().getName().contains("android.content.Intent")){
            return;
//                    System.out.println(old.PrintColor.ANSI_RESET + m + old.PrintColor.ANSI_GREEN + " <=== " + parent + old.PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
//                    int i =0;
        }else if(m.getDeclaringClass().getName().contains("java.lang.Thread")){
            return;

        }else if(m.getDeclaringClass().getName().contains("android.database")){
            return;

        }else if(m.getDeclaringClass().getName().contains("android.os.")){
            return;

        }else if(m.getDeclaringClass().getName().contains("android.app.")){
            return;

        }else if (m.getSignature().contains("void on")) {
            return;

        }else if (m.getSignature().contains("$lambda_")) {
            return;

        }
        else if (m.getSignature().contains("access$")) {
            return;

        }
        else if (m.getSignature().contains("void run(")) {
//            MethodSource source = m.getSource();
            int oyui =0 ;
//            return;
                    /*
                    BluetoothGatt
                    public void onClientConnectionState(final int status, int clientIf, boolean connected, String address) {
            Log.d("BluetoothGatt", "onClientConnectionState() - status=" + status + " clientIf=" + clientIf + " device=" + address);
            if (address.equals(BluetoothGatt.this.mDevice.getAddress())) {
                final int profileState = connected ? 2 : 0;
                BluetoothGatt.this.runOrQueueCallback(new Runnable() {
                    public void run() {
                    */
        }
        else if (m.getSignature().contains("createFromParcel(")) {
//                    <android.bluetooth.BluetoothDevice$2: java.lang.Object createFromParcel(android.os.Parcel)>
            return;
        }else if (m.getSignature().contains("android.os.Binder")) {
//                    <android.bluetooth.BluetoothDevice$2: java.lang.Object createFromParcel(android.os.Parcel)>
            return;
        }





        if(m.getDeclaringClass().isAbstract() || m.getDeclaringClass().isInterface())
        {
            System.out.println(PrintColor.ANSI_RED + m + "isAbstract "+ m.getDeclaringClass().isAbstract() + ";isInterface "+ m.getDeclaringClass().isInterface() + PrintColor.ANSI_RESET);
            return;
        }

        //找到所有函数输入包含该对象的方法 理论上都需要权限
        if (m.getSignature().contains("void <init>")) {
            //遍历找到传入参数类型为init类的
            String findClass = m.getDeclaringClass().getName();
            for(SootClass sc : Scene.v().getApplicationClasses()) {
                if (!sc.getName().contains("jdk.")&& !sc.isAbstract() && !sc.isInterface()) {
                    for(SootMethod temm : sc.getMethods()) {
                        List<Type> types= temm.getParameterTypes();
                        for(Type typeTem : types) {
                            if(typeTem.toString().equals(findClass)){
                                pre_visit(temm, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);
//                                            System.err.println(temm);
                                break;
                            }
                        }
                    }
                }
            }
        }


        //执行正常的CFG分析
        //没毛病继续走
        Iterator<Edge> temEdgesIterator = callGraph.edgesInto(m);
        Iterator<MethodOrMethodContext> parents = new Sources(temEdgesIterator);
        if (m.getSignature().contains("void run(")){
            while (parents.hasNext()) {
                SootMethod parent = (SootMethod) parents.next();
                if(!m.getDeclaringClass().hasOuterClass()){
                    System.out.println("run( not inner run() " + parent);
                    return;
                }
                if(parent.getDeclaringClass().toString().equals(m.getDeclaringClass().getOuterClass().toString())){
                    System.out.println("run( parent FOUND " + parent);
//                    System.exit(0);
                    pre_visit(parent, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);
                    return;
                }

            }
            return;
//            List<MethodOrMethodContext> temmm = Lists.newArrayList(parents);
//            for(MethodOrMethodContext temmmm: temmm){
//                if(temmmm.method())
//                System.out.println(temmmm);
//            }
//            SootClass runCLass = m.getDeclaringClass().getOuterClass();
//            for(SootMethod runCLassMethod: runCLass.getMethods()){
//                System.out.println(runCLassMethod);
//                String aaaa = runCLassMethod.getActiveBody().toString();
//                System.out.println(aaaa);
//                System.out.println(m.getDeclaringClass().toString());
//                if(aaaa.contains(m.getDeclaringClass().toString())){
//                    System.out.println("FOUND");
//                    System.exit(0);
//                }
//            }
//            System.exit(0);
        }


        if (parents == null) {
            return;
        }

        while (parents.hasNext()) {
            SootMethod parent = (SootMethod) parents.next();

            if(m.getSignature().contains("view")){
                int pppp = 0;
            }
            boolean found = false;
            for(String tem_method : uniqueMethodList)
            {
                if(tem_method.equals(parent.toString())){
                    found = true;
                    break;
                }
            }
            if(!found){
                uniqueMethodList.add(parent.toString());
            }

            System.out.println(PrintColor.ANSI_RESET + m + PrintColor.ANSI_GREEN + " <=== " + parent + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);

            if(!parent.getDeclaringClass().getName().contains("location") && !parent.getDeclaringClass().getName().contains("Location")){
                int a =0;
            }


            pre_visit(parent, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);

        }



    }

    class PermissionMthod{
        public SootMethod parentMethod;
        public List<String> permissionStrs;

        PermissionMthod(SootMethod parentMethod, List<String> permissionStrs){
            this.parentMethod = parentMethod;
            this.permissionStrs = permissionStrs;
        }
    }

    //查找有进行permission检测的method 并且存储请求的permission
    public List<String> methodHasCheckPermission(SootMethod m){
        List<String> permissionStrs = new ArrayList<String>();
        //native的方法不检查
        if(m.isNative()){
            return permissionStrs;
        }
        Body fun = m.getActiveBody();
        //遍历函数所在的代码块
        for(Unit u: fun.getUnits()) {
            String unitStrTem = u.toString();
            if(unitStrTem.contains("checkPermission(")||unitStrTem.contains("checkCallingPermission(")||unitStrTem.contains("checkCallingOrSelfPermission(")
                    ||unitStrTem.contains("enforcePermission(")||unitStrTem.contains("enforceCallingPermission(")||unitStrTem.contains("enforceCallingOrSelfPermission(")){
//            if(unitStrTem.contains("connectDevice(")||unitStrTem.contains("getLegacyParameters(")){
                if(u instanceof JAssignStmt) {
                    Value v = ((JAssignStmt) u).getRightOpBox().getValue();
                    for (ValueBox vvv : v.getUseBoxes()) {
                        if (vvv.getValue() instanceof StringConstant) {
                            //check的permission
                            String permissionStr = ((StringConstant) vvv.getValue()).value;
                            permissionStrs.add(permissionStr);
                            break;
                        }
                    }
                }else if(u instanceof JInvokeStmt){
                    Value v = ((JInvokeStmt) u).getInvokeExprBox().getValue();
                    for (ValueBox vvv : v.getUseBoxes()) {
                        if (vvv.getValue() instanceof StringConstant) {
                            //check的permission
                            String permissionStr = ((StringConstant) vvv.getValue()).value;
                            permissionStrs.add(permissionStr);
                            break;
                        }
                    }
                }else{
                    System.err.println("未知JxxStmt类型");
                }
            }
        }
        return permissionStrs;
    }

    @Override
    protected void internalTransform(String phaseName,
                                     Map options) {
        CallGraph bigCallGraph = new CallGraph();
        CallGraph callGraph = Scene.v().getCallGraph();
        int sieze = callGraph.size();

        //search methods in mainclass which call checkPermission
        Map<String,PermissionMthod> serviceHasPermissionMethods = new HashMap<String,PermissionMthod>();

        List<SootMethod> mainClassMethodList = mainClass.getMethods();
        System.out.println(mainClassMethodList.size());
//        System.exit(2);
        if (mainClassMethodList.size() == 0) {
            System.out.println(mainClassStr + "DOES NOT EXIST");
        }

//        for (SootMethod m : mainClassMethodList) {
//            System.out.println(m);
//        }

        // find permission
        if(phaseName.equals("wjtp.permission_finder")) {
            for (SootMethod m : mainClassMethodList) {

                List<String> permissionStrs = methodHasCheckPermission(m);
                if (permissionStrs.size() != 0) {
                    System.out.println(m + "  " + permissionStrs);
                    PermissionMthod permissionMthod = new PermissionMthod(m, permissionStrs);
                    serviceHasPermissionMethods.put(m.getSignature(), permissionMthod);
                }
//            Iterator<Edge> temEdgesIterator = callGraph.edgesOutOf(m);
//            Iterator<MethodOrMethodContext> targets = new Targets(temEdgesIterator);
//            if (targets != null) {
////            for(Edge temEdge: Lists.newArrayList(temEdgesIterator)){
////                callGraph.addEdge(temEdge);
////            }
//                while (targets.hasNext()) {
//                    SootMethod tgt = (SootMethod) targets.next();
//                    if(tgt.getName().contains("checkPermission")||tgt.getName().contains("checkCallingPermission")||tgt.getName().contains("checkCallingOrSelfPermission")
//                            ||tgt.getName().contains("enforcePermission")||tgt.getName().contains("enforceCallingPermission")||tgt.getName().contains("enforceCallingOrSelfPermission")){
//                        System.out.println(m + "" + old.PrintColor.ANSI_RED + " ===> " + old.PrintColor.ANSI_RESET + tgt);
//
//                        if(!serviceHasPermissionMethods.containsKey(m.getSignature())){
//                            List<String> permissionStrs = new ArrayList<String>();
//                            //得到函数所在的代码块
//                            Body fun = m.getActiveBody();
//                            //遍历函数所在的代码块
//                            for(Unit u: fun.getUnits()) {
////                                System.out.println(u);
//                                if(u instanceof JAssignStmt){
//                                    //找到函数
//                                    if(u.toString().contains("checkPermission(")||u.toString().contains("checkCallingPermission(")||u.toString().contains("checkCallingOrSelfPermission(")
//                                            ||u.toString().contains("enforcePermission(")||u.toString().contains("enforceCallingPermission(")||u.toString().contains("enforceCallingOrSelfPermission(")){
//                                        //遍历找函数参数
//                                        Value v = ((JAssignStmt) u).getRightOpBox().getValue();
//                                        for(ValueBox vvv : v.getUseBoxes()){
//                                            if(vvv.getValue() instanceof StringConstant){
//                                                //check的permission
//                                                String permissionStr = ((StringConstant)vvv.getValue()).value;
//                                                permissionStrs.add(permissionStr);
//                                                System.out.println(permissionStr);
////                                                break;
//                                            }
//                                        }
//
//                                    }
//
//                                }
//                            }
//                            if(permissionStrs.size()==0){
//                                System.err.println("未找到permission");
//                            }
//                            PermissionMthod permissionMthod = new PermissionMthod(m, permissionStrs);
//                            serviceHasPermissionMethods.put(m.getSignature(), permissionMthod);
//                            break;
//
//                        }
//
//
//                    }
//
//                }
//            }
            }

            //        System.exit(0);

//        SootClass c = Scene.v().getMainClass();

//        SootMethod m = mainClass.getMethodByName("requestLocationUpdates");
            //清空走过的点
//        visitedMethodSig.clear();
            for(PermissionMthod permissionMthod : serviceHasPermissionMethods.values()){
                SootMethod m = permissionMthod.parentMethod;
                List<String> visitedMethodSig = new ArrayList<String>();
                System.out.println("#########################");
                System.out.println("SEARCH FROM" + m + permissionMthod.permissionStrs);
                System.out.println("#########################");
                pre_visit(m, null, callGraph, bigCallGraph, permissionMthod.permissionStrs, visitedMethodSig);
            }
        }else if(phaseName.equals("wjtp.parent_call")) {
            // find parent
            for (SootMethod m : mainClassMethodList) {
                boolean contains = false;
                for (String fun : starts_call){
                    if (m.getSignature().contains(fun))
                        contains = true;
                }
                if (contains) {
                    List<String> visitedMethodSig = new ArrayList<String>();
                    System.out.println("#########################");
                    System.out.println("SEARCH FROM" + m);
                    System.out.println("#########################");
                    uniqueMethodList.add(m.toString());
                    List<String> permissionStrs = new ArrayList<String>();
                    pre_visit(m, null, callGraph, bigCallGraph, permissionStrs, visitedMethodSig);
                }
            }
        }else{
            System.out.println("Unsupported phaseName, Please check");
        }
        System.out.println("\n\n\n\n");

    }

    class PrintColor{
        public static final String ANSI_RESET = "\u001B[0m";
        public static final String ANSI_BLACK = "\u001B[30m";
        public static final String ANSI_RED = "\u001B[31m";
        public static final String ANSI_GREEN = "\u001B[32m";
        public static final String ANSI_YELLOW = "\u001B[33m";
        public static final String ANSI_BLUE = "\u001B[34m";
        public static final String ANSI_PURPLE = "\u001B[35m";
        public static final String ANSI_CYAN = "\u001B[36m";
        public static final String ANSI_WHITE = "\u001B[37m";
    }
}

