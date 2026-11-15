param([switch]$IncludeDeath)

# Deterministic correction of existing sprites; never regenerate or move pixels.
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
public static class PencilCorrection {
    public static void Apply(Bitmap image, Rectangle cell) {
        for (int y = cell.Top; y < cell.Bottom; y++)
        for (int x = cell.Left; x < cell.Right; x++) {
            Color c = image.GetPixel(x, y);
            if (c.A == 0) continue;
            double brightness = (c.R + c.G + c.B) / 3.0;
            // Keep ivory fill intact; retain graded pencil opacity and grain.
            double ink = Math.Max(0, Math.Min(1, (200 - brightness) / 100));
            if (ink == 0) continue;
            int alpha = (int)Math.Round(255 * Math.Pow(c.A / 255.0, 1 - 0.35 * ink));
            double shade = 1 - 0.12 * ink;
            image.SetPixel(x, y, Color.FromArgb(alpha,
                (int)Math.Round(c.R * shade), (int)Math.Round(c.G * shade),
                (int)Math.Round(c.B * shade)));
        }
    }
}
'@

$metadata = Get-Content (Join-Path $PSScriptRoot 'player-sprites.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$original = [Drawing.Bitmap]::new((Join-Path $PSScriptRoot 'player-character.png'))
$corrected = $original.Clone([Drawing.Rectangle]::new(0, 0, $original.Width, $original.Height), [Drawing.Imaging.PixelFormat]::Format32bppArgb)
try {
    $names = @('crouch_lowered', 'crouch_horizontal', 'crouch_walk_lowered', 'crouch_walk_horizontal')
    if ($IncludeDeath) { $names += 'death' }
    foreach ($name in $names) {
        foreach ($frame in $metadata.animations.$name.frames) {
            $r = $frame.rect
            [PencilCorrection]::Apply($corrected, [Drawing.Rectangle]::new($r[0], $r[1], $r[2], $r[3]))
        }
    }
    $corrected.Save((Join-Path $PSScriptRoot 'player-character-refined.png'), [Drawing.Imaging.ImageFormat]::Png)
    # Before/after contact sheet; standing reference is intentionally unchanged.
    $preview = [Drawing.Bitmap]::new(1000, 400)
    $graphics = [Drawing.Graphics]::FromImage($preview)
    try {
        $graphics.Clear([Drawing.Color]::FromArgb(248, 244, 232))
        $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $samples = @($metadata.animations.idle_lowered.frames[0], $metadata.animations.crouch_lowered.frames[0],
            $metadata.animations.crouch_horizontal.frames[0], $metadata.animations.death.frames[3], $metadata.animations.death.frames[7])
        for ($i = 0; $i -lt $samples.Count; $i++) {
            $r = $samples[$i].rect
            $sourceRect = [Drawing.Rectangle]::new($r[0], $r[1], $r[2], $r[3])
            $graphics.DrawImage($original, [Drawing.Rectangle]::new($i * 200, 0, 200, 200), $sourceRect, [Drawing.GraphicsUnit]::Pixel)
            $graphics.DrawImage($corrected, [Drawing.Rectangle]::new($i * 200, 200, 200, 200), $sourceRect, [Drawing.GraphicsUnit]::Pixel)
        }
        $preview.Save((Join-Path $PSScriptRoot 'preview-line-correction.png'), [Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $preview.Dispose() }
    Write-Output "Corrected: $($names -join ', '); original pixels, frame positions and anchors preserved."
} finally { $corrected.Dispose(); $original.Dispose() }
