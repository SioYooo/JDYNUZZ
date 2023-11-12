# apk="../app/build/outputs/apk/debug/app-debug.apk"
apk="../app/debug/app-debug.apk"
device="8CFX1NP4C"

# run these two lines first
#adb root
#adb disable-verity

adb -s $device root
adb -s $device remount

apksigner sign --key ../sign/platform.pk8 --cert ../sign/platform.x509.pem $apk
adb -s $device shell rm -rf /system/priv-app/mytestapp
adb -s $device shell rm -rf /system/app/mytestapp
adb -s $device shell mkdir /system/priv-app/mytestapp
adb -s $device push $apk /system/priv-app/mytestapp/
adb -s $device reboot
echo "应用已经推送，等待重启完成..."