# run these two lines first

device="8CFX1NP4C"

adb -s $device root
adb -s $device disable-verity
adb -s $device reboot
echo "系统已经关闭验证，可以推送系统app了..."

