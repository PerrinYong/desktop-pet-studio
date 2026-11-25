param([string]$Destination='.')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not [IO.Path]::IsPathRooted($Destination)){$Destination=Join-Path $PSScriptRoot $Destination}
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$target=Join-Path $Destination 'banner-750x400.jpg'
if(Test-Path -LiteralPath $target){throw "Refusing to overwrite $target"}
$source=[Drawing.Bitmap]::FromFile((Join-Path $PSScriptRoot 'raw/banner-master.png'))
$bitmap=[Drawing.Bitmap]::new(750,400,[Drawing.Imaging.PixelFormat]::Format24bppRgb)
$g=[Drawing.Graphics]::FromImage($bitmap)
$g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
$g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$scale=[Math]::Max(750.0/$source.Width,400.0/$source.Height)
$cropWidth=750.0/$scale;$cropHeight=400.0/$scale
$sx=($source.Width-$cropWidth)/2;$sy=($source.Height-$cropHeight)/2
$dest=[Drawing.Rectangle]::new(0,0,750,400)
$attrs=[Drawing.Imaging.ImageAttributes]::new()
$attrs.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
$g.DrawImage($source,$dest,[single]$sx,[single]$sy,[single]$cropWidth,[single]$cropHeight,[Drawing.GraphicsUnit]::Pixel,$attrs)
$codec=[Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
$params=[Drawing.Imaging.EncoderParameters]::new(1)
$params.Param[0]=[Drawing.Imaging.EncoderParameter]::new([Drawing.Imaging.Encoder]::Quality,[long]94)
$bitmap.Save($target,$codec,$params)
$report=[ordered]@{source_size=@($source.Width,$source.Height);output_size=@(750,400);source_crop_xywh=@($sx,$sy,$cropWidth,$cropHeight);uniform_scale=$scale;jpeg_quality=94;stretched=$false}
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Destination 'export-transform.json') -Encoding utf8
$params.Dispose();$attrs.Dispose();$g.Dispose();$bitmap.Dispose();$source.Dispose()
if((Get-Item -LiteralPath $target).Length -gt 500000){throw 'Export exceeds 500 KB'}
