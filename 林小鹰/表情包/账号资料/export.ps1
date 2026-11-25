param([string]$Destination='.')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not [IO.Path]::IsPathRooted($Destination)){$Destination=Join-Path $PSScriptRoot $Destination}
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$source=[Drawing.Bitmap]::FromFile((Join-Path $PSScriptRoot 'raw/profile-master.png'))
try {
    foreach($spec in @(@('avatar-240.png',240),@('icon-50.png',50))) {
        $path=Join-Path $Destination $spec[0]
        if(Test-Path -LiteralPath $path){throw "Refusing to overwrite $path"}
        $size=[int]$spec[1]
        $bitmap=[Drawing.Bitmap]::new($size,$size,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $g=[Drawing.Graphics]::FromImage($bitmap)
        $g.Clear([Drawing.Color]::Transparent)
        $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
        $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $scale=$size/[double][Math]::Max($source.Width,$source.Height)
        $w=[int][Math]::Round($source.Width*$scale);$h=[int][Math]::Round($source.Height*$scale)
        $rect=[Drawing.Rectangle]::new([int](($size-$w)/2),[int](($size-$h)/2),$w,$h)
        $attrs=[Drawing.Imaging.ImageAttributes]::new()
        $attrs.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
        $g.DrawImage($source,$rect,0,0,$source.Width,$source.Height,[Drawing.GraphicsUnit]::Pixel,$attrs)
        $bitmap.Save($path,[Drawing.Imaging.ImageFormat]::Png)
        $attrs.Dispose();$g.Dispose();$bitmap.Dispose()
        if((Get-Item -LiteralPath $path).Length -gt 500000){throw "File exceeds 500 KB: $path"}
    }
} finally {$source.Dispose()}
