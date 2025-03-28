class IdMap:
    """
    Ingat kembali di kuliah, bahwa secara praktis, sebuah dokumen dan
    sebuah term akan direpresentasikan sebagai sebuah integer. Oleh
    karena itu, kita perlu maintain mapping antara string term (atau
    dokumen) ke integer yang bersesuaian, dan sebaliknya. Kelas IdMap ini
    akan melakukan hal tersebut.
    """

    def __init__(self):
        """
        Mapping dari string (term atau nama dokumen) ke id disimpan dalam
        python's dictionary; cukup efisien. Mapping sebaliknya disimpan dalam
        python's list.

        contoh:
            str_to_id["halo"] ---> 8
            str_to_id["/collection/dir0/gamma.txt"] ---> 54

            id_to_str[8] ---> "halo"
            id_to_str[54] ---> "/collection/dir0/gamma.txt"
        """
        self.str_to_id = {}
        self.id_to_str = []

    def __len__(self):
        """Mengembalikan banyaknya term (atau dokumen) yang disimpan di IdMap."""
        return len(self.str_to_id)

    def __get_id(self, s):
        """
        Mengembalikan integer id i yang berkorespondensi dengan sebuah string s.
        Jika s tidak ada pada IdMap, lalu assign sebuah integer id baru dan kembalikan
        integer id baru tersebut.
        """
        if s in self.str_to_id:
            return self.str_to_id[s]
        else:
            new_id = len(self.str_to_id) + 1
            self.str_to_id[s] = new_id
            self.id_to_str.append(s)
            return new_id
    
    def __get_str(self, i):
        """Mengembalikan string yang terasosiasi dengan index i."""
        return self.id_to_str[i - 1]

    def __getitem__(self, key):
        """
        __getitem__(...) adalah special method di Python, yang mengizinkan sebuah
        collection class (seperti IdMap ini) mempunyai mekanisme akses atau
        modifikasi elemen dengan syntax [..] seperti pada list dan dictionary di Python.

        Silakan search informasi ini di Web search engine favorit Anda. Saya mendapatkan
        link berikut:

        https://stackoverflow.com/questions/43627405/understanding-getitem-method

        """
        return self.__get_id(key) if isinstance(key, str) else self.__get_str(key)

class QueryParser:
    """
    Class untuk melakukan parsing query untuk boolean search
    
    Parameters
    ----------
    query: str
        Query string yang akan di-parse. Input dijamin valid, tidak ada imbalanced parentheses.
        Tanda kurung buka dijamin "menempel" di awal kata yang mengikuti (atau tanda kurung buka lainnya) dan
        tanda kurung tutup dijamin "menempel" di akhir kata yang diikuti (atau tanda kurung tutup lainnya).
        Sebagai contoh, bisa lihat pada contoh method query_string_to_list() atau pada test case.
    stemmer
        Objek stemmer untuk stemming token
    stopwords: set
        Set yang berisi stopwords
    """
    def __init__(self, query: str, stemmer, stopwords: set):
        self.query = query
        self.stemmer = stemmer
        self.stopwords = stopwords
        self.token_list = self.__query_string_to_list()
        self.token_preprocessed = self.__preprocess_tokens()
    
    def is_valid(self):
        """
        Gunakan method ini untuk validasi query saat melakukan boolean retrieval,
        untuk menentukan apakah suatu query valid (tidak mengandung stopwords) atau tidak.
        """
        for token in self.token_list:
            if token in self.stopwords:
                return False
        return True

    def __query_string_to_list(self):
        """
        Melakukan parsing query dari yang berbentuk string menjadi list of tokens.
        Contoh: "term1 AND term2 OR (term3 DIFF term4)" --> ["term1", "AND", "term2", "OR", "(",
                                                             "term3", "DIFF", "term4", ")"]

        Returns
        -------
        List[str]
            query yang sudah di-parse
        """   
        tokens = []
        current = ""
        
        for char in self.query:
            if char == ' ':
                if current:
                    tokens.append(current)
                    current = ""
            elif char in '()':
                if current:
                    tokens.append(current)
                    current = ""
                tokens.append(char)
            else:
                current += char
        
        if current:
            tokens.append(current.lower())
        
        return tokens

    def __preprocess_tokens(self):
        """
        Melakukan pre-processing pada query input, cukup lakukan stemming saja.
        Asumsikan bahwa tidak ada stopwords yang diberikan pada query input.
        Jangan lakukan pre-processing pada token spesial ('AND', 'OR', 'DIFF', '(', ')')
        
        Returns
        -------
        List[str]
            Daftar token yang telah di-preprocess
        """
        result = []
        special_tokens = ['AND', 'OR', 'DIFF', '(', ')']
        
        for token in self.token_list:
            if token in special_tokens:
                result.append(token)
            else:
                result.append(self.stemmer.stem(token))
        
        return result

    def infix_to_postfix(self):
        """
        Fungsi ini mengubah ekspresi infix menjadi postfix dengan menggunakan Algoritma Shunting-Yard. 
        Evaluasi akan dilakukan secara postfix juga. Gunakan tokens yang sudah di-pre-processed.
        Contoh: "A AND B" (infix) --> ["A", "B", "AND"] (postfix)
        Untuk selengkapnya, silakan lihat algoritma berikut: 
        https://www.geeksforgeeks.org/convert-infix-expression-to-postfix-expression/

        Returns
        -------
        list[str]
            list yang berisi token dalam ekspresi postfix
        """
        precedence = {'OR': 1, 'AND': 2, 'DIFF': 2}
        output = []
        operator_stack = []
        
        for token in self.token_preprocessed:
            if token in ['AND', 'OR', 'DIFF']:
                while (operator_stack and operator_stack[-1] != '(' and 
                       precedence.get(operator_stack[-1], 0) >= precedence.get(token, 0)):
                    output.append(operator_stack.pop())
                operator_stack.append(token)
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output.append(operator_stack.pop())
                if operator_stack and operator_stack[-1] == '(':
                    operator_stack.pop()  # Pop the '('
            else:
                # If token is an operand, add to output
                output.append(token)
        
        # Pop all remaining operators
        while operator_stack:
            output.append(operator_stack.pop())
        
        return output

