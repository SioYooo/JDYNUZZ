# 提取 jni 相关 json 文件

## 首先运行 generate_compdb.py

```bash
# 生成 compile_commands.json

python3 generate_compdb.py /data_ssd_1/siyu/aosp/out/soong/build.ninja
```

## 然后运行 ninja_parse.py

```bash
python3 ninja_parse.py
```

## 最后在获得了 jni 相关的 json 文件后，运行 find_jni_java_class.py

```bash
python3 find_jni_java_class.py
```


```10.0.0_r2
python3 generate_compdb.py /data_ssd_1/siyu/10.0.0_r2/aosp/out/soong/build.ninja


```