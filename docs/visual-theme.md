# Niural-inspired presentation

The interview console follows the visual language of [Niural's public website](https://www.niural.com/), inspected on 25 September 2026. It remains clearly labelled as an interview prototype named Atlas.

## Observed reference and adaptation

| Website detail | Console adaptation |
|---|---|
| Violet-to-magenta announcement bar | Slim gradient ribbon identifying the Niural interview project |
| Near-black text on white, with light neutral borders | White navigation, white panels and subtle lavender surfaces |
| Inter body type; Inter Tight semibold headings | The same font families, bundled locally for offline use |
| Violet primary calls to action and rounded controls | Violet action buttons, pill labels, rounded inputs and dialogs |
| Spacious headings and restrained accent graphics | Clear workspace hierarchy, quiet gradients and small star details |

The rendered website's heading color was `rgb(20, 20, 23)`; its primary button used `oklch(0.569 0.2477 284.6)`. These tokens inform the stylesheet. The gradient is a visual adaptation, not a claim to reproduce an internal Niural brand specification.

Compliance outcomes retain separate red, green and amber treatments and explicit text labels. Branding does not change rule selection, review authority, historical data or calculations.

## Assets

Inter and Inter Tight are distributed under their SIL Open Font Licenses. Local WOFF2 files, license texts and source URLs are in `atlas/static/fonts/`. `scripts/fetch_theme_fonts.py` documents their acquisition from Google Fonts. The runtime uses only local assets; it makes no font-provider request.

Atlas uses its own lettermark and favicon. The company name identifies the interview context; the prototype does not present itself as a released Niural product.
