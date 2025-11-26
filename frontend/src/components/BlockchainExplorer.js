import React, { useState, useEffect } from 'react';
import { LedgerService } from '../services/ledger';
import {
    Box,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Card,
    CardContent,
    Grid,
    Chip,
    Container,
    Tab,
    Tabs
} from '@mui/material';
import {
    ViewInAr,
    ReceiptLong,
    AccountBalanceWallet,
    VerifiedUser
} from '@mui/icons-material';

const BlockchainExplorer = () => {
    const [blocks, setBlocks] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [wallet, setWallet] = useState(null);
    const [tabValue, setTabValue] = useState(0);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const blocksData = await LedgerService.getBlocks();
                setBlocks(blocksData.blocks);

                const txData = await LedgerService.getTransactions();
                setTransactions(txData.transactions);

                const walletData = await LedgerService.getWallet();
                setWallet(walletData);
            } catch (error) {
                console.error("Failed to fetch ledger data", error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // Auto-refresh
        return () => clearInterval(interval);
    }, []);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Typography variant="h4" gutterBottom sx={{ color: 'white', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 2 }}>
                <ViewInAr fontSize="large" /> Orbis Ethica Explorer
            </Typography>

            {/* Wallet Summary */}
            {wallet && (
                <Card sx={{ mb: 4, background: 'rgba(255, 255, 255, 0.05)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    <CardContent>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" color="text.secondary">My Address</Typography>
                                <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#4caf50' }}>
                                    {wallet.address}
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" color="text.secondary">Balance</Typography>
                                <Typography variant="h5" sx={{ color: 'white' }}>
                                    {wallet.liquid_balance.toLocaleString()} ETHC
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={4}>
                                <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                                <Chip
                                    icon={<VerifiedUser />}
                                    label={wallet.is_validator ? "Validator" : "Observer"}
                                    color={wallet.is_validator ? "success" : "default"}
                                    variant="outlined"
                                />
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            )}

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={tabValue} onChange={handleTabChange} textColor="inherit" indicatorColor="primary">
                    <Tab icon={<ViewInAr />} label="Latest Blocks" />
                    <Tab icon={<ReceiptLong />} label="Latest Transactions" />
                </Tabs>
            </Box>

            {/* Blocks Table */}
            {tabValue === 0 && (
                <TableContainer component={Paper} sx={{ background: 'rgba(0,0,0,0.2)' }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ color: '#aaa' }}>Height</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Hash</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Validator</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Txs</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Time</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {blocks.map((block) => (
                                <TableRow key={block.hash} hover>
                                    <TableCell sx={{ color: '#fff', fontWeight: 'bold' }}>#{block.index}</TableCell>
                                    <TableCell sx={{ fontFamily: 'monospace', color: '#4fc3f7' }}>
                                        {block.hash.substring(0, 16)}...
                                    </TableCell>
                                    <TableCell sx={{ color: '#fff' }}>{block.validator_id}</TableCell>
                                    <TableCell sx={{ color: '#fff' }}>{block.transactions_count}</TableCell>
                                    <TableCell sx={{ color: '#ccc' }}>{new Date(block.timestamp).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* Transactions Table */}
            {tabValue === 1 && (
                <TableContainer component={Paper} sx={{ background: 'rgba(0,0,0,0.2)' }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ color: '#aaa' }}>Type</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Sender</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Recipient</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Amount</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Description</TableCell>
                                <TableCell sx={{ color: '#aaa' }}>Time</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {transactions.map((tx) => (
                                <TableRow key={tx.id} hover>
                                    <TableCell>
                                        <Chip
                                            label={tx.type.toUpperCase()}
                                            size="small"
                                            color={tx.type === 'mint' ? 'success' : tx.type === 'transfer' ? 'primary' : 'default'}
                                        />
                                    </TableCell>
                                    <TableCell sx={{ fontFamily: 'monospace', color: '#ccc' }}>
                                        {tx.sender === 'system' ? 'SYSTEM' : tx.sender.substring(0, 12) + '...'}
                                    </TableCell>
                                    <TableCell sx={{ fontFamily: 'monospace', color: '#ccc' }}>
                                        {tx.recipient.substring(0, 12)}...
                                    </TableCell>
                                    <TableCell sx={{ color: '#fff', fontWeight: 'bold' }}>
                                        {tx.amount > 0 ? `${tx.amount} ETHC` : '-'}
                                    </TableCell>
                                    <TableCell sx={{ color: '#ccc', fontStyle: 'italic' }}>{tx.description}</TableCell>
                                    <TableCell sx={{ color: '#ccc' }}>{new Date(tx.timestamp).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
        </Container>
    );
};

export default BlockchainExplorer;
