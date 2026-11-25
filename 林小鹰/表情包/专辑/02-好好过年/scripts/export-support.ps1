param([string]$OutputRoot = '.')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot=Split-Path $PSScriptRoot -Parent
if (-not [IO.Path]::IsPathRooted($OutputRoot)) {$OutputRoot=Join-Path $projectRoot $OutputRoot}
$assets=Join-Path $OutputRoot 'assets'
if(Test-Path -LiteralPath $assets){throw "Refusing to overwrite: $assets"}
New-Item -ItemType Directory -Path $assets -Force | Out-Null
$specs=@(
@{name='cover-240.png';source='raw/cover-master.png';w=240;h=240;alpha=$true},
@{name='icon-50.png';source='raw/cover-master.png';w=50;h=50;alpha=$true},
@{name='banner-750x400.jpg';source='raw/banner-v2.png';w=750;h=400;alpha=$false}
)
$checks=@()
foreach($spec in $specs){
 $src=[Drawing.Bitmap]::FromFile((Join-Path $projectRoot $spec.source))
 $dst=[Drawing.Bitmap]::new($spec.w,$spec.h,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=[Drawing.Graphics]::FromImage($dst)
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 if($spec.alpha){
  $g.Clear([Drawing.Color]::Transparent)
  $scale=[Math]::Min(($spec.w-4)/$src.Width,($spec.h-4)/$src.Height)
  $w=[int][Math]::Round($src.Width*$scale);$h=[int][Math]::Round($src.Height*$scale)
  $rect=[Drawing.Rectangle]::new([int](($spec.w-$w)/2),[int](($spec.h-$h)/2),$w,$h)
  $g.DrawImage($src,$rect)
 }else{
  $g.Clear([Drawing.ColorTranslator]::FromHtml('#165931'))
  $scale=[Math]::Max($spec.w/[double]$src.Width,$spec.h/[double]$src.Height)
  $w=[int][Math]::Ceiling($src.Width*$scale);$h=[int][Math]::Ceiling($src.Height*$scale)
  $g.DrawImage($src,[Drawing.Rectangle]::new([int](($spec.w-$w)/2),[int](($spec.h-$h)/2),$w,$h))
 }
 $file=Join-Path $assets $spec.name
 $format=if($spec.alpha){[Drawing.Imaging.ImageFormat]::Png}else{[Drawing.Imaging.ImageFormat]::Jpeg}
 $dst.Save($file,$format)
 $g.Dispose();$src.Dispose();$dst.Dispose()
 $check=[Drawing.Bitmap]::FromFile($file)
 $minA=255;$maxA=0
 for($y=0;$y -lt $check.Height;$y++){for($x=0;$x -lt $check.Width;$x++){
  $a=$check.GetPixel($x,$y).A;$minA=[Math]::Min($minA,$a);$maxA=[Math]::Max($maxA,$a)
 }}
 $bytes=(Get-Item -LiteralPath $file).Length
 if($check.Width -ne $spec.w -or $check.Height -ne $spec.h -or $bytes -gt 500000){throw "Size check failed: $file"}
 if($spec.alpha -and ($minA -ne 0 -or $maxA -ne 255)){throw "Alpha check failed: $file"}
 if(-not $spec.alpha -and $minA -ne 255){throw "Banner must be opaque"}
 $checks+=@{file=('assets/'+$spec.name);source=$spec.source;width=$check.Width;height=$check.Height;bytes=$bytes;min_alpha=$minA;max_alpha=$maxA;sha256=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower()}
 $check.Dispose()
}
@{ok=$true;files=$checks}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputRoot 'support-validation.json') -Encoding utf8
$checks|Select-Object file,width,height,bytes|ConvertTo-Json

