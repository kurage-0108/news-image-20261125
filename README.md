# The World in One Page — 25 November 2026

An entry for the make.fun bounty **"Sum up 25 November's world news in one
image"** (`news-image-20261125`).

The entry is a program that writes one image to `/output/entry.png`: a
single-page broadsheet newspaper summing up the world news of Wednesday,
25 November 2026.

## What the image shows

- **37 stories** as reported that day: three front-page leads (the Strait of
  Hormuz tanker strikes, Pakistan's first astronaut reaching China's Tiangong
  station aboard Shenzhou-24, and overnight strikes across Ukraine) plus 28
  briefs in four regional columns and a six-item sport brief.
- A **world map** pinned with the day's story locations (key pins labelled),
  and a west-to-east **timeline strip** giving each dateline's local time at
  12:00 UTC (Washington 07:00 → Cartagena → London → Abuja → Berlin → Kyiv →
  Khartoum → Gaza → Riyadh → Delhi → Jakarta → Beijing → Tokyo → Canberra
  23:00).
- A **drawn scene**: the Strait of Hormuz at dawn, with two tankers burning
  after striking mines in the night.
- A **markets ticker** (Nikkei −2.76%, Nvidia −7%, Kospi −6.2%, Sensex +1.8%,
  Brent $87.49, …) with rises and falls colour-coded.

All stories were compiled on 25 Nov 2026 from that day's reporting by AP,
Reuters, BBC News, Just Security, SCMP, The Japan Times, The Economic Times,
AfricaFrontPage, Yeni Şafak, Anadolu and One Turn News. Headlines and one-line
summaries only — no article text is reproduced.

## Run it

```sh
python3 main.py   # Python 3.13, standard library only, no network
```

`main.py` copies the bundled `entry.png` (1024×1024 PNG, under 1 MiB) to
`/output/entry.png`. Because it only copies a fixed file, repeated runs write
byte-identical output.

## How the image was made

The page was typeset programmatically with Python and Pillow: rendered at
2048×2048 and downscaled to 1024×1024 so the dense column text stays crisp.
The map is drawn from Natural Earth country polygons (via the
`world.geo.json` dataset). Sources live in `src/`:

- `src/build_image.py` — the layout/rendering program
- `src/news.json` — the day's stories used on the page
- `src/world.geo.json` — country outlines for the map

## License

MIT — see `LICENSE`.
