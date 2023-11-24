### Due to the large size of AOSP, we cannot provided the compiled AOSP here. Please follow the compliation instruction of official documents. For convience, we provide the key commands we used

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

# cp two downloaded driver binary into the root folder of AOSP
# then execute these two shell scripts

# -------------
# Compilation 
# Document https://source.android.com/docs/setup/build/building

# Select the compilation target
lunch 4
# Enable hwaddress sanitizer
export SANITIZE_TARGET=hwaddress

# -------------
# Flash the system to device (Pixel 3), the device should unblock first following the instruction from https://www.androidauthority.com/unlock-pixel-3-bootloader-915961/

# connect pixel 3 to pc
apt-get install android-sdk-platform-tools-common

adb devices

adb reboot-bootloader
fastboot flashall -w
```

## JNI Analyzer

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

## AOSP Build for Emulator

#

``` shell
cd path to aosp

source ./build/envsetup.sh

lunch 4

export SANITIZE_TARGET=hwaddress

make -j64 all

# if encountered with library missing, try following commands
sudo apt-get update
sudo apt-get install libncurses5
```

## Emulator

``` shell
# run the emulator
emulator
```

## Cuttlefish

```shell
sudo apt install -y git devscripts config-package-dev debhelper-compat golang curl

git clone https://github.com/google/android-cuttlefish

cd android-cuttlefish

for dir in base frontend; do
  cd $dir
  debuild -i -us -uc -b -d
  cd ..
done

sudo dpkg -i ./cuttlefish-base_*_*64.deb || sudo apt-get install -f
sudo dpkg -i ./cuttlefish-user_*_*64.deb || sudo apt-get install -f
sudo usermod -aG kvm,cvdnetwork,render $USER
sudo reboot
```

In aosp dir

```shell
# installing dependancies
sudo apt-get install -y python git zip unzip curl wget llvm git-core gnupg flex bison gperf build-essential make zlib1g-dev gcc-multilib g++-multilib libc6-dev-i386 lib32ncurses5-dev x11proto-core-dev libx11-dev lib32z-dev libgl1-mesa-dev libxml2-utils xsltproc libssl-dev libbz2-dev libreadline-dev libsqlite3-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl libncurses5 libelf-dev clang lld rsync

# installing the repo launcher 
mkdir ~/bin
PATH=~/bin:$PATH
curl https://storage.googleapis.com/git-repo-downloads/repo 
mv repo ~/bin/repo
chmod a+x ~/bin/repo

# downloading the AOSP 
cd ~
mkdir aosp
cd aosp
repo init -u https://android.googlesource.com/platform/manifest -b android-12.0.0_r15
repo sync -j8

# build Android 
source build/envsetup.sh
lunch aosp_cf_x86_phone-userdebug
m -j8

# setup acloud 
acloud setup --host
reboot

# start acloud 
source build/envsetup.sh
lunch aosp_cf_x86_phone-userdebug
acloud create --local-instance 1 --local-image

# enter all y when acloud required

# install python 2.7 - optional
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$HOME/.pyenv/bin:$PATH"
export PATH="$HOME/.pyenv/shims:$PATH"
eval "$(pyenv init -)"

pyenv install 2.7.18
pyenv local 2.7.18
pyenv virtualenv 2.7.18 aosp
python --version
```
