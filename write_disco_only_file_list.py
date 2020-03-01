"""
Get list of files in DISCO Golden Age partition that are not in Navarro's corpus
"""

import codecs
import os
import analyze_corpus_overlap as co

ddir = "corpora/disco/tei/15th-17th/per-sonnet"
of = "data/filenames_disco_only.txt"

skip_prefixes = co.authors_d

keeps = set()
for fn in os.listdir(ddir):
    skip = False
    for pref in skip_prefixes:
        if pref in fn:
            skip = True
            break
    if not skip:
        # 'fn' changes for compatibility with filenames in earlier DISCO versions
        keeps.add(u"xv-xvii_cvc_sonnets/{}".format(
            fn.decode("utf8").replace("g~~", "~~").replace("xml", "txt")))

with codecs.open(of, "w", "utf8") as oufh:
    oufh.write("\n".join(sorted(keeps)))
