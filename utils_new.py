#coding=utf8

"""
Utilities for the DISCO manuscript revision
"""

__author__ = 'Pablo Ruiz'
__date__ = '26/12/19'
__email__ = 'pabloruizfabo@gmail.com'


import codecs
from lxml import etree
import os

from analyze_corpus_overlap import authors_d

nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

periodkeys = {"rom2ara": {"xv": ("DISCO Golden Age", "discoGA"),
                          "xvc": ("Navarro Golden Age", "navarroGA"),
                          "xviii": ("DISCO 18th", "disco18th"),
                          "xix": ("DISCO 19th", "disco19th")}}

terbinsort = [("ter", "bin", "oth"), ("bin", "ter", "oth")]

DBG = False


# metrical (and enjambment) info ----------------------------------------------

def find_enjambment(tree, fn, exclude_expansion=False):
    """
    Return a dict with presence/absence of enjambment hashed by line number.

    Parameters
    ----------
    tree : :obj:`lxml.etree.ElementTree`
        Parsed xml for extracting.
    fn : str
        Name of file tree was parsed from. Used for printing messages.
    exclude_expansion : bool, default False
        Whether to include Spang's (1983) "expansion" cases in the counts
        (subj/obj in different line to its governing verb counted in or not).

    Returns
    -------
    tuple
        Contains (1) a dict with whether line is enjambed or not and
        (2) a boolean with whether poem has 14 lines or not.
    """
    not14 = 0
    n2enj = {}
    lines = tree.xpath("//tei:l", namespaces=nspaces)
    idx = 0
    for line in lines:
        try:
           idx = int(line.attrib["n"])
        except ValueError:
            # ValueError in ADSO given keys like c1 for copla line 1
            if DBG:
                print("   - Line has no attrib []".format(line.text))
        if len(lines) != 14 and idx == 1:
            not14 += 1
            if DBG:
                print(" - Fname: [{}]~~[{}] lines".format(fn, len(lines)))
            # count dictionary will be empty
            break
        if idx > 14:
            break
        if "enjamb" in line.attrib:
            try:
                if "B" in line.attrib["enjamb"]:
                    if exclude_expansion and "B-ex" in line.attrib["enjamb"]:
                        n2enj[idx] = "O"
                    else:
                        n2enj[idx] = "B"
                else:
                    n2enj[idx] = "O"
            except ValueError:
                print("   - Error with line [{}]".format(line.text))
                continue
        else:
            n2enj[idx] = "O"
    return n2enj, not14


def check_file_keep(fn, remove_list, silent=False):
    """
    Check whether file should be kept or filtered out.

    Check is based on the filename and on an iterable with
    information about filenames to exclude.

    Parameters
    ----------
    fn : str
        Filename to check.
    remove_list : list
        Iterable with information to check filenames against.
    silent: bool
        If silent, won't print any messages

    Returns
    -------
    bool
        Whether to keep file or not.
    """
    keep = True
    for pref in remove_list:
        if fn.startswith(pref):
            if DBG and not silent:
                print("    - Skipping [{}] from remove list".format(fn))
            keep = False
        if not keep:
            break
    return keep


def extract_stanza_boundaries(idir, ofn, sheetname, remove_list=authors_d,
                              exclude_expansion=False):
    """
    Extract lines at a stanza boundary and their enjambment tag
    for a directory writing out to a file.

    Also returns a hash so that results can be added to an ODS
    spreadsheet.

    Parameters
    ----------
    idir : str
        Input directory.
    ofn : str
        Output file.
    sheetname : str
        Name of tab for the spreadsheet data to return.
    remove_list : list
        Iterable with information about file names to ignore.
    exclude_expansion : bool, default False
        Whether to include Spang's (1983) "expansion" cases in the counts
        (subj/obj in different line to its governing verb counted in or not).

    Returns
    -------
    dict
        In :obj:`pyexcel_ods` format, to dump data to ODS sheet
    """
    ols = []
    for fn in os.listdir(idir):
        keep = check_file_keep(fn, remove_list, silent=True)
        if not keep:
            continue
        ffn = os.path.join(idir, fn)
        tree = etree.parse(ffn)
        lines = tree.xpath("//tei:l", namespaces=nspaces)
        for line in lines:
            try:
               idx = int(line.attrib["n"])
            except ValueError:
                # ValueError in Navarro given keys like c1 for copla line 1
                if DBG:
                    print("   - Line no attrib [{}]".format(
                        line.text.decode("utf8") if isinstance(line.text, str)
                        else line.text.encode("utf8")))
                continue
            if int(idx) in (4, 8, 11):
                ol = []
                if "enjamb" in line.attrib and line.attrib["enjamb"].startswith("B"):
                    if exclude_expansion and "B-ex" in line.attrib["enjamb"]:
                        continue
                    cur_txt = line.text
                    next_line = lines[idx]
                    fn = fn.decode("utf8") if isinstance(fn, str) else fn
                    ol.append("\t".join(
                        [fn, cur_txt, str(idx), line.attrib["enjamb"]]))
                    ol.append("\t".join(
                        [fn, next_line.text, str(idx+1),
                         next_line.attrib["enjamb"]]))
                    ols.extend(ol)
    with codecs.open(ofn, "w", "utf8") as ofh:
        header = "FileName\tLine\tLNbr\tEnjType\n"
        ofh.write(header)
        ofh.write("\n".join(ols))
    data_for_ods = [header.strip().split("\t")]
    data_for_ods.extend([ll.split("\t") for ll in ols])
    return {sheetname: data_for_ods}
