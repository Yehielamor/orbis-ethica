import unittest
from solcx import compile_source, install_solc
from eth_tester import EthereumTester
from web3 import Web3, EthereumTesterProvider
import os

# Install specific solc version
install_solc('0.8.0')

class TestOrbisContracts(unittest.TestCase):
    def setUp(self):
        self.tester = EthereumTester()
        self.w3 = Web3(EthereumTesterProvider(self.tester))
        self.accounts = self.w3.eth.accounts
        self.owner = self.accounts[0]
        self.user1 = self.accounts[1]
        self.treasury = self.accounts[2]

    def compile_contract(self, file_path):
        with open(file_path, 'r') as f:
            source = f.read()
        
        compiled = compile_source(
            source,
            output_values=['abi', 'bin'],
            solc_version='0.8.0'
        )
        contract_id, contract_interface = next(iter(compiled.items()))
        return contract_interface

    def test_orbis_token_lifecycle(self):
        print("\nTesting OrbisToken (ETHC)...")
        interface = self.compile_contract('contracts/OrbisToken.sol')
        
        # Deploy
        OrbisToken = self.w3.eth.contract(abi=interface['abi'], bytecode=interface['bin'])
        tx_hash = OrbisToken.constructor().transact({'from': self.owner})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        token = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=interface['abi'])
        
        print(f"✅ Deployed at {token.address}")

        # 1. Mint (Reward)
        mint_amount = self.w3.to_wei(1000, 'ether')
        token.functions.mint(self.user1, mint_amount).transact({'from': self.owner})
        balance = token.functions.balanceOf(self.user1).call()
        self.assertEqual(balance, mint_amount)
        print(f"✅ Minted 1000 ETHC to User1")

        # 2. Transfer (Payment)
        transfer_amount = self.w3.to_wei(100, 'ether')
        token.functions.transfer(self.treasury, transfer_amount).transact({'from': self.user1})
        treasury_balance = token.functions.balanceOf(self.treasury).call()
        self.assertEqual(treasury_balance, transfer_amount)
        print(f"✅ Transferred 100 ETHC to Treasury")

        # 3. Burn (Fee)
        burn_amount = self.w3.to_wei(10, 'ether')
        token.functions.burn(burn_amount).transact({'from': self.user1})
        final_balance = token.functions.balanceOf(self.user1).call()
        expected_balance = mint_amount - transfer_amount - burn_amount
        self.assertEqual(final_balance, expected_balance)
        print(f"✅ Burned 10 ETHC from User1")

    def test_compliance_node_license(self):
        print("\nTesting ComplianceNode (NFT)...")
        interface = self.compile_contract('contracts/ComplianceNode.sol')
        
        # Deploy
        ComplianceNode = self.w3.eth.contract(abi=interface['abi'], bytecode=interface['bin'])
        tx_hash = ComplianceNode.constructor().transact({'from': self.owner})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        nft = self.w3.eth.contract(address=tx_receipt.contractAddress, abi=interface['abi'])
        
        print(f"✅ Deployed at {nft.address}")

        # 1. Mint License
        nft.functions.mintNodeLicense(self.user1).transact({'from': self.owner})
        balance = nft.functions.balanceOf(self.user1).call()
        self.assertEqual(balance, 1)
        print(f"✅ Minted License to User1")

        # 2. Check Validity
        is_valid = nft.functions.isValidNode(self.user1).call()
        self.assertTrue(is_valid)
        print(f"✅ User1 is a valid node")

        is_valid_random = nft.functions.isValidNode(self.treasury).call()
        self.assertFalse(is_valid_random)
        print(f"✅ Random user is NOT a valid node")

if __name__ == '__main__':
    unittest.main()
