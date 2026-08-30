# Spatial EDA — key stats (2021)

Generated from Final_data panel.

## Concentration (Point 1)

- Top 10 share of global CO₂: **69.8%**
- Top 20 share: **81.2%**
- Regional share: Asia 59.8% · North America 17.2% · Europe 14.6% · Africa 4.1% · South America 3.1% · Oceania 1.2%

## Map coverage (choropleths / globe)

- Basemap: Natural Earth **110m** admin-0
- Panel entities (2021): **213**
- Join onto map polygons: **169 / 213**
- Emissions on map: **~99.6%** of global Mt
- Omitted: **~0.4%** of Mt — mostly small islands/territories (e.g. Singapore, Bahrain, Hong Kong) not present at 110m
- **Top10 / Top20 / treemap / bars use the full panel**; map colour only shows joined entities

## Scale vs intensity (Point 2)

- See figure annotations for Spearman ρ and Top10∩Top10 overlap (printed when running `fig2b`).
- Per-capita choropleth colour clipped at **P98** so a few Gulf outliers do not flatten the scale.

## Fuel × region (Point 3)

- χ² independence (region × dominant fuel): chi2 ≈ 56.9, p ≈ 1.4e-08, Cramér's V ≈ 0.37 (medium association)

## Claim supported

排放大国不能被简单定义成同一种国家 — three global geographies (tonnes / intensity / fuel) do not align.
