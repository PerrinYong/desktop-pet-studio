知核 · 宣传片与序列帧制作幕后

成片：56 秒，1920 × 1080，24 fps，H.264 / AAC。
幕后片段：成片第 28—49 秒，独立导出为 21 秒视频。

assets/spritesheet.png 是经过验证的原宠物透明图集：
192 × 208 像素单元，8 列 × 11 行，73 幅有效姿态。
assets/jumping-source.png 是真实的五姿态跳跃生成源图。
角色画面复用原有素材；字幕、卡片、选帧框和时间轴由脚本绘制。
幕后内容是基于真实素材的制作过程可视化，不是操作录屏。
声音为脚本原创合成的器乐节奏和提示音，不含人声或外部歌曲。

重现：
1. 使用 Python 3.10 或以上版本。
2. python -m pip install -r requirements.txt
3. python render_film.py --output output

仅输出分镜检查：
python render_film.py --output output --stills-only

脚本默认使用 Windows 的 Microsoft YaHei 与 Bahnschrift 字体。
在其他系统运行时，将 CN、BOLD、LATIN 改为可用字体路径。

分镜：
00—05  主角亮相
05—09.5  专注思考
09.5—14  认真检查
14—18  耐心等待
18—22  行走、遇到问题、跳跃庆祝
22—28  十六向目光
28—34  原始条带、去背景、标记姿态
34—41  五帧跳跃、每帧时长、慢放与循环
41—49  完整图集与选帧播放
49—56  片尾

制作过程保留原始每帧停留时长，时间轴刻度与停留时长对应。
本项目仅制作本地视频，不修改已启用的 Pets 宠物。
