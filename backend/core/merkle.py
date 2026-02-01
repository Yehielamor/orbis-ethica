import hashlib


class MerkleTree:
    """
    Standard Merkle Tree implementation.
    Used to cryptographically verify the integrity of transactions in a block.
    """
    def __init__(self, transactions: list[str]):
        """
        Initialize with a list of transaction hashes (strings).
        """
        self.transactions = transactions
        self.tree = []
        self.root = self._build_tree()

    def _build_tree(self) -> str:
        """
        Builds the Merkle Tree and returns the Root Hash.
        """
        if not self.transactions:
            return hashlib.sha256(b"").hexdigest()

        # Start with the leaves (transaction hashes)
        current_level = self.transactions

        # Loop until we reach the root (single hash)
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                
                # If odd number of nodes, duplicate the last one
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left
                
                # Hash the pair
                combined = left + right
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(new_hash)
            
            current_level = next_level

        self.tree = current_level # In a full implementation, we'd store the whole tree
        return current_level[0]

    def get_root(self) -> str:
        return self.root
