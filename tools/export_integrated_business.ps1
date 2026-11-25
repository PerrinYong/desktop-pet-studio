param(
  [string]$FFmpeg,
  [string]$Album = '',
  [string]$Character = '林小羊',
  [string]$Revision = '图文融合-v2',
  [switch]$AvailableOnly
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing.Common,System.Drawing.Primitives -TypeDefinition @'
using System;
using System.Drawing;
public class AlphaArea {
 public static Rectangle Bounds(Bitmap b) {
  int l=b.Width,t=b.Height,r=-1,d=-1;
  for(int y=0;y<b.Height;y++) for(int x=0;x<b.Width;x++) {
   if(b.GetPixel(x,y).A < 16) continue;
   l=Math.Min(l,x);t=Math.Min(t,y);r=Math.Max(r,x);d=Math.Max(d,y);
  }
  if(r<l) throw new Exception("Empty alpha image");
  return Rectangle.FromLTRB(l,t,r+1,d+1);
 }
}
'@
$repo = Split-Path $PSScriptRoot
$albumBase = Join-Path $repo "$Character/表情包/专辑"
function Ensure-Directory([string]$p) { [IO.Directory]::CreateDirectory($p) | Out-Null }
function Save-Sized($img, $src, [int]$size, [string]$path, [bool]$white=$false) {
 $out=[Drawing.Bitmap]::new($size,$size)
 $g=[Drawing.Graphics]::FromImage($out)
 $g.Clear($(if($white){[Drawing.Color]::White}else{[Drawing.Color]::Transparent}))
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 $margin=[Math]::Max(3,[Math]::Round($size*0.025))
 $scale=($size-2*$margin)/[double][Math]::Max($src.Width,$src.Height)
 $w=[float]($src.Width*$scale); $h=[float]($src.Height*$scale)
 $dst=[Drawing.RectangleF]::new(($size-$w)/2,($size-$h)/2,$w,$h)
 $g.DrawImage($img,$dst,[Drawing.RectangleF]::new($src.X,$src.Y,$src.Width,$src.Height),[Drawing.GraphicsUnit]::Pixel)
 $g.Dispose()
 $out.Save($path,[Drawing.Imaging.ImageFormat]::Png)
 $out.Dispose()
}
function Contact($paths,[string]$path,[bool]$dark=$false,[int]$columns=4) {
 $rows=[int][Math]::Ceiling($paths.Count/[double]$columns)
 $b=[Drawing.Bitmap]::new($columns*260,$rows*276)
 $g=[Drawing.Graphics]::FromImage($b)
 $bg=if($dark){[Drawing.Color]::FromArgb(37,40,45)}else{[Drawing.Color]::FromArgb(245,243,239)}
 $g.Clear($bg)
 $font=[Drawing.Font]::new('Segoe UI',11)
 $brush=[Drawing.SolidBrush]::new($(if($dark){[Drawing.Color]::Silver}else{[Drawing.Color]::DimGray}))
 for($i=0;$i -lt $paths.Count;$i++){
  $im=[Drawing.Image]::FromFile($paths[$i]);$x=($i%$columns)*260;$y=[int][Math]::Floor($i/$columns)*276
  $g.DrawImage($im,$x+10,$y+5,240,240);$im.Dispose()
  $g.DrawString(('{0:D2}' -f ($i+1)),$font,$brush,$x+12,$y+248)
 }
 $g.Dispose();$font.Dispose();$brush.Dispose();$b.Save($path,[Drawing.Imaging.ImageFormat]::Png);$b.Dispose()
}
$names=if($Album){@($Album)}else{@('10-今晚有安排','11-随时招呼','12-有事您招呼')}
foreach($name in $names){
 $base=Join-Path $albumBase "$name/revisions/$Revision"
 $pack=Get-Content -LiteralPath "$base/pack.json" -Raw -Encoding utf8 | ConvertFrom-Json
 if($AvailableOnly){
  $pack.stickers=@($pack.stickers | Where-Object {
   $raw=if($pack.kind -eq 'animated'){if($_.sheet){$_.sheet}else{"raw/$($_.id)-sheet.png"}}else{if($_.image){$_.image}else{"raw/$($_.id).png"}}
   Test-Path -LiteralPath "$base/$raw"
  })
  if(!$pack.stickers.Count){continue}
 }
 foreach($d in @('exports/chat-512','exports/wechat-240','exports/white-240','exports/white-512','exports/thumbnails-120','preview')){Ensure-Directory "$base/$d"}
 $mainPaths=@(); $keyPaths=@()
 if($pack.kind -eq 'animated'){
  if(!$FFmpeg){throw 'Animated export requires -FFmpeg path'}
  Ensure-Directory "$base/animation/exports"
  foreach($s in $pack.stickers){
   $fd="$base/animation/frames/$($s.id)";Ensure-Directory $fd
   $sourceSheet=if($s.sheet){"$base/$($s.sheet)"}else{"$base/raw/$($s.id)-sheet.png"}
   $sheet=[Drawing.Bitmap]::new($sourceSheet)
   $cw=[int][Math]::Floor($sheet.Width/2);$ch=[int][Math]::Floor($sheet.Height/2)
   $cells=@();$union=[Drawing.Rectangle]::Empty
   for($k=0;$k -lt 4;$k++){
    $rect=[Drawing.Rectangle]::new(($k%2)*$cw,[int][Math]::Floor($k/2)*$ch,$cw,$ch)
    $cell=$sheet.Clone($rect,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $cell.Save("$fd/source-$k.png",[Drawing.Imaging.ImageFormat]::Png)
    $bounds=[AlphaArea]::Bounds($cell)
    $union=if($k -eq 0){$bounds}else{[Drawing.Rectangle]::Union($union,$bounds)}
    $cells+=,$cell
   }
   for($k=0;$k -lt 4;$k++){
    Save-Sized $cells[$k] $union 240 "$fd/key-$k.png"
    $keyPaths+="$fd/key-$k.png"
   }
   Contact @(0..3 | ForEach-Object {"$fd/key-$_.png"}) "$base/preview/$($s.id)-frames.png" $true
   $stem="$($s.id)-$($s.caption)"
   foreach($spec in @(@('chat-512',512,$false),@('wechat-240',240,$false),@('white-240',240,$true),@('white-512',512,$true),@('thumbnails-120',120,$false))){
    Save-Sized $cells[2] $union $spec[1] "$base/exports/$($spec[0])/$stem.png" $spec[2]
   }
   for($f=0;$f -lt $s.sequence.Count;$f++){
    Copy-Item -LiteralPath "$fd/key-$($s.sequence[$f]).png" -Destination ("$fd/frame-{0:D3}.png" -f $f)
   }
   & $FFmpeg -hide_banner -loglevel error -y -framerate 10 -i "$fd/frame-%03d.png" -filter_complex '[0:v]split[a][b];[a]palettegen=max_colors=128:reserve_transparent=1[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:alpha_threshold=128' -loop 0 -gifflags '-offsetting-transdiff' "$base/animation/exports/$($s.caption).gif"
   if($LASTEXITCODE -ne 0){throw "GIF export failed: $($s.id)"}
   foreach($cell in $cells){$cell.Dispose()};$sheet.Dispose()
   $mainPaths+="$base/exports/wechat-240/$stem.png"
  }
  Contact $keyPaths "$base/preview/序列帧总览-浅底.png"
  Contact $keyPaths "$base/preview/序列帧总览-深底.png" $true
  Ensure-Directory "$base/preview/gallery-frames"
  $galleryCount=($pack.stickers | ForEach-Object {$_.sequence.Count} | Measure-Object -Maximum).Maximum
  for($f=0;$f -lt $galleryCount;$f++){
   $paths=@($pack.stickers | ForEach-Object { "$base/animation/frames/$($_.id)/frame-$('{0:D3}' -f ($f % $_.sequence.Count)).png" })
   Contact $paths ("$base/preview/gallery-frames/frame-{0:D3}.png" -f $f)
  }
  $galleryName=if($pack.stickers.Count -eq 8){'八张动图总览.gif'}elseif($pack.stickers.Count -eq 16){'十六张动图总览.gif'}else{'动图总览.gif'}
  & $FFmpeg -hide_banner -loglevel error -y -framerate 10 -i "$base/preview/gallery-frames/frame-%03d.png" -frames:v $galleryCount -filter_complex '[0:v]split[a][b];[a]palettegen=max_colors=256[p];[b][p]paletteuse=dither=bayer:bayer_scale=3' -loop 0 "$base/preview/$galleryName"
  if($LASTEXITCODE -ne 0){throw 'Gallery encoding failed'}
 } else {
  foreach($s in $pack.stickers){
   $sourceImage=if($s.image){"$base/$($s.image)"}else{"$base/raw/$($s.id).png"}
   $im=[Drawing.Bitmap]::new($sourceImage)
   $bounds=[AlphaArea]::Bounds($im);$stem="$($s.id)-$($s.caption)"
   foreach($spec in @(@('chat-512',512,$false),@('wechat-240',240,$false),@('white-240',240,$true),@('white-512',512,$true),@('thumbnails-120',120,$false))){
    Save-Sized $im $bounds $spec[1] "$base/exports/$($spec[0])/$stem.png" $spec[2]
   }
   $im.Dispose();$mainPaths+="$base/exports/wechat-240/$stem.png"
  }
 }
 Contact $mainPaths "$base/preview/总览-浅底.png"
 Contact $mainPaths "$base/preview/总览-深底.png" $true
 if($name -eq '11-随时招呼' -and $Character -eq '林小羊'){
  $examples=@($pack.stickers | Where-Object { $_.id -in @('02','05','09','15') })
  $comparison=@($examples | ForEach-Object { "$albumBase/$name/exports/wechat-240/$($_.id)-$($_.caption).png" })
  $comparison+=@($examples | ForEach-Object { "$base/exports/wechat-240/$($_.id)-$($_.caption).png" })
  Contact $comparison "$base/preview/调整前后对比.png"
 }
 $provenance=Get-Content -LiteralPath "$base/provenance.json" -Raw -Encoding utf8 | ConvertFrom-Json
 foreach($entry in $provenance){
  $hash=(Get-FileHash -LiteralPath "$base/$($entry.archived)" -Algorithm SHA256).Hash.ToLower()
  $entry | Add-Member -NotePropertyName sha256 -NotePropertyValue $hash -Force
 }
 [IO.File]::WriteAllText("$base/provenance.json",($provenance | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 Write-Output "$name complete: $($pack.stickers.Count)"
}

