param([string]$OutputRoot='support-rebuild')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
$out=Join-Path $base $OutputRoot
if(Test-Path -LiteralPath $out){throw 'Choose a new OutputRoot'}
foreach($d in @('assets','static/transparent-240','static/white-240')){New-Item -ItemType Directory -Path (Join-Path $out $d) -Force|Out-Null}
function Graphics($canvas){
 $g=[Drawing.Graphics]::FromImage($canvas)
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 return $g
}
$cover=[Drawing.Bitmap]::FromFile((Join-Path $base 'assets/raw/cover.png'))
$left=$cover.Width;$top=$cover.Height;$right=0;$bottom=0
for($y=0;$y -lt $cover.Height;$y++){for($x=0;$x -lt $cover.Width;$x++){
 if($cover.GetPixel($x,$y).A -ge 24){$left=[Math]::Min($left,$x);$top=[Math]::Min($top,$y);$right=[Math]::Max($right,$x);$bottom=[Math]::Max($bottom,$y)}
}}
$crop=[Drawing.Rectangle]::new($left,$top,$right-$left+1,$bottom-$top+1)
foreach($size in @(240,50)){
 $canvas=[Drawing.Bitmap]::new($size,$size,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=Graphics $canvas
 $margin=if($size -eq 50){2}else{8}
 $scale=[Math]::Min(($size-$margin*2)/[double]$crop.Width,($size-$margin*2)/[double]$crop.Height)
 $w=[int][Math]::Round($crop.Width*$scale);$h=[int][Math]::Round($crop.Height*$scale)
 $g.DrawImage($cover,[Drawing.Rectangle]::new([int](($size-$w)/2),[int](($size-$h)/2),$w,$h),$crop.X,$crop.Y,$crop.Width,$crop.Height,[Drawing.GraphicsUnit]::Pixel)
 $name=if($size -eq 50){'icon-50.png'}else{'cover-240.png'}
 $canvas.Save((Join-Path $out ('assets/'+$name)),[Drawing.Imaging.ImageFormat]::Png)
 $g.Dispose();$canvas.Dispose()
}
$cover.Dispose()
$banner=[Drawing.Bitmap]::FromFile((Join-Path $base 'assets/raw/banner.png'))
$canvas=[Drawing.Bitmap]::new(750,400,[Drawing.Imaging.PixelFormat]::Format24bppRgb)
$g=Graphics $canvas
$scale=[Math]::Max(750/[double]$banner.Width,400/[double]$banner.Height)
$w=[int][Math]::Ceiling($banner.Width*$scale);$h=[int][Math]::Ceiling($banner.Height*$scale)
$g.DrawImage($banner,[Drawing.Rectangle]::new([int]((750-$w)/2),[int]((400-$h)/2),$w,$h))
$canvas.Save((Join-Path $out 'assets/banner-750x400.jpg'),[Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose();$canvas.Dispose();$banner.Dispose()
$pack=Get-Content -LiteralPath (Join-Path $base 'pack.json') -Raw|ConvertFrom-Json
foreach($s in $pack.stickers){
 $source=Join-Path $base ('animation/frames/'+$s.id+'/key-2.png')
 $name=$s.id.Split('-')[0]+'-'+$s.caption+'.png'
 Copy-Item -LiteralPath $source -Destination (Join-Path $out ('static/transparent-240/'+$name))
 $im=[Drawing.Bitmap]::FromFile($source)
 $canvas=[Drawing.Bitmap]::new(240,240,[Drawing.Imaging.PixelFormat]::Format24bppRgb)
 $g=Graphics $canvas
 $g.Clear([Drawing.Color]::White);$g.DrawImageUnscaled($im,0,0)
 $canvas.Save((Join-Path $out ('static/white-240/'+$name)),[Drawing.Imaging.ImageFormat]::Png)
 $g.Dispose();$canvas.Dispose();$im.Dispose()
}
[IO.File]::WriteAllText((Join-Path $out 'assets/专辑资料.txt'),"名称：林小羊·有事您招呼`n简介：挥挥手，点点头，收到就安排。林小羊用一点小动作，把邀约、回应和道谢聊得轻松又自然。`n类型：动态`n数量：8`n",[Text.UTF8Encoding]::new($false))
