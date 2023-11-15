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

        SootClass c = Scene.v().loadClassAndSupport("android.view.InputWindowHandle");ArrayList<String> supportClassList = new ArrayList<String>();supportClassList.add("android.media.audiofx.SourceDefaultEffect");supportClassList.add("android.media.MediaSync");supportClassList.add("com.android.server.broadcastradio.hal1.Tuner");supportClassList.add("android.media.audiopolicy.AudioVolumeGroup");supportClassList.add("com.android.server.vibrator.VibratorController$NativeWrapper");supportClassList.add("android.drm.DrmManagerClient");supportClassList.add("com.android.server.pm.PackageManagerShellCommandDataLoader");supportClassList.add("android.hardware.camera2.impl.CameraMetadataNative");supportClassList.add("android.opengl.GLES10Ext");supportClassList.add("android.hardware.display.DisplayManagerGlobal");supportClassList.add("android.media.MediaCodecList");supportClassList.add("android.graphics.Matrix");supportClassList.add("com.android.server.vibrator.VibratorManagerService");supportClassList.add("android.os.HidlMemory");supportClassList.add("android.view.KeyCharacterMap");supportClassList.add("android.graphics.pdf.PdfRenderer");supportClassList.add("com.android.server.net.NetworkStatsFactory");supportClassList.add("android.view.InputEventReceiver");supportClassList.add("android.app.backup.BackupDataInput");supportClassList.add("android.media.MediaCrypto");supportClassList.add("android.graphics.ColorMatrixColorFilter");supportClassList.add("android.view.SurfaceControl");supportClassList.add("android.hardware.camera2.utils.SurfaceUtils");supportClassList.add("android.os.Parcel");supportClassList.add("android.database.sqlite.SQLiteDebug");supportClassList.add("android.media.audiopolicy.AudioVolumeGroupChangeHandler");supportClassList.add("android.graphics.SumPathEffect");supportClassList.add("android.graphics.CanvasProperty");supportClassList.add("android.graphics.RecordingCanvas");supportClassList.add("android.opengl.ETC1");supportClassList.add("android.mtp.MtpDatabase");supportClassList.add("com.android.server.location.gnss.GnssConfiguration");supportClassList.add("android.os.MessageQueue");supportClassList.add("android.util.Log");supportClassList.add("com.android.server.gpu.GpuService");supportClassList.add("android.graphics.PathEffect");supportClassList.add("android.graphics.DrawFilter");supportClassList.add("android.graphics.Bitmap");supportClassList.add("android.graphics.RadialGradient");supportClassList.add("android.hardware.location.ActivityRecognitionHardware");supportClassList.add("android.graphics.text.PositionedGlyphs");supportClassList.add("android.os.HidlSupport");supportClassList.add("android.graphics.Camera");supportClassList.add("android.graphics.SweepGradient");supportClassList.add("android.graphics.fonts.Font");supportClassList.add("android.hardware.HardwareBuffer");supportClassList.add("com.android.server.location.gnss.hal.GnssNative");supportClassList.add("android.app.Activity");supportClassList.add("android.renderscript.RenderScript");supportClassList.add("android.app.admin.SecurityLog");supportClassList.add("com.google.android.gles_jni.GLImpl");supportClassList.add("com.android.commands.uinput.Device");supportClassList.add("com.android.server.SerialService");supportClassList.add("com.android.internal.os.KernelCpuTotalBpfMapReader");supportClassList.add("com.android.internal.content.NativeLibraryHelper");supportClassList.add("android.app.backup.FileBackupHelperBase");supportClassList.add("android.graphics.pdf.PdfEditor");supportClassList.add("android.media.RemoteDisplay");supportClassList.add("com.android.internal.os.Zygote");supportClassList.add("android.app.backup.FullBackup");supportClassList.add("com.android.server.am.BatteryStatsService");supportClassList.add("android.media.JetPlayer");supportClassList.add("android.graphics.fonts.Font$Builder");supportClassList.add("com.android.server.usb.UsbAlsaJackDetector");supportClassList.add("android.graphics.drawable.VectorDrawable");supportClassList.add("com.android.server.usb.UsbMidiDevice");supportClassList.add("android.graphics.Typeface");supportClassList.add("android.graphics.BLASTBufferQueue");supportClassList.add("android.graphics.animation.NativeInterpolatorFactory");supportClassList.add("KernelCpuUidClusterTimeBpfMapReader");supportClassList.add("android.view.VelocityTracker");supportClassList.add("com.android.server.location.gnss.GnssNetworkConnectivityHandler");supportClassList.add("android.view.SurfaceSession");supportClassList.add("android.opengl.GLES30");supportClassList.add("android.media.AudioTrack");supportClassList.add("android.opengl.EGL14");supportClassList.add("android.media.MediaCodec$LinearBlock");supportClassList.add("android.graphics.Color");supportClassList.add("android.graphics.TextureLayer");supportClassList.add("android.view.DisplayEventReceiver");supportClassList.add("com.android.internal.os.KernelCpuBpfTracking");supportClassList.add("android.app.NativeActivity");supportClassList.add("android.app.backup.BackupHelperDispatcher");supportClassList.add("android.graphics.fonts.FontFamily");supportClassList.add("android.content.res.AssetManager");supportClassList.add("com.android.internal.os.KernelSingleProcessCpuThreadReader");supportClassList.add("com.android.server.usb.UsbDeviceManager");supportClassList.add("com.android.printspooler.util.BitmapSerializeUtils");supportClassList.add("android.hardware.SystemSensorManager$BaseEventQueue");supportClassList.add("android.media.MediaExtractor");supportClassList.add("com.android.server.broadcastradio.hal1.BroadcastRadioService");supportClassList.add("android.media.ImageReader$SurfaceImage");supportClassList.add("android.graphics.fonts.FontFileUtil");supportClassList.add("android.graphics.DiscretePathEffect");supportClassList.add("android.opengl.Visibility");supportClassList.add("com.android.server.usb.UsbHostManager");supportClassList.add("android.media.AudioRecord");supportClassList.add("android.view.Surface");supportClassList.add("android.graphics.Interpolator");supportClassList.add("com.android.server.NetworkManagementSocketTagger");supportClassList.add("android.os.ServiceManager");supportClassList.add("android.media.MediaPlayer");supportClassList.add("com.android.server.tv.TvInputHal");supportClassList.add("android.net.LocalSocketImpl");supportClassList.add("android.database.sqlite.SQLiteGlobal");supportClassList.add("android.app.ActivityThread");supportClassList.add("android.media.CamcorderProfile");supportClassList.add("android.hardware.usb.UsbRequest");supportClassList.add("android.graphics.ComposePathEffect");supportClassList.add("android.graphics.PathMeasure");supportClassList.add("android.os.VintfObject");supportClassList.add("android.graphics.ColorSpace$Rgb");supportClassList.add("com.android.server.am.LowMemDetector");supportClassList.add("com.android.internal.os.ZygoteCommandBuffer");supportClassList.add("android.database.CursorWindow");supportClassList.add("android.graphics.RegionIterator");supportClassList.add("android.graphics.NinePatch");supportClassList.add("com.android.commands.hid.Device");supportClassList.add("android.security.Scrypt");supportClassList.add("com.android.server.lights.LightsService");supportClassList.add("android.app.backup.BackupDataOutput");supportClassList.add("android.opengl.GLES31");supportClassList.add("android.mtp.MtpDevice");supportClassList.add("android.media.audiofx.AudioEffect");supportClassList.add("android.graphics.text.LineBreaker");supportClassList.add("android.os.Binder");supportClassList.add("android.graphics.PathDashPathEffect");supportClassList.add("android.ddm.DdmHandleNativeHeap");supportClassList.add("android.graphics.YuvImage");supportClassList.add("android.view.InputChannel");supportClassList.add("android.media.audiopolicy.AudioProductStrategy");supportClassList.add("android.media.ImageWriter");supportClassList.add("android.graphics.Canvas");supportClassList.add("com.android.server.am.CachedAppOptimizer");supportClassList.add("com.android.internal.util.VirtualRefBasePtr");supportClassList.add("android.service.dataloader.DataLoaderService");supportClassList.add("android.content.res.XmlBlock");supportClassList.add("android.os.Trace");supportClassList.add("android.media.MediaDescrambler");supportClassList.add("android.hardware.camera2.DngCreator");supportClassList.add("android.os.SystemClock");supportClassList.add("android.graphics.Paint");supportClassList.add("android.os.Process");supportClassList.add("android.graphics.SurfaceTexture");supportClassList.add("android.graphics.RenderNode");supportClassList.add("android.util.PathParser");supportClassList.add("android.graphics.RuntimeShader");supportClassList.add("com.android.server.location.gnss.GnssVisibilityControl");supportClassList.add("android.text.AndroidCharacter");supportClassList.add("android.os.SELinux");supportClassList.add("android.graphics.HardwareRenderer");supportClassList.add("android.os.UEventObserver");supportClassList.add("android.opengl.EGL15");supportClassList.add("android.util.EventLog");supportClassList.add("com.android.internal.os.BinderInternal");supportClassList.add("android.media.MediaHTTPConnection");supportClassList.add("com.android.server.tv.UinputBridge");supportClassList.add("com.android.server.PersistentDataBlockService");supportClassList.add("android.hardware.camera2.impl.CameraExtensionJpegProcessor");supportClassList.add("android.graphics.pdf.PdfDocument");supportClassList.add("android.opengl.GLUtils");supportClassList.add("KernelCpuUidFreqTimeBpfMapReader");supportClassList.add("android.media.MediaMuxer");supportClassList.add("android.graphics.MaskFilter");supportClassList.add("com.android.server.connectivity.Vpn");supportClassList.add("android.graphics.RenderEffect");supportClassList.add("android.database.sqlite.SQLiteConnection");supportClassList.add("android.media.DecoderCapabilities");supportClassList.add("android.view.KeyEvent");supportClassList.add("android.graphics.ImageDecoder");supportClassList.add("com.android.server.stats.pull.StatsPullAtomService");supportClassList.add("android.opengl.GLES32");supportClassList.add("android.graphics.BlurMaskFilter");supportClassList.add("android.opengl.GLES31Ext");supportClassList.add("android.opengl.GLES11");supportClassList.add("android.opengl.GLES10");supportClassList.add("android.graphics.LinearGradient");supportClassList.add("android.util.MemoryIntArray");supportClassList.add("android.graphics.animation.RenderNodeAnimator");supportClassList.add("android.os.FileObserver$ObserverThread");supportClassList.add("android.graphics.text.MeasuredText$Builder");supportClassList.add("android.view.InputQueue");supportClassList.add("android.graphics.drawable.AnimatedVectorDrawable");supportClassList.add("android.media.MediaCodec");supportClassList.add("android.media.CameraProfile");supportClassList.add("android.graphics.Movie");supportClassList.add("android.graphics.BaseRecordingCanvas");supportClassList.add("android.media.ToneGenerator");supportClassList.add("android.os.BinderProxy");supportClassList.add("android.graphics.GraphicBuffer");supportClassList.add("android.media.MediaDrm");supportClassList.add("com.android.server.SystemServer");supportClassList.add("android.graphics.BitmapRegionDecoder");supportClassList.add("android.os.storage.StorageManager");supportClassList.add("android.graphics.Region");supportClassList.add("android.opengl.GLES11Ext");supportClassList.add("android.graphics.CornerPathEffect");supportClassList.add("android.os.PerformanceHintManager");supportClassList.add("android.graphics.ComposeShader");supportClassList.add("android.view.InputApplicationHandle");supportClassList.add("android.animation.PropertyValuesHolder");supportClassList.add("com.android.server.sensors.SensorService");supportClassList.add("android.content.res.ApkAssets");supportClassList.add("android.graphics.TableMaskFilter");supportClassList.add("android.content.res.ObbScanner");supportClassList.add("android.graphics.EmbossMaskFilter");supportClassList.add("android.media.audiofx.Visualizer");supportClassList.add("android.graphics.BitmapFactory");supportClassList.add("com.android.server.alarm.AlarmManagerService");supportClassList.add("android.mtp.MtpPropertyGroup");supportClassList.add("com.android.server.ConsumerIrService");supportClassList.add("android.graphics.LightingColorFilter");supportClassList.add("android.content.res.StringBlock");supportClassList.add("com.google.android.gles_jni.EGLImpl");supportClassList.add("com.android.server.locksettings.SyntheticPasswordManager");supportClassList.add("com.android.server.HardwarePropertiesManagerService");supportClassList.add("android.media.ImageReader");supportClassList.add("android.graphics.text.MeasuredText");supportClassList.add("com.android.internal.net.NetworkUtilsInternal");supportClassList.add("android.graphics.BlendModeColorFilter");supportClassList.add("android.view.InputEventSender");supportClassList.add("android.hardware.SerialPort");supportClassList.add("android.hardware.usb.UsbDeviceConnection");supportClassList.add("KernelCpuUidActiveTimeBpfMapReader");supportClassList.add("android.os.MemoryFile");supportClassList.add("android.media.SoundPool");supportClassList.add("android.graphics.text.TextRunShaper");supportClassList.add("android.media.MediaRecorder");supportClassList.add("android.media.ResampleInputStream");supportClassList.add("com.android.server.power.PowerManagerService");supportClassList.add("android.mtp.MtpServer");supportClassList.add("android.os.VintfRuntimeInfo");supportClassList.add("android.media.audiofx.StreamDefaultEffect");supportClassList.add("android.view.MotionEvent");supportClassList.add("android.graphics.Path");supportClassList.add("android.graphics.GraphicsStatsService");supportClassList.add("android.os.Debug");supportClassList.add("android.graphics.FontFamily");supportClassList.add("com.android.server.input.InputManagerService");supportClassList.add("android.graphics.PaintFlagsDrawFilter");supportClassList.add("android.opengl.EGLExt");supportClassList.add("com.android.internal.os.KernelSingleUidTimeReader$Injector");supportClassList.add("android.graphics.fonts.FontFamily$Builder");supportClassList.add("android.hardware.usb.UsbDevice");supportClassList.add("android.media.ImageWriter$WriterSurfaceImage");supportClassList.add("android.opengl.Matrix");supportClassList.add("android.text.Hyphenator");supportClassList.add("android.util.CharsetUtils");supportClassList.add("android.hardware.Camera");supportClassList.add("android.media.MediaMetadataRetriever");supportClassList.add("android.os.incremental.IncrementalManager");supportClassList.add("com.android.internal.os.ClassLoaderFactory");supportClassList.add("com.android.server.vr.VrManagerService");supportClassList.add("android.view.TextureView");supportClassList.add("com.android.server.adb.AdbDebuggingManager$PairingThread");supportClassList.add("android.graphics.BitmapShader");supportClassList.add("com.android.internal.os.DmabufInfoReader");supportClassList.add("android.graphics.DashPathEffect");supportClassList.add("android.graphics.Shader");supportClassList.add("android.opengl.GLES20");supportClassList.add("android.hardware.SystemSensorManager");supportClassList.add("com.android.server.net.NetworkStatsService");supportClassList.add("android.graphics.ColorFilter");supportClassList.add("com.android.server.broadcastradio.hal1.TunerCallback");supportClassList.add("android.graphics.drawable.AnimatedImageDrawable");supportClassList.add("android.media.EncoderCapabilities");supportClassList.add("com.android.internal.content.om.OverlayConfig");
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
        BufferedWriter writer = new BufferedWriter(new FileWriter("/home/siyu/tifs/JDYNUZZ/Fuzzing_Server/jni12.0/jni_methods.json"));
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
