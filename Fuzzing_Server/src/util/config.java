package util;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class config {
    static boolean RUN_ON_MAC = true;

    public static String javaClassFilePath = "java_class/java_class.json";
    public static String jniFilePath = "jni10.0/cleaned_java_jni.json";

    static String PC_jreDir = "D:/Program Files/Android/Android Studio/jre/jre/lib/rt.jar";
    static String PC_jceDir = "D:/Program Files/Android/Android Studio/jre/jre/lib/jce.jar";
    static String UBUNTU_jreDir = "/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/rt.jar";
    static String UBUNTU_jceDir = "/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jce.jar";
    static String PC_ANDROID_JAR = "E:/android-hidden-api-master/android-26/android.jar";
    static String PC_SERVICES_JAR = "E:/android-hidden-api-master/android-26/services.jar";
//    static String PC_ANDROID_JAR = "core.jar";
//    static String PC_SERVICES_JAR = "framework.jar";

    static String MAC_jreDir = "/Library/Java/JavaVirtualMachines/jdk1.8.0_231.jdk/Contents/Home/jre/lib/rt.jar";
    static String MAC_jceDir = "/Library/Java/JavaVirtualMachines/jdk1.8.0_231.jdk/Contents/Home/jre/lib/jce.jar";
//    static String MAC_ANDROID_JAR = "/Users/chaoranli/Academic/android-hidden-api-master/android-26/android.jar";
//    static String MAC_SERVICES_JAR = "/Users/chaoranli/Academic/android-hidden-api-master/android-26/services.jar";

//    static String MAC_jreDir = "/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/rt.jar";
//    static String MAC_jceDir = "/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/jce.jar";
    static String MAC_ANDROID_JAR = "/Users/chaoranli/Academic/android-hidden-api-master/android-26/android.jar";
    static String MAC_SERVICES_JAR = "/Users/chaoranli/Academic/android-hidden-api-master/android-26/services.jar";

    public static String loadJceDir(String t){
        String java_home = System.getProperty("java.home");
        String jce = java_home + "/lib/jce.jar";
        System.out.println("jce: " + jce);
        return jce;

//        if(t.equals("PC")) {
//            return PC_jceDir;
//        }else if(t.equals("MAC")) {
//            return MAC_jceDir;
//        }else if(t.equals("UBUNTU")) {
//            return UBUNTU_jceDir;
//        }else {
//            return null;
//        }
    }

    public static String loadJreDir(String t){

        String java_home = System.getProperty("java.home");
        System.out.println("java_home: " + java_home);
        String jre = java_home + "/lib/rt.jar";
        System.out.println("jre: " + jre);
        return jre;

//        if(t.equals("PC")) {
//            return PC_jreDir;
//        }else if(t.equals("MAC")) {
//            return MAC_jreDir;
//        }else if(t.equals("UBUNTU")) {
//            return UBUNTU_jreDir;
//        }else {
//            return null;
//        }
    }

    public static String loadJreDir(boolean RUN_ON_MAC){
        if(RUN_ON_MAC){
            return MAC_jreDir;
        }else {
            return PC_jreDir;
        }
    }

    public static String loadJreDir(){
        return loadJreDir(RUN_ON_MAC);
    }

    public static String loadJceDir(boolean RUN_ON_MAC){
        if(RUN_ON_MAC){
            return MAC_jceDir;
        }else {
            return PC_jceDir;
        }
    }

    public static String loadJceDir(){
        return loadJceDir(RUN_ON_MAC);
    }

    public static String loadAndroidJAR(boolean RUN_ON_MAC){
        if(RUN_ON_MAC){
            return MAC_ANDROID_JAR;
        }else {
            return PC_ANDROID_JAR;
        }
    }

    public static String loadAndroidJAR(){
        return loadAndroidJAR(RUN_ON_MAC);
    }

    public static String loadServicesJAR(boolean RUN_ON_MAC){
        if(RUN_ON_MAC){
            return MAC_SERVICES_JAR;
        }else {
            return PC_SERVICES_JAR;
        }
    }

    public static String loadServicesJAR(){
        return loadServicesJAR(RUN_ON_MAC);
    }

    public static String loadPath(boolean RUN_ON_MAC){
//        return loadJreDir(RUN_ON_MAC) + File.pathSeparator + loadJceDir(RUN_ON_MAC) + File.pathSeparator + "E://android-8.0.0_r34/out/target/common/obj/JAVA_LIBRARIES/voip-common_intermediates/classes.jar";

        return loadJreDir(RUN_ON_MAC) + File.pathSeparator + loadJceDir(RUN_ON_MAC) + File.pathSeparator + loadAndroidJAR(RUN_ON_MAC) + File.pathSeparator + loadServicesJAR(RUN_ON_MAC);
    }

    public static String loadScrClassPath(boolean RUN_ON_MAC){
        String r = loadJreDir(RUN_ON_MAC) + File.pathSeparator + loadJceDir(RUN_ON_MAC);

        return r;
    }

    public static String loadPath(){
        return loadPath(RUN_ON_MAC);
    }

    public static String loadJarPath(String t){
        String r = loadJreDir(t) + File.pathSeparator + loadJceDir(t);

        List<String> jar_list = new ArrayList<String>();
        String BASE = "12.0";
        if (RUN_ON_MAC){

            // ===========================7.0=======
//            BASE = "/hci/chaoran_data/pythonProject/jar/";
//            BASE = "/Users/chaoranli/Downloads/jar/";
//            BASE = "jar7.0/";

            // ===========================7.1=======
//            BASE = "/Users/chaoranli/Downloads/jar7.1/";
//            BASE = "jar7.1/";

            // ===========================8.0=======
//            BASE = "/Users/chaoranli/PycharmProjects/test/jar";

            // ===========================8.1=======
//            BASE = "jar8.1/";

            // ===========================9.0=======
//            BASE = "/Users/chaoranli/Downloads/jar9.0/";
//            BASE = "jar9.0/";

            // ===========================10.0=======
//            BASE = "/Users/chaoranli/Downloads/jar10.0/";
//            BASE = "jar10.0/";

            // ===========================10.0=======
//            BASE = "/Users/chaoranli/Downloads/jar10.0/";
            BASE = "jar/jar12.0/";
        }

        // ===========================8.0=======
//        jar_list.add(BASE + "/services.devicepolicy_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.power-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "/services.appwidget_intermediates.jar");
//        jar_list.add(BASE + "/dialer-dagger2-compiler_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-fragment_intermediates.jar");
//        jar_list.add(BASE + "/dialer-javax-annotation-api-target_intermediates.jar");
////        jar_list.add(BASE + "jar/sdk_v8_intermediates.jar");
//        jar_list.add(BASE + "/android.hidl.base-V1.0-java-static_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-compat_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-v4_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-animatedvectordrawable_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.usb-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.radio-V1.1-java-static_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-media-compat_intermediates.jar");
//        jar_list.add(BASE + "/dialer-guava_intermediates.jar");
//        jar_list.add(BASE + "/dialer-disklrucache-target_intermediates.jar");
//        jar_list.add(BASE + "/libphonenumber_intermediates.jar");
//        jar_list.add(BASE + "/tzdata_update2_intermediates.jar");
////        jar_list.add(BASE + "jar/android_system_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "/com.android.vcard_intermediates.jar");
//        jar_list.add(BASE + "/dialer-mime4j-core-target_intermediates.jar");
//        jar_list.add(BASE + "/apache-xml_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.usb-V1.1-java_intermediates.jar");
////        jar_list.add(BASE + "jar/sdk_v17_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-core-utils_intermediates.jar");
//        jar_list.add(BASE + "/services.midi_intermediates.jar");
//        jar_list.add(BASE + "/services.voiceinteraction_intermediates.jar");
//        jar_list.add(BASE + "/dialer-auto-value_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-transition_intermediates.jar");
//        jar_list.add(BASE + "/services.restrictions_intermediates.jar");
//        jar_list.add(BASE + "/bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "/org.apache.http.legacy_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "/dialer-commons-io-target_intermediates.jar");
//        jar_list.add(BASE + "/services.core_intermediates.jar");
//        jar_list.add(BASE + "/conscrypt_intermediates.jar");
//        jar_list.add(BASE + "/framework_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-v7-appcompat_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.oemlock-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.biometrics.fingerprint-V2.1-java-static_intermediates.jar");
//        jar_list.add(BASE + "/dialer-guava-target_intermediates.jar");
//        jar_list.add(BASE + "/services.backup_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.wifi-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.tv.cec-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "/services.usb_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-design_intermediates.jar");
//        jar_list.add(BASE + "/telephony-common_intermediates.jar");
////        jar_list.add(BASE + "jar/android_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "/dialer-dagger2-producers_intermediates.jar");
//        jar_list.add(BASE + "/volley_intermediates.jar");
//        jar_list.add(BASE + "/dialer-mime4j-dom-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.thermal-V1.0-java-constants_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-annotations_intermediates.jar");
//        jar_list.add(BASE + "/jacocoagent_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.radio.deprecated-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "/core-all_intermediates.jar");
//        jar_list.add(BASE + "/libprotobuf-java-lite_intermediates.jar");
//        jar_list.add(BASE + "/libphonenumber-platform_intermediates.jar");
//        jar_list.add(BASE + "/services.autofill_intermediates.jar");
//        jar_list.add(BASE + "/services.accessibility_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.vibrator-V1.1-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/libprotobuf-java-nano_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-stub-target_intermediates.jar");
//        jar_list.add(BASE + "/okhttp_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-core-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.vibrator-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/services.print_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.weaver-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "/android.hidl.base-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.tetheroffload.control-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "/ims-common_intermediates.jar");
//        jar_list.add(BASE + "/framework-protos_intermediates.jar");
//        jar_list.add(BASE + "/core-oj_intermediates.jar");
//        jar_list.add(BASE + "/icu4j_intermediates.jar");
//        jar_list.add(BASE + "/dialer-dagger2_intermediates.jar");
//        jar_list.add(BASE + "/dialer-javax-annotation-api_intermediates.jar");
//        jar_list.add(BASE + "/dialer-gifdecoder-target_intermediates.jar");
//        jar_list.add(BASE + "/services_intermediates.jar");
//        jar_list.add(BASE + "/services.net_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-okhttp-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hidl.manager-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "/bouncycastle-nojarjar_intermediates.jar");
//        jar_list.add(BASE + "/tzdata_shared2_intermediates.jar");
//        jar_list.add(BASE + "/dialer-glide-target_intermediates.jar");
//        jar_list.add(BASE + "/services.companion_intermediates.jar");
//        jar_list.add(BASE + "/android-common_intermediates.jar");
////        jar_list.add(BASE + "/sdk_v21_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.health-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/jacoco-asm_intermediates.jar");
//        jar_list.add(BASE + "/dialer-dagger2-target_intermediates.jar");
//        jar_list.add(BASE + "/ext_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-vectordrawable_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.usb-V1.0-java_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-v7-recyclerview_intermediates.jar");
////        jar_list.add(BASE + "jar/legacy-test_intermediates.jar");
//        jar_list.add(BASE + "/jsr305_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.tv.input-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/voip-common_intermediates.jar");
//        jar_list.add(BASE + "/dialer-javax-inject_intermediates.jar");
//        jar_list.add(BASE + "/org.apache.http.legacy.boot_intermediates.jar");
//        jar_list.add(BASE + "/core-lambda-stubs_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-dynamic-animation_intermediates.jar");
//        jar_list.add(BASE + "/services.usage_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-v13_intermediates.jar");
//        jar_list.add(BASE + "/core-libart_intermediates.jar");
////        jar_list.add(BASE + "jar/android-support-v7-cardview_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-context-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.usb-V1.1-java-constants_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-protobuf-lite-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.radio-V1.0-java-static_intermediates.jar");
////        jar_list.add(BASE + "jar/sdk_v9_intermediates.jar");
//        jar_list.add(BASE + "/dialer-libshortcutbadger-target_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.configstore-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "/dialer-javax-inject-target_intermediates.jar");
////        jar_list.add(BASE + "jar/services.coverage_intermediates.jar");
//        jar_list.add(BASE + "/android.hardware.light-V2.0-java_intermediates.jar");
//        jar_list.add(BASE + "/dialer-grpc-all-target_intermediates.jar");

        // ===========================7.0=======
//        jar_list.add(BASE + "services.core_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "okhttp_intermediates.jar");
//        jar_list.add(BASE + "core-lambda-stubs_intermediates.jar");
//        jar_list.add(BASE + "ims-common_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle-nojarjar_intermediates.jar");
//        jar_list.add(BASE + "framework-protos_intermediates.jar");
//        jar_list.add(BASE + "framework_intermediates.jar");
////        jar_list.add(BASE + "sdk_v8_intermediates.jar");
//        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "voip-common_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber-platform_intermediates.jar");
////        jar_list.add(BASE + "sdk_v21_intermediates.jar");
//        jar_list.add(BASE + "core-libart_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-nano_intermediates.jar");
////        jar_list.add(BASE + "android_test_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "ext_intermediates.jar");
//        jar_list.add(BASE + "android_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "android_system_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "core-junit_intermediates.jar");
//        jar_list.add(BASE + "conscrypt_intermediates.jar");
//        jar_list.add(BASE + "core-oj_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy.boot_intermediates.jar");
//        jar_list.add(BASE + "apache-xml_intermediates.jar");
//        jar_list.add(BASE + "icu4j_intermediates.jar");
//        jar_list.add(BASE + "services.net_intermediates.jar");
//        jar_list.add(BASE + "core-all_intermediates.jar");
//        jar_list.add(BASE + "tzdata_update_intermediates.jar");
//        jar_list.add(BASE + "services.voiceinteraction_intermediates.jar");

        // ===========================7.1=======
//        jar_list.add(BASE + "services.core_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "okhttp_intermediates.jar");
//        jar_list.add(BASE + "core-lambda-stubs_intermediates.jar");
//        jar_list.add(BASE + "ims-common_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle-nojarjar_intermediates.jar");
//        jar_list.add(BASE + "framework-protos_intermediates.jar");
//        jar_list.add(BASE + "framework_intermediates.jar");
////        jar_list.add(BASE + "sdk_v8_intermediates.jar");
//        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "voip-common_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber-platform_intermediates.jar");
//        jar_list.add(BASE + "sdk_v21_intermediates.jar");
//        jar_list.add(BASE + "core-libart_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-nano_intermediates.jar");
////        jar_list.add(BASE + "android_test_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "ext_intermediates.jar");
//        jar_list.add(BASE + "android_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "android_system_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "core-junit_intermediates.jar");
//        jar_list.add(BASE + "conscrypt_intermediates.jar");
//        jar_list.add(BASE + "core-oj_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy.boot_intermediates.jar");
//        jar_list.add(BASE + "apache-xml_intermediates.jar");
//        jar_list.add(BASE + "icu4j_intermediates.jar");
//        jar_list.add(BASE + "services.net_intermediates.jar");
//        jar_list.add(BASE + "core-all_intermediates.jar");
//        jar_list.add(BASE + "tzdata_update_intermediates.jar");
//        jar_list.add(BASE + "services.voiceinteraction_intermediates.jar");



        // ===========================8.1=======
//        jar_list.add(BASE + "dialer-grpc-stub-target_intermediates.jar");
//        jar_list.add(BASE + "services.core_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2_intermediates.jar");
//        jar_list.add(BASE + "dialer-commons-io-target_intermediates.jar");
//        jar_list.add(BASE + "android-support-v4_intermediates.jar");
//        jar_list.add(BASE + "services.usage_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2-producers_intermediates.jar");
//        jar_list.add(BASE + "android-common_intermediates.jar");
//        jar_list.add(BASE + "services.usb_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-inject_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.usb-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "services.print_intermediates.jar");
//        jar_list.add(BASE + "services.appwidget_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2-compiler_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.weaver-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "dialer-guava-target_intermediates.jar");
//        jar_list.add(BASE + "services.midi_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "jsr305_intermediates.jar");
//        jar_list.add(BASE + "android-support-v13_intermediates.jar");
//        jar_list.add(BASE + "okhttp_intermediates.jar");
//        jar_list.add(BASE + "core-lambda-stubs_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.light-V2.0-java_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.vibrator-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "apptoolkit-arch-core-common_intermediates.jar");
//        jar_list.add(BASE + "legacy-test_intermediates.jar");
//        jar_list.add(BASE + "jacoco-asm_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.biometrics.fingerprint-V2.1-java-static_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.configstore-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "ims-common_intermediates.jar");
//        jar_list.add(BASE + "android-support-design_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-okhttp-target_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle-nojarjar_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.tv.input-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "framework-protos_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.health-V1.0-java-constants_intermediates.jar");
////        jar_list.add(BASE + "sdk_v17_intermediates.jar");
//        jar_list.add(BASE + "services.backup_intermediates.jar");
////        jar_list.add(BASE + "android-support-dynamic-animation_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-annotation-api-target_intermediates.jar");
//        jar_list.add(BASE + "framework_intermediates.jar");
////        jar_list.add(BASE + "sdk_v8_intermediates.jar");
////        jar_list.add(BASE + "android-support-fragment_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-annotation-api_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.tv.cec-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "dialer-guava_intermediates.jar");
//        jar_list.add(BASE + "services.accessibility_intermediates.jar");
//        jar_list.add(BASE + "voip-common_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio-V1.1-java-static_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber-platform_intermediates.jar");
////        jar_list.add(BASE + "android-support-annotations_intermediates.jar");
//        jar_list.add(BASE + "services_intermediates.jar");
////        jar_list.add(BASE + "android-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "services.companion_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.usb-V1.1-java-constants_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.manager-V1.0-java_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-appcompat_intermediates.jar");
////        jar_list.add(BASE + "sdk_v21_intermediates.jar");
//        jar_list.add(BASE + "core-libart_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.base-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "time_zone_distro_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-context-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-libshortcutbadger-target_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-nano_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-inject-target_intermediates.jar");
//        jar_list.add(BASE + "volley_intermediates.jar");
////        jar_list.add(BASE + "android-support-media-compat_intermediates.jar");
////        jar_list.add(BASE + "android-support-transition_intermediates.jar");
//        jar_list.add(BASE + "services.restrictions_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-dom-target_intermediates.jar");
//        jar_list.add(BASE + "ext_intermediates.jar");
////        jar_list.add(BASE + "android_stubs_current_intermediates.jar");
////        jar_list.add(BASE + "android-support-vectordrawable_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-cardview_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio.deprecated-V1.0-java-static_intermediates.jar");
////        jar_list.add(BASE + "android-support-animatedvectordrawable_intermediates.jar");
//        jar_list.add(BASE + "android_system_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "apptoolkit-lifecycle-runtime_intermediates.jar");
//        jar_list.add(BASE + "conscrypt_intermediates.jar");
//        jar_list.add(BASE + "core-oj_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.usb-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy.boot_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.base-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.oemlock-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "dialer-disklrucache-target_intermediates.jar");
//        jar_list.add(BASE + "com.android.vcard_intermediates.jar");
//        jar_list.add(BASE + "dialer-auto-value_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-core-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-gifdecoder-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.power-V1.0-java_intermediates.jar");
////        jar_list.add(BASE + "services.coverage_intermediates.jar");
//        jar_list.add(BASE + "apache-xml_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-recyclerview_intermediates.jar");
//        jar_list.add(BASE + "icu4j_intermediates.jar");
//        jar_list.add(BASE + "apptoolkit-lifecycle-common_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-protobuf-lite-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.thermal-V1.0-java-constants_intermediates.jar");
////        jar_list.add(BASE + "android-support-compat_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.usb-V1.0-java-constants_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2-target_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-lite_intermediates.jar");
//        jar_list.add(BASE + "services.net_intermediates.jar");
////        jar_list.add(BASE + "android-support-core-utils_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber_intermediates.jar");
//        jar_list.add(BASE + "android.test.mock_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.vibrator-V1.1-java-constants_intermediates.jar");
//        jar_list.add(BASE + "core-all_intermediates.jar");
//        jar_list.add(BASE + "time_zone_distro_installer_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.tetheroffload.control-V1.0-java-static_intermediates.jar");
//        jar_list.add(BASE + "jacocoagent_intermediates.jar");
//        jar_list.add(BASE + "services.autofill_intermediates.jar");
//        jar_list.add(BASE + "services.voiceinteraction_intermediates.jar");
////        jar_list.add(BASE + "sdk_v9_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-all-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-glide-target_intermediates.jar");
//        jar_list.add(BASE + "services.devicepolicy_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-core-target_intermediates.jar");

// ===========================9.0=======
//        jar_list.add(BASE + "com.android.location.provider_intermediates.jar");
//        jar_list.add(BASE + "Launcher3QuickStepLib_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-stub-target_intermediates.jar");
//        jar_list.add(BASE + "glide_intermediates.jar");
//        jar_list.add(BASE + "libbackup_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.2-java_intermediates.jar");
//        jar_list.add(BASE + "framework-oahl-backward-compatibility_intermediates.jar");
//        jar_list.add(BASE + "dialer-zxing-target_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-gridlayout_intermediates.jar");
//        jar_list.add(BASE + "guava_intermediates.jar");
//        jar_list.add(BASE + "settings-logtags_intermediates.jar");
//        jar_list.add(BASE + "dialer-commons-io-target_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v4_intermediates.jar");
//        jar_list.add(BASE + "junit_intermediates.jar");
//        jar_list.add(BASE + "latinime-common_intermediates.jar");
//        jar_list.add(BASE + "colorpicker_intermediates.jar");
//        jar_list.add(BASE + "uiautomator_intermediates.jar");
//        jar_list.add(BASE + "android-common_intermediates.jar");
//        jar_list.add(BASE + "sm_intermediates.jar");
//        jar_list.add(BASE + "com.android.media.remotedisplay_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-mediarouter_intermediates.jar");
//        jar_list.add(BASE + "content_intermediates.jar");
//        jar_list.add(BASE + "bmgrlib_intermediates.jar");
//        jar_list.add(BASE + "android-arch-lifecycle-extensions_intermediates.jar");
//        jar_list.add(BASE + "bluetooth-protos-lite_intermediates.jar");
//        jar_list.add(BASE + "dialer-guava-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.fragment_fragment_intermediates.jar");
//        jar_list.add(BASE + "android-opt-timezonepicker_intermediates.jar");
//        jar_list.add(BASE + "android-slices-builders_intermediates.jar");
//        jar_list.add(BASE + "car-list_intermediates.jar");
//        jar_list.add(BASE + "cr_intermediates.jar");
//        jar_list.add(BASE + "SystemUI-tags_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "jsr305_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v13_intermediates.jar");
//        jar_list.add(BASE + "okhttp_intermediates.jar");
//        jar_list.add(BASE + "Launcher3CommonDepsLib_intermediates.jar");
//        jar_list.add(BASE + "SettingsLib_intermediates.jar");
//        jar_list.add(BASE + "xmp_toolkit_intermediates.jar");
//        jar_list.add(BASE + "bluetooth.mapsapi_intermediates.jar");
//        jar_list.add(BASE + "ethernet-service_intermediates.jar");
//        jar_list.add(BASE + "telephony-protos_intermediates.jar");
//        jar_list.add(BASE + "ims-common_intermediates.jar");
//        //jar_list.add(BASE + "android-support-design_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-okhttp-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "androidx.gridlayout_gridlayout_intermediates.jar");
//        jar_list.add(BASE + "android-ex-camera2-portability_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v17-preference-leanback_intermediates.jar");
//        //jar_list.add(BASE + "android-support-dynamic-animation_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-annotation-api-target_intermediates.jar");
//        jar_list.add(BASE + "framework_intermediates.jar");
//        //jar_list.add(BASE + "android-support-fragment_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "android-opt-bitmap_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.supplicant-V1.0-java_intermediates.jar");
//        //jar_list.add(BASE + "android.test.base_intermediates.jar");
//        jar_list.add(BASE + "libphotoviewer_intermediates.jar");
//        jar_list.add(BASE + "voip-common_intermediates.jar");
//        jar_list.add(BASE + "requestsync_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-v4_intermediates.jar");
//        jar_list.add(BASE + "com.android.gallery3d.common2_intermediates.jar");
//        //jar_list.add(BASE + "android-support-annotations_intermediates.jar");
//        jar_list.add(BASE + "services_intermediates.jar");
//        //jar_list.add(BASE + "android-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "com.android.future.usb.accessory_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.manager-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "libphotoviewer_appcompat_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-appcompat_intermediates.jar");
//        jar_list.add(BASE + "media_cmd_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-preference_intermediates.jar");
//        jar_list.add(BASE + "dialer-error-prone-target_intermediates.jar");
//        //jar_list.add(BASE + "sdk_v21_intermediates.jar");
//        jar_list.add(BASE + "com.android.emailcommon_intermediates.jar");
//        jar_list.add(BASE + "core-libart_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-context-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.recyclerview_recyclerview_intermediates.jar");
//        jar_list.add(BASE + "vr_intermediates.jar");
//        jar_list.add(BASE + "bu_intermediates.jar");
//        jar_list.add(BASE + "dialer-libshortcutbadger-target_intermediates.jar");
//        jar_list.add(BASE + "svclib_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-nano_intermediates.jar");
//        //jar_list.add(BASE + "android_test_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "libchips_intermediates.jar");
//        //jar_list.add(BASE + "android.test.runner_intermediates.jar");
//        jar_list.add(BASE + "android-opt-datetimepicker_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio.config-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "wifi-service_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-inject-target_intermediates.jar");
//        jar_list.add(BASE + "volley_intermediates.jar");
//        //jar_list.add(BASE + "android-support-media-compat_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-v13_intermediates.jar");
//        //jar_list.add(BASE + "android-support-transition_intermediates.jar");
//        jar_list.add(BASE + "android-common-framesequence_intermediates.jar");
//        jar_list.add(BASE + "owasp-html-sanitizer_intermediates.jar");
//        jar_list.add(BASE + "android-arch-core-runtime_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-dom-target_intermediates.jar");
//        jar_list.add(BASE + "xz-java_intermediates.jar");
//        jar_list.add(BASE + "android-arch-lifecycle-common_intermediates.jar");
//        jar_list.add(BASE + "ext_intermediates.jar");
//        jar_list.add(BASE + "inputmethod-common_intermediates.jar");
//        jar_list.add(BASE + "android_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "telecom_intermediates.jar");
//        //jar_list.add(BASE + "android-support-car_intermediates.jar");
//        jar_list.add(BASE + "javax.obex_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-cardview_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.secure_element-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "android_system_stubs_current_intermediates.jar");
//        jar_list.add(BASE + "android-slices-view_intermediates.jar");
//        jar_list.add(BASE + "android-ex-camera2-utils_intermediates.jar");
//        jar_list.add(BASE + "monkeylib_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio-V1.2-java_intermediates.jar");
//        jar_list.add(BASE + "sap-api-java-static_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio-V1.0-java_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v14-preference_intermediates.jar");
//        jar_list.add(BASE + "libSharedSystemUI_intermediates.jar");
//        jar_list.add(BASE + "conscrypt_intermediates.jar");
//        //jar_list.add(BASE + "android-support-percent_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "core-oj_intermediates.jar");
//        jar_list.add(BASE + "locksettings_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy.boot_intermediates.jar");
//        jar_list.add(BASE + "appwidget_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.base-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "androidx.core_core_intermediates.jar");
//        jar_list.add(BASE + "dialer-disklrucache-target_intermediates.jar");
//        jar_list.add(BASE + "com.android.vcard_intermediates.jar");
//        jar_list.add(BASE + "android-arch-lifecycle-runtime_intermediates.jar");
//        jar_list.add(BASE + "SystemUISharedLib_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-core-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.hostapd-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "dialer-gifdecoder-target_intermediates.jar");
//        jar_list.add(BASE + "mp4parser_intermediates.jar");
//        jar_list.add(BASE + "apache-xml_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.supplicant-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "com.android.mediadrm.signer_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-recyclerview_intermediates.jar");
//        jar_list.add(BASE + "uiautomator.core_intermediates.jar");
//        jar_list.add(BASE + "setup-wizard-lib-gingerbread-compat_intermediates.jar");
//        jar_list.add(BASE + "SystemUI-proto_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.radio.deprecated-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-protobuf-lite-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-glide-annotation-target_intermediates.jar");
//        //jar_list.add(BASE + "android-support-compat_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v7-palette_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2-target_intermediates.jar");
//        jar_list.add(BASE + "am_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "calendar-common_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-lite_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-micro_intermediates.jar");
//        jar_list.add(BASE + "dpm_intermediates.jar");
//        jar_list.add(BASE + "androidx.annotation_annotation_intermediates.jar");
//        jar_list.add(BASE + "services.net_intermediates.jar");
//        //jar_list.add(BASE + "android-support-core-utils_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber_intermediates.jar");
//        jar_list.add(BASE + "inputlib_intermediates.jar");
//        //jar_list.add(BASE + "android.test.mock_intermediates.jar");
//        jar_list.add(BASE + "setup-wizard-lib_intermediates.jar");
//        //jar_list.add(BASE + "android-support-v17-leanback_intermediates.jar");
//        jar_list.add(BASE + "SystemUIPluginLib_intermediates.jar");
//        jar_list.add(BASE + "android-slices-core_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-all-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-glide-target_intermediates.jar");
//        jar_list.add(BASE + "hid_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-core-target_intermediates.jar");



        //// ===========================10.0=======
//        jar_list.add(BASE + "com.android.location.provider_intermediates.jar");
//        jar_list.add(BASE + "Launcher3QuickStepLib_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-stub-target_intermediates.jar");
//        jar_list.add(BASE + "glide_intermediates.jar");
//        jar_list.add(BASE + "libbackup_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.2-java_intermediates.jar");
//        jar_list.add(BASE + "androidx.lifecycle_lifecycle-common_intermediates.jar");
//        jar_list.add(BASE + "dialer-zxing-target_intermediates.jar");
//        jar_list.add(BASE + "dialer-j2objc-annotations-target_intermediates.jar");
//        jar_list.add(BASE + "guava_intermediates.jar");
//        jar_list.add(BASE + "settings-logtags_intermediates.jar");
//        jar_list.add(BASE + "dialer-commons-io-target_intermediates.jar");
//        jar_list.add(BASE + "contextualcards_intermediates.jar");
////        jar_list.add(BASE + "android-support-v4_intermediates.jar");
//        jar_list.add(BASE + "dialer-okio-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.dynamicanimation_dynamicanimation_intermediates.jar");
//        jar_list.add(BASE + "colorpicker_intermediates.jar");
//        jar_list.add(BASE + "uiautomator_intermediates.jar");
//        jar_list.add(BASE + "android-common_intermediates.jar");
//        jar_list.add(BASE + "sm_intermediates.jar");
//        jar_list.add(BASE + "com.android.media.remotedisplay_intermediates.jar");
//        jar_list.add(BASE + "content_intermediates.jar");
//        jar_list.add(BASE + "updatable-media_intermediates.jar");
//        jar_list.add(BASE + "bluetooth-protos-lite_intermediates.jar");
//        jar_list.add(BASE + "bmgr_intermediates.jar");
//        jar_list.add(BASE + "dialer-guava-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.slice_slice-builders_intermediates.jar");
//        jar_list.add(BASE + "androidx.fragment_fragment_intermediates.jar");
//        jar_list.add(BASE + "android-opt-timezonepicker_intermediates.jar");
//        jar_list.add(BASE + "bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "com.android.runtime.debug.core-oj_intermediates.jar");
//        jar_list.add(BASE + "ksoap2_intermediates.jar");
//        jar_list.add(BASE + "jsr305_intermediates.jar");
////        jar_list.add(BASE + "android-support-v13_intermediates.jar");
//        jar_list.add(BASE + "okhttp_intermediates.jar");
//        jar_list.add(BASE + "Launcher3CommonDepsLib_intermediates.jar");
//        jar_list.add(BASE + "androidx.preference_preference_intermediates.jar");
//        jar_list.add(BASE + "SettingsLib_intermediates.jar");
//        jar_list.add(BASE + "xmp_toolkit_intermediates.jar");
//        jar_list.add(BASE + "bluetooth.mapsapi_intermediates.jar");
//        jar_list.add(BASE + "ethernet-service_intermediates.jar");
//        jar_list.add(BASE + "ims-common_intermediates.jar");
////        jar_list.add(BASE + "android-support-design_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-okhttp-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "setupcompat_intermediates.jar");
//        jar_list.add(BASE + "android-ex-camera2-portability_intermediates.jar");
//        jar_list.add(BASE + "dialer-animal-sniffer-annotations-target_intermediates.jar");
////        jar_list.add(BASE + "android-support-dynamic-animation_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-annotation-api-target_intermediates.jar");
//        jar_list.add(BASE + "framework_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "setupdesign_intermediates.jar");
//        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.supplicant-V1.0-java_intermediates.jar");
////        jar_list.add(BASE + "android.test.base_intermediates.jar");
//        jar_list.add(BASE + "libphotoviewer_intermediates.jar");
//        jar_list.add(BASE + "voip-common_intermediates.jar");
//        jar_list.add(BASE + "androidx.room_room-runtime_intermediates.jar");
//        jar_list.add(BASE + "requestsync_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-v4_intermediates.jar");
//        jar_list.add(BASE + "com.android.gallery3d.common2_intermediates.jar");
////        jar_list.add(BASE + "android-support-annotations_intermediates.jar");
//        jar_list.add(BASE + "services_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.hostapd-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "managedprovisioning_protoslite_intermediates.jar");
////        jar_list.add(BASE + "android-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "com.android.future.usb.accessory_intermediates.jar");
//        jar_list.add(BASE + "com.android.media.updatable-media_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.manager-V1.0-java_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-appcompat_intermediates.jar");
//        jar_list.add(BASE + "dialer-error-prone-target_intermediates.jar");
//        jar_list.add(BASE + "SettingsLib-search_intermediates.jar");
//        jar_list.add(BASE + "launcherprotosnano_intermediates.jar");
//        jar_list.add(BASE + "core-libart_intermediates.jar");
//        jar_list.add(BASE + "com.android.runtime.debug.okhttp_intermediates.jar");
//        jar_list.add(BASE + "PluginCoreLib_intermediates.jar");
//        jar_list.add(BASE + "androidx.appcompat_appcompat_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-context-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.recyclerview_recyclerview_intermediates.jar");
//        jar_list.add(BASE + "media_intermediates.jar");
//        jar_list.add(BASE + "vr_intermediates.jar");
//        jar_list.add(BASE + "androidx-constraintlayout_constraintlayout-solver_intermediates.jar");
//        jar_list.add(BASE + "bu_intermediates.jar");
//        jar_list.add(BASE + "dialer-libshortcutbadger-target_intermediates.jar");
//        jar_list.add(BASE + "svclib_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-nano_intermediates.jar");
//        jar_list.add(BASE + "androidx-constraintlayout_constraintlayout_intermediates.jar");
//        jar_list.add(BASE + "libchips_intermediates.jar");
//        jar_list.add(BASE + "dialer-okhttp-target_intermediates.jar");
////        jar_list.add(BASE + "android.test.runner_intermediates.jar");
//        jar_list.add(BASE + "android-opt-datetimepicker_intermediates.jar");
//        jar_list.add(BASE + "androidx.car_car_intermediates.jar");
//        jar_list.add(BASE + "androidx.lifecycle_lifecycle-livedata_intermediates.jar");
//        jar_list.add(BASE + "wifi-service_intermediates.jar");
//        jar_list.add(BASE + "dialer-javax-inject-target_intermediates.jar");
//        jar_list.add(BASE + "SecondaryDisplayLauncherLib_intermediates.jar");
//        jar_list.add(BASE + "volley_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.supplicant-V1.2-java_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-v13_intermediates.jar");
////        jar_list.add(BASE + "android-support-transition_intermediates.jar");
//        jar_list.add(BASE + "android-common-framesequence_intermediates.jar");
//        jar_list.add(BASE + "androidx.slice_slice-view_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-dom-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.cardview_cardview_intermediates.jar");
//        jar_list.add(BASE + "com.android.runtime.debug.core-libart_intermediates.jar");
//        jar_list.add(BASE + "ext_intermediates.jar");
//        jar_list.add(BASE + "wifi_service_proto_intermediates.jar");
//        jar_list.add(BASE + "telecom_intermediates.jar");
//        jar_list.add(BASE + "javax.obex_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-preference-v14_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-cardview_intermediates.jar");
//        jar_list.add(BASE + "androidx.slice_slice-core_intermediates.jar");
//        jar_list.add(BASE + "androidx.palette_palette_intermediates.jar");
//        jar_list.add(BASE + "LauncherPluginLib_intermediates.jar");
//        jar_list.add(BASE + "androidx.lifecycle_lifecycle-extensions_intermediates.jar");
//        jar_list.add(BASE + "monkeylib_intermediates.jar");
//        jar_list.add(BASE + "sap-api-java-static_intermediates.jar");
//        jar_list.add(BASE + "conscrypt_intermediates.jar");
//        jar_list.add(BASE + "core-oj_intermediates.jar");
//        jar_list.add(BASE + "locksettings_intermediates.jar");
//        jar_list.add(BASE + "appwidget_intermediates.jar");
//        jar_list.add(BASE + "android.hidl.base-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "androidx.core_core_intermediates.jar");
//        jar_list.add(BASE + "dialer-disklrucache-target_intermediates.jar");
//        jar_list.add(BASE + "com.android.vcard_intermediates.jar");
//        jar_list.add(BASE + "com.google.android.material_material_intermediates.jar");
//        jar_list.add(BASE + "SystemUISharedLib_intermediates.jar");
//        jar_list.add(BASE + "dialer-mime4j-core-target_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi-V1.3-java_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.hostapd-V1.0-java_intermediates.jar");
//        jar_list.add(BASE + "dialer-gifdecoder-target_intermediates.jar");
//        jar_list.add(BASE + "mp4parser_intermediates.jar");
//        jar_list.add(BASE + "apache-xml_intermediates.jar");
//        jar_list.add(BASE + "com.android.conscrypt.conscrypt_intermediates.jar");
//        jar_list.add(BASE + "android.hardware.wifi.supplicant-V1.1-java_intermediates.jar");
//        jar_list.add(BASE + "com.android.mediadrm.signer_intermediates.jar");
//        jar_list.add(BASE + "org.apache.http.legacy_intermediates.jar");
////        jar_list.add(BASE + "android-support-v7-recyclerview_intermediates.jar");
//        jar_list.add(BASE + "uiautomator.core_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-protobuf-lite-target_intermediates.jar");
//        jar_list.add(BASE + "com.android.runtime.debug.apache-xml_intermediates.jar");
//        jar_list.add(BASE + "dialer-glide-annotation-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.transition_transition_intermediates.jar");
//        jar_list.add(BASE + "dialer-dagger2-target_intermediates.jar");
//        jar_list.add(BASE + "am_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-core-ui_intermediates.jar");
//        jar_list.add(BASE + "com.android.nfc_extras_intermediates.jar");
//        jar_list.add(BASE + "calendar-common_intermediates.jar");
//        jar_list.add(BASE + "libprotobuf-java-lite_intermediates.jar");
//        jar_list.add(BASE + "androidx.lifecycle_lifecycle-runtime_intermediates.jar");
//        jar_list.add(BASE + "dpm_intermediates.jar");
//        jar_list.add(BASE + "libnanohttpd_intermediates.jar");
//        jar_list.add(BASE + "androidx.annotation_annotation_intermediates.jar");
//        jar_list.add(BASE + "services.net_intermediates.jar");
//        jar_list.add(BASE + "libphonenumber_intermediates.jar");
//        jar_list.add(BASE + "inputlib_intermediates.jar");
////        jar_list.add(BASE + "android.test.mock_intermediates.jar");
//        jar_list.add(BASE + "setup-wizard-lib_intermediates.jar");
//        jar_list.add(BASE + "settings-contextual-card-protos-lite_intermediates.jar");
//        jar_list.add(BASE + "settings-log-bridge-protos-lite_intermediates.jar");
//        jar_list.add(BASE + "zxing-core-1.7_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-all-target_intermediates.jar");
//        jar_list.add(BASE + "com.android.runtime.debug.bouncycastle_intermediates.jar");
//        jar_list.add(BASE + "dialer-glide-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.legacy_legacy-support-core-utils_intermediates.jar");
//        jar_list.add(BASE + "hid_intermediates.jar");
//        jar_list.add(BASE + "iconloader_base_intermediates.jar");
//        jar_list.add(BASE + "dialer-grpc-core-target_intermediates.jar");
//        jar_list.add(BASE + "androidx.media_media_intermediates.jar");




        //// ===========================12.0=======

        jar_list.add(BASE + "com.android.location.provider_intermediates.jar");
        jar_list.add(BASE + "Launcher3QuickStepLib_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-stub-target_intermediates.jar");
        jar_list.add(BASE + "service-media-s.com.android.media_intermediates.jar");
        jar_list.add(BASE + "glide_intermediates.jar");
        jar_list.add(BASE + "libbackup_intermediates.jar");
        jar_list.add(BASE + "dialer-zxing-target_intermediates.jar");
        jar_list.add(BASE + "dialer-j2objc-annotations-target_intermediates.jar");
        jar_list.add(BASE + "guava_intermediates.jar");
        jar_list.add(BASE + "dialer-commons-io-target_intermediates.jar");
        jar_list.add(BASE + "service-appsearch.com.android.appsearch_intermediates.jar");
        jar_list.add(BASE + "android-support-v4_intermediates.jar");
        jar_list.add(BASE + "conscrypt.com.android.conscrypt_intermediates.jar");
        jar_list.add(BASE + "android.net.ipsec.ike.com.android.ipsec_intermediates.jar");
        jar_list.add(BASE + "dialer-okio-target_intermediates.jar");
        jar_list.add(BASE + "colorpicker_intermediates.jar");
        jar_list.add(BASE + "uiautomator_intermediates.jar");
        jar_list.add(BASE + "android-common_intermediates.jar");
        jar_list.add(BASE + "sm_intermediates.jar");
        jar_list.add(BASE + "com.android.media.remotedisplay_intermediates.jar");
        jar_list.add(BASE + "abx_intermediates.jar");
        jar_list.add(BASE + "framework-statsd.com.android.os.statsd_intermediates.jar");
        jar_list.add(BASE + "framework-wifi.com.android.wifi_intermediates.jar");
        jar_list.add(BASE + "content_intermediates.jar");
        jar_list.add(BASE + "bmgr_intermediates.jar");
        jar_list.add(BASE + "dialer-guava-target_intermediates.jar");
        jar_list.add(BASE + "androidx.fragment_fragment_intermediates.jar");
        jar_list.add(BASE + "android-opt-timezonepicker_intermediates.jar");
        jar_list.add(BASE + "jsr305_intermediates.jar");
        jar_list.add(BASE + "android-support-v13_intermediates.jar");
        jar_list.add(BASE + "Launcher3CommonDepsLib_intermediates.jar");
        jar_list.add(BASE + "incident-helper-cmd_intermediates.jar");
        jar_list.add(BASE + "SystemUI-statsd_intermediates.jar");
        jar_list.add(BASE + "xmp_toolkit_intermediates.jar");
        jar_list.add(BASE + "service-permission.com.android.permission_intermediates.jar");
        jar_list.add(BASE + "ethernet-service_intermediates.jar");
        jar_list.add(BASE + "ims-common_intermediates.jar");
        jar_list.add(BASE + "android-support-design_intermediates.jar");
        jar_list.add(BASE + "uinput_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-okhttp-target_intermediates.jar");
        jar_list.add(BASE + "framework-sdkextensions.com.android.sdkext_intermediates.jar");
        jar_list.add(BASE + "framework-mediaprovider.com.android.mediaprovider_intermediates.jar");
        jar_list.add(BASE + "android-ex-camera2-portability_intermediates.jar");
        jar_list.add(BASE + "dialer-animal-sniffer-annotations-target_intermediates.jar");
        jar_list.add(BASE + "android-support-dynamic-animation_intermediates.jar");
        jar_list.add(BASE + "service-connectivity.com.android.tethering_intermediates.jar");
        jar_list.add(BASE + "dialer-javax-annotation-api-target_intermediates.jar");
        jar_list.add(BASE + "updatable-media.com.android.media_intermediates.jar");
        jar_list.add(BASE + "core-oj.com.android.art_intermediates.jar");
        jar_list.add(BASE + "telephony-common_intermediates.jar");
//        jar_list.add(BASE + "android.test.base_intermediates.jar");
        jar_list.add(BASE + "libphotoviewer_intermediates.jar");
        jar_list.add(BASE + "framework-permission-s.com.android.permission_intermediates.jar");
        jar_list.add(BASE + "voip-common_intermediates.jar");
        jar_list.add(BASE + "requestsync_intermediates.jar");
        jar_list.add(BASE + "androidx.legacy_legacy-support-v4_intermediates.jar");
        jar_list.add(BASE + "services_intermediates.jar");
        jar_list.add(BASE + "android-support-core-ui_intermediates.jar");
        jar_list.add(BASE + "framework-connectivity.com.android.tethering_intermediates.jar");
        jar_list.add(BASE + "androidx.viewpager_viewpager_intermediates.jar");
        jar_list.add(BASE + "com.android.future.usb.accessory_intermediates.jar");
        jar_list.add(BASE + "android.hidl.manager-V1.0-java_intermediates.jar");
        jar_list.add(BASE + "android-support-v7-appcompat_intermediates.jar");
        jar_list.add(BASE + "service-scheduling.com.android.scheduling_intermediates.jar");
        jar_list.add(BASE + "dialer-error-prone-target_intermediates.jar");
        jar_list.add(BASE + "androidx.appcompat_appcompat_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-context-target_intermediates.jar");
        jar_list.add(BASE + "androidx.recyclerview_recyclerview_intermediates.jar");
        jar_list.add(BASE + "vr_intermediates.jar");
        jar_list.add(BASE + "bu_intermediates.jar");
        jar_list.add(BASE + "dialer-libshortcutbadger-target_intermediates.jar");
        jar_list.add(BASE + "libchips_intermediates.jar");
        jar_list.add(BASE + "dialer-okhttp-target_intermediates.jar");
//        jar_list.add(BASE + "android.test.runner_intermediates.jar");
        jar_list.add(BASE + "dialer-javax-inject-target_intermediates.jar");
        jar_list.add(BASE + "volley_intermediates.jar");
        jar_list.add(BASE + "okhttp.com.android.art_intermediates.jar");
        jar_list.add(BASE + "framework-graphics_intermediates.jar");
        jar_list.add(BASE + "androidx.legacy_legacy-support-v13_intermediates.jar");
        jar_list.add(BASE + "android-support-transition_intermediates.jar");
        jar_list.add(BASE + "android-common-framesequence_intermediates.jar");
        jar_list.add(BASE + "monkey_intermediates.jar");
        jar_list.add(BASE + "dialer-mime4j-dom-target_intermediates.jar");
        jar_list.add(BASE + "ext_intermediates.jar");
        jar_list.add(BASE + "core-libart.com.android.art_intermediates.jar");
        jar_list.add(BASE + "telecom_intermediates.jar");
        jar_list.add(BASE + "lockagent_intermediates.jar");
        jar_list.add(BASE + "javax.obex_intermediates.jar");
        jar_list.add(BASE + "framework-scheduling.com.android.scheduling_intermediates.jar");
        jar_list.add(BASE + "android-support-v7-cardview_intermediates.jar");
        jar_list.add(BASE + "bouncycastle.com.android.art_intermediates.jar");
        jar_list.add(BASE + "androidx.palette_palette_intermediates.jar");
        jar_list.add(BASE + "framework-permission.com.android.permission_intermediates.jar");
        jar_list.add(BASE + "framework-minus-apex_intermediates.jar");
        jar_list.add(BASE + "service-statsd.com.android.os.statsd_intermediates.jar");
        jar_list.add(BASE + "locksettings_intermediates.jar");
        jar_list.add(BASE + "appwidget_intermediates.jar");
        jar_list.add(BASE + "android.hidl.base-V1.0-java_intermediates.jar");
        jar_list.add(BASE + "androidx.core_core_intermediates.jar");
        jar_list.add(BASE + "dialer-disklrucache-target_intermediates.jar");
        jar_list.add(BASE + "com.android.vcard_intermediates.jar");
        jar_list.add(BASE + "SystemUISharedLib_intermediates.jar");
        jar_list.add(BASE + "dialer-mime4j-core-target_intermediates.jar");
        jar_list.add(BASE + "dialer-gifdecoder-target_intermediates.jar");
        jar_list.add(BASE + "svc_intermediates.jar");
        jar_list.add(BASE + "com.android.mediadrm.signer_intermediates.jar");
        jar_list.add(BASE + "org.apache.http.legacy_intermediates.jar");
        jar_list.add(BASE + "android-support-v7-recyclerview_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-protobuf-lite-target_intermediates.jar");
        jar_list.add(BASE + "dialer-glide-annotation-target_intermediates.jar");
        jar_list.add(BASE + "service-wifi.com.android.wifi_intermediates.jar");
        jar_list.add(BASE + "dialer-dagger2-target_intermediates.jar");
        jar_list.add(BASE + "am_intermediates.jar");
        jar_list.add(BASE + "apache-xml.com.android.art_intermediates.jar");
        jar_list.add(BASE + "androidx.legacy_legacy-support-core-ui_intermediates.jar");
        jar_list.add(BASE + "core-icu4j.com.android.i18n_intermediates.jar");
        jar_list.add(BASE + "com.android.nfc_extras_intermediates.jar");
        jar_list.add(BASE + "calendar-common_intermediates.jar");
        jar_list.add(BASE + "libprotobuf-java-lite_intermediates.jar");
        jar_list.add(BASE + "framework-appsearch.com.android.appsearch_intermediates.jar");
        jar_list.add(BASE + "framework-tethering.com.android.tethering_intermediates.jar");
        jar_list.add(BASE + "androidx.annotation_annotation_intermediates.jar");
        jar_list.add(BASE + "libphonenumber_intermediates.jar");
//        jar_list.add(BASE + "android.test.mock_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-all-target_intermediates.jar");
        jar_list.add(BASE + "dialer-glide-target_intermediates.jar");
        jar_list.add(BASE + "androidx.legacy_legacy-support-core-utils_intermediates.jar");
        jar_list.add(BASE + "androidx.collection_collection_intermediates.jar");
        jar_list.add(BASE + "hid_intermediates.jar");
        jar_list.add(BASE + "dialer-grpc-core-target_intermediates.jar");
        jar_list.add(BASE + "androidx.media_media_intermediates.jar");



        for (String tem: jar_list){
            r += File.pathSeparator + tem;
        }
        System.out.println(r);
        return r;
    }

    public static String loadJarPath(){
        return loadJarPath("UBUNTU");
//        return loadJarPath("MAC");
    }

}
