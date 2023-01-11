#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import click
import numpy as np
import pandas as pd
import qnorm
from missingpy import MissForest
from pandas import DataFrame

from ibaq.ibaqpy_commons import remove_contaminants_decoys, INTENSITY, SAMPLE_ID, NORM_INTENSITY, \
    PEPTIDE_SEQUENCE, PEPTIDE_CHARGE, FRACTION, RUN, BIOREPLICATE, PEPTIDE_CANONICAL, SEARCH_ENGINE, \
    PROTEIN_NAME, STUDY_ID, CONDITION, plot_distributions, plot_box_plot


def print_dataset_size(dataset: DataFrame, message: str, verbose: bool) -> None:
    if verbose:
        print(message + str(len(dataset.index)))

def print_help_msg(command) -> None:
    """
    Print help information
    :param command: command to print helps
    :return: print help
    """
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))

def remove_outliers_iqr(dataset: DataFrame):
    """
    This method removes outliers from the dataframe inplace, the variable used for the outlier removal is Intensity
    :param dataset: Peptide dataframe
    :return: None
    """
    Q1 = dataset[INTENSITY].quantile(0.25)
    Q3 = dataset[INTENSITY].quantile(0.75)
    IQR = Q3 - Q1

    dataset.query('(@Q1 - 1.5 * @IQR) <= Intensity <= (@Q3 + 1.5 * @IQR)', inplace=True)

def remove_missing_values(normalize_df: DataFrame, ratio: float = 0.3) -> DataFrame:
    """
    Remove missing values if the peptide do not have values in the most of the samples
    :param normalize_df: data frame with the data
    :param ratio: ratio of samples without intensity values.
    :return:
    """
    n_samples = len(normalize_df.columns)
    normalize_df = normalize_df.dropna(thresh=round(n_samples * ratio))
    return normalize_df

def get_canonical_peptide(peptide_sequence: str)-> str:
    """
    This function returns a peptide sequence without the modification information
    :param peptide_sequence: peptide sequence with mods
    :return: peptide sequence
    """
    clean_peptide = re.sub("[\(\[].*?[\)\]]", "", peptide_sequence)
    clean_peptide = clean_peptide.replace(".","")
    return clean_peptide

def intensity_normalization(dataset: DataFrame, field: str, class_field: str = "all", scaling_method: str = "msstats") -> DataFrame:

    ## TODO add imputation and/or removal to those two norm strategies
    if scaling_method == 'msstats':
        g = dataset.groupby(['Run', 'Fraction'])[INTENSITY].apply(np.median)
        g.name = 'RunMedian'
        dataset = dataset.join(g, on=['Run', 'Fraction'])
        dataset['FractionMedian'] = dataset['RunMedian'].groupby(dataset['Fraction']).transform('median')
        dataset[NORM_INTENSITY] = dataset[INTENSITY] - dataset['RunMedian'] + dataset['FractionMedian']
        return dataset

    elif scaling_method == 'qnorm':
        # pivot to have one col per sample
        normalize_df = pd.pivot_table(dataset, index=[PEPTIDE_SEQUENCE, PEPTIDE_CHARGE, FRACTION, RUN, BIOREPLICATE, PROTEIN_NAME, STUDY_ID, CONDITION],
                                      columns=class_field, values=field, aggfunc={field: np.mean})
        normalize_df = qnorm.quantile_normalize(normalize_df, axis=1)
        normalize_df = normalize_df.reset_index()
        normalize_df = normalize_df.melt(id_vars=[PEPTIDE_SEQUENCE, PEPTIDE_CHARGE, FRACTION, RUN, BIOREPLICATE, PROTEIN_NAME, STUDY_ID, CONDITION])
        normalize_df.rename(columns={'value': NORM_INTENSITY}, inplace=True)
        print(dataset.head())
        return normalize_df

    return dataset

