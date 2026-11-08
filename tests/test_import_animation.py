"""Universal input routes through existing Visual Atlas frame packing and QA."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageDraw
from tools.import_animation import decode_animated, decode_video, main


class AnimationImportTests(unittest.TestCase):
    def test_apng_and_webp_preserve_frame_time_and_alpha(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frames = []
            for x in (5, 13, 21):
                img = Image.new('RGBA', (48, 48))
                ImageDraw.Draw(img).rectangle((x, 4, x+10, 30), fill=(240, 50, 60, 255))
                frames.append(img)
            for ext in ('.png', '.webp'):
                path = root / ('sample' + ext)
                frames[0].save(path, save_all=True, append_images=frames[1:],
                               duration=[100, 150, 200], loop=0)
                result, delays, _ = decode_animated(path)
                self.assertEqual(len(result), 3)
                self.assertEqual(delays, [100, 150, 200])
                self.assertEqual(result[0].getpixel((0,0))[3], 0)
                target = root / ('result' + ext + '.zip')
                self.assertEqual(main([str(path), '--out', str(root/'review'), '--pack', str(target),
                                       '--approve-visual', '--id', 'test.walk']), 0)
                with ZipFile(target) as archive:
                    manifest=json.loads(archive.read('manifest.json'))
                    self.assertEqual(manifest['assets'][-1]['kind'], 'sequence')
                    self.assertEqual(len(manifest['assets'][-1]['frames']), 3)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg not installed')
    def test_video_alpha_gate_and_opaque_scene_option(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            video=root/'scene.mp4'
            subprocess.run(['ffmpeg','-loglevel','error','-y','-f','lavfi',
                '-i','testsrc2=size=64x64:rate=16','-t','0.5','-pix_fmt','yuv420p',str(video)],check=True)
            frames, delays, _=decode_video(video,16,0,0.5)
            self.assertEqual(len(frames),8)
            self.assertEqual(sum(delays),500)
            out=root/'review'
            self.assertEqual(main([str(video),'--out',str(out),'--fps','16','--seconds','0.5']),1)
            self.assertEqual(main([str(video),'--out',str(out),'--fps','16','--seconds','0.5',
                '--allow-opaque','--pack',str(root/'scene.zip'),'--id','scene.demo',
                '--approve-visual']),0)
            with ZipFile(root/'scene.zip') as z:
                manifest=json.loads(z.read('manifest.json'))
                self.assertEqual(len(manifest['assets'][-1]['frames']),8)
                self.assertEqual(sum(f['duration_ms'] for f in manifest['assets'][-1]['frames']),500)

    def test_rejects_unsupported_and_still(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            still=root/'still.png';Image.new('RGBA',(32,32)).save(still)
            with self.assertRaisesRegex(ValueError,'Expected animated'):
                decode_animated(still)
            with self.assertRaises(SystemExit):
                main([str(still),'--out',str(root/'review'),'--pack',str(root/'out.zip')])


if __name__=='__main__':unittest.main()
