
"""
Sumber: https://www.geeksforgeeks.org/optimal-binary-search-tree-dp-24/
"""
def sum_freq(freq, i, j):
    return sum(freq[i:j+1])

def optimalSearchTree(keys, freq):
    n = len(keys)

    # Create 2D table to store results of subproblems
    dp = [[0] * n for _ in range(n)]
    root = [[0] * n for _ in range(n)]  # Stores root of optimal BST

    # For single key, cost is frequency of the key
    for i in range(n):
        dp[i][i] = freq[i]
        root[i][i] = i  # Single element is the root

    # Consider chains of length 2, 3, ... n
    for l in range(2, n + 1):
        for i in range(n - l + 1):
            j = i + l - 1
            dp[i][j] = float('inf')
            fsum = sum_freq(freq, i, j)

            # Try making each key in range [i..j] root
            for r in range(i, j + 1):
                c = ((dp[i][r - 1] if r > i else 0) +
                     (dp[r + 1][j] if r < j else 0) +
                     fsum)

                if c < dp[i][j]:
                    dp[i][j] = c
                    root[i][j] = r  # Store root

    return dp[0][n - 1], root

def construct_tree(root, keys, i, j):
    if i > j:
        return None
    r = root[i][j]
    return {
        "key": keys[r],
        "left": construct_tree(root, keys, i, r - 1),
        "right": construct_tree(root, keys, r + 1, j)
    }

def print_tree(tree, level=0, prefix=""):
    if tree is not None:
        print(" " * (4 * level) + prefix + str(tree["key"]))
        if tree["left"] or tree["right"]:
            print_tree(tree["left"], level + 1, "L--- ")
            print_tree(tree["right"], level + 1, "R--- ")


keys = ["aku", "cari", "nasi", "uduk"]
freq = [10, 5, 20, 15]

cost, root = optimalSearchTree(keys, freq)
tree = construct_tree(root, keys, 0, len(keys) - 1)

print_tree(tree)
print(cost)