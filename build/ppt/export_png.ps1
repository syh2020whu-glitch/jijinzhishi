param([string]$Pptx, [string]$OutDir, [int]$Width = 1280)
$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Pptx, $true, $false, $false)
$h = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
foreach ($s in $pres.Slides) {
  $s.Export((Join-Path $OutDir ("slide-{0:D2}.png" -f $s.SlideIndex)), "PNG", $Width, $h)
}
$pres.Close()
if ($app.Presentations.Count -eq 0) { $app.Quit() }
