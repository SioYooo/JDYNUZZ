# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

#指定CMake构建本地库时所需的最小版本
cmake_minimum_required(VERSION 3.4.1)

# Creates and names a library, sets it as either STATIC
# or SHARED, and provides the relative paths to its source code.
# You can define multiple libraries, and CMake builds them for you.
# Gradle automatically packages shared libraries with your APK.
set(CMAKE_C_FLAGS "${}CMAKE_C_FLAGS) -fprofile-instr-generate -fcoverage-mapping")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-instr-generate -fcoverage-mapping")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -fprofile-instr-generate -fcoverage-mapping")

add_library( # Sets the name of the library.
            #将资源文件生成动态链接库（so文件）的库名称(文件名称：“lib" +设置的名称)
             native-lib

             # Sets the library as a shared library.

             SHARED

             # Provides a relative path to your source file(s).
        native-lib.cpp)

# Searches for a specified prebuilt library and stores the path as a
# variable. Because CMake includes system libraries in the search path by
# default, you only need to specify the name of the public NDK library
# you want to add. CMake verifies that the library exists before
# completing its build.

find_library( # Sets the name of the path variable.

              log-lib

              # Specifies the name of the NDK library that
              # you want CMake to locate.
              log )

# Specifies libraries CMake should link to your target library. You
# can link multiple libraries, such as libraries you define in this
# build script, prebuilt third-party libraries, or system libraries.

target_link_libraries( # Specifies the target library.
                       #将所有的add_library中的库链接起来，有多少个add_library成的库就将其添加到这里
                       #这个和add_library中的指定的so库名称一致
                       native-lib

                       # Links the target library to the log library
                       # included in the NDK.
                       ${log-lib} )