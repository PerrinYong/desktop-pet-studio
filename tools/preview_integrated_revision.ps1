param()
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$repo=Split-Path $PSScriptRoot
$examples=@(
 @('林小羊','02-上班有点咩','01-人已到工位.png'),
 @('林小羊','04-羊毛失控','01-我裂开了.png'),
 @('林小鹰','01-日常营业','05-辛苦啦.png'),
 @('林小鹰','01-日常营业','10-让我缓缓.png')
)
$b=[Drawing.Bitmap]::new(1040,624)
$g=[Drawing.Graphics]::FromImage($b)
$g.Clear([Drawing.Color]::FromArgb(245,243,239))
$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$f=[Drawing.Font]::new('Microsoft YaHei',15)
$brush=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(64,58,52))
$g.DrawString('调整前：画面与底部文字分离',$f,$brush,16,12)
$g.DrawString('调整后：文字进入动作、表情与道具',$f,$brush,16,324)
for($i=0;$i -lt 4;$i++){
 $e=$examples[$i]
 $base=Join-Path $repo "$($e[0])/表情包/专辑/$($e[1])"
 foreach($row in 0..1){
  $sub=if($row -eq 0){'exports/wechat-240'}else{'revisions/图文融合-v2/exports/wechat-240'}
  $im=[Drawing.Image]::FromFile((Join-Path $base "$sub/$($e[2])"))
  $g.DrawImage($im,$i*260+10,$row*312+56,240,240)
  $im.Dispose()
 }
}
$g.Dispose();$f.Dispose();$brush.Dispose()
$b.Save((Join-Path $repo 'docs/图文融合-全系列对比.png'),[Drawing.Imaging.ImageFormat]::Png)
$b.Dispose()

