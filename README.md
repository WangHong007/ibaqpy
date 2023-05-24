# ibaqpy

[![Python application](https://github.com/bigbio/ibaqpy/actions/workflows/python-app.yml/badge.svg)](https://github.com/bigbio/ibaqpy/actions/workflows/python-app.yml)
[![Upload Python Package](https://github.com/bigbio/ibaqpy/actions/workflows/python-publish.yml/badge.svg)](https://github.com/bigbio/ibaqpy/actions/workflows/python-publish.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/6a1961c7d57c4225b4891f73d58cac6b)](https://app.codacy.com/gh/bigbio/ibaqpy/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![PyPI version](https://badge.fury.io/py/ibaqpy.svg)](https://badge.fury.io/py/ibaqpy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ibaqpy)

iBAQ (intensity Based Absolute Quantification) determines the abundance of a protein by dividing the total precursor intensities by the number of theoretically observable peptides of the protein. The TPA (Total Protein Approach) value is determined by summing peptide intensities of each protein and then dividing by the molecular mass to determine the relative concentration of each protein. By using [ProteomicRuler](https://www.sciencedirect.com/science/article/pii/S1535947620337749), it is possible to calculate the protein copy number and absolute concentration. **ibaqpy** compute IBAQ values, TPA values, copy numbers and concentration for proteins starting from a msstats input file and a SDRF experimental design file. This package provides multiple tools: 

- `peptide_file_generation.py`: generate a peptide file from a msstats input file and a SDRF experimental design file. 

- `peptide_normalization.py`: Normalize the input output file from script `peptide_file_generation.py`. It includes multiple steps such as peptidoform normalization, peptidorom to peptide summarization, peptide intensity normalization, and imputation. 

- `compute_ibaq.py`: Compute IBAQ values from the output file from script `peptide_normalization.py`.

- `compute_tpa.py`: Compute TPA values, protein copy numbers and concentration from the output file from script `peptide_file_generation.py`.


### How to install ibaqpy

Ibaqpy is available in PyPI and can be installed using pip:

```asciidoc
pip install ibaqpy
```

You can install the package from code: 

1. Clone the repository:

```asciidoc
>$ git clone https://github.com/bigbio/ibaqpy
>$ cd ibaqpy
```

2. Install conda environment:

```asciidoc
>$ mamba env create -f conda-environment.yaml
```

3. Install ibaqpy:

```asciidoc
>$ python setup.py install
```

### Collecting intensity files 

Absolute quantification files has been store in the following url: 

```
https://ftp.pride.ebi.ac.uk/pub/databases/pride/resources/proteomes/absolute-expression/
```

Inside each project reanalysis folder, the folder proteomicslfq contains the msstats input file with the structure `{Name of the project}_msstats_in.csv`. 

E.g. http://ftp.pride.ebi.ac.uk/pub/databases/pride/resources/proteomes/absolute-expression/PXD003947/proteomicslfq/PXD003947.sdrf_openms_design_msstats_in.csv 

### Generate Peptidoform Intesity file - peptide_file_generation.py

```asciidoc
python  peptide_file_generation.py --msstats PXD003947.sdrf_openms_design_msstats_in.csv --sdrf PXD003947.sdrf.tsv --min_aa 7 --min_unique 2 --output PXD003947-peptides.csv
```

The command provides an additional `flag` for compression data analysis where the msstats and sdrf files are compressed. 

```asciidoc
python peptide_file_generation.py --help
Usage: peptide_file_generation.py [OPTIONS]

  Conversion of peptide intensity information into a file that containers
  peptide intensities but also the metadata around the conditions, the
  retention time, charge states, etc.

  :param msstats: MsStats file import generated by quantms 
  :param sdrf: SDRF file import generated by quantms 
  :param min_aa: Minimum number of amino acids to filter peptides
  :param min_unique: Minimum number of unique peptides to filter proteins
  :param compress: Read all files compress
  :param output: Peptide intensity file including other all properties for
                 normalization

Options:
  -m, --msstats TEXT  MsStats file import generated by quantms  [required]
  -s, --sdrf TEXT     SDRF file import generated by quantms  [required]
  --min_aa            Minimum number of amino acids to filter peptides (default: 7)
  --min_unique        Minimum number of unique peptides to filter proteins (default: 2)
  --compress          Read all files compress
  -o, --output TEXT   Peptide intensity file including other all properties
                      for normalization
  --help              Show this message and exit.
```

### Peptide Normalization - peptide_normalization.py

```asciidoc
python peptide_normalization.py --peptides PXD003947-peptides.csv --impute --normalize --contaminants data/contaminants_ids.tsv --output PXD003947-peptides-norm.tsv
``` 

The command provides an additional `flag` for skip_normalization, impute, pnormalization, compress, log2, violin, verbose.

```asciidoc
python peptide_normalization.py --help
Usage: peptide_normalization.py [OPTIONS]

  Normalize the peptide intensities using different methods for a file output
  of peptides with the format described in peptide_file_generation.py.

  :param peptides: Peptides files from the peptide file generation tool
  :param contaminants: Contaminants and high abundant proteins to be removed
  :param output: Peptide intensity file including other all properties for normalization
  :param skip_normalization: Skip normalization step
  :param nmethod: Normalization method used to normalize intensities for all samples
  :param impute: Impute the missing values using MissForest
  :param pnormalization: Normalize the peptide intensities using different methods
  :param compress: Read the input peptides file in compress gzip file
  :param log2: Transform to log2 the peptide intensity values before normalization
  :param violin: Use violin plot instead of boxplot for distribution representations
  :param verbose: Print addition information about the distributions of the intensities, 
                  number of peptides remove after normalization, etc.
  :param qc_report: PDF file to store multiple QC images

Options:
  --peptides TEXT       Peptides files from the peptide file generation tool  [required]
  --contaminants TEXT   Contaminants and high abundant proteins to be removed
  --skip_normalization  Skip normalization step (default: False)
  --nmethod             Normalization method used to normalize intensities for all samples
                        (default: qnorm)
  --impute              Impute the missing values using MissForest
  --pnormalization      Normalize the peptide intensities using different methods
  --compress            Read the input peptides file in compress gzip file
  --log2                Transform to log2 the peptide intensity values before normalization
  --violin              Use violin plot instead of boxplot for distribution representations
  --verbose             Print addition information about the distributions of the intensities, 
                        number of peptides remove after normalization, etc.
  --qc_report           PDF file to store multiple QC images (default: "peptideNorm-QCprofile.pdf")
  --output TEXT         Peptide intensity file including other all properties for normalization
  --help                Show this message and exit.
```

Peptide normalization starts from the output file from script `peptide_file_generation.py`. The structure of the input contains the following columns: 

- ProteinName: Protein name
- PeptideSequence: Peptide sequence including post-translation modifications `(e.g. .(Acetyl)ASPDWGYDDKN(Deamidated)GPEQWSK)`
- PrecursorCharge: Precursor charge
- FragmentIon: Fragment ion
- ProductCharge: Product charge
- IsotopeLabelType: Isotope label type
- Condition: Condition label `(e.g. heart)`
- BioReplicate: Biological replicate index `(e.g. 1)`
- Run: Run index `(e.g. 1)`
- Fraction: Fraction index `(e.g. 1)`
- Intensity: Peptide intensity
- Reference: Name of the RAW file containing the peptide intensity `(e.g. Adult_Heart_Gel_Elite_54_f16)`
- SampleID: Sample ID `(e.g. PXD003947-Sample-3)`
- StudyID: Study ID `(e.g. PXD003947)`. In most of the cases the study ID is the same as the ProteomeXchange ID.

#### Removing Contaminants and Decoys

The first step is to remove contaminants and decoys from the input file. The script `peptide_normalization.py` provides a parameter `--contaminants` for the user to provide a file with a list of protein accessions which represent each contaminant in the file. An example file can be seen in `data/contaminants.txt`. In addition to all the proteins accessions, the tool remove all the proteins with the following prefixes: `CONTAMINANT` and `DECOY`.

#### Peptidoform Normalization

A peptidoform is a combination of a `PeptideSequence(Modifications) + Charge + BioReplicate + Fraction`. In the current version of the file, each row correspond to one peptidoform. 

The current version of the tool uses the parackage [qnorm](https://pypi.org/project/qnorm/) to normalize the intensities for each peptidofrom. **qnorm** implements a quantile normalization method. 

#### Peptidoform to Peptide Summarization

For each peptidoform a peptide sequence (canonical) with not modification is generated. The intensity of all peptides group by biological replicate are `sum`. 

Then, the intensities of the peptides across different biological replicates are summarize using the function `median`. 

At the end of this step, for each peptide, the corresponding protein + the intensity of the peptide is stored. 

#### Peptide Intensity Imputation and Normalization

Before the final two steps (peptide normalization and imputation), the algorithm removes all peptides that are source of missing values significantly. The algorithm removes all peptides that have more than 80% of missing values and peptides that do not appear in more than 1 sample. 

Finally, two extra steps are performed: 

- ``peptide intensity imputation``: Imputation is performed using the package [missingpy](https://pypi.org/project/missingpy/). The algorithm uses a Random Forest algorithm to perform the imputation.
- ``peptide intensity normalization``: Similar to the normalization of the peptidoform intensities, the peptide intensities are normalized using the package [qnorm](https://pypi.org/project/qnorm/).

### Compute IBAQ - compute_ibaq.py
IBAQ is an absolute quantitative method based on strength that can be used to estimate the relative abundance of proteins in a sample. IBAQ value is the total intensity of a protein divided by the number of theoretical peptides.

```asciidoc
python compute_ibaq.py --fasta Homo-sapiens-uniprot-reviewed-contaminants-decoy-202210.fasta --peptides PXD003947-peptides.csv --enzyme "Trypsin" --normalize --output PXD003947-ibaq.tsv
``` 

The command provides an additional `flag` for normalize IBAQ values.

```asciidoc
python compute_ibaq.py --help
Usage: compute_ibaq.py [OPTIONS]

  Compute the IBAQ values for a file output of peptides with the format described in
  peptide_normalization.py.

  :param min_aa: Minimum number of amino acids to consider a peptide
  :param max_aa: Maximum number of amino acids to consider a peptide
  :param fasta: Fasta file used to perform the peptide identification
  :param peptides: Peptide intensity file
  :param enzyme: Enzyme used to digest the protein sample
  :param normalize: use some basic normalization steps
  :param output: output format containing the ibaq values
  :param verbose: Print addition information about the distributions of the intensities, 
                  number of peptides remove after normalization, etc.
  :param qc_report: PDF file to store multiple QC images

Options:
  -f, --fasta TEXT      Protein database to compute IBAQ values  [required]
  -p, --peptides TEXT   Peptide identifications with intensities following the peptide intensity output  [required]
  -e, --enzyme          Enzyme used during the analysis of the dataset (default: Trypsin)
  -n, --normalize       Normalize IBAQ values using by using the total IBAQ of the experiment
  --min_aa              Minimum number of amino acids to consider a peptide (default: 7)
  --max_aa              Maximum number of amino acids to consider a peptide (default: 30)
  -o, --output TEXT     Output format containing the ibaq values
  --verbose             Print addition information about the distributions of the intensities, 
                        number of peptides remove after normalization, etc.
  --qc_report           PDF file to store multiple QC images (default: "IBAQ-QCprofile.pdf")
  --help                Show this message and exit.
```

#### Performs the Enzymatic Digestion
The current version of this tool uses OpenMS method to load fasta file, and use [ProteaseDigestion](https://openms.de/current_doxygen/html/classOpenMS_1_1ProteaseDigestion.html) to enzyme digestion of protein sequences, and finally get the theoretical peptide number of each protein.

#### Calculate the IBAQ Value
First, peptide intensity dataframe was grouped according to protein name, sample name and condition. The protein intensity of each group was summed. Finally, the sum of the intensity of the protein is divided by the number of theoretical peptides.

If protein-group exists in the peptide intensity dataframe, the intensity of all proteins in the protein-group is summed based on the above steps, and then multiplied by the number of proteins in the protein-group.

#### IBAQ Normalization  
Normalize the ibaq values using the total ibaq of the sample. The resulted ibaq values are then multiplied by 100'000'000 (PRIDE database noramalization), for the ibaq ppb and log10 shifted by 10 (ProteomicsDB)

### Compute TPA - compute_tpa.py
The total protein approach (TPA) is a label- and standard-free method for absolute protein quantitation of proteins using large-scale proteomic data. In the current version of the tool, the TPA value is the total intensity of the protein divided by its theoretical molecular mass.

[ProteomicRuler](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4256500/) is a method for protein copy number and concentration estimation that does not require the use of isotope labeled standards. It uses the mass spectrum signal of histones as a "proteomic ruler" because it is proportional to the amount of DNA in the sample, which in turn depends on cell count. Thus, this approach can add an absolute scale to the mass spectrometry readout and allow estimates of the copy number of individual proteins in each cell.

```asciidoc
python compute_tpa.py --fasta Homo-sapiens-uniprot-reviewed-contaminants-decoy-202210.fasta --contaminants contaminants_ids.tsv --peptides PXD003947-peptides.csv --ruler --ploidy 2 --cpc 200 --output PXD003947-tpa.tsv
``` 

Note: The peptide intensity file used in the calculation of TPA and the ProteomicRuler is not normalized!

```asciidoc
python compute_tpa.py --help
Usage: compute_tpa.py [OPTIONS]

  Compute the protein copy numbers and concentrations according to a file output of peptides with the
  format described in peptide_file_generation.py.

  :param fasta: Fasta file used to perform the peptide identification
  :param peptides: Peptide intensity file
  :param contaminants: Contaminants file
  :param ruler: Whether to compute protein copy number, weight and concentration.
  :param ploidy: Ploidy number
  :param cpc: Cellular protein concentration(g/L)
  :param output: Output format containing the TPA values, protein copy numbers and concentrations
  :param verbose: Print addition information about the distributions of the intensities, 
                  number of peptides remove after normalization, etc.
  :param qc_report: PDF file to store multiple QC images

Options:
  -f, --fasta TEXT      Protein database to compute IBAQ values  [required]
  -p, --peptides TEXT   Peptide identifications with intensities following the peptide intensity output  [required]
  --contaminants        Contaminants and high abundant proteins to be removed
  -r, --ruler           Calculate protein copy number and concentration according to ProteomicRuler
  -n, --ploidy          Ploidy number (default: 2)
  -c, --cpc             Cellular protein concentration(g/L) (default: 200)
  -o, --output TEXT     Output format containing the TPA values, protein copy numbers and concentrations
  --verbose             Print addition information about the distributions of the intensities, 
                        number of peptides remove after normalization, etc.
  --qc_report           PDF file to store multiple QC images (default: "TPA-QCprofile.pdf")
  --help                Show this message and exit.
```

#### Calculate the TPA Value
The OpenMS tool was used to calculate the theoretical molecular mass of each protein. Similar to the calculation of IBAQ, the TPA value of protein-group was the sum of its intensity divided by the sum of the theoretical molecular mass.

#### Calculate the Cellular Protein Copy Number and Concentration
The protein copy calculation follows the following formula:
```
protein copies per cell = protein MS-signal *  (avogadro / molecular mass) * (DNA mass / histone MS-signal)
```
For cellular protein copy number calculation, the uniprot accession of histones were obtained from species first, and the molecular mass of DNA was calculated. Then the dataframe was grouped according to different conditions, and the copy number, molar number and mass of proteins were calculated.

In the calculation of protein concentration, the volume is calculated according to the cell protein concentration first, and then the protein mass is divided by the volume to calculate the intracellular protein concentration.

### Credits 

- Julianus Pfeuffer
- Yasset Perez-Riverol
- Hong Wang
