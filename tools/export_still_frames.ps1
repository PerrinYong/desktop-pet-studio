param([Parameter(Mandatory=$true)][string]$Plan)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing.Common,System.Drawing.Primitives -TypeDefinition @'
using System;
using System.Drawing;
public class StillBounds {
 public static Rectangle Find(Bitmap b) {
  int l=b.Width,t=b.Height,r=-1,d=-1;
  for(int y=0;y<b.Height;y++) for(int x=0;x<b.Width;x++) {
   if(b.GetPixel(x,y).A<16) continue;
   l=Math.Min(l,x);t=Math.Min(t,y);r=Math.Max(r,x);d=Math.Max(d,y);
  }
  if(r<l) throw new Exception("Empty source frame");
  return Rectangle.FromLTRB(l,t,r+1,d+1);
 }
}
'@
$data=Get-Content -LiteralPath $Plan -Raw -Encoding utf8 | ConvertFrom-Json
foreach($job in $data.jobs){
 $im=[Drawing.Bitmap]::new($job.source)
 try {
  $bounds=[StillBounds]::Find($im)
  foreach($size in @(240,512,120)){
   $b=[Drawing.Bitmap]::new($size,$size)
   $g=[Drawing.Graphics]::FromImage($b)
   $g.Clear([Drawing.Color]::Transparent)
   $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
   $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
   $margin=[Math]::Max(3,[Math]::Round($size*0.025))
   $scale=($size-2*$margin)/[double][Math]::Max($bounds.Width,$bounds.Height)
   $w=[float]($bounds.Width*$scale);$h=[float]($bounds.Height*$scale)
   $g.DrawImage($im,[Drawing.RectangleF]::new(($size-$w)/2,($size-$h)/2,$w,$h),[Drawing.RectangleF]::new($bounds.X,$bounds.Y,$bounds.Width,$bounds.Height),[Drawing.GraphicsUnit]::Pixel)
   $g.Dispose()
   $dir=if($size -eq 120){'缩略图-120'}else{"透明-$size"}
   $b.Save((Join-Path $job.target "$dir/$($job.name).png"),[Drawing.Imaging.ImageFormat]::Png)
   if($size -ne 120){
    $white=[Drawing.Bitmap]::new($size,$size)
    $wg=[Drawing.Graphics]::FromImage($white)
    $wg.Clear([Drawing.Color]::White)
    $wg.DrawImageUnscaled($b,0,0);$wg.Dispose()
    $white.Save((Join-Path $job.target "纯白-$size/$($job.name).png"),[Drawing.Imaging.ImageFormat]::Png)
    $white.Dispose()
   }
   $b.Dispose()
  }
 } finally {$im.Dispose()}
}
foreach($preview in $data.previews){
 $cols=4;$rows=[int][Math]::Ceiling($preview.paths.Count/4.0)
 $b=[Drawing.Bitmap]::new(1040,$rows*280)
 $g=[Drawing.Graphics]::FromImage($b)
 $g.Clear($(if($preview.dark){[Drawing.Color]::FromArgb(37,40,45)}else{[Drawing.Color]::White}))
 $font=[Drawing.Font]::new('Microsoft YaHei',10)
 $brush=[Drawing.SolidBrush]::new($(if($preview.dark){[Drawing.Color]::Silver}else{[Drawing.Color]::DimGray}))
 for($i=0;$i -lt $preview.paths.Count;$i++){
  $p=$preview.paths[$i];$im=[Drawing.Image]::FromFile($p)
  $x=($i%4)*260;$y=[int][Math]::Floor($i/4)*280
  $g.DrawImage($im,$x+10,$y+4,240,240);$im.Dispose()
  $label=[IO.Path]::GetFileNameWithoutExtension($p)
  $g.DrawString($label,$font,$brush,$x+10,$y+250)
 }
 $g.Dispose();$font.Dispose();$brush.Dispose()
 $b.Save($preview.target,[Drawing.Imaging.ImageFormat]::Png);$b.Dispose()
}
Write-Output "Selected still exports: $($data.jobs.Count); preview sheets: $($data.previews.Count)"
