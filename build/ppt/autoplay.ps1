# 放映到该页时自动播放音视频（第 8 页关雎拟音、第 9 页录屏），并让封面释文逐字淡入。build_deck.js 之后运行：
#   powershell -ExecutionPolicy Bypass -File build/ppt/autoplay.ps1 -Pptx 吉金智识-决赛答辩-v2.pptx
# pptxgenjs 只能生成"单击播放"的媒体，这里用 PowerPoint COM 给每个媒体加一个"与上一动画同时"的播放效果，
# 同一页没有其他动画，所以等于进页即播。
# 名字以 fadein- 开头的图形（封面篆书下的释文）按名字顺序逐个淡入：进页 0.8 秒后出第一个，之后每隔 0.3 秒一个。
param([string]$Pptx)
$ErrorActionPreference = "Stop"
$Pptx = (Resolve-Path $Pptx).Path
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($Pptx, $false, $false, $false)
foreach ($s in $pres.Slides) {
  foreach ($sh in @($s.Shapes)) {
    if ($sh.Type -ne 16) { continue }                    # msoMedia
    $seq = $s.TimeLine.MainSequence
    for ($i = $seq.Count; $i -ge 1; $i--) { if ($seq.Item($i).Shape.Name -eq $sh.Name) { $seq.Item($i).Delete() } }
    $eff = $seq.AddEffect($sh, 83, 0, 2)                 # msoAnimEffectMediaPlay，msoAnimTriggerWithPrevious
    $eff.Timing.TriggerDelayTime = 0
    $sh.AnimationSettings.PlaySettings.StopAfterSlides = 1
    Write-Output ("slide {0}: {1} autoplay" -f $s.SlideIndex, $sh.Name)
  }
  $fades = @($s.Shapes) | Where-Object { $_.Name -like 'fadein-*' } | Sort-Object Name
  $first = $true
  foreach ($sh in $fades) {
    $eff = $s.TimeLine.MainSequence.AddEffect($sh, 10, 0, 3)   # msoAnimEffectFade，msoAnimTriggerAfterPrevious
    $eff.Timing.Duration = 0.5
    $eff.Timing.TriggerDelayTime = $(if ($first) { 0.8 } else { 0.3 })
    $first = $false
  }
  if ($fades.Count) { Write-Output ("slide {0}: {1} fade-ins" -f $s.SlideIndex, $fades.Count) }
}
$pres.Save()
$pres.Close()
if ($app.Presentations.Count -eq 0) { $app.Quit() }
