# DISCO analyses
- Scripts to reproduce results of our submission about the DISCO corpus

## Requirements
- Requires Python 2.7
- See `requirements.txt` for the libraries used by the scripts

## Reproducing
- To reproduce, run

    ```bash
    ./reproduce.sh
    ```
    - The scripts print their output path to console
    - The outputs used for the paper are in directory [analyses](./analyses). Note that running `reproduce.sh` will overwrite those outputs 

- The required versions of the corpora are already in the repository:
    - [DISCO](./corpora/disco). The files here correspond to commit [9011a46](https://github.com/postdataproject/disco/tree/9011a462db60b2a11a0f92308fcc95f0b9aa6f82) in the corpus repository
    - [Navarro et al.'s](./corpora/navarro) *Spanish Golden Age Sonnet Corpus*. The files here correspond to commit [ed72610](https://github.com/bncolorado/CorpusSonetosSigloDeOro/tree/ed72610018879e9a23ba724c2dc9adb50263d1ec)

## Scripts usage

- **Author metadata** ***(Table 1)***:
    [`author_metadata.py`](./author_metadata.py)
- **Metrical patterns** ***(Table 2 and Figure 1)***:
    - [`metrical_pattern_counts_disco.py`](./metrical_pattern_counts_disco.py): Aggregates over DISCO corpus 
    - [`metrical_pattern_counts_navarro.py`](./metrical_pattern_counts_navarro.py): Aggregates over Navarro's corpus 
    - [`metrical_pattern_counts_merged.py`](./metrical_pattern_counts_merged.py): Merges results for both corpora; outputs a table with the top *n* patterns, that the plot in Figure 1 is based on
- **Line syllable-length and rhyme schemes** ***(Table 3)***: [`line_syllable_length_and_rhyme_scheme.py`](./line_syllable_length_and_rhyme_scheme.py)
    - Shows whether a sonnet uses alexandrine or hendecasyllable meter
    - Shows whether quatrains have enclosed or alternate rhyme
- **Metrical pattern sequences (binary/ternary)** ***(Table 4)***: [`binary_ternary_metrical_sequences.py`](./binary_ternary_metrical_sequences.py)
    - Counts two-line sequences according to the rhythm of each line (binary or ternary)
- **Enjambment** ***(Table 5 and Figure 2)***: [`enjambment_counts_and_plot.py`](./enjambment_counts_and_plot.py)
    - Count and plot enjambments per line-position
- **Other**
    - Overlap between DISCO and Navarro's Golden Age corpus was analyzed with [`analyze_corpus_overlap.py`](./analyze_corpus_overlap.py)
    - The list of files exclusively in DISCO's Golden Age section was created with [`write_disco_only_file_list.py`](./write_disco_only_file_list.py)

### Expected output

    # Table 1 - Author metadata - Running [author_metadata.py]
    - Writing author metadata to [analyses/author_metadata.txt]
    
    # Table 2 - Subcorpus counts DISCO - Running [metrical_pattern_counts_disco.py]
    - Writing counts to [analyses/metrics/patterns/counts]
    
    # Table 2 - Subcorpus counts Navarro - Running [metrical_pattern_counts_navarro.py]
    - Writing counts to [analyses/metrics/patterns/counts/patcounts_ga-navarro.txt]
    
    # Table 2 - Merged counts - Running [metrical_pattern_counts_merged.py]
    - Writing all counts to [analyses/metrics/patterns/counts/patcounts_all.txt]
    - Writing summary for pattern plot to [data/metrical_pattern_summary.ods]
    
    
    # Figure 1 - Metrical patterns - Running [metrical_pattern_plot.py]
    - Writing results to [analyses/metrics]
    - Writing final plot to file [analyses/metrics/metrical_pattern_summary_vertical.jpg]
    
    
    # Table 3 - Meter and Rhyme scheme in 19th century - Running [line_syllable_length_and_rhyme_scheme.py]
    - Writing results to [analyses/syll_and_stanza.txt]
    
    
    # Table 4 - Running [binary_ternary_metrical_sequences.py]
    - Writing binary-ternary pattern data to [analyses/metrics/binary_ternary_2019/binary-ternary_results.txt]
    
    
    # Table 5 and Figure 2 - Enjambment - Running [enjambment_counts_and_plot.py]
    - Writing results to [analyses/enjambment-validated/enj_no_expansion]
    - Writing final plot to file [plot_enjambment_noex_grouped.jpg]
