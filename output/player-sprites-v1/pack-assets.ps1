Add-Type -AssemblyName System.Drawing
$root = $PSScriptRoot
$srcRoot = 'C:/Users/unico/.codex/generated_images/01a1de59-4478-7823-86f0-78e48b7ead7e'
$files = @{ A='exec-f51cd477-b758-4e97-bfef-6719fe93088d.png'; B='exec-8321a706-2a0d-4e64-a24f-add623dd79a7.png'; C='exec-830c8681-9f58-4119-ac0d-48a4743028ea.png'; D='exec-0c9db9b2-c6f6-43f1-8a2f-14339fdc1624.png'; FX='exec-3c4a4b09-4adf-40e6-bb94-025a0db5a0c4.png' }
foreach($key in $files.Keys){Copy-Item -LiteralPath (Join-Path $srcRoot $files[$key]) -Destination (Join-Path $root "source/$key.png") -Force}
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Drawing2D;
public class SpritePack {
public static List<int[]> Segments(int[] counts,int threshold,int gap){
 var list=new List<int[]>();int start=-1,last=-1;
 for(int i=0;i<counts.Length;i++){if(counts[i]>=threshold){if(start<0)start=i;last=i;}else if(start>=0 && i-last>gap){if(last-start>=5)list.Add(new[]{start,last});start=-1;}}
 if(start>=0 && last-start>=5)list.Add(new[]{start,last});return list;
}
public static Rectangle[] Rows(Bitmap b){
 int[] n=new int[b.Height];for(int y=0;y<b.Height;y++)for(int x=0;x<b.Width;x++)if(b.GetPixel(x,y).A>80)n[y]++;
 var ss=Segments(n,6,13);var rows=new List<Rectangle>();foreach(var s in ss)rows.Add(new Rectangle(0,Math.Max(0,s[0]-3),b.Width,Math.Min(b.Height-1,s[1]+3)-Math.Max(0,s[0]-3)+1));return rows.ToArray();
}
public static Rectangle[] Frames(Bitmap b,Rectangle row){
 int[] n=new int[b.Width];for(int x=0;x<b.Width;x++)for(int y=row.Top;y<row.Bottom;y++)if(b.GetPixel(x,y).A>80)n[x]++;
 var ss=Segments(n,2,16);var fs=new List<Rectangle>();foreach(var s in ss)fs.Add(new Rectangle(Math.Max(0,s[0]-3),row.Y,Math.Min(b.Width-1,s[1]+3)-Math.Max(0,s[0]-3)+1,row.Height));return fs.ToArray();
}
public static int[] Pack(Bitmap source, Rectangle crop,Bitmap target,int col,int row,string mode){
 int hx0=crop.Right,hy0=crop.Bottom,hx1=-1,hy1=-1;
 bool[,] bright=new bool[crop.Width,crop.Height];bool[,] seen=new bool[crop.Width,crop.Height];int largest=0;
 for(int y=0;y<crop.Height;y++)for(int x=0;x<crop.Width;x++){var c=source.GetPixel(x+crop.X,y+crop.Y);bright[x,y]=c.A>210&&c.R>195&&c.G>185&&c.B>165;}
 for(int y=0;y<crop.Height;y++)for(int x=0;x<crop.Width;x++){
 if(!bright[x,y]||seen[x,y])continue;
 var q=new Queue<Point>();q.Enqueue(new Point(x,y));seen[x,y]=true;int count=0,l=x,t=y,r=x,d=y;
 while(q.Count>0){var p=q.Dequeue();count++;l=Math.Min(l,p.X);t=Math.Min(t,p.Y);r=Math.Max(r,p.X);d=Math.Max(d,p.Y);
 foreach(var v in new[]{new Point(p.X-1,p.Y),new Point(p.X+1,p.Y),new Point(p.X,p.Y-1),new Point(p.X,p.Y+1)}){if(v.X>=0&&v.Y>=0&&v.X<crop.Width&&v.Y<crop.Height&&!seen[v.X,v.Y]&&bright[v.X,v.Y]){seen[v.X,v.Y]=true;q.Enqueue(v);}}
 }
 if(count>largest){largest=count;hx0=l+crop.X;hy0=t+crop.Y;hx1=r+crop.X;hy1=d+crop.Y;}
 }
 float diameter=hx1>=hx0?Math.Max(hx1-hx0+1,hy1-hy0+1):32;
 float scale=40f/diameter;
 if(mode=="fx")scale=Math.Min(210f/crop.Width,210f/crop.Height);
 float w=crop.Width*scale,h=crop.Height*scale;
 if(w>224||h>224){scale*=Math.Min(224/w,224/h);w=crop.Width*scale;h=crop.Height*scale;}
 float xoff=128-w/2,yoff=220-h;
 if(mode=="air") {xoff=128-((hx0+hx1)/2f-crop.X)*scale;yoff=80-(hy0-crop.Y)*scale;}
 if(mode=="ground"){xoff=128-((hx0+hx1)/2f-crop.X)*scale;}
 if(mode=="tumble"||mode=="fx"){xoff=128-w/2;yoff=150-h/2;}
 if(mode=="fx")yoff=128-h/2;
 xoff=Math.Max(8,Math.Min(248-w,xoff));yoff=Math.Max(8,Math.Min(248-h,yoff));
 using(var g=Graphics.FromImage(target)){g.CompositingMode=CompositingMode.SourceCopy;g.InterpolationMode=InterpolationMode.HighQualityBicubic;g.PixelOffsetMode=PixelOffsetMode.HighQuality;g.DrawImage(source,new RectangleF(col*256+xoff,row*256+yoff,w,h),crop,GraphicsUnit.Pixel);}
 return new[]{(int)Math.Round(xoff),(int)Math.Round(yoff),(int)Math.Round(w),(int)Math.Round(h)};
}
public static int[] Muzzle(Bitmap b,int col,int row,string aim){
 int bx=col*256,by=row*256;int best=-99999,mx=128,my=150;
 for(int y=8;y<235;y++)for(int x=8;x<248;x++){var c=b.GetPixel(bx+x,by+y);if(c.A<100||c.R>160||c.G>160||c.B>160)continue;
 bool ok=aim=="up"?x>=134:aim=="horizontal"?y>=100&&y<=180:aim=="diagonal"?x>=135&&y<=150:x>=140;
 if(!ok)continue;int score=aim=="up"?-y*4:aim=="diagonal"?x-y:x*4;if(score>best){best=score;mx=x;my=y;}}
 return new[]{mx,my};
}
}
'@
$layouts = @(
@('A',0,'idle_lowered',4,6,$true,'ground','lowered'),
@('A',1,'idle_horizontal',4,6,$true,'ground','horizontal'),
@('A',2,'idle_up',4,6,$true,'ground','up'),
@('A',3,'run_lowered',8,12,$true,'ground','lowered'),
@('A',4,'run_horizontal',8,12,$true,'ground','horizontal'),
@('A',5,'run_diagonal',8,12,$true,'ground','diagonal'),
@('B',0,'jump_rise_lowered',2,8,$false,'air','lowered'),
@('B',1,'jump_rise_horizontal',2,8,$false,'air','horizontal'),
@('B',2,'jump_rise_up',2,8,$false,'air','up'),
@('B',3,'jump_rise_diagonal',2,8,$false,'air','diagonal'),
@('B',4,'fall_lowered',2,8,$true,'air','lowered'),
@('B',5,'fall_horizontal',2,8,$true,'air','horizontal'),
@('B',6,'fall_up',2,8,$true,'air','up'),
@('B',7,'fall_diagonal',2,8,$true,'air','diagonal'),
@('C',0,'crouch_lowered',4,6,$true,'ground','lowered'),
@('C',1,'crouch_horizontal',4,6,$true,'ground','horizontal'),
@('C',2,'crouch_walk_lowered',8,10,$true,'ground','lowered'),
@('C',3,'crouch_walk_horizontal',8,10,$true,'ground','horizontal'),
@('C',4,'hurt',2,16,$false,'ground','none'),
@('C',5,'death',8,12,$false,'ground','none'),
@('D',0,'parry_attempt',4,25,$false,'tumble','none'),
@('D',1,'parry_success_launch',3,20,$false,'tumble','none'),
@('D',2,'recoil_set_a',8,20,$false,'ground','mixed'),
@('D',3,'recoil_set_b',8,20,$false,'ground','mixed')
)
$images=@{};$rows=@{}
foreach($key in $files.Keys){$images[$key]=[System.Drawing.Bitmap]::new((Join-Path $root "source/$key.png"));$rows[$key]=[SpritePack]::Rows($images[$key]);Write-Output "$key rows=$($rows[$key].Count)"}
$atlas=[System.Drawing.Bitmap]::new(2048,6144,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$animations=[ordered]@{}
$frameTotal=0
for($r=0;$r -lt $layouts.Count;$r++){
$l=$layouts[$r];$key=$l[0];$rects=[SpritePack]::Frames($images[$key],$rows[$key][$l[1]])
if($rects.Count -ne $l[3]){throw "$($l[2]) expected $($l[3]) frames, detected $($rects.Count)"}
$frames=@()
for($c=0;$c -lt $rects.Count;$c++){
$mode=$l[6];$aim=$l[7]
if($r -eq 22){$aim=@('horizontal','up','horizontal','diagonal','horizontal','up','diagonal','horizontal')[$c];if($c -in @(4,5,6)){$mode='air'}}
if($r -eq 23){$aim=@('horizontal','horizontal','horizontal','up','diagonal','horizontal','horizontal','horizontal')[$c];if($c -in @(2,3,4)){$mode='air'}}
$bounds=[SpritePack]::Pack($images[$key],$rects[$c],$atlas,$c,$r,$mode)
$muzzle=if($aim -eq 'none'){$null}else{[SpritePack]::Muzzle($atlas,$c,$r,$aim)}
$frames+= [ordered]@{rect=@(($c*256),($r*256),256,256);pico2d_clip_rect=@(($c*256),(6144-($r+1)*256),256,256);duration_seconds=(1.0/$l[4]);foot_anchor=@(128,220);rotation_pivot=@(128,150);content_bounds=$bounds;muzzle=$muzzle;aim=$aim;muzzle_precision='automatic silhouette estimate; validate before gameplay integration';source_rect=@($rects[$c].X,$rects[$c].Y,$rects[$c].Width,$rects[$c].Height)}
$frameTotal++
}
$animations[$l[2]]=[ordered]@{frame_count=$rects.Count;fps=$l[4];loop=$l[5];hold_last_frame=($l[2] -eq 'death');aim=$l[7];frames=$frames}
}
$atlas.Save((Join-Path $root 'player-character.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$recoils=[ordered]@{}
$recoilNames=@('idle_horizontal','idle_up','run_horizontal_left_contact','run_diagonal','jump_rise_horizontal','jump_rise_up','jump_rise_diagonal','crouch_horizontal','run_horizontal_right_contact','run_horizontal_right_contact_alternate','fall_horizontal','fall_up','fall_diagonal','crouch_walk_horizontal_left_contact','crouch_walk_horizontal_right_contact','idle_horizontal_alternate')
for($i=0;$i -lt 16;$i++){
$set=if($i -lt 8){'recoil_set_a'}else{'recoil_set_b'}
$fr=$animations[$set].frames[$i%8]
$recoils[$recoilNames[$i]]=[ordered]@{frame_count=1;fps=20;loop=$false;hold_last_frame=$false;after='resume base animation at current movement phase';frames=@($fr)}
}
$animations.Remove('recoil_set_a');$animations.Remove('recoil_set_b')
$fx=[System.Drawing.Bitmap]::new(1024,512,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$effects=[ordered]@{}
for($r=0;$r -lt 2;$r++){
$expected=if($r -eq 0){4}else{3}
$rects=@()
for($c=0;$c -lt $expected;$c++){ $sx=[int][Math]::Floor($c*$images['FX'].Width/4);$sy=[int][Math]::Floor($r*$images['FX'].Height/2);$sw=[int][Math]::Floor(($c+1)*$images['FX'].Width/4)-$sx;$sh=[int][Math]::Floor(($r+1)*$images['FX'].Height/2)-$sy;$rects += [System.Drawing.Rectangle]::new($sx,$sy,$sw,$sh) }
if($rects.Count -ne $expected){throw "FX row$r detected $($rects.Count)"}
$ff=@()
for($c=0;$c -lt $expected;$c++){
$bounds=[SpritePack]::Pack($images['FX'],$rects[$c],$fx,$c,$r,'fx')
$ff+= [ordered]@{rect=@(($c*256),($r*256),256,256);pico2d_clip_rect=@(($c*256),(512-($r+1)*256),256,256);attachment_anchor=@(128,128);character_attachment=@(128,150);duration_seconds=$(if($r -eq 0){0.04}else{0.05});content_bounds=$bounds}
}
$name=if($r -eq 0){'parry_attempt_trail'}else{'parry_success_flash'}
$effects[$name]=[ordered]@{frame_count=$expected;fps=$(if($r -eq 0){25}else{20});loop=$false;frames=$ff}
}
$fx.Save((Join-Path $root 'player-parry-fx.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$standingHeight=$animations['idle_lowered'].frames[0].content_bounds[3]
$metadata=[ordered]@{
schema_version=3;status='generated_asset_set';character_image='player-character.png';character_image_size=@(2048,6144);effect_image='player-parry-fx.png';effect_image_size=@(1024,512);cell_size=@(256,256);character_frame_count=$frameTotal;coordinate_system='top-left origin; x right, y down. All anchors are local cell coordinates. pico2d_clip_rect uses bottom-left origin.';facing='right; left facing uses horizontal mirror, mirrored point x = 256 - x';head_fill_target='#F8F4E8';head_fill_note='Generated ivory has pencil texture and slight color variation, not exact solid RGB.';game_reference=@{standing_size=@(36,56);crouching_size=@(36,28);fire_interval=0.15;invincibility_time=1.0;parry_window=0.16};animations=$animations;effects=$effects;
recoil_animations=$recoils;aliases=@{parry_failure='fall_lowered or current aimed fall';run_diagonal_recoil_right_contact='recoil_animations.run_diagonal'};render_reference=@{uniform_scale=(56.0/$standingHeight);standing_source_height=$standingHeight;draw_cell_size=@((256.0*56/$standingHeight),(256.0*56/$standingHeight));foot_anchor=@(128,220);note='Scale the entire cell uniformly and register foot anchor to player bottom; do not force full cell to 36x56. Collisions remain game-defined.'};
transitions=@{hurt='resume current locomotion after 0.125 seconds; use game invincibility blink without baked transparency';death='play once then hold final frame';parry_attempt='four frames at 0.04s each; success interrupts immediately';parry_success_launch='play 0.15s curled launch, then jump rise while vy>0, fall when vy<=0; world motion comes from physics';parry_failure='no recoil: return to active fall pose after 0.16s';jump_rise='hold last pose until apex then choose matching fall aim'};
limitations=@('AI generated run cycles approximate half-cycle symmetry; anatomical near/far leg crossing is not mechanically guaranteed.','Muzzle locations are silhouette-derived estimates, not manually calibrated gun bore measurements.','Per-frame head and sole alignment reduces drift but limb proportions and pencil strokes retain generated variation.');game_code_modified=$false;generation_mode='built-in image_gen';prompts='prompts.txt'
}
$metadata | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 (Join-Path $root 'player-sprites.json')
$atlas.Dispose();$fx.Dispose();foreach($im in $images.Values){$im.Dispose()}
Write-Output "Packed $frameTotal character frames and 7 effect frames."

