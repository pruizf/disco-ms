#coding=utf-8

"""See which sonnets in disco are part of borja navarro's corpus"""

import codecs
import os
import re


# disco dir
ddir = "corpora/disco/txt/alltxt-per-author"
# borja dir
bdir = "corpora/navarro/CorpusSonetosSigloDeOroTXT_per-author"

authors_d = {
    'Arguijo,_Juan_de': 'JuanDeArguijo',
    'Cáncer_y_Velasco,_Jerónimo': 'CancerYVelasco',
    'Figueroa,_Francisco_de': 'FranciscoDeFigueroa',
    'Fray_Luis_de_León': 'FrayLuisDeLeon',
    'Henríquez_Gómez,_Antonio': 'AntonioEnriquezGomez',
    'Hurtado_de_Mendoza,_Antonio': 'AntonioHurtadoDeMendoza',
    'Jauregui,_Juan_de': 'JuanDeJauregui',
    'Marqués_de_Santillana': 'LopezDeMendoza',
    'Martín_de_la_Plaza,_Luis': 'LuisMartinDeLaPlaza',
    'Matos,_Gregorio_de': 'GregorioDeMatos',
    'Pantaleón_de_Ribera,_Anastasio': 'PantaleonDeRibera',
    'Polo_de_Medina,_Jacinto': 'PoloDeMedina',
    'Ramírez_Pagan,_Diego': 'DiegoRamirezPagan',
    'Rey_de_Artieda,_Andrés': 'ReyDeArtieda',
    'Salinas,_Juan_de': 'JuanDeSalinas',
    'Villegas,_Esteban_Manuel_de': 'EstebanManuelDeVillegas',
    'Virués,_Cristóbal_de': 'CristobalDeVirues'
}

max_possible = 0
if __name__ == "__main__":
    all_shared = 0
    for prefix in sorted(authors_d):
        curdir = [fname for fname in os.listdir(ddir) if fname.startswith(prefix)]
        assert len(curdir) == 1
        # DISCO directory name
        ddname = curdir[0]
        # accumulate incipits in borja's corpus
        bdname = os.path.join(bdir, authors_d[prefix])
        #b_incipits = []
        b_incipits = set()
        for bfname in os.listdir(bdname):
            bffname = os.path.join(bdname, bfname)
            with codecs.open(bffname, mode="r", encoding="utf8") as fh:
                txt = fh.read().strip()
                lines = re.split(r"\r?\n+", txt)
                assert len(lines) > 0
                b_incipits.add(lines[0].strip().lower())
        # check our incipits
        print("- {}".format(ddname))
        shared = 0
        fcurdir = os.path.join(ddir, ddname)
        inc_done = set()
        inc_skipped_done = set()
        for fname in os.listdir(fcurdir):
            ffname = os.path.join(fcurdir, fname)
            with codecs.open(ffname, mode="r", encoding="utf8") as fh:
                txt = fh.read().strip()
                lines = re.split(r"\r?\n+", txt)
                assert len(lines) > 0
                d_incipit = lines[0].strip().lower()
                if d_incipit in b_incipits and d_incipit not in inc_done:
                    shared += 1
                    inc_done.add(d_incipit)
                else:
                    fname = fname.decode("utf8") if isinstance(fname, str) else fname
                    d_incipit = d_incipit.decode("utf8") if \
                        isinstance(d_incipit, str) else d_incipit
                    print(u"  - {}\n    - {}".format(fname, d_incipit))
                    if d_incipit not in inc_skipped_done:
                        max_possible += 1
                    inc_skipped_done.add(d_incipit)
        all_shared += shared
        print("  Shared {} of {}".format(shared, len(os.listdir(fcurdir))))

    print("Total shared: {}".format(all_shared))
    # in case of punctuation or other small variations across Navarro vs. DISCO
    print("Possibly shared, additionally: {}".format(max_possible))

