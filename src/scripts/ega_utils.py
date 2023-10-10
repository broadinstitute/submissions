import dataclasses
from enum import Enum


class LibraryLayouts(str, Enum):
    SINGLE = "SINGLE"
    PAIRED = "PAIRED"


class LibraryStrategy(str, Enum):
    WGS = "WGS"
    WGA = "WGA"
    WXS = "WXS"
    RNA_SEQ = "RNA-Seq"
    SSRNA_SEQ = "ssRNA-seq"
    MIRNA_SEQ = "miRNA-Seq"
    NCRNA_SEQ = "ncRNA-Seq"
    FL_CDNA = "FL-cDNA"
    EST = "EST"
    Hi_C = "Hi-C"
    ATAC_SEQ = "ATAC-seq"
    WCS = "WCS"
    RAD_SEQ = "RAD-Seq"
    CLONE = "CLONE"
    POOLCLONE = "POOLCLONE"
    AMPLICON = "AMPLICON"
    CLONEEND = "CLONEEND"
    FINISHING = "FINISHING"
    CHIP_SEQ = "ChIP-Seq"
    MNASE_Seq = "MNase-Seq"
    DNASE_HYPERSENSITIVITY = "DNase-Hypersensitivity"
    BISULFATE_SEQ = "Bisulfite-Seq"
    CTS = "CTS"
    MRE_SEQ = "MRE-Seq"
    MEDIP_SEQ = "MeDIP-Seq"
    MBD_SEQ = "MBD-Seq"
    TN_SEQ = "Tn-Seq"
    VALIDATION = "VALIDATION"
    FAIRE_SEQ = "FAIRE-seq"
    SELEX = "SELEX"
    RIP_SEQ = "RIP-Seq"
    CHIA_PET = "ChIA-PET"
    SYNTHETIC_LONG_READ = "Synthetic-Long-Read"
    TARGETED_CAPTURE = "Targeted-Capture"
    TETHERED_CHROMATIN_CONFORMATION_CAPTURE = "Tethered Chromatin Conformation Capture"
    NOME_SEQ = "NOMe-Seq"
    CHM_SEQ = "ChM-Seq"
    GBS = "GBS"
    OTHER = "OTHER"
    SNRNA_SEQ = "snRNA-seq"
    RIBO_SEQ = "Ribo-Seq"


class LibrarySource(str, Enum):
    GENOMIC = "GENOMIC"
    GENOMIC_SINGLE_CELL = "GENOMIC SINGLE CELL"
    TRANSCRIPTOMIC = "TRANSCRIPTOMIC"
    TRANSCRIPTOMIC_SINGLE_CELL = "TRANSCRIPTOMIC SINGLE CELL"
    METAGENOMIC = "METAGENOMIC"
    METATRANSCRIPTOMIC = "METATRANSCRIPTOMIC"
    SYNTHETIC = "SYNTHETIC"
    VIRAL_RNA = "VIRAL RNA"
    OTHER = "OTHER"


class LibrarySelection(str, Enum):
    RANDOM = "RANDOM"
    PCR = "PCR"
    RANDOM_PCR = "RANDOM PCR"
    RT_PCR = "RT-PCR"
    HMPR = "HMPR"
    MF = "MF"
    REPEAT_FRACTIONATION = "repeat fractionation"
    SIZE_FRACTIONATION = "size fractionation"
    MSLL = "MSLL"
    CDNA = "cDNA"
    CDNA_RANDOMPRIMING = "cDNA_randomPriming"
    CDNA_OLIGO_DT = "cDNA_oligo_dT"
    POLYA = "PolyA"
    OLIGO_DT = "Oligo-dT"
    INVERSE_RRNA = "Inverse rRNA"
    INVERSE_RRNA_ELECTION = "Inverse rRNA selection"
    CHIP = "ChIP"
    CHIP_SEQ = "ChIP-Seq"
    MNASE = "MNase"
    DNASE = "DNase"
    HYBRID_SELECTION = "Hybrid Selection"
    REDUCED_REPRESENTATION = "Reduced Representation"
    RESTRICTION_DIGEST = "Restriction Digest",
    FIVE_METHYLCYTIDINE_ANTIBODY = "5-methylcytidine antibody"
    MBD2_PROTEIN_METHYL_CPG_BINDING_DOMAIN = "MBD2 protein methyl-CpG binding domain"
    CAGE = "CAGE"
    RACE = "RACE"
    MDA = "MDA"
    PADLOCK_PROBES_CAPTURE_METHOD = "padlock probes capture method"
    OTHER = "other"
    UNSPECIFIED = "unspecified"


class RunFileType(str, Enum):
    SRF = "srf"
    SFF = "sff"
    FASTQ = "fastq"
    ILLUMINA_NATIVE = "Illumina_native"
    ILLUMINA_NATIVE_GSEQ = "Illumina_native_qseq"
    SOLID_NATIVE_CSFASTA = "SOLiD_native_csfasta"
    PACBIO_HDF5 = "PacBio_HDF5"
    BAM = "bam"
    CRAM = "cram"
    COMPLETEGENOMICS_NATIVE = "CompleteGenomics_native"
    OXFORDNANOPORE_NATIVE = "OxfordNanopore_native"


INSTRUMENT_MODEL_MAPPING = {
    "HISEQ_X_10": 9,
    "HISEQ_2000": 16,
    "HISEQ_2500": 17,
    "HISEQ_4000": 19,
    "MISEQ": 22,
    "NOVA_SEQ_X": 24,
    "NOVA_SEQ_6000": 25,
    "NEXT_SEQ_500": 26,
}
