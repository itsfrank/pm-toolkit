# Catalogs

One file per space or collection that `wiki-expand` surveyed (`<space>.md`): a line for every
page in scope, ingested or not, so agents can find a page the wiki hasn't read yet.
`python3 tools/wiki.py catalog-search <terms>` searches them. Format: see `wiki/README.md`.
