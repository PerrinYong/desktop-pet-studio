param([string]$Destination='.')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not [IO.Path]::IsPathRooted($Destination)){$Destination=Join-Path $PSScriptRoot $Destination}
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$codec=[Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object MimeType -eq 'image/jpeg'
$records=@()
foreach($spec in @(@('avatar',640,640,500000),@('banner',750,400,80000))) {
    $id=$spec[0];$width=[int]$spec[1];$height=[int]$spec[2];$limit=[long]$spec[3]
    $name=if($id -eq 'avatar'){'avatar-640.jpg'}else{'banner-750x400.jpg'}
    $target=Join-Path $Destination $name
    if(Test-Path -LiteralPath $target){throw "Refusing to overwrite $target"}
    $source=[Drawing.Bitmap]::FromFile((Join-Path $PSScriptRoot ('raw/'+$id+'-master.png')))
    $bitmap=[Drawing.Bitmap]::new($width,$height,[Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $g=[Drawing.Graphics]::FromImage($bitmap)
    $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $scale=[Math]::Max($width/[double]$source.Width,$height/[double]$source.Height)
    $sw=$width/$scale;$sh=$height/$scale;$sx=($source.Width-$sw)/2;$sy=($source.Height-$sh)/2
    $attrs=[Drawing.Imaging.ImageAttributes]::new();$attrs.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
    $g.DrawImage($source,[Drawing.Rectangle]::new(0,0,$width,$height),[single]$sx,[single]$sy,[single]$sw,[single]$sh,[Drawing.GraphicsUnit]::Pixel,$attrs)
    $saved=$false
    foreach($quality in @(96,94,92,90,88,85,82,78,74,70,65)) {
        $params=[Drawing.Imaging.EncoderParameters]::new(1)
        $params.Param[0]=[Drawing.Imaging.EncoderParameter]::new([Drawing.Imaging.Encoder]::Quality,[long]$quality)
        $stream=[IO.MemoryStream]::new()
        $bitmap.Save($stream,$codec,$params)
        $bytes=$stream.ToArray();$stream.Dispose();$params.Dispose()
        if($bytes.Length -le $limit){[IO.File]::WriteAllBytes($target,$bytes);$saved=$true;break}
    }
    if(-not $saved){throw "Could not satisfy size limit: $name"}
    $records += [ordered]@{file=$name;source_size=@($source.Width,$source.Height);output_size=@($width,$height);source_crop_xywh=@($sx,$sy,$sw,$sh);uniform_scale=$scale;jpeg_quality=$quality;bytes=$bytes.Length;maximum_bytes=$limit;stretched=$false}
    $attrs.Dispose();$g.Dispose();$bitmap.Dispose();$source.Dispose()
}
$records | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Destination 'export-transform.json') -Encoding utf8
$records | ForEach-Object { [pscustomobject]$_ } | Select-Object file,bytes,jpeg_quality | ConvertTo-Json
