param([string]$OutputRoot)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$sourceRoot=Split-Path $PSScriptRoot -Parent
if(-not $OutputRoot){throw 'Choose a new directory with -OutputRoot.'}
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
if(Test-Path -LiteralPath $OutputRoot){throw "Refusing to overwrite $OutputRoot"}
$pack=Get-Content -LiteralPath (Join-Path $sourceRoot 'pack.json') -Raw|ConvertFrom-Json
foreach($folder in @('exports/chat-512','exports/wechat-240','exports/thumbnails-120','assets','preview')){
 New-Item -ItemType Directory -Path (Join-Path $OutputRoot $folder) -Force|Out-Null
}
function Open-Graphics($canvas){
 $g=[Drawing.Graphics]::FromImage($canvas)
 $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 return $g
}
function Get-Bounds($im){
 $left=$im.Width;$top=$im.Height;$right=-1;$bottom=-1
 for($y=0;$y -lt $im.Height;$y++){for($x=0;$x -lt $im.Width;$x++){
  if($im.GetPixel($x,$y).A -ge 24){
   $left=[Math]::Min($left,$x);$top=[Math]::Min($top,$y)
   $right=[Math]::Max($right,$x);$bottom=[Math]::Max($bottom,$y)
  }
 }}
 if($right -lt 0){throw 'Source has no visible pixels'}
 return [Drawing.Rectangle]::new($left,$top,$right-$left+1,$bottom-$top+1)
}
function Draw-Cutout($g,$im,$crop,$x,$y,$w,$h){
 $scale=[Math]::Min($w/[double]$crop.Width,$h/[double]$crop.Height)
 $dw=[int][Math]::Round($crop.Width*$scale);$dh=[int][Math]::Round($crop.Height*$scale)
 $rect=[Drawing.Rectangle]::new([int]($x+($w-$dw)/2),[int]($y+($h-$dh)/2),$dw,$dh)
 $g.DrawImage($im,$rect,$crop.X,$crop.Y,$crop.Width,$crop.Height,[Drawing.GraphicsUnit]::Pixel)
}
$font=[Drawing.FontFamily]::new('Microsoft YaHei')
$ink=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml('#252320'))
$stroke=[Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('#FFF7EB'),10)
$stroke.LineJoin=[Drawing.Drawing2D.LineJoin]::Round
foreach($s in $pack.stickers){
 $im=[Drawing.Bitmap]::FromFile((Join-Path $sourceRoot $s.raw))
 $crop=Get-Bounds $im
 $big=[Drawing.Bitmap]::new(512,512,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=Open-Graphics $big
 $g.Clear([Drawing.Color]::Transparent)
 Draw-Cutout $g $im $crop 20 14 472 377
 $glyph=[Drawing.Drawing2D.GraphicsPath]::new()
 $size=[Math]::Min(90,[Math]::Floor(455/$s.caption.Length))
 $glyph.AddString($s.caption,$font,[int][Drawing.FontStyle]::Bold,$size,[Drawing.PointF]::new(0,0),[Drawing.StringFormat]::GenericTypographic)
 $box=$glyph.GetBounds()
 $translate=[Drawing.Drawing2D.Matrix]::new()
 $translate.Translate([single]((512-$box.Width)/2-$box.X),[single](446-$box.Height/2-$box.Y))
 $glyph.Transform($translate)
 $g.DrawPath($stroke,$glyph);$g.FillPath($ink,$glyph)
 $g.Dispose();$glyph.Dispose();$translate.Dispose()
 $name=$s.id+'-'+$s.caption+'.png'
 $big.Save((Join-Path $OutputRoot ('exports/chat-512/'+$name)),[Drawing.Imaging.ImageFormat]::Png)
 $small=[Drawing.Bitmap]::new(240,240,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=Open-Graphics $small
 $g.DrawImage($big,[Drawing.Rectangle]::new(0,0,240,240))
 $g.Dispose()
 $small.Save((Join-Path $OutputRoot ('exports/wechat-240/'+$name)),[Drawing.Imaging.ImageFormat]::Png)
 $thumb=[Drawing.Bitmap]::new(120,120,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=Open-Graphics $thumb
 Draw-Cutout $g $im $crop 5 5 110 110
 $g.Dispose()
 $thumb.Save((Join-Path $OutputRoot ('exports/thumbnails-120/'+$name)),[Drawing.Imaging.ImageFormat]::Png)
 $big.Dispose();$small.Dispose();$thumb.Dispose();$im.Dispose()
}
$im=[Drawing.Bitmap]::FromFile((Join-Path $sourceRoot 'raw/cover.png'))
$crop=Get-Bounds $im
foreach($size in @(240,50)){
 $out=[Drawing.Bitmap]::new($size,$size,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=Open-Graphics $out
 $pad=if($size -eq 50){2}else{8}
 Draw-Cutout $g $im $crop $pad $pad ($size-2*$pad) ($size-2*$pad)
 $g.Dispose()
 $name=if($size -eq 50){'icon-50.png'}else{'cover-240.png'}
 $out.Save((Join-Path $OutputRoot ('assets/'+$name)),[Drawing.Imaging.ImageFormat]::Png);$out.Dispose()
}
$im.Dispose()
$im=[Drawing.Bitmap]::FromFile((Join-Path $sourceRoot 'raw/banner.png'))
$out=[Drawing.Bitmap]::new(750,400)
$g=Open-Graphics $out
$g.Clear([Drawing.ColorTranslator]::FromHtml('#B2D2CC'))
$scale=[Math]::Max(750/$im.Width,400/$im.Height)
$dw=[int][Math]::Ceiling($im.Width*$scale);$dh=[int][Math]::Ceiling($im.Height*$scale)
$g.DrawImage($im,[Drawing.Rectangle]::new([int]((750-$dw)/2),[int]((400-$dh)/2),$dw,$dh))
$g.Dispose();$im.Dispose()
$out.Save((Join-Path $OutputRoot 'assets/banner-750x400.jpg'),[Drawing.Imaging.ImageFormat]::Jpeg);$out.Dispose()

$title=[Drawing.Font]::new('Microsoft YaHei',34,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
$sub=[Drawing.Font]::new('Microsoft YaHei',18,[Drawing.GraphicsUnit]::Pixel)
foreach($theme in @('light','dark')){
 $dark=$theme -eq 'dark'
 $canvas=[Drawing.Bitmap]::new(1080,1140)
 $g=Open-Graphics $canvas
 $bg=if($dark){'#152422'}else{'#F4F0E7'}
 $fg=if($dark){'#F3EFE6'}else{'#233A35'}
 $brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($fg))
 $g.Clear([Drawing.ColorTranslator]::FromHtml($bg))
 $g.DrawString('林小羊 · 今晚有安排',$title,$brush,32,18)
 $g.DrawString('门店接待   /   16 张静态   /   KTV · 台球 · 足浴',$sub,$brush,35,66)
 for($i=0;$i -lt $pack.stickers.Count;$i++){
  $s=$pack.stickers[$i];$x=24+($i%4)*266;$y=94+[int][Math]::Floor($i/4)*260
  $name=$s.id+'-'+$s.caption+'.png'
  $img=[Drawing.Image]::FromFile((Join-Path $OutputRoot ('exports/wechat-240/'+$name)))
  $g.DrawImageUnscaled($img,$x,$y);$img.Dispose()
  $g.DrawString(($s.id+'  '+$s.category),$sub,$brush,($x+87),($y+235))
 }
 $canvas.Save((Join-Path $OutputRoot ('preview/contact-'+$theme+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)
 $g.Dispose();$brush.Dispose();$canvas.Dispose()
}
$title.Dispose();$sub.Dispose();$stroke.Dispose();$ink.Dispose();$font.Dispose()
& (Join-Path $PSScriptRoot 'export-white.ps1') -ExportRoot (Join-Path $OutputRoot 'exports')
