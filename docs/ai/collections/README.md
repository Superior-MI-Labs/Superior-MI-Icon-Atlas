# Recipe: large multi-manifest collections and compatibility packs

**Start from:** [Potion Lab ZIP](../../demo/potions-collection.zip). One ZIP is one user-owned Bag, not necessarily one asset. It may include many texture sheets and manifest groups.

1. Partition by logical source ownership (e.g. character body, equipment, animations, GUI). Each group's manifest owns its textures and asset definitions.
2. Add one optional `collection.json` listing all pack manifests, display labels/categories and an `entry_asset` for automatic preview.
3. Keep asset IDs unique across **all** manifests and resolve cross-group references. Avoid copying one asset to every pack.
4. Define versioned compatibility interfaces and declared slot options for interchangeable parts. Do not infer compatibility from tags or being on the same texture sheet.
5. Define presets and defaults, then exercise every allowed option. Include **all** selected asset dependencies in the ZIP/export.
6. Run [release checklist](../RELEASE-CHECKLIST.md), and verify the entire Bag opens and group navigation works.

For a large animation character with 20 sheets, the user should open **one** Bag card, browse named animations/states, and preview the declared default without configuring anything.


## Required collection / compatible slot pipeline

1. Inventory every pack, manifest, texture, dependency, entry asset and asset count.
2. Define versioned slot interfaces (logical sizes, pivots, masks), not similarity by tags.
3. Check every accepted candidate against the declared slot contract, geometry and ownership.
4. Validate defaults and each preset, including animated/static swaps and all state inputs.
5. Reject unknown refs, cycles, incompatible versions, conflicting IDs and missing dependencies.
6. Open the whole ZIP as one Bag, inspect each group and entry, export/reimport, and rerun checks.