def get_peptidoform_normalize_intensities(dataset: DataFrame, higher_intensity: bool = True) -> DataFrame:
    """
    Select the best peptidoform for the same sample and the same replicates. A peptidoform is the combination of
    a (PeptideSequence + Modifications) + Charge state.
    :param dataset: dataset including all properties
    :param higher_intensity: select based on normalize intensity, if false based on best scored peptide
    :return:
    """
    dataset = dataset[dataset[NORM_INTENSITY].notna()]
    if higher_intensity:
        dataset = dataset.loc[dataset.groupby([PEPTIDE_SEQUENCE, PEPTIDE_CHARGE, SAMPLE_ID, CONDITION, BIOREPLICATE])[NORM_INTENSITY].idxmax()].reset_index(drop=True)
    else:
        dataset = dataset.loc[dataset.groupby([PEPTIDE_SEQUENCE, PEPTIDE_CHARGE, SAMPLE_ID, CONDITION, BIOREPLICATE])[
            SEARCH_ENGINE].idxmax()].reset_index(drop=True)
    return dataset

def sum_peptidoform_intensities(dataset: DataFrame) -> DataFrame:
    """
    Sum the peptidoform intensities for all peptidofrom across replicates of the same sample.
    :param dataset: Dataframe to be analyzed
    :return: dataframe with the intensities
    """
    dataset = dataset[dataset[NORM_INTENSITY].notna()]
    normalize_df = dataset.groupby([PEPTIDE_CANONICAL, SAMPLE_ID, BIOREPLICATE, CONDITION])[NORM_INTENSITY].sum()
    normalize_df = normalize_df.reset_index()
    normalize_df = pd.merge(normalize_df, dataset[[PROTEIN_NAME, PEPTIDE_CANONICAL, SAMPLE_ID, BIOREPLICATE, CONDITION]], how='left', on=[PEPTIDE_CANONICAL, SAMPLE_ID, BIOREPLICATE, CONDITION])
    return normalize_df

def average_peptide_intensities(dataset: DataFrame) -> DataFrame:
    """
    Median the intensities of all the peptidoforms for a specific peptide sample combination.
    :param dataset: Dataframe containing all the peptidoforms
    :return: New dataframe
    """
    dataset_df = dataset.groupby([PEPTIDE_CANONICAL, SAMPLE_ID, CONDITION])[NORM_INTENSITY].median()
    dataset_df = dataset_df.reset_index()
    dataset_df = pd.merge(dataset_df, dataset[[PROTEIN_NAME, PEPTIDE_CANONICAL, SAMPLE_ID, CONDITION]], how='left', on=[PEPTIDE_CANONICAL, SAMPLE_ID, CONDITION])
    return dataset_df

def remove_low_frequency_peptides(dataset_df: DataFrame, percentage_samples: float = 0.20):
    """
    Remove peptides that are present in less than 20% of the samples.
    :param dataset_df: dataframe with the data
    :param percentage_samples: percentage of samples
    :return:
    """

    normalize_df = pd.pivot_table(dataset_df,index=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION],
                                  columns=SAMPLE_ID, values=NORM_INTENSITY, aggfunc={NORM_INTENSITY: np.mean})
    # Count the number of null values in each row
    null_count = normalize_df.isnull().sum(axis=1)

    # Find the rows that have null values above the threshold
    rows_to_drop = null_count[null_count >= (1 - percentage_samples) * normalize_df.shape[1]].index

    # Drop the rows with too many null values
    normalize_df = normalize_df.drop(rows_to_drop)

    # Remove rows with non-null values in only one column
    normalize_df = normalize_df[normalize_df.notnull().sum(axis=1) != normalize_df.shape[1] - 1]

    normalize_df = normalize_df.reset_index()
    normalize_df = normalize_df.melt(
        id_vars=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION])
    normalize_df.rename(columns={'value': NORM_INTENSITY}, inplace=True)

    # Remove rows with null values in NORMALIZE_INTENSITY
    normalize_df = normalize_df[normalize_df[NORM_INTENSITY].notna()]

    print(normalize_df.head())
    return normalize_df

