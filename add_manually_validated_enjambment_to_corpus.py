"""
Using the manually validated data for lines at stanza boundary,
correct the automatic annotations.
"""

from lxml import etree
import os
from pyexcel_ods import get_data
import re
from shutil import copy2

nspaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

# data where lines at stanza boundary were checked manually
validated_data = "data/enjambment_across_stanza_all_to_validate.ods"

# Corpora -----------------------------
disco_teidir = "corpora/disco/tei"
disco_subdirs = ['15th-17th', '18th', '19th']
adso_dir = "corpora/navarro/CorpusSonetosSigloDeOroWithEnjambment"
# Selected corpora
dirs_todo = []
for sc_name in disco_subdirs:
    dirs_todo.append(os.path.join(disco_teidir,
                                  os.path.join(sc_name, "per-sonnet")))
dirs_todo.insert(0, adso_dir)

# Correct cases as per manual annotations and write new files to '-validated' folders
for dname in dirs_todo:
    oname = dname + "-validated12"
    if not os.path.exists(oname):
        os.makedirs(oname)
    sheet_name = os.path.basename(os.path.split(dname)[0])
    data = get_data(validated_data)#, sheet_name)
    print("\n\n== {} ==\n".format(sheet_name))
    for fname in os.listdir(dname):
        change = False
        rows = [row for row in data[sheet_name] if len(row) > 0
                and row[0] == fname.decode("utf8")]
        if len(rows) != 0:
            parser = etree.XMLParser(remove_blank_text=True)
            kotree = etree.parse(os.path.join(dname, fname), parser).getroot()
            for row in rows:
                try:
                    # validation data
                    lnbr, etype, validation = row[2].strip(), row[3].strip(), row[4].strip()
                    # enj type was modified manually (only lines 4, 8, 11)
                    try:
                        mmodif = str(row[7]).strip()
                    except IndexError:
                        mmodif = "0"
                except IndexError:
                    continue
                assert kotree.xpath(
                    "//tei:l[@n='{}']/text()".format(lnbr),
                    namespaces=nspaces)[0] == row[1]
                #if validation == "ko":
                if validation == "ko" or mmodif == "1":
                    # find elements with wrong enjambment
                    bad_enj_node_B = kotree.xpath(
                        "//tei:l[@n='{}']".format(lnbr), namespaces=nspaces)[0]
                    bad_enj_node_I = kotree.xpath("//tei:l[@n='{}']".format(str(int(lnbr)+1)),
                                                  namespaces=nspaces)[0]
                    bad_enj_value_B = bad_enj_node_B.xpath("@enjamb")[0]
                    bad_enj_value_I = bad_enj_node_I.xpath("@enjamb")[0]
                    # correct values
                    #  remove if no enjambment should be there
                    if validation == "ko":
                        ok_enj_value_B = re.sub(r"B-\w+", "", bad_enj_value_B).strip()
                        ok_enj_value_I = re.sub(r"I-\w+", "", bad_enj_value_I).strip()
                        # set corrected values
                        bad_enj_node_B.attrib['enjamb'] = ok_enj_value_B
                        bad_enj_node_I.attrib['enjamb'] = ok_enj_value_I
                        # remove attribute if it is now empty
                        for ele in bad_enj_node_B, bad_enj_node_I:
                            if ele.attrib['enjamb'] == "":
                                ele.attrib.pop('enjamb')
                    #   modify with value from sheet if position was ok but type was ko
                    #   (mmodif there only in across stanza boundary, modified manually on sheet)
                    elif mmodif == "1":
                        # B- value from sheet directly
                        ok_enj_value_B = etype.strip()
                        # I- value needs to be recreated
                        #   remove old I
                        initial_correction_I = re.sub(r"I-\w+", "", bad_enj_value_I).strip()
                        #   create new I from new B
                        add_to_I = etype.strip().replace("B-", "I-").strip()
                        #   concatenate
                        new_I_full = "{} {}".format(initial_correction_I.strip(), add_to_I.strip())
                        #   deduplicate
                        enj_set_I = " ".join(sorted(set(new_I_full.split(" "))))
                        ok_enj_value_I = enj_set_I.strip()
                        # set corrected values
                        bad_enj_node_B.attrib['enjamb'] = ok_enj_value_B
                        bad_enj_node_I.attrib['enjamb'] = ok_enj_value_I
                    change = True

            # serialize corrected file
            if change:
                sertree = etree.tostring(kotree, xml_declaration=True,
                                         encoding="utf8", pretty_print=True)
                with open(os.path.join(oname, fname), "wb") as ofh:
                    print("=> {}".format(os.path.basename(fname)))
                    ofh.write(sertree)
            else:
                copy2(os.path.join(dname, fname), os.path.join(oname, fname))
        else:
            copy2(os.path.join(dname, fname), os.path.join(oname, fname))
