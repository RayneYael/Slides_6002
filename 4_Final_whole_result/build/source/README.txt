exploration_slides_source.pptx  -  BUILD INPUT, NOT A DELIVERABLE

build_final_deck.py opens this file and uses its 7 slides as the "Exploration of
Dataset" section of the final deck, then re-styles them (banner, palette, fonts,
animation) and appends every other slide around them. Deleting it makes
build_final_deck.py fail with PackageNotFoundError.

It used to sit next to the final deck in 4_Final_whole_result/, which is why it
kept looking like a stale leftover; it now lives here so the delivery folder holds
only CA6002_Group30_Final_Presentation.pptx.

If it is ever lost, regenerate it from the finished deck:  python extract_src.py
