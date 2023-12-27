import json
from typing import Iterable, Optional
import click

import stix2_to_digraph.converter as converter


@click.group()
@click.option("--indent", default=4)
@click.pass_context
def main(ctx: click.Context, indent: int):
    ctx.obj = {"indent": indent}


@main.command("alias-map")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--allow-deprecated/--no-deprecated", default=False, show_default=True)
@click.option("--allow-revoked/--no-revoked", default=False, show_default=True)
@click.option("--include-names/--no-names", default=True, show_default=True)
@click.option("--lowercase/--no-lowercase", default=True, show_default=True)
@click.pass_context
def get_aliases(
    ctx: click.Context,
    paths: Iterable[str],
    allow_deprecated: bool,
    allow_revoked: bool,
    include_names: bool,
    lowercase: bool,
):
    """
    Get node aliases.
    """
    if not paths:
        raise click.UsageError("No data sources specified")

    data_source = converter.get_data_source(paths)
    rows = tuple(
        converter.iter_stix2_objects(
            data_source=data_source,
            ignore_deprecated=allow_deprecated is False,
            ignore_revoked=allow_revoked is False,
        )
    )
    m = converter.get_alias_map(rows, include_names=include_names, lowercase=lowercase)
    print(json.dumps(m, sort_keys=True, indent=ctx.obj["indent"]))
