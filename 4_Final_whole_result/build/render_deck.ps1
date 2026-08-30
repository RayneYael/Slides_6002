$ErrorActionPreference = 'Stop'
$src = "C:\Users\user\Desktop\Overall_Data Visual Assignment\4_Final_whole_result\CA6002_Group30_Final_Presentation.pptx"
$outdir = "C:\Users\user\Desktop\Overall_Data Visual Assignment\4_Final_whole_result\build\render"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
Get-ChildItem $outdir -Filter *.png | Remove-Item -Force
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open($src, $true, $false, $false)  # ReadOnly, Untitled, WithWindow=false
$i = 1
foreach ($slide in $pres.Slides) {
    $path = Join-Path $outdir ("slide_{0:d2}.png" -f $i)
    $slide.Export($path, "PNG", 1600, 900)
    $i++
}
$pres.Close()
$pp.Quit()
Write-Output "exported $($i-1) slides"
