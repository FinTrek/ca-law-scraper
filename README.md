# ca-law-scraper

## Prerequisites

You need the `PITXML` directory that contains the every law and their revisions.

This can be found by going to the Canadian Justice Laws website and going to their open FTP server that hosts the PITXML files.
(They also host a compressed archive of the directory, in the format that this script already expects, so that would be the file that I'd recommend using.)
The archive file is ~100 MB and uncompressed is ~7 GB.

You also need an empty git repository in the root of this folder called `docs`, as that is where the Markdown file will be placed and committed when being rendered.

## Run
```
source venv/bin/activate
pip install -r requirements.txt
python makehistory.py
```
...That's it, really. It takes a couple hours (at least for me on my laptop) to generate the docs directory, so I'd recommend leaving it running overnight.

## Known problems
...The code is a mess, yes.

Most of the comments in `makehistory.py` come from the generation of `docs.json`, which basically just sorts out the metadata of the files, which is used for linking different laws to others.

A lot of the code is a bunch of recursive stuff that comprises the way certain tags can be nested within each other, which mainly just involved me copying and pasting how other rendering functions handle the same sections in their own rendering function. Lost yet? So am I.

## Contributing
You're free to whatever you want to (within reason, of course). Make pull requests, make issues, go for it.
