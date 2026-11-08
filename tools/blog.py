"""Build the static Lab Notes page from one authored JSON post collection."""
from __future__ import annotations
import json
import re
from datetime import date
from html import escape
from pathlib import Path
from shutil import copy2

SCHEMA = 'smi-lab-notes/1'
LINK = re.compile(r'(?:https://[^\s"<>]+|[a-z0-9][a-z0-9/_-]*\.html)\Z')
MEDIA = re.compile(r'blog-media/[a-z0-9][a-z0-9._-]*\.(?:mp4|webm|png|webp|gif)\Z')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def render_blog(root: Path, dest: Path):
    data = json.loads((root / 'blog' / 'posts.json').read_text(encoding='utf-8'))
    if data.get('schema') != SCHEMA or not isinstance(data.get('posts'), list) or len(data['posts']) > 50:
        raise ValueError('Invalid Lab Notes post registry')
    seen, output = set(), []
    for post in sorted(data['posts'], key=lambda p: p['date'], reverse=True):
        slug, heading, summary, paragraphs = post['slug'], post['title'], post['summary'], post['paragraphs']
        date.fromisoformat(post['date'])
        if not SLUG.fullmatch(slug) or slug in seen:
            raise ValueError('Invalid or duplicate Lab Notes slug')
        seen.add(slug)
        if not all(isinstance(s, str) and 0 < len(s) <= 2000 for s in [heading, summary, *paragraphs]):
            raise ValueError('Lab Notes content must be plain text within size limits')
        if not isinstance(paragraphs, list) or not paragraphs or len(paragraphs) > 12:
            raise ValueError('Lab Notes article needs 1..12 paragraphs')
        links = post.get('links', [])
        if not isinstance(links, list) or len(links) > 8:
            raise ValueError('Too many Lab Notes links')
        hrefs = []
        for item in links:
            if not isinstance(item, dict) or not LINK.fullmatch(item['url']):
                raise ValueError('Unsafe Lab Notes link')
            hrefs.append(f'<a href="{escape(item["url"], quote=True)}" rel="noopener noreferrer">{escape(item["label"])}</a>')
        media_html = ''
        media = post.get('media')
        if media is not None:
            path = media['path']
            if not MEDIA.fullmatch(path):
                raise ValueError('Unsafe Lab Notes media path')
            source = root / 'web' / path
            if not source.is_file() or source.is_symlink() or source.stat().st_size > 25 * 1024 * 1024:
                raise ValueError('Missing or oversized Lab Notes media')
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, target)
            if source.suffix in ('.mp4', '.webm'):
                media_html = (f'<figure><video controls muted loop playsinline preload="metadata" '
                              f'src="{escape(path, quote=True)}"></video>'
                              f'<figcaption>{escape(media["caption"])}</figcaption></figure>')
            else:
                media_html = (f'<figure><img loading="lazy" src="{escape(path, quote=True)}" '
                              f'alt="{escape(media["caption"], quote=True)}">'
                              f'<figcaption>{escape(media["caption"])}</figcaption></figure>')
        content = ''.join('<p>' + escape(paragraph) + '</p>' for paragraph in paragraphs)
        link_html = '<p class="note-links">' + ' · '.join(hrefs) + '</p>' if hrefs else ''
        output.append(f'<article id="{slug}" class="note"><time datetime="{post["date"]}">{post["date"]}</time>'
                      f'<h2>{escape(heading)}</h2><p class="note-summary">{escape(summary)}</p>'
                      + media_html + content + link_html + '</article>')
    template = (root / 'web' / 'blog.html').read_text(encoding='utf-8')
    if template.count('<!-- BLOG_POSTS -->') != 1:
        raise ValueError('Lab Notes HTML template missing its single content slot')
    target = dest / 'blog.html'
    target.write_text(template.replace('<!-- BLOG_POSTS -->', '\n'.join(output) if output else '<p>No entries published yet.</p>'), encoding='utf-8')
    return len(output)
