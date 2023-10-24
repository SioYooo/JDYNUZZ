### Due to the large size of AOSP, we cannot provided the compiled AOSP here. Please follow the compliation instruction of official documents. For convience, we provide the key commands we used.

## Environment required
PC with Ubuntu 18.04

Pixel 3


## Pre-processing
```
# -------------
# Download the AOSP, version android-12.0.0_r31
# Document https://source.android.com/docs/setup/build/downloading

# -------------
# Download and Extract Pixel 3 Driver Binary from https://developers.google.com/android/drivers#bluelinesp1a.210812.016.c1

# -------------
# Compilation 
# Document https://source.android.com/docs/setup/build/building

# Select the compilation target
lunch 4
# Enable hwaddress sanitizer
export SANITIZE_TARGET=hwaddress

# -------------
# Flash the system to device (Pixel 3), the device should unblock first following the instruction from https://www.androidauthority.com/unlock-pixel-3-bootloader-915961/
adb reboot-bootloader
fastboot flashall -w
```

## JNI Anslyzer
```
# get the maaping between Java-side and Native-side JNI functions
python3 find_jin_java_class.py

# extract and process the dependencies
python3 dependency.py
python3 dependency_post_process.py
python3 Dependency_analysis.py
```

## Fuzzing Client
```
# connct Pixel 3 to PC, install the fuzzing client as a system app.
cd /Fuzzing Client/shell/

# remount the Android system disk as writeable
./init_Install_system_priv-app_in_real_device.sh

# sign the app with platform signature and install app as system app
./Install_system_priv-app_in_real_device.sh
```

## Fuzzing Server
```
# run the fuzzing server
java -jar fuzzEngine.jar
```
