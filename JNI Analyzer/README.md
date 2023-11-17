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