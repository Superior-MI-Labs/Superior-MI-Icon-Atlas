# Visual Atlas Lab Notes

Edit `blog/posts.json` to publish a new entry on the static **Lab Notes** tab. The site builder renders the articles at build time: no separate CMS, backend, dynamic HTML, or asset catalog.

Each post has a unique `slug`, an ISO `date`, `title`, `summary`, and an array of plain-text `paragraphs`. Optional `links` use a human-readable `label` and either HTTPS or a local `.html` page. Optional `media` uses a local `blog-media/*.mp4|webm|png|webp|gif` file and a `caption`; the source file must live under `web/blog-media/` and is copied only when referenced. Keep videos below 25 MB. The builder escapes all text and rejects unsafe link paths.

Order is newest first, automatically; keep completed experiments factual, label prototypes, and don't publish unapproved character artwork or third-party media without rights review. Existing public Sky prototype links can be used without republishing textures.

Run `python3 -m unittest tests.test_blog` (or `bash RUN-ALL.sh`) before publishing.
