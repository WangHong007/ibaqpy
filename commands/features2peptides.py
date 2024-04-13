#!/usr/bin/env python
import click
from ibaq.peptide_normalization import peptide_normalization


@click.command()
@click.option(
    "-p",
    "--parquet",
    help="Parquet file import generated by quantms.io",
)
@click.option(
    "-s", "--sdrf", help="SDRF file import generated by quantms", default=None
)
@click.option(
    "--min_aa", help="Minimum number of amino acids to filter peptides", default=7
)
@click.option(
    "--min_unique",
    help="Minimum number of unique peptides to filter proteins",
    default=2,
)
@click.option(
    "--remove_ids",
    help="Remove specific protein ids from the analysis using a file with one id per line",
)
@click.option(
    "--remove_decoy_contaminants",
    help="Remove decoy and contaminants proteins from the analysis",
    is_flag=True,
    default=False,
)
@click.option(
    "--remove_low_frequency_peptides",
    help="Remove peptides that are present in less than 20% of the samples",
    is_flag=True,
    default=False,
)
@click.option(
    "--output",
    help="Peptide intensity file including other all properties for normalization",
)
@click.option(
    "--skip_normalization", help="Skip normalization step", is_flag=True, default=False
)
@click.option(
    "--nmethod",
    help="Normalization method used to normalize feature intensities for all samples (options: mean, median, iqr, none)",
    default="median",
)
@click.option(
    "--pnmethod",
    help="Normalization method used to normalize peptides intensities for all samples (options: mean, median, max, global, max_min, none)",
    default="max_min",
)
@click.option(
    "--log2",
    help="Transform to log2 the peptide intensity values before normalization",
    is_flag=True,
)
@click.option(
    "--save_parquet",
    help="Save normalized peptides to parquet",
    is_flag=True,
)
def features2parquet(
    parquet: str,
    sdrf: str,
    min_aa: int,
    min_unique: int,
    remove_ids: str,
    remove_decoy_contaminants: bool,
    remove_low_frequency_peptides: bool,
    output: str,
    skip_normalization: bool,
    nmethod: str,
    pnmethod: str,
    log2: bool,
    save_parquet: bool,
) -> None:
    peptide_normalization(**click.get_current_context().params)


if __name__ == "__main__":
    features2parquet()
