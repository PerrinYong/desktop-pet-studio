$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
$specs=(Get-Content -LiteralPath (Join-Path $base 'pack.json') -Raw | ConvertFrom-Json).stickers
$folder=Join-Path $base 'review'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
for($page=0;$page -lt 4;$page++){
 $items=$specs[($page*4)..($page*4+3)]
 $dest=Join-Path $folder ('sources-'+($page+1)+'.jpg')
 if(Test-Path -LiteralPath $dest){continue}
 $missing=@($items | Where-Object { -not (Test-Path -LiteralPath (Join-Path $base ('animation/raw/'+$_.id+'-sheet.png'))) })
 if($missing.Count){continue}
 $bmp=[Drawing.Bitmap]::new(1280,1360)
 $g=[Drawing.Graphics]::FromImage($bmp);$g.Clear([Drawing.ColorTranslator]::FromHtml('#E7E1D8'))
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $font=[Drawing.Font]::new('Microsoft YaHei',20,[Drawing.FontStyle]::Bold)
 for($j=0;$j -lt 4;$j++){
  $s=$items[$j];$x=($j%2)*640;$y=[Math]::Floor($j/2)*680
  $im=[Drawing.Bitmap]::FromFile((Join-Path $base ('animation/raw/'+$s.id+'-sheet.png')))
  $g.DrawString($s.caption,$font,[Drawing.Brushes]::Black,[single]($x+12),[single]($y+4))
  $g.DrawImage($im,[Drawing.Rectangle]::new([int]$x,[int]($y+40),640,640));$im.Dispose()
 }
 $bmp.Save($dest,[Drawing.Imaging.ImageFormat]::Jpeg)
 $font.Dispose();$g.Dispose();$bmp.Dispose()
}

