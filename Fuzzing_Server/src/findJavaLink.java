import javaLink.JavaLink;
import javaLink.JavaLinkFound;
import util.JniClass;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

public class findJavaLink {

    public static String runCMD(String commandStr) {
        BufferedReader br = null;
        try {
            Process p = Runtime.getRuntime().exec(commandStr);
            br = new BufferedReader(new InputStreamReader(p.getInputStream(), Charset.forName("GBK")));
            String line = null;
            StringBuilder sb = new StringBuilder();
            while ((line = br.readLine()) != null) {
                sb.append(line + "\n");
            }
//            System.out.println(sb.toString());
            return sb.toString();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (br != null) {
                try {
                    br.close();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }

        }
        return null;
    }

    public static void main(String[] args) throws IOException {
        if(args.length != 0) {
            List<JniClass>  jniList = Engine.load();
            String mainClassStr = args[0];
            String[] clazzL = mainClassStr.split("\\.");
            String mainClassStrLast = clazzL[clazzL.length - 1];
            ArrayList<String> starts_call = new ArrayList<String>();
            for(JniClass jniClass : jniList){
                String clazz = jniClass.getClass_();

                if(mainClassStr.equals(clazz)) {
                    String fun = jniClass.getFun();
                    starts_call.add(fun + "(");
                }
            }
            ArrayList<String> supportClassList = new ArrayList<String>();
            JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
        }else{
            List<JniClass>  jniList = Engine.load();
            HashSet<String> hs = new HashSet<>();
            for(JniClass jniClass : jniList){
                String clazz = jniClass.getClass_();
                hs.add(clazz);
            }
            System.out.println(hs.size());
            for(String s : hs){
                String cmd = "java -jar JavaLink.jar " + s;
                System.out.println(cmd);
                runCMD(cmd);
            }
        }
//========================================
// 调用的server需要手动加入 不能自动找到
//========================================
//android.permission.CAMERA
//        String mainClassStrLast = "ICameraService$Stub$Proxy";
//        String mainClassStr = "android.hardware." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("validateConnectLocked(");
//        starts_call.add("connectHelper(");
//        starts_call.add("connect(");
//        starts_call.add("connectLegacy(");
//        starts_call.add("connectDevice(");
//        starts_call.add("initializeShimMetadata(");
//        starts_call.add("getLegacyParametersLazy(");
//        starts_call.add("getLegacyParameters(");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call);

//========================================
//android.permission.ACCESS_FM_RADIO 8.0有 7.0无 8.1无 7.1无 9.0无
//        String mainClassStrLast = "TunerAdapter";
//        String mainClassStr = "android.hardware.radio." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("native_setup(");
//        starts_call.add("setConfiguration(");
//        starts_call.add("setMute(");
//        starts_call.add("getMute(");
//        starts_call.add("step(");
//        starts_call.add("scan(");
//        starts_call.add("tune(");
//        starts_call.add("cancel(");
//        starts_call.add("getProgramInformation(");
//        starts_call.add("isAntennaConnected(");
//        starts_call.add("hasControl(");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call);

//========================================
//android.permission.CONTROL_WIFI_DISPLAY
//        String mainClassStrLast = "RemoteDisplay";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("nativeListen(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.display.DisplayManagerService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
//[android.permission.RECORD_AUDIO] AND [android.permission.CAMERA]
//        String mainClassStrLast = "MediaRecorder";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
////        starts_call.add("setVideoSource(");
//        starts_call.add("setAudioSource(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("android.filterpacks.videosink.MediaEncoderFilter");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
//android.permission.ACCESS_DRM_CERTIFICATES
//        String mainClassStrLast = "MediaDrm";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("signRSANative(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.mediadrm.signer.MediaDrmSigner");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
        //编译好的jar里没有这个库
//        com.android.mediadrm.signer.MediaDrmSigner: signRSA(android.media.MediaDrm, byte[],  java.lang.String, byte[], byte[])
//========================================
//android.permission.LOCATION_HARDWARE 8.0有 7.0无 7.1无
//        String mainClassStrLast = "SystemSensorManager";
//        String mainClassStr = "android.hardware." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("nativeSetOperationParameter(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.systemui.util.AsyncSensorManager");
//        supportClassList.add("com.android.server.SensorNotificationService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//        String mainClassStrLast = "SensorNotificationService";
//        String mainClassStr = "com.android.server." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("onLocationChanged(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
// android.permission.INTERNET [http:// or https:// or rtsp://]
//        String mainClassStrLast = "MediaPlayer";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("nativeSetDataSource(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//        String mainClassStrLast = "VideoView";
//        String mainClassStr = "android.widget." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("refer source code to find methods which invoke openVideo(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
////        supportClassList.add("android.media.RingtoneManager");
////        supportClassList.add("android.widget.VideoView");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
//android.permission.ACCESS_SURFACE_FLINGER
//        String mainClassStrLast = "SurfaceControl";
//        String mainClassStr = "android.view." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        //before 10.0
//        starts_call.add("nativeGetHdrCapabilities(");
//        //10.0
////        starts_call.add("nativeGetNativeTransactionFinalizer(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
////        supportClassList.add("com.android.server.display.LocalDisplayAdapter");
////        supportClassList.add("com.android.server.display.DisplayManagerService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
//android.permission.READ_FRAME_BUFFER
//        String mainClassStrLast = "SurfaceControl";
//        String mainClassStr = "android.view." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("nativeScreenshot(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("android.media.projection");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

        ////takeScreenshot(
//        String mainClassStrLast = "UiAutomationConnection";
//        String mainClassStr = "android.app." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("takeScreenshot(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

        ////captureScreenshotTextureAndSetViewport(
        //prepare(
//        String mainClassStrLast = "ColorFade";
//        String mainClassStr = "com.android.server.display." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("prepare(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

        ////ScreenRotationAnimation(
//        String mainClassStrLast = "ScreenRotationAnimation";
//        String mainClassStr = "com.android.server.wm." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("ScreenRotationAnimation(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);


//========================================
// android_hardware_SoundTrigger.cpp
//android.permission.CAPTURE_AUDIO_HOTWORD
//        String mainClassStrLast = "SoundTrigger";
//        String mainClassStr = "android.hardware.soundtrigger." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("listModules(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.soundtrigger.SoundTriggerHelper");
//        supportClassList.add("com.android.server.soundtrigger.SoundTriggerModule");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//---------------------------------------
        //android.permission.CAPTURE_AUDIO_HOTWORD
//        String mainClassStrLast = "SoundTriggerModule";
//        String mainClassStr = "android.hardware.soundtrigger." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("native_setup(");
//        starts_call.add("loadSoundModel(");
//        starts_call.add("unloadSoundModel(");
//        starts_call.add("startRecognition(");
//        starts_call.add("stopRecognition(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.soundtrigger.SoundTriggerHelper");
//        supportClassList.add("com.android.server.soundtrigger.SoundTriggerModule");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
// android_media_AudioSystem.cpp

//        //android.permission.MODIFY_AUDIO_SETTINGS
//        String mainClassStrLast = "AudioSystem";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("setParameters(");
////        starts_call.add("muteMicrophone(");
////        starts_call.add("setDeviceConnectionState(");
////        starts_call.add("handleDeviceConfigChange(");
////        starts_call.add("setPhoneState(");
////        starts_call.add("setForceUse(");
////        starts_call.add("initStreamVolume(");
////        starts_call.add("setStreamVolumeIndex(");
////        starts_call.add("setMasterVolume(");
////        starts_call.add("setMasterMute(");
////        starts_call.add("setMasterMono(");
//
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.audio.AudioService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
//------------------10.0---------------------
        //android.permission.MODIFY_AUDIO_SETTINGS
//        String mainClassStrLast = "AudioSystem";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("setParameters(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.audio.AudioService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
//------------------10.0---------------------
//android.permission.MODIFY_AUDIO_ROUTING
//String mainClassStrLast = "AudioSystem";
//String mainClassStr = "android.media." + mainClassStrLast;
//ArrayList<String> starts_call = new ArrayList<String>();
//starts_call.add("setForceUse(");
//ArrayList<String> supportClassList = new ArrayList<String>();
//supportClassList.add("com.android.server.audio.AudioService");
//JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
//------------------10.0---------------------
        //android.permission.CAPTURE_MEDIA_OUTPUT
//String mainClassStrLast = "AudioSystem";
//String mainClassStr = "android.media." + mainClassStrLast;
//ArrayList<String> starts_call = new ArrayList<String>();
//starts_call.add("registerPolicyMixes(");
//ArrayList<String> supportClassList = new ArrayList<String>();
//supportClassList.add("com.android.server.audio.AudioService");
//JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
//---------------------------------------
        //android.permission.MODIFY_AUDIO_ROUTING
//        String mainClassStrLast = "AudioSystem";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("createAudioPatch(");
//        starts_call.add("releaseAudioPatch(");
//        starts_call.add("setAudioPortConfig(");
//        starts_call.add("registerPolicyMixes(");
//
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.audio.AudioService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//---------------------------------------
        //uid == AID_SYSTEM
//        String mainClassStrLast = "AudioSystem";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("setLowRamDevice(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("com.android.server.audio.AudioService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//========================================
//android.permission.RECORD_AUDIO
//        String mainClassStrLast = "AudioRecord";
//        String mainClassStr = "android.media." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
////        starts_call.add("native_setup(");
////        starts_call.add("deferred_connect(");
////        starts_call.add("AudioRecord(");
////        starts_call.add("native_read_in_direct_buffer(");
////        starts_call.add("read(");
//        starts_call.add("native_start(");
////        starts_call.add("startRecording(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        supportClassList.add("android.filterpacks.videosink.MediaEncoderFilter");
////        supportClassList.add("com.android.server.soundtrigger.SoundTriggerService");
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);

//        //==================test========
//        String mainClassStrLast = "ContentService";
//        String mainClassStr = "com.android.server.content." + mainClassStrLast;
//        ArrayList<String> starts_call = new ArrayList<String>();
//        starts_call.add("setSyncAutomaticallyAsUser(");
//        ArrayList<String> supportClassList = new ArrayList<String>();
//        JavaLink.run(mainClassStrLast, mainClassStr, 1, starts_call, supportClassList);
    }

}
