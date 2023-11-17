package javaLink;

import com.alibaba.fastjson.JSON;
import soot.*;
import soot.options.Options;

import util.JniClass;
import util.config;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

public class ExtractJNINew {
    static LinkedList<String> excludeList;

    public static void main(String[] args) throws IOException {
        String path = config.loadJarPath();
        System.out.println(path);
        Scene.v().setSootClassPath(path);

        //add an intra-procedural analysis phase to Soot

        excludeJDKLibrary();

        Options.v().set_whole_program(true);
        Options.v().set_app(true);
        Options.v().set_validate(true);

        SootClass c = Scene.v().loadClassAndSupport("env->FindClass(kClassName)");ArrayList<String> supportClassList = new ArrayList<String>();supportClassList.add("nContextDeinitToClient");supportClassList.add("android.graphics.animation.NativeInterpolatorFactory");supportClassList.add("android.graphics.animation.RenderNodeAnimator");supportClassList.add("android.graphics.Canvas");supportClassList.add("android.graphics.ColorSpace$Rgb");supportClassList.add("android.graphics.drawable.AnimatedVectorDrawable");supportClassList.add("android.graphics.drawable.VectorDrawable");supportClassList.add("android.graphics.Matrix");supportClassList.add("android.graphics.RecordingCanvas");supportClassList.add("android.graphics.RenderNode");supportClassList.add("android.util.PathParser");supportClassList.add("android.graphics.Bitmap");supportClassList.add("android.graphics.BitmapFactory");supportClassList.add("android.graphics.Camera");supportClassList.add("android.graphics.CanvasProperty");supportClassList.add("([F)J");supportClassList.add("android.graphics.FontFamily");supportClassList.add("android.graphics.ImageDecoder");supportClassList.add("android.graphics.Interpolator");supportClassList.add("([B)J");supportClassList.add("android.graphics.NinePatch");supportClassList.add("android.graphics.Paint");supportClassList.add("android.graphics.DrawFilter");supportClassList.add("android.graphics.Path");supportClassList.add("(FF)J");supportClassList.add("android.graphics.PathMeasure");supportClassList.add("nativeUpdateShader");supportClassList.add("nativeCreateShaderEffect");supportClassList.add("android.graphics.Typeface");supportClassList.add("android.graphics.YuvImage");supportClassList.add("android.graphics.fonts.Font$Builder");supportClassList.add("android.graphics.fonts.FontFamily$Builder");supportClassList.add("android.graphics.text.LineBreaker");supportClassList.add("android.graphics.text.MeasuredText");supportClassList.add("android.graphics.text.TextRunShaper");supportClassList.add("android.graphics.drawable.AnimatedImageDrawable");supportClassList.add("android.graphics.TextureLayer");supportClassList.add("android.graphics.HardwareRenderer");supportClassList.add("android.graphics.BitmapRegionDecoder");supportClassList.add("android.graphics.GraphicsStatsService");supportClassList.add("android.graphics.Movie");supportClassList.add("android.graphics.RegionIterator");supportClassList.add("android.graphics.pdf.PdfDocument");supportClassList.add("android.graphics.pdf.PdfEditor");supportClassList.add("android.graphics.pdf.PdfRenderer");supportClassList.add("com.android.server.am.CachedAppOptimizer");supportClassList.add("com.android.server.alarm.AlarmManagerService");supportClassList.add("android.animation.PropertyValuesHolder");supportClassList.add("android.os.SystemClock");supportClassList.add("android.os.Trace");supportClassList.add("android.text.AndroidCharacter");supportClassList.add("android.util.EventLog");supportClassList.add("android.util.Log");supportClassList.add("android.content.res.StringBlock");supportClassList.add("android.content.res.XmlBlock");supportClassList.add("com.android.internal.util.VirtualRefBasePtr");supportClassList.add("com.android.internal.content.NativeLibraryHelper");supportClassList.add("com.google.android.gles_jni.EGLImpl");supportClassList.add("com.google.android.gles_jni.GLImpl");supportClassList.add("android.app.Activity");supportClassList.add("android.app.ActivityThread");supportClassList.add("android.app.NativeActivity");supportClassList.add("android.app.admin.SecurityLog");supportClassList.add("android.opengl.EGL14");supportClassList.add("android.opengl.EGL15");supportClassList.add("android.opengl.EGLExt");supportClassList.add("android.opengl.GLES10");supportClassList.add("android.opengl.GLES10Ext");supportClassList.add("android.opengl.GLES11");supportClassList.add("android.opengl.GLES11Ext");supportClassList.add("android.opengl.GLES20");supportClassList.add("android.opengl.GLES30");supportClassList.add("android.opengl.GLES31");supportClassList.add("android.opengl.GLES31Ext");supportClassList.add("android.opengl.GLES32");supportClassList.add("android.database.CursorWindow");supportClassList.add("android.database.sqlite.SQLiteConnection");supportClassList.add("android.database.sqlite.SQLiteGlobal");supportClassList.add("android.database.sqlite.SQLiteDebug");supportClassList.add("android.graphics.GraphicBuffer");supportClassList.add("android.graphics.SurfaceTexture");supportClassList.add("android.view.DisplayEventReceiver");supportClassList.add("android.view.InputChannel");supportClassList.add("android.view.InputEventReceiver");supportClassList.add("android.view.InputEventSender");supportClassList.add("android.view.InputQueue");supportClassList.add("android.view.KeyCharacterMap");supportClassList.add("android.view.KeyEvent");supportClassList.add("android.view.MotionEvent");supportClassList.add("android.view.Surface");supportClassList.add("android.view.SurfaceControl");supportClassList.add("android.graphics.BLASTBufferQueue");supportClassList.add("android.view.SurfaceSession");supportClassList.add("android.view.TextureView");supportClassList.add("android.view.VelocityTracker");supportClassList.add("android.text.Hyphenator");supportClassList.add("android.os.Debug");supportClassList.add("FindClassOrDie(env, CLASS_PATH)");supportClassList.add("android.os.HidlSupport");supportClassList.add("android.os.MemoryFile");supportClassList.add("android.os.MessageQueue");supportClassList.add("android.os.Parcel");supportClassList.add("android.os.PerformanceHintManager");supportClassList.add("android.os.SELinux");supportClassList.add("android.os.ServiceManager");supportClassList.add("android.os.storage.StorageManager");supportClassList.add("android.os.UEventObserver");supportClassList.add("android.os.VintfObject");supportClassList.add("android.os.VintfRuntimeInfo");supportClassList.add("android.os.incremental.IncrementalManager");supportClassList.add("android.net.LocalSocketImpl");supportClassList.add("android.service.dataloader.DataLoaderService");supportClassList.add("android.content.res.AssetManager");supportClassList.add("android.os.Binder");supportClassList.add("android.util.CharsetUtils");supportClassList.add("android.util.MemoryIntArray");supportClassList.add("android.os.Process");supportClassList.add("android.media.AudioRecord");supportClassList.add("android.media.AudioTrack");supportClassList.add("android.media.audiopolicy.AudioProductStrategy");supportClassList.add("android.media.audiopolicy.AudioVolumeGroup");supportClassList.add("android.media.audiopolicy.AudioVolumeGroupChangeHandler");supportClassList.add("android.media.RemoteDisplay");supportClassList.add("android.media.ToneGenerator");supportClassList.add("android.hardware.Camera");supportClassList.add("FAIL");supportClassList.add("android.hardware.camera2.DngCreator");supportClassList.add("FAIL");supportClassList.add("FAIL");supportClassList.add("android.hardware.display.DisplayManagerGlobal");supportClassList.add("android.hardware.HardwareBuffer");supportClassList.add("nativeInjectSensorData");supportClassList.add("android.hardware.SerialPort");supportClassList.add("android.hardware.usb.UsbDevice");supportClassList.add("android.hardware.usb.UsbDeviceConnection");supportClassList.add("android.hardware.usb.UsbRequest");supportClassList.add("android.hardware.location.ActivityRecognitionHardware");supportClassList.add("android.os.FileObserver$ObserverThread");supportClassList.add("android.opengl.Matrix");supportClassList.add("com.android.server.NetworkManagementSocketTagger");supportClassList.add("android.ddm.DdmHandleNativeHeap");supportClassList.add("android.app.backup.BackupDataInput");supportClassList.add("android.app.backup.BackupDataOutput");supportClassList.add("android.app.backup.FileBackupHelperBase");supportClassList.add("android.app.backup.BackupHelperDispatcher");supportClassList.add("android.app.backup.FullBackup");supportClassList.add("android.content.res.ApkAssets");supportClassList.add("android.content.res.ObbScanner");supportClassList.add("android.security.Scrypt");supportClassList.add("com.android.internal.content.om.OverlayConfig");supportClassList.add("com.android.internal.net.NetworkUtilsInternal");supportClassList.add("com.android.internal.os.ClassLoaderFactory");supportClassList.add("com.android.internal.os.DmabufInfoReader");supportClassList.add("com.android.internal.os.KernelCpuBpfTracking");supportClassList.add("com.android.internal.os.KernelCpuTotalBpfMapReader");supportClassList.add("KernelCpuUidFreqTimeBpfMapReader");supportClassList.add("com.android.internal.os.KernelSingleProcessCpuThreadReader");supportClassList.add("com.android.internal.os.KernelSingleUidTimeReader$Injector");supportClassList.add("MakeGlobalRefOrDie(env, FindClassOrDie(env, kZygoteInitClassName))");supportClassList.add("com.android.internal.os.ZygoteCommandBuffer");supportClassList.add("android.view.InputWindowHandle");supportClassList.add("android.view.InputApplicationHandle");supportClassList.add("android.media.audiofx.AudioEffect");supportClassList.add("android.media.audiofx.SourceDefaultEffect");supportClassList.add("android.media.audiofx.StreamDefaultEffect");supportClassList.add("android.media.audiofx.Visualizer");supportClassList.add("com.android.internal.car.CarServiceHelperService");supportClassList.add("env->GetObjectClass(object)");supportClassList.add("com.android.commands.hid.Device");supportClassList.add("android.media.ImageWriter");supportClassList.add("android.media.ImageReader");supportClassList.add("android.media.JetPlayer");supportClassList.add("android.media.MediaCrypto");supportClassList.add("android.media.MediaCodec");supportClassList.add("android.media.MediaCodecList");supportClassList.add("android.media.MediaDescrambler");supportClassList.add("android.media.MediaDrm");supportClassList.add("android.media.MediaExtractor");supportClassList.add("android.media.MediaHTTPConnection");supportClassList.add("android.media.MediaMetadataRetriever");supportClassList.add("android.media.MediaMuxer");supportClassList.add("android.media.MediaPlayer");supportClassList.add("android.media.EncoderCapabilities");supportClassList.add("android.media.MediaRecorder");supportClassList.add("android.media.MediaSync");supportClassList.add("android.media.ResampleInputStream");supportClassList.add("android.mtp.MtpDatabase");supportClassList.add("android.mtp.MtpDevice");supportClassList.add("android.mtp.MtpServer");supportClassList.add("android.media.tv.tuner.Tuner");supportClassList.add("com.android.server.net.NetworkStatsFactory");supportClassList.add("com.android.printspooler.util.BitmapSerializeUtils");supportClassList.add("nContextDeinitToClient");supportClassList.add("com.android.server.broadcastradio.hal1.BroadcastRadioService");supportClassList.add("com.android.server.broadcastradio.hal1.Tuner");supportClassList.add("com.android.server.broadcastradio.hal1.TunerCallback");supportClassList.add("com.android.server.adb.AdbDebuggingManager$PairingThread");supportClassList.add("com.android.server.am.BatteryStatsService");supportClassList.add("com.android.server.ConsumerIrService");supportClassList.add("com.android.server.connectivity.Vpn");supportClassList.add("com.android.server.gpu.GpuService");supportClassList.add("com.android.server.HardwarePropertiesManagerService");supportClassList.add("com.android.server.input.InputManagerService");supportClassList.add("com.android.server.lights.LightsService");supportClassList.add("com.android.server.location.gnss.hal.GnssNative");supportClassList.add("com.android.server.locksettings.SyntheticPasswordManager");supportClassList.add("com.android.server.net.NetworkStatsService");supportClassList.add("com.android.server.power.PowerManagerService");supportClassList.add("com.android.server.SerialService");supportClassList.add("com.android.server.stats.pull.StatsPullAtomService");supportClassList.add("com.android.server.SystemServer");supportClassList.add("com.android.server.tv.UinputBridge");supportClassList.add("com.android.server.tv.TvInputHal");supportClassList.add("com.android.server.vr.VrManagerService");supportClassList.add("com.android.server.usb.UsbAlsaJackDetector");supportClassList.add("com.android.server.usb.UsbDeviceManager");supportClassList.add("com.android.server.usb.UsbMidiDevice");supportClassList.add("com.android.server.usb.UsbHostManager");supportClassList.add("com.android.server.vibrator.VibratorController$NativeWrapper");supportClassList.add("com.android.server.vibrator.VibratorManagerService");supportClassList.add("com.android.server.PersistentDataBlockService");supportClassList.add("com.android.server.am.LowMemDetector");supportClassList.add("com.android.server.pm.PackageManagerShellCommandDataLoader");supportClassList.add("com.android.server.sensors.SensorService");supportClassList.add("android.media.SoundPool");supportClassList.add("com.android.commands.uinput.Device");

        for(String classTem : supportClassList){
            Scene.v().forceResolve(classTem, SootClass.BODIES);
        }
        c.setApplicationClass();
//        Scene.v().addBasicClass("com.android.server.LocationManagerService");

        Scene.v().loadNecessaryClasses();
        // 初始化 Soot

        // 创建 JNI 调用信息的列表
        List<JniClass> jniMethods = new ArrayList<>();

        int count = 0;
        // 遍历所有类和方法
        for (SootClass clazz : Scene.v().getApplicationClasses()) {
            System.out.println(clazz.getName());
            for (SootMethod method : clazz.getMethods()) {
                if (method.isNative()){
                    // 获取方法的返回类型
                    List<String> returnType = Collections.singletonList(method.getReturnType().toString());

                    // 获取方法的参数类型
                    List<String> parameters = new ArrayList<>();
                    if (method.getParameterCount() == 0) {
                        // 如果没有参数，按您的要求添加空字符串
                        parameters.add("");
                    } else {
                        method.getParameterTypes().forEach(type -> parameters.add(type.toString()));
                    }

                    // 检查方法是否为静态
                    boolean isStatic = method.isStatic();

                    // 添加 JNI 方法信息
                    jniMethods.add(new JniClass(clazz.getName(), returnType, method.getName(), parameters, isStatic));
                    count++;
                }
            }
        }

        System.out.println("Found JNI methods: " + count);

        // 输出结果
        BufferedWriter writer = new BufferedWriter(new FileWriter("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/jni12.0/jni_with_isStatic.json"));
        writer.write(JSON.toJSONString(jniMethods));
        writer.close();
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

    private static void excludeJDKLibrary()
    {
        Options.v().set_exclude(excludeList());
        Options.v().set_no_bodies_for_excluded(true);
        Options.v().set_allow_phantom_refs(true);
    }
}