def sort_intersect_list(list_A, list_B):
    """
    Intersects two (ascending) sorted lists and returns the sorted result
    Melakukan Intersection dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-intersect.

    Returns
    -------
    List[Comparable]
        intersection yang sudah terurut
    """
    result = []
    i, j = 0, 0
    
    while i < len(list_A) and j < len(list_B):
        if list_A[i] == list_B[j]:
            result.append(list_A[i])
            i += 1
            j += 1
        elif list_A[i] < list_B[j]:
            i += 1
        else:
            j += 1
    
    return result

def sort_union_list(list_A, list_B):
    """
    Melakukan union dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-union.

    Returns
    -------
    List[Comparable]
        union yang sudah terurut
    """
    result = []
    i, j = 0, 0
    
    while i < len(list_A) and j < len(list_B):
        if list_A[i] == list_B[j]:
            result.append(list_A[i])
            i += 1
            j += 1
        elif list_A[i] < list_B[j]:
            result.append(list_A[i])
            i += 1
        else:
            result.append(list_B[j])
            j += 1
    
    # Add remaining elements
    while i < len(list_A):
        result.append(list_A[i])
        i += 1
        
    while j < len(list_B):
        result.append(list_B[j])
        j += 1
    
    return result

def sort_diff_list(list_A, list_B):
    """
    Melakukan difference dua (ascending) sorted lists dan mengembalikan hasilnya
    yang juga terurut.

    Parameters
    ----------
    list_A: List[Comparable]
    list_B: List[Comparable]
        Dua buah sorted list yang akan di-difference.

    Returns
    -------
    List[Comparable]
        difference yang sudah terurut
    """
    result = []
    i, j = 0, 0
    
    while i < len(list_A) and j < len(list_B):
        if list_A[i] == list_B[j]:
            i += 1
            j += 1
        elif list_A[i] < list_B[j]:
            result.append(list_A[i])
            i += 1
        else:
            j += 1
    
    # Add remaining elements from list_A
    while i < len(list_A):
        result.append(list_A[i])
        i += 1
    
    return result

if __name__ == '__main__':

    """
        NILAI DIGESER 1 ANGKA KARENA ID DIMULAI DARI 1
    """

    doc = ["halo", "semua", "selamat", "pagi", "semua"]
    term_id_map = IdMap()
    assert [term_id_map[term] for term in doc] == [1, 2, 3, 4, 2], "term_id salah"
    assert term_id_map[2] == "semua", "term_id salah"
    assert term_id_map[1] == "halo", "term_id salah"
    assert term_id_map["selamat"] == 3, "term_id salah"
    assert term_id_map["pagi"] == 4, "term_id salah"

    docs = ["/collection/0/data0.txt",
            "/collection/0/data10.txt",
            "/collection/1/data53.txt"]
    doc_id_map = IdMap()
    assert [doc_id_map[docname] for docname in docs] == [1, 2, 3], "docs_id salah"
    
    assert sort_intersect_list([2, 3, 4], [3, 4]) == [3, 4], "sorted_intersect salah"
    assert sort_intersect_list([5, 6], [2, 5, 8]) == [5], "sorted_intersect salah"
    assert sort_intersect_list([], []) == [], "sorted_intersect salah"

    assert sort_union_list([2, 3, 4], [3, 4]) == [2, 3, 4], "sorted_union salah"
    assert sort_union_list([5, 6], [2, 5, 8]) == [2, 5, 6, 8], "sorted_union salah"
    assert sort_union_list([], []) == [], "sorted_union salah"

    assert sort_diff_list([2, 3, 4], [3, 4]) == [2], "sorted_diff salah"
    assert sort_diff_list([5, 6], [2, 5, 8]) == [6], "sorted_diff salah"
    assert sort_diff_list([], []) == [], "sorted_diff salah"

    from porter2stemmer import Porter2Stemmer
    qp = QueryParser("((term1 AND term2) OR term3) DIFF (term6 AND (term4 OR term5) DIFF (term7 OR term8))", 
                     Porter2Stemmer(), set())
    assert qp.token_list == ['(', '(', 'term1', 'AND', 'term2', ')', 'OR', 'term3', ')', 
                                     'DIFF', '(', 'term6', 'AND', '(', 'term4', 'OR', 'term5', 
                                     ')', 'DIFF', '(', 'term7', 'OR', 'term8', ')', ')'], "parsing to list salah"
    assert qp.infix_to_postfix() == ['term1', 'term2', 'AND', 'term3', 'OR', 'term6', 'term4', 
                                     'term5', 'OR', 'AND', 'term7', 'term8', 'OR', 'DIFF', 'DIFF'], "postfix salah"
    
    qp1 = QueryParser("term1 OR ((term2 AND term3) DIFF (term4 OR term5))", Porter2Stemmer(), set())
    assert qp1.token_list == ['term1', 'OR', '(', '(', 'term2', 'AND', 'term3', ')', 'DIFF', 
                              '(', 'term4', 'OR', 'term5', ')', ')'], "parsing to list salah"
    assert qp1.infix_to_postfix() == ['term1', 'term2', 'term3', 'AND', 'term4', 'term5', 'OR', 
                                      'DIFF', 'OR'], "postfix salah"
