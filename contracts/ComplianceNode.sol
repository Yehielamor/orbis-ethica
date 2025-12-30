// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ComplianceNode (ORBIS-NODE)
 * @dev Implementation of the Orbis Node License (NFT).
 *      Standard ERC-721 logic for identifying authorized validators.
 */
contract ComplianceNode {
    string public name = "Orbis Node License";
    string public symbol = "ORBIS-NODE";

    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256) public balanceOf;
    mapping(uint256 => address) public getApproved;
    mapping(address => mapping(address => bool)) public isApprovedForAll;

    uint256 public nextTokenId = 1;
    address public owner;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == 0x80ac58cd || interfaceId == 0x5b5e139f;
    }

    function transferFrom(address from, address to, uint256 tokenId) external {
        require(ownerOf[tokenId] == from, "From is not owner");
        require(to != address(0), "Transfer to zero address");
        
        require(
            msg.sender == from || 
            getApproved[tokenId] == msg.sender || 
            isApprovedForAll[from][msg.sender],
            "Not authorized"
        );

        balanceOf[from]--;
        balanceOf[to]++;
        ownerOf[tokenId] = to;

        delete getApproved[tokenId];

        emit Transfer(from, to, tokenId);
    }

    function approve(address spender, uint256 tokenId) external {
        address _owner = ownerOf[tokenId];
        require(msg.sender == _owner || isApprovedForAll[_owner][msg.sender], "Not authorized");
        getApproved[tokenId] = spender;
        emit Approval(_owner, spender, tokenId);
    }

    function setApprovalForAll(address operator, bool approved) external {
        isApprovedForAll[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    /**
     * @dev Issue a new Node License to a validator.
     */
    function mintNodeLicense(address to) external onlyOwner {
        uint256 tokenId = nextTokenId;
        nextTokenId++;

        balanceOf[to]++;
        ownerOf[tokenId] = to;

        emit Transfer(address(0), to, tokenId);
    }

    /**
     * @dev Check if an address holds a valid node license.
     */
    function isValidNode(address node) external view returns (bool) {
        return balanceOf[node] > 0;
    }
}
