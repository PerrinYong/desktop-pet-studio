param([Parameter(Mandatory=$true)][string]$FFmpeg,[string]$OutputRoot='animation')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
$out=Join-Path $base $OutputRoot
$specs=(Get-Content -LiteralPath (Join-Path $base 'pack.json') -Raw | ConvertFrom-Json).stickers
$gallery=Join-Path $out 'preview/gallery-frames'
if(Test-Path -LiteralPath $gallery){throw 'Gallery frames already exist'}
New-Item -ItemType Directory -Path $gallery | Out-Null
foreach($theme in @('light','dark')){
 for($t=0;$t -lt 16;$t++){
  if($theme -eq 'dark' -and $t -gt 0){continue}
  $board=[Drawing.Bitmap]::new(1000,640)
  $g=[Drawing.Graphics]::FromImage($board)
  $bg=if($theme -eq 'dark'){'#080E16'}else{'#F4F0E7'}
  $fg=if($theme -eq 'dark'){'#F4F0E7'}else{'#302B27'}
  $g.Clear([Drawing.ColorTranslator]::FromHtml($bg))
  $font=[Drawing.Font]::new('Microsoft YaHei',25,[Drawing.FontStyle]::Bold)
  $small=[Drawing.Font]::new('Microsoft YaHei',12)
  $brush=[Drawing.SolidBrush]::new([Drawing.ColorTranslator]::FromHtml($fg))
  $g.DrawString('林小羊 · 羊年一起过',$font,$brush,20,12)
  $g.DrawString('8 张春节动图 / 拜年 · 团圆 · 守岁 · 开工',$small,$brush,22,56)
  for($i=0;$i -lt $specs.Count;$i++){
   $s=$specs[$i];$n=$t%$s.sequence.Count
   $frame=[Drawing.Bitmap]::FromFile((Join-Path $out ('frames/'+$s.id+('/frame-{0:D3}.png' -f $n))))
   $x=5+($i%4)*250;$y=95+[Math]::Floor($i/4)*260
   $g.DrawImageUnscaled($frame,[int]$x,[int]$y);$frame.Dispose()
  }
  if($t -eq 0){$board.Save((Join-Path $out ('preview/contact-'+$theme+'.jpg')),[Drawing.Imaging.ImageFormat]::Jpeg)}
  if($theme -eq 'light'){$board.Save((Join-Path $gallery ('frame-{0:D3}.png' -f $t)),[Drawing.Imaging.ImageFormat]::Png)}
  $font.Dispose();$small.Dispose();$brush.Dispose();$g.Dispose();$board.Dispose()
 }
}
& $FFmpeg -hide_banner -loglevel error -framerate 10 -i (Join-Path $gallery 'frame-%03d.png') -filter_complex '[0:v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3' -loop 0 (Join-Path $out 'preview/八张动图总览.gif')
if($LASTEXITCODE -ne 0){throw 'Gallery encoding failed'}



