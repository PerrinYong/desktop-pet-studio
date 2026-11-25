param([string]$OutputRoot='exports')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$base=Split-Path $PSScriptRoot -Parent
if(-not [IO.Path]::IsPathRooted($OutputRoot)){$OutputRoot=Join-Path $base $OutputRoot}
if(Test-Path -LiteralPath $OutputRoot){throw "Refusing to overwrite $OutputRoot"}
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
$plan=Get-Content -LiteralPath (Join-Path $base 'plan.json') -Raw | ConvertFrom-Json
$checks=[Collections.Generic.List[object]]::new()
function Export-Asset($source,$dest,$width,$height,$transparent){
 $src=[Drawing.Bitmap]::FromFile($source)
 $dst=[Drawing.Bitmap]::new($width,$height,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=[Drawing.Graphics]::FromImage($dst)
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 if($transparent){
  $g.Clear([Drawing.Color]::Transparent)
  $left=$src.Width;$top=$src.Height;$right=-1;$bottom=-1
  for($y=0;$y -lt $src.Height;$y++){for($x=0;$x -lt $src.Width;$x++){
   if($src.GetPixel($x,$y).A -gt 16){$left=[Math]::Min($left,$x);$right=[Math]::Max($right,$x);$top=[Math]::Min($top,$y);$bottom=[Math]::Max($bottom,$y)}
  }}
  if($right -lt 0){throw "Empty alpha source: $source"}
  $sx=[Math]::Max(0,$left-3);$sy=[Math]::Max(0,$top-3)
  $sw=[Math]::Min($src.Width-$sx,$right-$sx+4);$sh=[Math]::Min($src.Height-$sy,$bottom-$sy+4)
  $pad=if($width -eq 50){2}else{8}
  $s=[Math]::Min(($width-2*$pad)/$sw,($height-2*$pad)/$sh)
  $dw=[int][Math]::Round($sw*$s);$dh=[int][Math]::Round($sh*$s)
  $rect=[Drawing.Rectangle]::new([int](($width-$dw)/2),[int](($height-$dh)/2),$dw,$dh)
  $g.DrawImage($src,$rect,$sx,$sy,$sw,$sh,[Drawing.GraphicsUnit]::Pixel)
 }else{
  $g.Clear([Drawing.Color]::FromArgb(255,210,185,160))
  $scale=[Math]::Max($width/[double]$src.Width,$height/[double]$src.Height)
  $dw=[int][Math]::Ceiling($src.Width*$scale);$dh=[int][Math]::Ceiling($src.Height*$scale)
  $g.DrawImage($src,[Drawing.Rectangle]::new([int](($width-$dw)/2),[int](($height-$dh)/2),$dw,$dh))
 }
 $fmt=if($transparent){[Drawing.Imaging.ImageFormat]::Png}else{[Drawing.Imaging.ImageFormat]::Jpeg}
 $dst.Save($dest,$fmt);$g.Dispose();$dst.Dispose();$src.Dispose()
 $checks.Add(@{file=[IO.Path]::GetRelativePath($OutputRoot,$dest).Replace('\','/');width=$width;height=$height;bytes=(Get-Item -LiteralPath $dest).Length;source=[IO.Path]::GetRelativePath($base,$source).Replace('\','/');sha256=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()})
}
$profile=Join-Path $OutputRoot 'profile'
New-Item -ItemType Directory -Path $profile | Out-Null
Export-Asset (Join-Path $base 'raw/profile-avatar.png') (Join-Path $profile 'avatar-240.png') 240 240 $true
Export-Asset (Join-Path $base 'raw/profile-avatar.png') (Join-Path $profile 'icon-50.png') 50 50 $true
foreach($a in $plan.albums){
 $dir=Join-Path $OutputRoot $a.id
 New-Item -ItemType Directory -Path $dir | Out-Null
 Export-Asset (Join-Path $base ('raw/'+$a.id+'-cover.png')) (Join-Path $dir 'cover-240.png') 240 240 $true
 Export-Asset (Join-Path $base ('raw/'+$a.id+'-cover.png')) (Join-Path $dir 'icon-50.png') 50 50 $true
 Export-Asset (Join-Path $base ('raw/'+$a.id+'-banner.png')) (Join-Path $dir 'banner-750x400.jpg') 750 400 $false
}
@{files=$checks;note='Technical export only; original art generated with built-in image_gen.'}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $OutputRoot 'export-manifest.json') -Encoding utf8
$checks|Select-Object file,width,height,bytes|ConvertTo-Json
