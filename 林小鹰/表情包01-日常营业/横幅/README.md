# 林小鹰 · 日常营业详情页横幅

上传文件：[banner-750x400.jpg](banner-750x400.jpg)。750×400 像素，JPG，不透明；实际文件大小见 validation.json。

画面以三个时刻呈现同一只小鹰的一天：认真工作、喝茶休息、开心收工。灰白黏土角色与已有表情一致，背景采用青绿与暖金，避免白底，不添加任何文字、标志或界面元素。

制作要求来自用户提供的微信详情页横幅截图，存于 requirements.png。按截图要求制作 1 张正式上传用横幅；未向微信提交。

raw/banner-master.png 保留生成原图；prompt.md 保留提示词；export.ps1 负责保持纵横比的居中裁切与导出，不进行横向拉伸或压扁。背景延伸到画面四边，角色耳簇、翅膀和脚完整保留。

重新导出到新目录：`pwsh -File export.ps1 -Destination rebuild`。
