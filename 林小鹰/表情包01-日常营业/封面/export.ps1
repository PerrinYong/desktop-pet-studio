param([string]$Destination='.')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not [IO.Path]::IsPathRooted($Destination)){$Destination=Join-Path $PSScriptRoot $Destination}
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$target=Join-Path $Destination 'cover-240.png'
if(Test-Path -LiteralPath $target){throw "Refusing to overwrite $target"}
$source=[Drawing.Bitmap]::FromFile((Join-Path $PSScriptRoot 'raw/cover-master.png'))
$bitmap=[Drawing.Bitmap]::new(240,240,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g=[Drawing.Graphics]::FromImage($bitmap)
$g.Clear([Drawing.Color]::Transparent)
$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
$g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$scale=240.0/[Math]::Max($source.Width,$source.Height)
$w=[int][Math]::Round($source.Width*$scale);$h=[int][Math]::Round($source.Height*$scale)
$dest=[Drawing.Rectangle]::new([int]((240-$w)/2),[int]((240-$h)/2),$w,$h)
$attrs=[Drawing.Imaging.ImageAttributes]::new()
$attrs.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
$g.DrawImage($source,$dest,0,0,$source.Width,$source.Height,[Drawing.GraphicsUnit]::Pixel,$attrs)
$bitmap.Save($target,[Drawing.Imaging.ImageFormat]::Png)
$attrs.Dispose();$g.Dispose();$bitmap.Dispose();$source.Dispose()
if((Get-Item -LiteralPath $target).Length -gt 500000){throw 'Export exceeds 500 KB'}
