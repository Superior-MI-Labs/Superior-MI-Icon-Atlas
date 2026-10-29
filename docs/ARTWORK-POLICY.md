# Artwork rights and inclusion policy

## Public default: original-only

An icon is eligible for default distribution only if it has an inspectable origin method, source construction materials, no third-party glyph/path/font/brand dependency, and a reviewed license classification. AI-assisted rendering alone is not proof of exclusive ownership; human review is a separate gate.

### Quarantined

- Material Design Icons (Pictogrammers) direct and composite derivatives: generally Apache-2.0, but **third-party authored**. May be offered separately with notices, not inside original-only exports.
- Font Awesome 4.7 vector/font derivatives: check OFL terms and keep with applicable license notices if separately distributed.
- Trademarked logos/flags/emblems: independent trademark and accurate-representation review.
- Legacy automatically generated and abbreviation-first assets: provenance and/or design quality not yet verified.

## Independently designed replacements

Make new visual designs using common ideas (e.g., circles and branches to suggest a graph) with fresh construction, proportions and layout. Do not trace, import, path-transform, or mechanically simplify another illustrator's shapes and call the result original. Similar subject matter is fine; copied protectable expression is not.

Every new sheet must include: `artwork_source`, `source_kind`, `license`, `third_party_glyphs`, `human_visual_review`, per-cell `crop_rgba_sha256`, sheet `sha256`, `tags`, `synonyms`, exact `rect_px` and `uv`. Older IDs cannot be overwritten without an explicit compatibility transition.
