"""Lab Notes uses one authored registry and safe generated HTML."""
import json
import tempfile
import unittest
from pathlib import Path
from shutil import copytree
from tools.blog import render_blog


class BlogTests(unittest.TestCase):
    def source(self, root):
        repo=Path(__file__).resolve().parents[1]
        copytree(repo/'blog',root/'blog')
        (root/'web').mkdir()
        (root/'web'/'blog.html').write_bytes((repo/'web'/'blog.html').read_bytes())
        return root/'blog'/'posts.json'

    def test_build_and_sanitization(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest=self.source(root);dest=root/'site';dest.mkdir()
            self.assertEqual(render_blog(root,dest),1)
            html=(dest/'blog.html').read_text()
            self.assertIn('Exploring Better Character Animation',html)
            self.assertIn('sky-prototype.html',html)
            record=json.loads(manifest.read_text())
            record['posts'][0]['paragraphs'].append('<img src=x onerror=alert(1)>')
            manifest.write_text(json.dumps(record))
            render_blog(root,dest)
            html=(dest/'blog.html').read_text()
            self.assertNotIn('<img src=x onerror',html)
            self.assertIn('&lt;img src=x onerror',html)

    def test_unsafe_link_and_missing_media_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest=self.source(root);dest=root/'site';dest.mkdir()
            record=json.loads(manifest.read_text())
            record['posts'][0]['links'][0]['url']='javascript:alert(1)'
            manifest.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                render_blog(root,dest)
            record['posts'][0]['links'][0]['url']='sky-prototype.html'
            record['posts'][0]['media']={'path':'blog-media/not-here.mp4','caption':'Walk preview'}
            manifest.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'Missing'):
                render_blog(root,dest)


if __name__=='__main__':unittest.main()
