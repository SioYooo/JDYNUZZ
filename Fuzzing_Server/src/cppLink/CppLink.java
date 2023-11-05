package cppLink;/////////////////////////////////////////////////////////////////////////////////////////////////
// 在JAVA中查钊ServiceManager.getService(BINDER_NAME) e.g.CAMERA_SERVICE_BINDER_NAME
//
// 返回一个IBinder 这个对象调用的函数 实际implement在cpp通过BINDER_NAME连接
// 1. 找到这个函数的传入值
// 2.找到这个函数返回对象的调用函数
/////////////////////////////////////////////////////////////////////////////////////////////////


import soot.*;
import soot.jimple.StringConstant;
import soot.jimple.internal.*;
import soot.jimple.spark.SparkTransformer;
import soot.jimple.toolkits.callgraph.CHATransformer;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;
import soot.jimple.toolkits.callgraph.Sources;
import soot.options.Options;
import util.LocalVar;
import util.config;
import util.helper;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class CppLink extends SceneTransformer {

    static LinkedList<String> excludeList;
    //    //第一张组测试
//    static String mainClassStrLast = "LocationManagerService";
//    static String mainClassStr = "com.android.server." + mainClassStrLast;
//    //第二张组测试
//    static String mainClassStrLast = "ActivityRecognitionHardware";
//    static String mainClassStr = "android.hardware.location." + mainClassStrLast;
    //第二张组测试
//    static String mainClassStrLast = "CameraManager$CameraManagerGlobal";
//    static String mainClassStr = "android.hardware.camera2." + mainClassStrLast;
    static String mainClassStrLast = null;
    static String mainClassStr = null;

    //    static String mainClassStr = "android.content.Context";
    static SootClass mainClass = null;
    static BufferedWriter out = null;

    public static void run(String mainClassStrLast, String mainClassStr){

        CppLink.mainClassStrLast = mainClassStrLast;
        CppLink.mainClassStr = mainClassStr;

        helper.createDir("cpplink");
        try{
            out = new BufferedWriter(new FileWriter("cpplink/cpp_link_"+ mainClassStr +".txt"));
        }catch (IOException e){
            e.printStackTrace();
            System.exit(1);
        }


//        String[] classesDir = {"E:\\AndroidSdk\\sources\\android-26", "C:/Program Files/Java/jre1.8.0_191/lib/rt.jar"};
        String classesDir = "E:/AndroidSdk/sources/android-26";

//        String classesDir = "test/testCallGraph";
//        String mainClass = "testers.CallGraphs";

//		//set classpath
//        String javapath = System.getProperty("java.class.path");
        String javapath = "";
//        String jreDir = "C:/Program Files/Java/jre1.8.0_191/lib/rt.jar";
//        String jceDir = "C:/Program Files/Java/jre1.8.0_191/lib/jce.jar";
//        String jreDir = "D:/Program Files/Android/Android Studio/jre/jre/lib/rt.jar";
//        String jceDir = "D:/Program Files/Android/Android Studio/jre/jre/lib/jce.jar";
//        String jreDir = "C:/Program Files/Java/jre-9/lib/jrt-fs.jar";
//        String jceDir = "";
//        String path = classesDir+File.pathSeparator+jredir;
//        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + "E:/AndroidSdk/platforms/android-26/android.jar";
        String path = config.loadJarPath();
        System.out.println(path);
        //        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + "E:/android-hidden-api-master/android-26/services.jar";
//        String path = jreDir + File.pathSeparator + jceDir + File.pathSeparator + classesDir;
//        Options.v().set_prepend_classpath(true);
        Scene.v().setSootClassPath(path);
//        Options.v().set_soot_classpath(path);
//        Scene.v().setSootClassPath(jredir+File.pathSeparator+"C:/Program Files/Java/jre1.8.0_191/lib/rt.jar");
//        Scene.v().setSootClassPath("E:/AndroidSdk/sources/android-26"+File.pathSeparator+jredir);

        //add an intra-procedural analysis phase to Soot
        CppLink analysis = new CppLink();
        Pack pack = PackManager.v().getPack("wjtp");
//        if(pack.get("wjtp.CppLink")==null){
//            pack.add(new Transform("wjtp.CppLink", analysis));
//        }
        pack.add(new Transform("wjtp.CppLink", analysis));


        excludeJDKLibrary();

//        Options.v().set_process_dir(Arrays.asList(classesDir));

        Options.v().set_whole_program(true);
        Options.v().set_app(true);
        Options.v().set_validate(true);



//        Scene.v().loadNecessaryClasses();
        SootClass c = Scene.v().forceResolve(mainClassStr, SootClass.BODIES);
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
////                    System.err.println("Find server class:" + sc);
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

        System.out.println("close the out stream." + PrintColor.ANSI_RESET);

        try{
            out.close();
        }catch (IOException e){
            e.printStackTrace();
            System.exit(1);
        }
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

    public boolean isBinderMethod(SootMethod m){
        //获取method的class
        SootClass c = m.getDeclaringClass();
        SootClass targetClass = null;
        //实际implement的class
        for (SootClass temC : Scene.v().getApplicationClasses()) {
            if(temC.getName().equals(c.getName() + "$Stub$Proxy")){
                System.out.println(temC.getName());
                targetClass = temC;
                break;
            }
        }
        if(targetClass==null){
            throw new IllegalArgumentException("Cannot find implement class: " + c.getName() + "$Stub$Proxy");
        }

        //在implement的class中找method impl的
        SootMethod implMethod = null;
        for(SootMethod method : targetClass.getMethods()) {
            if(method.getSubSignature().equals(m.getSubSignature())){
                implMethod = method;
                break;
            }
        }
        if(implMethod==null){
            throw new IllegalArgumentException("Cannot find implement method: " + m.getSignature());
        }

        //获取实际impl method的代码
        Body body = implMethod.getActiveBody();

        //含有发送Parcel行为 则为IBinder函数 后面需要连接C++
        for(Unit u: body.getUnits()) {
            String unitString = u.toString();
            if(unitString.contains("<android.os.Parcel: android.os.Parcel obtain()>()")){
                int i=0;
                return true;
            }
        }

        return false;
    }


    protected void pre_visit(SootMethod m, SootMethod p, CallGraph callGraph, CallGraph bigCallGraph, List<String> permissionStrs, List<String> visitedMethodSig, int depth, LocalVar globalVar) throws IOException {
        //有问题不能继续分析下去

        //防止重复走死循环
        if(!visitedMethodSig.contains(m.getSignature())) {
            visitedMethodSig.add(m.getSignature());
        }else{
            return;
        }

        //AIDL相关分析
        if(m.getSignature().contains("$Stub: boolean onTransact(")){
            //stub -> interface, interface -> Proxy
            SootClass classProxy = getInnerClass(m.getDeclaringClass(),"Proxy");
            SootMethod mthodInterface = classProxy.getMethod(p.getName(),p.getParameterTypes());
            m = mthodInterface;
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

        // CFG逆向回溯终止API 前两个涉及handler处理
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

        }else if (m.getSignature().contains("void on")) {
            return;

        }else if (m.getSignature().contains("void run(")) {
            return;
                    /*
                    BluetoothGatt
                    public void onClientConnectionState(final int status, int clientIf, boolean connected, String address) {
            Log.d("BluetoothGatt", "onClientConnectionState() - status=" + status + " clientIf=" + clientIf + " device=" + address);
            if (address.equals(BluetoothGatt.this.mDevice.getAddress())) {
                final int profileState = connected ? 2 : 0;
                BluetoothGatt.this.runOrQueueCallback(new Runnable() {
                    public void run() {
                    */
        }else if (m.getSignature().contains("createFromParcel(")) {
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
                                depth++;
                                pre_visit(temm, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig, depth, globalVar);
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
//        List<MethodOrMethodContext> temmm = Lists.newArrayList(parents);
//        System.exit(0);

        if (parents == null) {
            return;
        }

        while (parents.hasNext()) {
            SootMethod parent = (SootMethod) parents.next();

            System.out.println(PrintColor.ANSI_RESET + m + PrintColor.ANSI_GREEN + " <=== " + parent + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
            /*
            * 如果有全局变量，则如要查找所有全局变量调用的函数是不是c函数，是则记录
            * */
            if(globalVar !=null){
                System.out.println("************");
                System.out.println("FIND globalVar call FUNCTION" + parent);
                System.out.println("************");
                Body body = parent.getActiveBody();
                List<LocalVar> localVars = new ArrayList<LocalVar>();
                String mXxxService = null;
                for(Unit u: body.getUnits()) {
//                    System.out.println(u.getClass().getName()+ " " + u);
                    if(u instanceof JIdentityStmt) {
                        //全局变量引用 (类变量)
                        JimpleLocal left = (JimpleLocal)((JIdentityStmt) u).getLeftOp();
                        String left_local_name = left.getName();

//                        ThisRef ref = (ThisRef)((JIdentityStmt) u).getRightOp();
                        Value ref = ((JIdentityStmt) u).getRightOp();
                        localVars.add(new LocalVar(left_local_name, ref));
                    }else if(u instanceof JAssignStmt) {
                        Value right_warp = ((JAssignStmt) u).getRightOpBox().getValue();
                        Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                        //右边两种情况
                        if(right_warp instanceof JVirtualInvokeExpr) {
                            JVirtualInvokeExpr right = (JVirtualInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();

                            if (mXxxService != null && right_localName.equals(mXxxService)) {
                                if(isBinderMethod(right_method)){
                                    System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                }
                            }
                        }
                        else if(right_warp instanceof JInterfaceInvokeExpr) {
                            JInterfaceInvokeExpr right = (JInterfaceInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();


                            if (mXxxService != null && right_localName.equals(mXxxService)) {
                                if(isBinderMethod(right_method)){
                                    System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                }
                            }

                        }
                        else if(right_warp instanceof JStaticInvokeExpr) {
                            JStaticInvokeExpr right = (JStaticInvokeExpr) right_warp;

                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();
//                            //找到method m返回的变量 输出所有m调用的isBinder(interface)函数
//                            if (right_fun.contains("asInterface(")) {
//                                localVars.add(new LocalVar(left_localName, right_method));
//                            }

                        }
                        else if(left_warp instanceof JimpleLocal && right_warp instanceof JInstanceFieldRef) {
                            // 全局变量赋值
                            // Local.xxx = Local;
                            // $r3 = r0.<android.net.sip.SipManager: android.net.sip.ISipService mSipService>

                            //r0.<android.net.sip.SipManager: android.net.sip.ISipService mSipService>
                            JInstanceFieldRef right = (JInstanceFieldRef) right_warp;

                            //r0
                            JimpleLocal right_local = (JimpleLocal) right.getBase();
                            String right_localName = right_local.getName();

                            //<android.net.sip.SipManager: android.net.sip.ISipService mSipService>
                            SootField right_field = right.getField();

                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();

                            String new_right = "";
                            for(LocalVar localVar: localVars){
                                if(right_localName.equals(localVar.left)){
                                    new_right = localVar.right.toString();
                                }
                            }

                            if(globalVar.left.equals(new_right+"."+right_field.toString())){
                                mXxxService = left_localName;
                            }
                        }
                    }else if(u instanceof JInvokeStmt){
                        Value value = ((JInvokeStmt) u).getInvokeExprBox().getValue();
                        if(value instanceof JInterfaceInvokeExpr) {
                            JInterfaceInvokeExpr interfaceValue = (JInterfaceInvokeExpr) value;
                            SootMethod mathod = interfaceValue.getMethod();
                            String localName = ((JimpleLocal) interfaceValue.getBase()).getName();

                            if (mXxxService != null && localName.equals(mXxxService)) {
                                if(isBinderMethod(mathod)){
                                    System.out.println(PrintColor.ANSI_BLUE + mathod + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(mathod.toString()+ "|" + permissionStrs+"\n");
                                }
                            }

                        }
                    }
                }

            }

            /*
            * 如函数中有getService()
            * 在同级找asInterface的
            * 1.赋值给的全局变量
            * 2.调用的c函数名
            * */
            if(depth==0){
                System.out.println("************");
                System.out.println("FIND asInterface() FUNCTION WHICH CONTAINS IxxxService getXXXService()" + m);
                System.out.println("************");
                Body body = m.getActiveBody();
//                String last_local = null;
                List<LocalVar> localVars = new ArrayList<LocalVar>();
                for(Unit u: body.getUnits()) {
                    //赋值语句 xxx = xxx;

                    if(u instanceof JAssignStmt) {
                        Value right_warp = ((JAssignStmt) u).getRightOpBox().getValue();
                        //右边两种情况
                        if(right_warp instanceof JVirtualInvokeExpr) {
                            JVirtualInvokeExpr right = (JVirtualInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();
                            //找到method m返回的变量 输出所有m调用的isBinder(interface)函数
                            for(LocalVar localVar: localVars){
//                                ((SootMethod) localVar.right).getReturnType().toString().equals("")
                                if(localVar.right instanceof SootMethod && right_localName.equals(localVar.left)){
                                    if(isBinderMethod(right_method)){
                                        System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                        out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                    }
                                }
                            }

                            if (right_fun.contains("asInterface(")) {
                                localVars.add(new LocalVar(left_localName, right_method));
                            }
                        }
                        else if(right_warp instanceof JInterfaceInvokeExpr) {
                            JInterfaceInvokeExpr right = (JInterfaceInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();

                            for(LocalVar localVar: localVars){
//                                ((SootMethod) localVar.right).getReturnType().toString().equals("")
                                if(localVar.right instanceof SootMethod && right_localName.equals(localVar.left)){
                                    if(isBinderMethod(right_method)){
                                        System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                        out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                    }
                                }
                            }

                            if (right_fun.contains("asInterface(")) {
                                localVars.add(new LocalVar(left_localName, right_method));
                            }

                        }
                        else if(right_warp instanceof JStaticInvokeExpr) {
                            JStaticInvokeExpr right = (JStaticInvokeExpr) right_warp;

                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();
                            //找到method m返回的变量 输出所有m调用的isBinder(interface)函数
                            if (right_fun.contains("asInterface(")) {
                                localVars.add(new LocalVar(left_localName, right_method));
                            }
                        }
                        else if(right_warp instanceof JimpleLocal) {
                            // xxx = Local;
                            JimpleLocal right = (JimpleLocal) right_warp;
                            String right_localName = right.getName();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            if(left_warp instanceof JimpleLocal){
                                // Local = Local;
                                JimpleLocal left = (JimpleLocal) left_warp;
                                String left_localName = left.getName();
                                for(LocalVar localVar: localVars){
                                    if(right_localName.equals(localVar.left)){
                                        localVar.left = left_localName;
                                    }
                                }
                            }
                            else if(left_warp instanceof JInstanceFieldRef){
                                // 全局变量赋值
                                // Local.xxx = Local;
                                //r0.<android.net.sip.SipManager: android.net.sip.ISipService mSipService> = $r3

                                //r0.<android.net.sip.SipManager: android.net.sip.ISipService mSipService>
                                JInstanceFieldRef left = (JInstanceFieldRef) left_warp;

                                //r0
                                JimpleLocal left_local = (JimpleLocal)left.getBase();
                                String left_localName = left_local.getName();

                                //<android.net.sip.SipManager: android.net.sip.ISipService mSipService>
                                SootField left_field = left.getField();

                                String new_left = "";
                                for(LocalVar localVar: localVars){
                                    if(left_localName.equals(localVar.left)){
                                        new_left = localVar.right.toString();
                                    }
                                }

                                for(LocalVar localVar: localVars){
                                    if(right_localName.equals(localVar.left)){
                                        localVar.left = new_left + "." + left_field.toString();
                                        globalVar = localVar;
                                    }
                                }
                            }



                        }

                    }else if(u instanceof JIdentityStmt) {
                        //全局变量引用 (类变量)
                        JimpleLocal left = (JimpleLocal)((JIdentityStmt) u).getLeftOp();
                        String left_local_name = left.getName();

                        Value ref = ((JIdentityStmt) u).getRightOp();
                        localVars.add(new LocalVar(left_local_name, ref));
                    }
                }

                for(LocalVar localVar: localVars){
                    System.out.println(localVar.left + " === " + localVar.right);
                }
            }


            //如果一个函数返回值是 IxxService
            String return_class = m.getReturnType().toString();
            // android.hardware.ICameraService
            // 按指定模式在字符串查找
            String pattern = "\\.I\\S.+?Service";
            Pattern r = Pattern.compile(pattern);
            Matcher re_result = r.matcher(return_class);

            if(re_result.find()){
//                getCameraService
                System.out.println("************");
                System.out.println("SEARCH FROM FUNCTION WHICH CONTAINS IxxxService getXXXService()" + parent);
                System.out.println("************");
                Body body = parent.getActiveBody();

                List<SootMethod> methodList = new ArrayList<SootMethod>();
                String last_local = null;
                //遍历函数所在的代码块
                //for(Unit u: body.getUnits()) {
                //System.out.println(u);
                //}
                for(Unit u: body.getUnits()) {
                    //赋值语句 xxx = xxx;
                    boolean aaa = u instanceof JAssignStmt;
                    boolean bbb = u instanceof JInvokeStmt;
                    if(u instanceof JAssignStmt) {
                        Value right_warp = ((JAssignStmt) u).getRightOpBox().getValue();
                        //右边两种情况
                        if(right_warp instanceof JVirtualInvokeExpr) {
                            JVirtualInvokeExpr right = (JVirtualInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();
                            //找到method m返回的变量 输出所有m调用的isBinder(interface)函数
                            if (last_local != null && right_localName.equals(last_local)) {
                                if(isBinderMethod(right_method)){
                                    methodList.add(right_method);
                                    System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                }

                            }else if (right_fun.contains(m.getSignature())) {
                                last_local = left_localName;

                            }
                        }else if(right_warp instanceof JInterfaceInvokeExpr) {
                            JInterfaceInvokeExpr right = (JInterfaceInvokeExpr) right_warp;
                            Value right_base = right.getBase();
                            JimpleLocal right_local = (JimpleLocal) right_base;

                            String right_localName = right_local.getName();
                            SootMethod right_method = right.getMethod();
                            String right_fun = right_method.getSignature();

                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
                            JimpleLocal left = (JimpleLocal) left_warp;
                            String left_localName = left.getName();

                            if (last_local != null && right_localName.equals(last_local)) {
                                if(isBinderMethod(right_method)){
                                    methodList.add(right_method);
                                    System.out.println(PrintColor.ANSI_BLUE + right_method + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(right_method.toString()+ "|" + permissionStrs+"\n");
                                }
                            }else if (right_fun.contains(m.getSignature())) {
                                last_local = left_localName;

                            }
                        }else if(right_warp instanceof JimpleLocal) {
//                            JimpleLocal right = (JimpleLocal) right_warp;
//                            String right_localName = right.getName();
//
//                            Value left_warp = ((JAssignStmt) u).getLeftOpBox().getValue();
//                            JimpleLocal left = (JimpleLocal) left_warp;
//                            String left_localName = left.getName();


                        }
                        int iii=0;
                    }else if(u instanceof JInvokeStmt){
                        Value value = ((JInvokeStmt) u).getInvokeExprBox().getValue();
                        if(value instanceof JInterfaceInvokeExpr) {
                            JInterfaceInvokeExpr interfaceValue = (JInterfaceInvokeExpr) value;
                            SootMethod mathod = interfaceValue.getMethod();
                            String localName = ((JimpleLocal) interfaceValue.getBase()).getName();

                            if (last_local != null && localName.equals(last_local)) {
                                if(isBinderMethod(mathod)){
                                    methodList.add(mathod);
                                    System.out.println(PrintColor.ANSI_BLUE + mathod + PrintColor.ANSI_YELLOW + "  :::  " + permissionStrs);
                                    out.write(mathod.toString()+ "|" + permissionStrs+"\n");
                                }
                            }

                        }
                    }
                    int iii=0;


                }
                int iii=0;


            }

            depth++;
            pre_visit(parent, m, callGraph, bigCallGraph, permissionStrs, visitedMethodSig, depth, globalVar);





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
        if(m.toString().contains("createSipService(")){
            int iii=0;
        }
        Body fun = m.getActiveBody();
        //遍历函数所在的代码块
        for(Unit u: fun.getUnits()) {
            String unitStrTem = u.toString();
            if(unitStrTem.contains("getService(")){
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
                    System.err.println("methodHasCheckPermission: 未知JxxStmt类型");
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
        if (mainClassMethodList.size()==0){
            System.out.println(mainClassStr + "DOES NOT EXIST");
        }
        for(SootMethod m : mainClassMethodList) {
            System.out.println(m);
        }

        for(SootMethod m : mainClassMethodList) {

            List<String> permissionStrs = methodHasCheckPermission(m);
            if(permissionStrs.size()!=0){
                System.out.println(m +"  "+ permissionStrs);
                //找到m函数中的asInterface()
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
        System.out.println("\n\n\n\n");
//        System.exit(0);

//        SootClass c = Scene.v().getMainClass();

//        SootMethod m = mainClass.getMethodByName("requestLocationUpdates");
        //清空走过的点
//        visitedMethodSig.clear();
        for(PermissionMthod permissionMthod : serviceHasPermissionMethods.values()){
            SootMethod m = permissionMthod.parentMethod;
            List<String> visitedMethodSig = new ArrayList<String>();
            System.out.println("#########################");
            System.out.println("SEARCH FROM FUNCTION WHICH CONTAINS getService()" + m + permissionMthod.permissionStrs);
            System.out.println("#########################");
            int depth = 0;
            try {
                pre_visit(m, null, callGraph, bigCallGraph, permissionMthod.permissionStrs, visitedMethodSig, depth, null);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }




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

