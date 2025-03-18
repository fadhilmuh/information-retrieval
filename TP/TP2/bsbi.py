import os
import pickle
import contextlib
import heapq
import time

from index import InvertedIndexReader, InvertedIndexWriter
from util import IdMap, QueryParser, sort_diff_list, sort_intersect_list, sort_union_list
from compression import StandardPostings, VBEPostings, Simple8bPostings, EliasGammaPostings

from nltk.corpus import stopwords

import gc

# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')

""" 
Ingat untuk install tqdm terlebih dahulu
pip intall tqdm
"""
from tqdm import tqdm

class BSBIIndex:
    """
    Attributes
    ----------
    term_id_map(IdMap): Untuk mapping terms ke termIDs
    doc_id_map(IdMap): Untuk mapping relative paths dari dokumen (misal,
                    /collection/0/gamma.txt) to docIDs
    data_path(str): Path ke data
    output_path(str): Path ke output index files
    postings_encoding: Lihat di compression.py, kandidatnya adalah StandardPostings,
                    VBEPostings, dsb.
    index_name(str): Nama dari file yang berisi inverted index
    """
    def __init__(self, data_path, output_path, postings_encoding, index_name = "main_index"):
        self.term_id_map = IdMap()
        self.doc_id_map = IdMap()
        self.data_path = data_path
        self.output_path = output_path
        self.index_name = index_name
        self.postings_encoding = postings_encoding

        # Untuk menyimpan nama-nama file dari semua intermediate inverted index
        self.intermediate_indices = []

    def save(self):
        """Menyimpan doc_id_map and term_id_map ke output directory via pickle"""

        with open(os.path.join(self.output_path, 'terms.dict'), 'wb') as f:
            pickle.dump(self.term_id_map, f)
        with open(os.path.join(self.output_path, 'docs.dict'), 'wb') as f:
            pickle.dump(self.doc_id_map, f)

    def load(self):
        """Memuat doc_id_map and term_id_map dari output directory"""

        with open(os.path.join(self.output_path, 'terms.dict'), 'rb') as f:
            self.term_id_map = pickle.load(f)
        with open(os.path.join(self.output_path, 'docs.dict'), 'rb') as f:
            self.doc_id_map = pickle.load(f)

    def start_indexing(self):
        """
        Base indexing code
        BAGIAN UTAMA untuk melakukan Indexing dengan skema BSBI (blocked-sort
        based indexing)

        Method ini scan terhadap semua data di collection, memanggil parse_block
        untuk parsing dokumen dan memanggil invert_write yang melakukan inversion
        di setiap block dan menyimpannya ke index yang baru.
        """
        # loop untuk setiap sub-directory di dalam folder collection (setiap block)]
        for block_path in tqdm(sorted(next(os.walk(self.data_path))[1])):
            gc.collect()
            td_pairs = self.parsing_block(block_path)
            index_id = 'intermediate_index_'+block_path
            self.intermediate_indices.append(index_id)
            with InvertedIndexWriter(index_id, self.postings_encoding, path = self.output_path) as index:
                self.write_to_index(td_pairs, index)
                td_pairs = None
    
        self.save()

        gc.collect()
        with InvertedIndexWriter(self.index_name, self.postings_encoding, path = self.output_path) as merged_index:
            with contextlib.ExitStack() as stack:
                indices = [stack.enter_context(InvertedIndexReader(index_id, self.postings_encoding, path=self.output_path))
                               for index_id in self.intermediate_indices]
                self.merge_index(indices, merged_index)

    def parsing_block(self, block_path):
        """
        Lakukan parsing terhadap text file sehingga menjadi sequence of
        <termID, docID> pairs.

        Anda bisa menggunakan stemmer bahasa Inggris yang tersedia, seperti Porter Stemmer
        https://github.com/evandempsey/porter2-stemmer

        Untuk membuang stopwords, Anda dapat menggunakan library seperti NLTK.

        Untuk "sentence segmentation" dan "tokenization", bisa menggunakan
        regex atau boleh juga menggunakan tools lain yang berbasis machine
        learning.

        Parameters
        ----------
        block_path : str
            Relative Path ke directory yang mengandung text files untuk sebuah block.

            CATAT bahwa satu folder di collection dianggap merepresentasikan satu block.
            Konsep block di soal tugas ini berbeda dengan konsep block yang terkait
            dengan operating systems.

        Returns
        -------
        List[Tuple[Int, Int]]
            Returns all the td_pairs extracted from the block
            Mengembalikan semua pasangan <termID, docID> dari sebuah block (dalam hal
            ini sebuah sub-direktori di dalam folder collection)

        Harus menggunakan self.term_id_map dan self.doc_id_map untuk mendapatkan
        termIDs dan docIDs. Dua variable ini harus persis untuk semua pemanggilan
        parse_block(...).
        """
        import re
        from porter2stemmer import Porter2Stemmer
        stemmer = Porter2Stemmer()
        en_stopwords = stopwords.words('english')
        td_pairs = []
        block_dir = os.path.join(self.data_path, block_path)
        for filename in sorted(os.listdir(block_dir)):
            file_path = os.path.join(block_dir, filename)
            if os.path.isfile(file_path):
                # Map document relative path to docID
                doc_id = self.doc_id_map[os.path.join(block_path, filename)]
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                tokens = re.findall(r'\b\w+\b', text.lower())
                # Remove stopwords and punctuation
                tokens = [token for token in tokens if token.lower() not in en_stopwords]
                for token in tokens:
                    stemmed = stemmer.stem(token)
                    term_id = self.term_id_map[stemmed]
                    td_pairs.append((term_id, doc_id))

        # Sort td_pairs by termID and docID
        td_pairs.sort(key=lambda x: (x[0], x[1]))  # Sort by termID first, then docID
        return td_pairs

    def write_to_index(self, td_pairs, index):
        """
        Melakukan inversion td_pairs (list of <termID, docID> pairs) dan
        menyimpan mereka ke index. Disini diterapkan konsep BSBI dimana 
        hanya di-mantain satu dictionary besar untuk keseluruhan block.
        Namun dalam teknik penyimpanannya digunakan srategi dari SPIMI
        yaitu penggunaan struktur data hashtable (dalam Python bisa
        berupa Dictionary)

        ASUMSI: td_pairs CUKUP di memori

        Parameters
        ----------
        td_pairs: List[Tuple[Int, Int]]
            List of termID-docID pairs
        index: InvertedIndexWriter
            Inverted index pada disk (file) yang terkait dengan suatu "block"
        """
        term_dict = {}
        for term_id, doc_id in td_pairs:
            if term_id not in term_dict:
                term_dict[term_id] = set()
            term_dict[term_id].add(doc_id)
        for term_id in sorted(term_dict.keys()):
            index.append(term_id, sorted(list(term_dict[term_id])))

    def merge_index(self, indices, merged_index):
        # Multiway merge using a heap. Each heap element is a tuple (term, unique_id, postings_list, reader)
        heap = []
        for reader in indices:
            try:
                term, postings = next(reader)
                heapq.heappush(heap, (term, id(reader), postings, reader))
            except StopIteration:
                pass
        
        while heap:
            current_term, _, postings, reader = heapq.heappop(heap)
            merged_postings = postings
            # Merge all entries with same term
            while heap and heap[0][0] == current_term:
                _, _, postings_next, reader_next = heapq.heappop(heap)
                merged_postings = sort_union_list(merged_postings, postings_next)
                try:
                    next_term, next_postings = next(reader_next)
                    heapq.heappush(heap, (next_term, id(reader_next), next_postings, reader_next))
                except StopIteration:
                    pass
            # Write merged postings for the term
            merged_index.append(current_term, merged_postings)
            try:
                next_term, next_postings = next(reader)
                heapq.heappush(heap, (next_term, id(reader), next_postings, reader))
            except StopIteration:
                pass

    def boolean_retrieve(self, query):
        try:
            self.load()
        except FileNotFoundError:
            print("Index files not found. Please run indexing first.")

        # Import stemmer when needed
        from porter2stemmer import Porter2Stemmer
        
        # Instantiate query parser with empty stopwords set.
        en_stopwords = stopwords.words('english')
        qp = QueryParser(query, Porter2Stemmer(), stopwords=en_stopwords)
        if not qp.is_valid():
            raise ValueError("Invalid query syntax.")
        postfix = qp.infix_to_postfix()
        stack = []
        # Open the merged index for operand retrieval
        with InvertedIndexReader(self.index_name, self.postings_encoding, path=self.output_path) as reader:
            for token in postfix:
                if token in ['AND', 'OR', 'DIFF']:
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    if token == 'AND':
                        result = sort_intersect_list(operand1, operand2)
                    elif token == 'OR':
                        result = sort_union_list(operand1, operand2)
                    elif token == 'DIFF':
                        result = sort_diff_list(operand1, operand2)
                    stack.append(result)
                else:
                    # For operand tokens, check if token exists in term_id_map.
                    if token in self.term_id_map.str_to_id:
                        term_id = self.term_id_map[token]
                        postings = reader.get_postings_list(term_id)
                    else:
                        postings = []
                    stack.append(postings)
            if stack:
                final_postings = stack.pop()
            else:
                final_postings = []
        # Map docIDs to document names using doc_id_map
        result_docs = [self.doc_id_map[doc_id] for doc_id in final_postings]
        return result_docs

if __name__ == "__main__":
    pass
    # BSBI_instance = BSBIIndex(data_path = 'arxiv_collections', \
    #                           postings_encoding = VBEPostings, \
    #                           output_path = 'index_vb')
    # BSBI_instance.start_indexing() # memulai indexing!

    # BSBI_instance_simple8b = BSBIIndex(data_path = 'arxiv_collections', \
    #                           postings_encoding = Simple8bPostings, \
    #                           output_path = 'index_simple8b')
    # BSBI_instance_simple8b.start_indexing() # memulai indexing!

    # BSBI_instance_elias_gamma = BSBIIndex(data_path = 'arxiv_collections', \
    #                             postings_encoding = EliasGammaPostings, \
    #                             output_path = 'index_eliasgamma')
    # BSBI_instance_elias_gamma.start_indexing() # memulai indexing!