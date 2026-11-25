param([string]$ExportRoot)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not $ExportRoot){$ExportRoot=Join-Path (Split-Path $PSScriptRoot -Parent) 'exports'}
$variants=@(
 @{From='wechat-240';To='white-240';Size=240},
 @{From='chat-512';To='white-512';Size=512}
)
# Check both destinations before writing either set.
foreach($variant in $variants){
 $source=Join-Path $ExportRoot $variant.From
 $dest=Join-Path $ExportRoot $variant.To
 if(-not (Test-Path -LiteralPath $source -PathType Container)){throw "Missing source $source"}
 if(Test-Path -LiteralPath $dest){throw "Refusing to overwrite $dest"}
 if(-not (Get-ChildItem -LiteralPath $source -File -Filter '*.png')){throw "No PNG files in $source"}
}
foreach($variant in $variants){
 $dest=Join-Path $ExportRoot $variant.To
 New-Item -ItemType Directory -Path $dest | Out-Null
 foreach($file in Get-ChildItem -LiteralPath (Join-Path $ExportRoot $variant.From) -File -Filter '*.png'){
  $image=[Drawing.Bitmap]::FromFile($file.FullName)
  try{
   if($image.Width -ne $variant.Size -or $image.Height -ne $variant.Size){throw "Unexpected size: $($file.Name)"}
   $canvas=[Drawing.Bitmap]::new($image.Width,$image.Height,[Drawing.Imaging.PixelFormat]::Format24bppRgb)
   try{
    $graphics=[Drawing.Graphics]::FromImage($canvas)
    try{
     $graphics.Clear([Drawing.Color]::White)
     $graphics.DrawImageUnscaled($image,0,0)
    }finally{$graphics.Dispose()}
    $canvas.Save((Join-Path $dest $file.Name),[Drawing.Imaging.ImageFormat]::Png)
   }finally{$canvas.Dispose()}
  }finally{$image.Dispose()}
 }
}
