# Boolean Retrieval System with BSBI Algorithm

This project implements a Boolean Retrieval System that leverages the Blocked Sort-Based Indexing (BSBI) algorithm alongside multiple postings list compression techniques, developed as part of the information retrieval course at Universitas Indonesia.

## Project Overview

This information retrieval system implements:
- BSBI (Blocked Sort-Based Indexing) for efficient index construction
- Boolean query processing with AND, OR, and DIFF (difference) operators
- Multiple compression techniques for postings lists:
    - Standard Postings (uncompressed)
    - Variable-Byte Encoding (VBE)
    - Simple8b encoding
    - Elias Gamma encoding

## Requirements

- Python 3.6+
- NLTK
- Porter2Stemmer
- tqdm
- bitarray (for Elias Gamma encoding)

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
```bash
pip install nltk tqdm bitarray
pip install porter2stemmer
```

3. Download NLTK resources:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## File Structure

- `bsbi.py`: Implementation of the BSBI indexing algorithm
- `compression.py`: Implementations of different postings list compression techniques
- `index.py`: Classes for reading and writing inverted indices
- `util.py`: Utility functions for query parsing, list operations, and ID mapping
- `search.py`: Script for performing searches on the built indices

## Usage

### 1. Prepare your collection

Place your document collection in a directory structure where each subdirectory represents a block. For example:
```
arxiv_collections/
├── 0/
│   ├── document1.txt
│   ├── document2.txt
│   └── ...
├── 1/
│   ├── document3.txt
│   ├── document4.txt
│   └── ...
└── ...
```

### 2. Build the index

To build indices with different compression methods:

```python
from bsbi import BSBIIndex
from compression import VBEPostings, Simple8bPostings, EliasGammaPostings

# Build index with Variable-Byte Encoding
BSBI_instance = BSBIIndex(
        data_path='arxiv_collections',
        postings_encoding=VBEPostings,
        output_path='index_vb'
)
BSBI_instance.start_indexing()

# Build index with Simple8b encoding
BSBI_instance_simple8b = BSBIIndex(
        data_path='arxiv_collections',
        postings_encoding=Simple8bPostings,
        output_path='index_simple8b'
)
BSBI_instance_simple8b.start_indexing()

# Build index with Elias Gamma encoding
BSBI_instance_elias_gamma = BSBIIndex(
        data_path='arxiv_collections',
        postings_encoding=EliasGammaPostings,
        output_path='index_eliasgamma'
)
BSBI_instance_elias_gamma.start_indexing()
```

### 3. Perform searches

Use the `boolean_retrieve` method to execute boolean queries:

```python
# Example queries
queries = ["(cosmological AND (quantum OR continuum)) AND geodesics"]

for query in queries:
        print("Query  : ", query)
        print("Results:")
        results = BSBI_instance.boolean_retrieve(query)
        print(len(results), "results found")
        for doc in results[:5]:  # Print first 5 results
                print(doc)
```

## Query Syntax

The system supports boolean queries with the following operators:
- `AND`: Intersection of two result sets
- `OR`: Union of two result sets
- `DIFF`: Difference between two result sets (set subtraction)

Parentheses can be used to group expressions and control precedence.

## Implementation Details

- The BSBI algorithm divides the document collection into blocks, indexes each block separately, and then merges the blocks to create the final index.
- Query processing uses the Shunting-Yard algorithm to convert infix notation to postfix notation for evaluation.
- Each compression technique offers different space-time trade-offs:
    - Standard Postings: No compression (baseline)
    - VBE: Variable-Byte Encoding for efficient storage of small integers
    - Simple8b: Word-aligned compression method that packs multiple integers into 64-bit words
    - Elias Gamma: Prefix code that is efficient for small positive integers

## Performance Considerations

The choice of compression method affects both index size and query performance. Generally:
- Standard Postings: Fastest retrieval but largest index size
- VBE: Good balance between compression and speed
- Simple8b: Better compression than VBE, slightly slower retrieval
- Elias Gamma: Best compression, but slowest retrieval