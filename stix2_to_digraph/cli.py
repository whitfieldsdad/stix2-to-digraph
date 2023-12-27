import json
from typing import Iterable, Optional
import click

import stix2_to_digraph.converter as converter


@click.group()
@click.option("--indent", default=4)
@click.pass_context
def main(ctx: click.Context, indent: int):
    ctx.obj = {"indent": indent}


@main.command("triples")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--allow-deprecated/--no-deprecated", default=False, show_default=True)
@click.option("--allow-revoked/--no-revoked", default=False, show_default=True)
@click.option("--separator", default=" ", show_default=True)
@click.option("--tabs", is_flag=True)
def get_triples(
    paths: Iterable[str],
    allow_deprecated: bool,
    allow_revoked: bool,
    separator: str,
    tabs: bool,
):
    """
    Get triples.
    """
    rows = iter_objects(
        paths=paths, allow_deprecated=allow_deprecated, allow_revoked=allow_revoked
    )
    g = converter.stix2_objects_to_networkx(rows)
    triples = converter.nx_digraph_to_triples(g)

    separator = "\t" if tabs else separator
    for a, t, b in triples:
        print(f"{a}{separator}{t}{separator}{b}")


@main.command("quads")
@click.argument("namespace", required=True)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--allow-deprecated/--no-deprecated", default=False, show_default=True)
@click.option("--allow-revoked/--no-revoked", default=False, show_default=True)
def get_quads(
    namespace: str,
    paths: Iterable[str],
    allow_deprecated: bool,
    allow_revoked: bool,
    separator: str,
    tabs: bool,
):
    """
    Get quads.
    """
    rows = iter_objects(
        paths=paths, allow_deprecated=allow_deprecated, allow_revoked=allow_revoked
    )
    g = converter.stix2_objects_to_networkx(rows)
    triples = converter.nx_digraph_to_triples(g)

    separator = "\t" if tabs else separator
    for a, t, b in triples:
        print(f"{namespace}{separator}{a}{separator}{t}{separator}{b}")


def iter_objects(paths: Iterable[str], allow_deprecated: bool, allow_revoked: bool):
    if not paths:
        raise click.UsageError("No data sources specified")

    data_source = converter.get_data_source(paths)
    rows = converter.iter_stix2_objects(
        data_source=data_source,
        ignore_deprecated=allow_deprecated is False,
        ignore_revoked=allow_revoked is False,
    )
    yield from rows


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
