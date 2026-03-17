# Local Setup

```bash
./make.sh setup
./make.sh test
python -m drts_tsn.cli.main --help
```

Editable installation exposes the `drts` console command. The repository also includes `sitecustomize.py` so local module execution works from the repository root before installation.
