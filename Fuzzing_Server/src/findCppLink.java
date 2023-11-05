import cppLink.CppLink;

public class findCppLink {
    public static void main(String[] args){
        String mainClassStrLast = "CameraManager$CameraManagerGlobal";
        String mainClassStr = "android.hardware.camera2." + mainClassStrLast;
        CppLink.run(mainClassStrLast, mainClassStr);

//        String mainClassStrLast = "ICameraService";
//        String mainClassStr = "android.hardware." + mainClassStrLast;
//        CppLink.run(mainClassStrLast, mainClassStr);

//        String filePath = "/Volumes/android/android-8.0.0_r34/frameworks/base/core/java/android/hardware/Camera.java";
//        String mainClassStrLast = "Camera";
//        String mainClassStr = "android.hardware." + mainClassStrLast;
//        CppLink.run(mainClassStrLast, mainClassStr);


//        List<JavaClass> javaClasses = loadJavaClass.load();
//        int i = 7;
//        String mainClassStrLast = javaClasses.get(i).getLast();
//        String mainClassStr = javaClasses.get(i).getBase() + mainClassStrLast;
//        String path = javaClasses.get(i).getFile_path();
//        System.out.println(mainClassStrLast);
//        System.out.println(mainClassStr);
//        System.out.println(path);
//        CppLink.run(mainClassStrLast, mainClassStr);

//        List<JavaClass> javaClasses = loadJavaClass.load();
//        int len = javaClasses.size();
//        for(int i=0; i<len; i++){
//            System.out.println("============================");
//            System.out.println("Analyzeing INDEX: " + i);
//            String mainClassStrLast = javaClasses.get(i).getLast();
//            String mainClassStr = javaClasses.get(i).getBase() + mainClassStrLast;
//            System.out.println(mainClassStrLast);
//            System.out.println(mainClassStr);
//            CppLink.run(mainClassStrLast, mainClassStr);
//        }

//        String mainClassStrLast = args[0];
//        String mainClassStr = args[1] + mainClassStrLast;
//        System.out.println(mainClassStrLast);
//        System.out.println(mainClassStr);
//        CppLink.run(mainClassStrLast, mainClassStr);

    }
}