def peptide_intensity_normalization(dataset_df: DataFrame, field: str, class_field: str, scaling_method: str):
    """
    Normalize the peptide intensities using different methods.
    :param dataset_df: dataframe with the data
    :param field: field to normalize
    :param class_field: field to use as class
    :param scaling_method: method to use for the normalization
    :return:
    """
    if scaling_method == 'qnorm':
        # pivot to have one col per sample
        normalize_df = pd.pivot_table(dataset_df, index=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION],
                                      columns=class_field, values=field, aggfunc={field: np.mean})
        normalize_df = qnorm.quantile_normalize(normalize_df, axis=1)
        normalize_df = normalize_df.reset_index()
        normalize_df = normalize_df.melt(id_vars=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION])
        normalize_df.rename(columns={'value': NORM_INTENSITY}, inplace=True)
        normalize_df = normalize_df[normalize_df[NORM_INTENSITY].notna()]
        return normalize_df

    return dataset_df

def impute_peptide_intensities(dataset_df, field, class_field):
    """
    Impute the missing values using different methods.
    :param dataset_df: dataframe with the data
    :param field: field to impute
    :param class_field: field to use as class
    :return:
    """
    # pivot to have one col per sample
    normalize_df = pd.pivot_table(dataset_df, index=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION],
                                  columns=class_field, values=field, aggfunc={field: np.mean})
    # Impute the missing values
    imputer = MissForest(max_iter=5)
    imputed_data = imputer.fit_transform(normalize_df)
    normalize_df = pd.DataFrame(imputed_data, columns=normalize_df.columns, index=normalize_df.index)

    # Melt the dataframe
    normalize_df = normalize_df.reset_index()
    normalize_df = normalize_df.melt(id_vars=[PEPTIDE_CANONICAL, PROTEIN_NAME, CONDITION])
    normalize_df.rename(columns={'value': NORM_INTENSITY}, inplace=True)
    return normalize_df

@click.command()
@click.option("--peptides", help="Peptides files from the peptide file generation tool")
@click.option("--contaminants", help="Contaminants and high abundant proteins to be removed")
@click.option("--output", help="Peptide intensity file including other all properties for normalization")
@click.option('--nmethod', help="Normalization method used to normalize intensities for all samples (options: qnorm)", default="qnorm")
@click.option("--impute", help="Impute the missing values using MissForest", is_flag=True)
@click.option("--pnormalization", help="Normalize the peptide intensities using different methods (options: qnorm)", is_flag=True)
@click.option("--compress", help="Read the input peptides file in compress gzip file", is_flag= True)
@click.option("--log2", help="Transform to log2 the peptide intensity values before normalization", is_flag=True)
@click.option("--violin", help="Use violin plot instead of boxplot for distribution representations", is_flag=True)
@click.option("--verbose",
              help="Print addition information about the distributions of the intensities, number of peptides remove "
                   "after normalization, etc.",
              is_flag=True)
