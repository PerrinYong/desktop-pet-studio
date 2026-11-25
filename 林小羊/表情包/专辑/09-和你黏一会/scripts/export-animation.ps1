param([Parameter(Mandatory=$true)][string]$FFmpeg,[string]$OutputRoot='animation',[string]$OnlyId='')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
$out=Join-Path $base $OutputRoot
foreach($sub in @('frames','exports','preview')) {
 $dir=Join-Path $out $sub
 if(Test-Path -LiteralPath $dir){throw "Refusing to overwrite: $dir"}
 New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
$specs=(Get-Content -LiteralPath (Join-Path $base 'pack.json') -Raw | ConvertFrom-Json).stickers
if($OnlyId){$specs=@($specs | Where-Object {$_.id -eq $OnlyId});if($specs.Count -ne 1){throw 'Unknown sticker id'}}
$records=@()
foreach($spec in $specs){
 $frames=Join-Path $out ('frames/'+$spec.id)
 New-Item -ItemType Directory -Path $frames -Force | Out-Null
 $sheet=[Drawing.Bitmap]::FromFile((Join-Path $base ('animation/raw/'+$spec.id+'-sheet.png')))
 if($sheet.Width%2 -ne 0 -or $sheet.Height%2 -ne 0){throw 'Sheet dimensions must be even'}
 $cw=[int]($sheet.Width/2);$ch=[int]($sheet.Height/2)
 for($i=0;$i -lt 4;$i++){
  $x=[int](($i%2)*$cw);$y=[int]([Math]::Floor($i/2)*$ch)
  $cut=$sheet.Clone([Drawing.Rectangle]::new($x,$y,$cw,$ch),[Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $cut.Save((Join-Path $frames ('source-'+$i+'.png')),[Drawing.Imaging.ImageFormat]::Png)
  $canvas=[Drawing.Bitmap]::new(240,240,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g=[Drawing.Graphics]::FromImage($canvas);$g.Clear([Drawing.Color]::Transparent)
  $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  $scale=[Math]::Min(210.0/$cw,188.0/$ch)
  $w=[int][Math]::Round($cw*$scale);$h=[int][Math]::Round($ch*$scale)
  $g.DrawImage($cut,[Drawing.Rectangle]::new([int]((240-$w)/2),2,$w,$h))
  $path=[Drawing.Drawing2D.GraphicsPath]::new()
  $family=[Drawing.FontFamily]::new('Microsoft YaHei')
  $path.AddString($spec.caption,$family,[int][Drawing.FontStyle]::Bold,34,[Drawing.PointF]::new(0,0),[Drawing.StringFormat]::GenericDefault)
  $bounds=$path.GetBounds()
  $matrix=[Drawing.Drawing2D.Matrix]::new()
  $matrix.Translate([single]((240-$bounds.Width)/2-$bounds.X),[single](202-$bounds.Y))
  $path.Transform($matrix)
  $pen=[Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('#FFF9EE'),5)
  $pen.LineJoin=[Drawing.Drawing2D.LineJoin]::Round
  $brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml('#302B27'))
  $g.DrawPath($pen,$path);$g.FillPath($brush,$path)
  $canvas.Save((Join-Path $frames ('key-'+$i+'.png')),[Drawing.Imaging.ImageFormat]::Png)
  $brush.Dispose();$pen.Dispose();$matrix.Dispose();$path.Dispose();$family.Dispose();$g.Dispose();$canvas.Dispose();$cut.Dispose()
 }
 $sheet.Dispose()
 for($i=0;$i -lt $spec.sequence.Count;$i++){
  Copy-Item -LiteralPath (Join-Path $frames ('key-'+$spec.sequence[$i]+'.png')) -Destination (Join-Path $frames ('frame-{0:D3}.png' -f $i))
 }
 $gif=Join-Path $out ('exports/'+$spec.caption+'.gif')
 & $FFmpeg -hide_banner -loglevel error -framerate 10 -i (Join-Path $frames 'frame-%03d.png') -filter_complex '[0:v]split[a][b];[a]palettegen=max_colors=128:reserve_transparent=1[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:alpha_threshold=128' -loop 0 -gifflags '-offsetting-transdiff' $gif
 if($LASTEXITCODE -ne 0){throw "GIF encoding failed"}
 foreach($theme in @('light','dark')){
  $board=[Drawing.Bitmap]::new(1000,280)
  $g=[Drawing.Graphics]::FromImage($board)
  $color=if($theme -eq 'dark'){'#080E16'}else{'#F4F0E7'}
  $g.Clear([Drawing.ColorTranslator]::FromHtml($color))
  for($i=0;$i -lt 4;$i++){
   $frame=[Drawing.Bitmap]::FromFile((Join-Path $frames ('key-'+$i+'.png')))
   $g.DrawImageUnscaled($frame,10+$i*250,20);$frame.Dispose()
  }
  $board.Save((Join-Path $out ('preview/'+$spec.id+'-'+$theme+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)
  $g.Dispose();$board.Dispose()
 }
 $records+=@{id=$spec.id;caption=$spec.caption;size=@(240,240);sequence=$spec.sequence;frame_ms=100;loop_ms=($spec.sequence.Count*100);loop='forever';file=('exports/'+$spec.caption+'.gif');bytes=(Get-Item -LiteralPath $gif).Length;sha256=(Get-FileHash -LiteralPath $gif -Algorithm SHA256).Hash.ToLower()}
}
@{kind='keyframe_animation';frames_per_sheet=4;fps=10;files=$records}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'timing.json') -Encoding utf8
$records | Select-Object caption,bytes | ConvertTo-Json


