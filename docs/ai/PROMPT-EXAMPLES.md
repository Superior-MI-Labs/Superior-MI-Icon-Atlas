# Short creator requests to use with the AI guide

These are requests for the **production agent**, not image prompts. Give the agent [START-HERE.md](START-HERE.md) and a natural request such as:

- **Animated interface pack:** “Make a fantasy HUD pack with a nine-slice frame, a health bar, and an animated mana bar. Define normalized value inputs, compatible fill slots, and Health/Mana presets. Make everything work on a 320×64 UI canvas.”
- **Character collection:** “Create a small pixel-art drone with idle, moving, charging and damaged states. Use multiple texture sheets if useful; give each animation sensible frames/FPS and set idle as default.”
- **Animated icon:** “Make a 96px monoline shield icon with a looping cyan glow and an optional red warning badge. White tintable base, transparent background.”
- **Website banner:** “Make a 1200×300 animated header with three independently animated layers, a quiet default state and a looping flourish. Use only supported Canvas/manifest effects.”
- **Potion collection:** “Make compatible glass bottles and interchangeable fluids with blue, green and purple versions; one animated fluid and three presets.”

For image generation the agent derives a short [visual brief](IMAGE-ENGINE-WORKFLOW.md); the rest belongs to assembly and QA.

**No magic phrase required:** The assistant should recover the context of your conversation, translate it into a precise working brief, select the closest working template, build real assets, test them, and return one ZIP and its QA receipt.
