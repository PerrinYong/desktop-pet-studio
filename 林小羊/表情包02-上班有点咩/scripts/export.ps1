param([string]$OutputRoot = '.')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path $PSScriptRoot -Parent
$manifest = Get-Content -LiteralPath (Join-Path $projectRoot 'pack.json') -Raw | ConvertFrom-Json
if (-not [IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot = Join-Path $projectRoot $OutputRoot }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
foreach ($name in @('exports','preview','validation.json')) {
    if (Test-Path -LiteralPath (Join-Path $OutputRoot $name)) { throw "Refusing to overwrite: $name" }
}
foreach ($dir in @('exports/chat-512','exports/wechat-240','exports/thumbnails-120','preview')) {
    New-Item -ItemType Directory -Path (Join-Path $OutputRoot $dir) -Force | Out-Null
}

function New-Canvas([int]$width,[int]$height) {
    return [Drawing.Bitmap]::new($width,$height,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
}
function New-Graphics($bitmap) {
    $g=[Drawing.Graphics]::FromImage($bitmap)
    $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.TextRenderingHint=[Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    return $g
}
function Export-Padded($source,[int]$size,[string]$target) {
    $bitmap=New-Canvas $size $size
    $g=New-Graphics $bitmap
    $g.Clear([Drawing.Color]::Transparent)
    $pad=[int][Math]::Ceiling($size/30)
    $scale=($size-2*$pad)/[double][Math]::Max($source.Width,$source.Height)
    $w=[int][Math]::Round($source.Width*$scale)
    $h=[int][Math]::Round($source.Height*$scale)
    $dest=[Drawing.Rectangle]::new([int](($size-$w)/2),[int](($size-$h)/2),$w,$h)
    $attrs=[Drawing.Imaging.ImageAttributes]::new()
    $attrs.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY)
    $g.DrawImage($source,$dest,0,0,$source.Width,$source.Height,[Drawing.GraphicsUnit]::Pixel,$attrs)
    $bitmap.Save($target,[Drawing.Imaging.ImageFormat]::Png)
    $attrs.Dispose();$g.Dispose();$bitmap.Dispose()
}

$results=@()
foreach($item in $manifest.stickers) {
    $srcPath=Join-Path $projectRoot $item.raw
    $src=[Drawing.Bitmap]::FromFile($srcPath)
    $name=$item.id+'-'+$item.caption+'.png'
    foreach($spec in @(@('chat-512',512),@('wechat-240',240),@('thumbnails-120',120))) {
        $path=Join-Path $OutputRoot ('exports/'+$spec[0]+'/'+$name)
        Export-Padded $src ([int]$spec[1]) $path
    }
    $src.Dispose()
    $main=Join-Path $OutputRoot ('exports/wechat-240/'+$name)
    $bmp=[Drawing.Bitmap]::FromFile($main)
    $transparent=0;$edgePixels=0;$minX=240;$minY=240;$maxX=-1;$maxY=-1
    for($y=0;$y -lt 240;$y++) { for($x=0;$x -lt 240;$x++) {
        $a=$bmp.GetPixel($x,$y).A
        if($a -eq 0) {$transparent++}
        if($a -gt 16) {
            $minX=[Math]::Min($minX,$x);$minY=[Math]::Min($minY,$y)
            $maxX=[Math]::Max($maxX,$x);$maxY=[Math]::Max($maxY,$y)
        }
        if(($x -eq 0 -or $x -eq 239 -or $y -eq 0 -or $y -eq 239) -and $a -gt 0) {$edgePixels++}
    }}
    $bmp.Dispose()
    $bytes=(Get-Item -LiteralPath $main).Length
    $thumbBytes=(Get-Item -LiteralPath (Join-Path $OutputRoot ('exports/thumbnails-120/'+$name))).Length
    if($transparent -eq 0 -or $edgePixels -ne 0 -or $bytes -gt 100000 -or $thumbBytes -gt 50000) { throw "Export check failed for $name" }
    $results += [ordered]@{id=$item.id;caption=$item.caption;size=@(240,240);bytes=$bytes;thumbnail_bytes=$thumbBytes;transparent_fraction=[Math]::Round($transparent/57600.0,4);outer_edge_nontransparent_pixels=$edgePixels;alpha_bbox=@($minX,$minY,$maxX,$maxY);sha256=(Get-FileHash -LiteralPath $main -Algorithm SHA256).Hash.ToLower();raw_sha256=(Get-FileHash -LiteralPath $srcPath -Algorithm SHA256).Hash.ToLower()}
}

foreach($theme in @('light','dark')) {
    $board=New-Canvas 1280 948
    $g=New-Graphics $board
    $bg=if($theme -eq 'dark'){'#080E16'}else{'#F4F0E7'}
    $fg=if($theme -eq 'dark'){'#F1EEE7'}else{'#282B2D'}
    $muted=if($theme -eq 'dark'){'#A3AFBB'}else{'#6D6F70'}
    $g.Clear([Drawing.ColorTranslator]::FromHtml($bg))
    $brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($fg))
    $sub=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($muted))
    $gold=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml('#B59A62'))
    $title=[Drawing.Font]::new('Microsoft YaHei',46,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
    $subtitle=[Drawing.Font]::new('Microsoft YaHei',23,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
    $small=[Drawing.Font]::new('Microsoft YaHei',18,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
    $g.FillRectangle($gold,48,46,6,99)
    $g.DrawString('林小羊',$title,$brush,72,40)
    $g.DrawString('上班有点咩  /  8 个聊天瞬间',$subtitle,$sub,75,112)
    for($i=0;$i -lt $manifest.stickers.Count;$i++) {
        $item=$manifest.stickers[$i]
        $col=$i%4;$row=[Math]::Floor($i/4)
        $x=48+$col*296;$y=188+$row*316
        $name=$item.id+'-'+$item.caption+'.png'
        $im=[Drawing.Bitmap]::FromFile((Join-Path $OutputRoot ('exports/wechat-240/'+$name)))
        $g.DrawImageUnscaled($im,[int]($x+28),[int]$y)
        $g.DrawString(($item.id+'  /  '+$item.display_scene),$small,$sub,[single]($x+30),[single]($y+258))
        $im.Dispose()
    }
    $g.DrawString('简笔小羊 · 静态透明表情 · 240px 原尺寸展示',$small,$sub,48,878)
    $board.Save((Join-Path $OutputRoot ('preview/contact-'+$theme+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)
    $small.Dispose();$subtitle.Dispose();$title.Dispose();$gold.Dispose();$sub.Dispose();$brush.Dispose();$g.Dispose();$board.Dispose()
}

$report=[ordered]@{ok=$true;count=$results.Count;format='PNG RGBA';kind='static';exports=@(512,240,120);main_internal_target_bytes=100000;thumbnail_internal_target_bytes=50000;official_submission_rules_verified=$false;wechat_client_tested=$false;files=$results}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputRoot 'validation.json') -Encoding utf8
$results | Measure-Object -Property bytes -Maximum -Minimum | Select-Object Maximum,Minimum | ConvertTo-Json


