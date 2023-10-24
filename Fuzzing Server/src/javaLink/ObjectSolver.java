package javaLink;

import soot.PhaseOptions;
import soot.Scene;
import soot.SootClass;
import soot.SootMethod;
import soot.jimple.spark.SparkTransformer;
import soot.jimple.toolkits.callgraph.CHATransformer;
import soot.options.Options;
import util.config;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;


public class ObjectSolver {

    public static boolean RUN_ON_MAC = true;
    public static ArrayList<String> uniqueMethodList = new ArrayList();

    static LinkedList<String> excludeList;
    static String mainClassStr = "";

    public static void main(String[] args) throws IOException {
        mainClassStr = "android.os.Parcel";

        String path = config.loadJarPath();
        System.out.println(path);
        Scene.v().setSootClassPath(path);

        //add an intra-procedural analysis phase to Soot

        excludeJDKLibrary();

        Options.v().set_whole_program(true);
        Options.v().set_app(true);
        Options.v().set_validate(true);
//        System.out.println(Scene.v().hasMainClass());
//        SootClass c = Scene.v().forceResolve("android.database.CursorWindow", SootClass.BODIES);
        SootClass c = Scene.v().loadClassAndSupport(mainClassStr);
        c.setApplicationClass();
//        Scene.v().addBasicClass("com.android.server.LocationManagerService");

        Scene.v().loadNecessaryClasses();

        for (SootMethod m : c.getMethods()) {
            System.out.println(m);
            if(m.isConstructor()){
                System.out.println("| Constructor: " + m);
            }
        }

//
//        int count = 0;
//        List<JniClass> JniClasses = new ArrayList<>();
//        for(SootClass sc : Scene.v().getApplicationClasses()) {
//            if(!sc.getName().contains("jdk.")){
//                for (SootMethod m : sc.getMethods()) {
//                    if(m.isNative()){
//                        count++;
//                        String tmp = m.toString();
//                        System.out.println(tmp);
//                        tmp = tmp.substring(1,tmp.length()-1);
//                        String[] tmp2 = tmp.split(":");
//                        String class_ = tmp2[0];
//                        String[] tmp3 = tmp2[1].trim().split(" ");
//                        List<String> return_ = new ArrayList<>();
//                        return_.add(tmp3[0]);
//                        String[] tmp4 = tmp3[1].trim().split("\\(");
//                        String fun = tmp4[0];
//                        String tmp5 = tmp4[1].substring(0,tmp4[1].length() - 1);
//                        List<String> parameters = Arrays.asList(tmp5.split(","));
//                        JniClass o = new JniClass(class_,return_,fun, parameters);
//                        JniClasses.add(o);
//                    }
//                }
//            }
//        }
//        System.out.println(count);
//        String jsonStr = JSON.toJSONString(JniClasses);
//        System.out.println(jsonStr);
//        BufferedWriter out = new BufferedWriter(new FileWriter("jni12.0/jni.json"));
//        out.write(jsonStr);
//        out.close();
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

    private static LinkedList<String> excludeList(){
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

