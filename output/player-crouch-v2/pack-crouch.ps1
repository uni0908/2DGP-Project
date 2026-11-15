param([switch]$WithWalk)
Add-Type -AssemblyName System.Drawing
$originalPack = Get-Content (Join-Path $PSScriptRoot '../player-sprites-v1/pack-assets.ps1') -Raw
$helper = [regex]::Match($originalPack, "(?s)TypeDefinition @'\r?\n(.*?)\r?\n'@").Groups[1].Value
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition $helper
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
public static class CrouchBounds {
    public static Rectangle Tight(Bitmap image, Rectangle crop) {
        int left=crop.Right, top=crop.Bottom, right=crop.Left, bottom=crop.Top;
        for(int y=crop.Top;y<crop.Bottom;y++) for(int x=crop.Left;x<crop.Right;x++) {
            if(image.GetPixel(x,y).A<60) continue;
            left=Math.Min(left,x);top=Math.Min(top,y);right=Math.Max(right,x);bottom=Math.Max(bottom,y);
        }
        return Rectangle.FromLTRB(Math.Max(crop.Left,left-2),Math.Max(crop.Top,top-2),
            Math.Min(crop.Right,right+3),Math.Min(crop.Bottom,bottom+3));
    }
}
'@
$atlas = [Drawing.Bitmap]::new(1024, 768, [Drawing.Imaging.PixelFormat]::Format32bppArgb)
$source = [Drawing.Bitmap]::new((Join-Path $PSScriptRoot 'crouch-all-fours-preview.png'))
$animations = [ordered]@{}

function Add-Animation($name, $image, $crops, $row, $fps) {
    $frames = @()
    for ($col = 0; $col -lt $crops.Count; $col++) {
        $crop = [CrouchBounds]::Tight($image, $crops[$col])
        $bounds = [SpritePack]::Pack($image, $crop, $atlas, $col, $row, 'ground')
        $anchorX = $bounds[0] + $bounds[2] / 2.0
        $mx = 0; $my = 0
        for ($y = 8; $y -lt 240; $y++) {
            for ($x = 8; $x -lt 248; $x++) {
                $color = $atlas.GetPixel($col * 256 + $x, $row * 256 + $y)
                if ($color.A -gt 120 -and $color.R -lt 140 -and $x -gt $mx) { $mx = $x; $my = $y }
            }
        }
        $frames += [ordered]@{
            rect = @(($col * 256), ($row * 256), 256, 256)
            pico2d_clip_rect = @(($col * 256), (768 - ($row + 1) * 256), 256, 256)
            duration_seconds = (1.0 / $fps)
            foot_anchor = @($anchorX, 220)
            content_bounds = $bounds
            muzzle = @($mx, $my)
            image = 'crouch'
        }
    }
    $animations[$name] = [ordered]@{ frames = $frames; fps = $fps; loop = $true; frame_count = $frames.Count }
}

try {
    $crops = [SpritePack]::Frames($source, [Drawing.Rectangle]::new(0, 0, $source.Width, $source.Height))
    if ($crops.Count -ne 3) { throw "Expected three reference poses, found $($crops.Count)" }
    Add-Animation 'crouch_lowered' $source @($crops[1]) 0 1
    Add-Animation 'crouch_horizontal' $source @($crops[2]) 1 1
    if ($WithWalk) {
        $walk = [Drawing.Bitmap]::new((Join-Path $PSScriptRoot 'crouch-walk-source.png'))
        try {
            $rows = [SpritePack]::Rows($walk)
            if ($rows.Count -ne 2) { throw "Expected two crawl rows, found $($rows.Count)" }
            # Four columns share each row with static rows in separate atlas files.
            $walkAtlas = [Drawing.Bitmap]::new(1024, 768, [Drawing.Imaging.PixelFormat]::Format32bppArgb)
            $staticAtlas = $atlas
            $atlas = $walkAtlas
            foreach ($row in 0, 1) {
                $crops = [SpritePack]::Frames($walk, $rows[$row])
                if ($crops.Count -ne 4) { throw "Expected four crawl frames, found $($crops.Count)" }
                $name = @('crouch_walk_lowered', 'crouch_walk_horizontal')[$row]
                Add-Animation $name $walk $crops $row 8
                foreach ($frame in $animations[$name].frames) { $frame.image = 'crouch_walk' }
            }
            $walkAtlas.Save((Join-Path $PSScriptRoot 'player-crouch-walk.png'), [Drawing.Imaging.ImageFormat]::Png)
            $atlas = $staticAtlas
            $walkAtlas.Dispose()
        } finally { $walk.Dispose() }
    }
    $atlas.Save((Join-Path $PSScriptRoot 'player-crouch.png'), [Drawing.Imaging.ImageFormat]::Png)
    $animations | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $PSScriptRoot 'player-crouch.json') -Encoding UTF8
    Write-Output "Packed $($animations.Count) crouch animations."
} finally { $source.Dispose(); $atlas.Dispose() }
