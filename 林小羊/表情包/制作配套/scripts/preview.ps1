param([string]$AssetsRoot='exports',[string]$PreviewRoot='preview')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
if(-not [IO.Path]::IsPathRooted($AssetsRoot)){$AssetsRoot=Join-Path $base $AssetsRoot}
if(-not [IO.Path]::IsPathRooted($PreviewRoot)){$PreviewRoot=Join-Path $base $PreviewRoot}
if(Test-Path -LiteralPath $PreviewRoot){throw "Refusing to overwrite $PreviewRoot"}
New-Item -ItemType Directory -Path $PreviewRoot | Out-Null
$plan=Get-Content -LiteralPath (Join-Path $base 'plan.json') -Raw|ConvertFrom-Json
$font=[Drawing.Font]::new('Microsoft YaHei',22,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
$small=[Drawing.Font]::new('Microsoft YaHei',16,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
function Draw-Img($g,$p,$x,$y,$w,$h){
 $im=[Drawing.Image]::FromFile($p)
 $g.DrawImage($im,[Drawing.Rectangle]::new($x,$y,$w,$h));$im.Dispose()
}
for($page=0;$page -lt 2;$page++){
 $canvas=[Drawing.Bitmap]::new(1200,960)
 $g=[Drawing.Graphics]::FromImage($canvas);$g.Clear([Drawing.ColorTranslator]::FromHtml('#F4EFE7'))
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.DrawString('林小羊 / 场景专辑配套',$font,[Drawing.Brushes]::Black,24,16)
 for($j=0;$j -lt 4;$j++){
  $a=$plan.albums[$page*4+$j];$x=24+($j%2)*590;$y=62+[int][Math]::Floor($j/2)*440
  $g.DrawString(($a.name+' · '+$a.scene),$font,[Drawing.Brushes]::Black,$x,$y)
  Draw-Img $g (Join-Path $AssetsRoot ($a.id+'/banner-750x400.jpg')) $x ($y+40) 555 296
  $g.FillRectangle([Drawing.Brushes]::White,$x,($y+345),100,88)
  Draw-Img $g (Join-Path $AssetsRoot ($a.id+'/cover-240.png')) ($x+8) ($y+347) 84 84
  $g.FillRectangle([Drawing.Brushes]::White,($x+115),($y+345),62,62)
  Draw-Img $g (Join-Path $AssetsRoot ($a.id+'/icon-50.png')) ($x+121) ($y+351) 50 50
  $g.DrawString(($a.kind+' · '+$a.count+' 张'),$small,[Drawing.Brushes]::Black,($x+190),($y+353))
  $g.DrawString('独立封面 / 面板图标 / 故事横幅',$small,[Drawing.Brushes]::Black,($x+190),($y+384))
 }
 $canvas.Save((Join-Path $PreviewRoot ('albums-'+($page+1)+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)
 $g.Dispose();$canvas.Dispose()
}
# Transparent assets on light and dark backgrounds, plus native 50px icon checks.
$items=@(@{id='profile';name='林小羊';file='avatar-240.png'})
foreach($a in $plan.albums){$items+=@{id=$a.id;name=$a.name;file='cover-240.png'}}
foreach($theme in @('light','dark')){
 $c=[Drawing.Bitmap]::new(1250,850);$g=[Drawing.Graphics]::FromImage($c)
 $bg=if($theme -eq 'dark'){'#172027'}else{'#F2F0EB'}
 $brush=if($theme -eq 'dark'){[Drawing.Brushes]::White}else{[Drawing.Brushes]::Black}
 $g.Clear([Drawing.ColorTranslator]::FromHtml($bg))
 for($i=0;$i -lt $items.Count;$i++){
  $a=$items[$i];$x=10+($i%5)*248;$y=15+[int][Math]::Floor($i/5)*415
  Draw-Img $g (Join-Path $AssetsRoot ($a.id+'/'+$a.file)) $x $y 240 240
  $g.DrawString($a.name,$font,$brush,($x+10),($y+250))
  Draw-Img $g (Join-Path $AssetsRoot ($a.id+'/icon-50.png')) ($x+10) ($y+298) 50 50
  $g.DrawString('50px',$small,$brush,($x+73),($y+313))
 }
 $c.Save((Join-Path $PreviewRoot ('covers-'+$theme+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)
 $g.Dispose();$c.Dispose()
}
$font.Dispose();$small.Dispose()
