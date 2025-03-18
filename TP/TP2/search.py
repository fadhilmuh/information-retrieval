from bsbi import BSBIIndex
from compression import VBEPostings, Simple8bPostings, EliasGammaPostings

# sebelumnya sudah dilakukan indexing
# BSBIIndex hanya sebagai abstraksi untuk index tersebut
BSBI_instance = BSBIIndex(data_path = 'arxiv_collections', \
                          postings_encoding = VBEPostings, \
                          output_path = 'index_vb')

BSBI_instance_simple8b = BSBIIndex(data_path = 'arxiv_collections', \
                          postings_encoding = Simple8bPostings, \
                          output_path = 'index_simple8b')

BSBI_instance_elias_gamma = BSBIIndex(data_path = 'arxiv_collections', \
                          postings_encoding = EliasGammaPostings, \
                          output_path = 'index_eliasgamma')

queries = ["(cosmological AND (quantum OR continuum)) AND geodesics"]
# queries = ["(cosmological AND (quantum OR continuum)) OR geodesics"]
# queries = ["cosmological AND quantum"]
# queries = ["((enhanced) OR (sensitivity) OR (signal)) AND (cosmological)"]
# queries = ["fully AND differential AND calculation AND perturbative AND quantum AND chromodynamics AND presented AND production AND massive AND photon AND pairs AND hadron AND colliders AND order AND perturbative AND contributions AND anti AND quark AND subprocesses AND included AND well AND resummation AND gluon AND radiation AND valid AND logarithmic AND accuracy AND region AND phase AND space AND specified AND calculation AND reliable AND Good AND agreement AND demonstrated AND data AND Fermilab AND Tevatron AND predictions AND made AND detailed AND tests AND CDF AND data AND Predictions AND shown AND distributions AND diphoton AND pairs AND produced AND energy AND Large AND Hadron AND Collider AND LHC AND Distributions AND diphoton AND pairs AND decay AND Higgs AND boson AND contrasted AND produced AND QCD AND processes AND LHC AND showing AND enhanced AND sensitivity AND signal AND obtained AND judicious AND selection AND events"]

for query in queries:
    print("Query  : ", query)
    print("Results:")
    res = BSBI_instance.boolean_retrieve(query)
    print(len(res), "results found")
    if len(res) > 0:
        print(res[0], res[-1])
    # for doc in BSBI_instance.boolean_retrieve(query):
    #     print(doc)
    print()

for query in queries:
    print("Query  : ", query)
    print("Results:")
    res = BSBI_instance_simple8b.boolean_retrieve(query)
    print(len(res), "results found")
    if len(res) > 0:
        print(res[0], res[-1])
    # for doc in BSBI_instance_simple8b.boolean_retrieve(query):
    #     print(doc)
    print()


for query in queries:
    print("Query  : ", query)
    print("Results:")
    res = BSBI_instance_elias_gamma.boolean_retrieve(query)
    print(len(res), "results found")
    if len(res) > 0:
        print(res[0], res[-1])
    # for doc in BSBI_instance_simple8b.boolean_retrieve(query):
    #     print(doc)
    print()