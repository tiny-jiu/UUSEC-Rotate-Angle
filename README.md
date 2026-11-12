UUSEC旋转验证码识别项目通过图像匹配识别 UUSEC 旋转验证码的角度。脚本将待识别图片与参考图库逐一比较，先粗筛，再细查，找出相关度最高的参考图和旋转角度。

脚本会将每张参考图预先旋转到 360 个角度，并使用圆形掩码只保留图片中的有效区域。识别时先每隔 3 度进行一次粗搜索，再在最佳角度附近逐度细查，最终根据相关系数确定最匹配的参考图和角度。使用前需要在脚本同目录下创建 `images/` 目录，并将参考 PNG 图片放入其中。

安装依赖可使用以下命令：

```bash
pip install numpy opencv-python pillow playwright
python -m playwright install chromium
```

修改 `rotate_angle.py` 中的 `TARGET`，然后运行：

```bash
python rotate_angle.py
```

也可以直接把目标地址作为第一个命令行参数：

```bash
python rotate_angle.py http://target.example/
```

脚本会输出匹配到的参考图、旋转角度、相关系数和验证结果。本项目仅供安全研究和已获授权的测试使用。