def peptide_normalization(peptides: str, contaminants: str, output: str, nmethod: str, impute: bool, pnormalization: bool,  compress: bool, log2: bool,
                          violin: bool, verbose: bool) -> None:
    """
    Normalize the peptide intensities using different methods.
    :param peptides:
    :param contaminants:
    :param output:
    :param nmethod:
    :param impute:
    :param pnormalization:
    :param compress:
    :param log2:
    :param violin:
    :param verbose:
    :return:
    """

    if peptides is None or output is None:
        print_help_msg(peptide_normalization)
        exit(1)

    pd.set_option('display.max_columns', None)
    print("Loading data..")
    compression_method = 'gzip' if compress else None
    if compress:
        dataset_df = pd.read_csv(peptides, sep=",", compression=compression_method)
    else:
        dataset_df = pd.read_csv(peptides, sep=",")
    print_dataset_size(dataset_df, "Number of peptides: ", verbose)

    print("Logarithmic if specified..")
    dataset_df.loc[dataset_df.Intensity == 0, INTENSITY] = 1
    dataset_df[NORM_INTENSITY] = np.log2(dataset_df[INTENSITY]) if log2 else dataset_df[INTENSITY]

    # Print the distribution of the original peptide intensities from quantms analysis
    if verbose:
        plot_distributions(dataset_df, INTENSITY, SAMPLE_ID, log2=not log2)
        plot_box_plot(dataset_df, INTENSITY, SAMPLE_ID, log2=not log2,
                      title="Original peptidoform intensity distribution (no normalization)", violin=violin)

    # Remove high abundant and contaminants proteins and the outliers
    if contaminants is not None:
        print("Remove contaminants...")
        dataset_df = remove_contaminants_decoys(dataset_df, contaminants)
    print_dataset_size(dataset_df, "Peptides after contaminants removal: ", verbose)

    print("Normalize intensities.. ")
    dataset_df = intensity_normalization(dataset_df, field=NORM_INTENSITY, class_field=SAMPLE_ID, scaling_method=nmethod)

    if verbose:
        log_after_norm = nmethod == "msstats" or nmethod == "qnorm" or ((nmethod == "quantile" or nmethod == "robust") and not log2)
        plot_distributions(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm)
        plot_box_plot(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm,
                      title="Peptidoform intensity distribution after normalization, method: " + nmethod, violin=violin)

    print("Select the best peptidoform across fractions...")
    print("Number of peptides before peptidofrom selection: " + str(len(dataset_df.index)))
    dataset_df = get_peptidoform_normalize_intensities(dataset_df)
    print("Number of peptides after peptidofrom selection: " + str(len(dataset_df.index)))

    # Add the peptide sequence canonical without the modifications
    print("Add Canonical peptides to the dataframe...")
    dataset_df[PEPTIDE_CANONICAL] = dataset_df[PEPTIDE_SEQUENCE].apply(lambda x: get_canonical_peptide(x))

    print("Sum all peptidoforms per Sample...")
    print("Number of peptides before sum selection: " + str(len(dataset_df.index)))
    dataset_df = sum_peptidoform_intensities(dataset_df)
    print("Number of peptides after sum: " + str(len(dataset_df.index)))

    print("Average all peptidoforms per Peptide/Sample...")
    print("Number of peptides before average: " + str(len(dataset_df.index)))
    dataset_df = average_peptide_intensities(dataset_df)
    print("Number of peptides after average: " + str(len(dataset_df.index)))

    if verbose:
        log_after_norm = nmethod == "msstats" or nmethod == "qnorm" or ((nmethod == "quantile" or nmethod == "robust") and not log2)
        plot_distributions(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm)
        plot_box_plot(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm,
                      title="Peptide intensity distribution method: " + nmethod, violin=violin)

    print("Peptides before removing low frequency peptides: " + str(len(dataset_df.index)))
    dataset_df = remove_low_frequency_peptides(dataset_df, 0.20)
    print_dataset_size(dataset_df, "Peptides after remove low frequency peptides: ", verbose)


    # Perform imputation using Random Forest in Peptide Intensities
    if impute:
       dataset_df = impute_peptide_intensities(dataset_df, field=NORM_INTENSITY, class_field=SAMPLE_ID)

    if pnormalization:
       print("Normalize at Peptide level...")
       dataset_df = peptide_intensity_normalization(dataset_df, field=NORM_INTENSITY, class_field=SAMPLE_ID, scaling_method=nmethod)

    if verbose:
        log_after_norm = nmethod == "msstats" or nmethod == "qnorm" or ((nmethod == "quantile" or nmethod == "robust") and not log2)
        plot_distributions(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm)
        plot_box_plot(dataset_df, NORM_INTENSITY, SAMPLE_ID, log2=log_after_norm,
                      title="Normalization at peptide level method: " + nmethod, violin=violin)

    print("Save the normalized peptide intensities...")
    dataset_df.to_csv(output, index=False, sep=',')



if __name__ == '__main__':
    peptide_normalization()
