本目录包含两个 Python 脚本，用于把 PyTorch 训练得到的 KWS 模型权重导出为固件可直接读取的二进制文件。新的 `kws_engine.c` 采用 v3 格式
：文件头除了魔数与版本号外，还携带四个卷积层的输出通道数，随后是各层连续的浮点权重数组。所有数值均使用 Zynq A9 默认的小端序存
储（低地址保存最低有效字节）。

## 1. 从 `.pt` 直接生成文本与二进制

```bash
python3 export_kws_weights.py \
    path/to/kws_checkpoint.pt \
    --txt-out kws_weights.txt \
    --bin-out bnn_weights_binary_new.bin
```

脚本会完成以下步骤：

1. 读取 PyTorch `state_dict`（支持 `checkpoint["model"]` 格式），自动定位 `conv1`~`conv4` 与最终全连接层的权重张量；
2. 推断每个卷积层的输出通道数，写入 `layout conv1 conv2 conv3 conv4` 行，同时统计分类数；
3. 按固件期望的顺序把所有浮点权重展开到 `kws_weights.txt`，方便人工核对；
4. 生成符合 v3 规范的 `bnn_weights_binary_new.bin`：文件头写入魔数 `0x4B575331`、版本 `0x00030000`、类别数与保留字段，再紧跟四个
   通道数和连续的权重数据块。

若模型的层命名不同，可在脚本中调整 `_infer_conv_weight` 的候选键列表以适配自定义结构。

## 2. 基于文本重新封装二进制

如果你想先在文本文件中修改部分权重，再打包成固件格式，可运行：

```bash
python3 txt_to_bin.py kws_weights.txt --bin-out bnn_weights_binary_new.bin
```

文本文件需包含以下段落：

- `magic`、`version`、`num_classes`、`reserved` 四个头字段；
- 一行 `layout c1 c2 c3 c4` 指明各卷积层输出通道数；
- 依次出现的 `section conv1_weights <count>` … `section fc_weights <count>` 块，每个块后跟 `<count>` 行 `float32` 数值。

`txt_to_bin.py` 会严格校验头部与布局信息，再以 `<f`（小端 float）编码写入权重，确保生成的 `bnn_weights_binary_new.bin` 与
`kws_engine.c` 中的读取逻辑完全对应。

---

无论选择哪种路径，请将最终的 `bnn_weights_binary_new.bin` 拷贝到 SD 卡的 `0:/` 根目录（或在固件中调整 `KWS_DEFAULT_WEIGHT_PATH`），
这样 KWS 引擎即可在初始化阶段一次性加载全部权重。若二进制文件或布局不匹配，固件会在串口打印错误信息，便于定位问题。 
