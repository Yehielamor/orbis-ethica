import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6429/api';

export const LedgerService = {
    getBlocks: async (limit = 10, offset = 0) => {
        try {
            const response = await axios.get(`${API_URL}/ledger/blocks`, {
                params: { limit, offset }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching blocks:', error);
            throw error;
        }
    },

    getTransactions: async (limit = 20, offset = 0) => {
        try {
            const response = await axios.get(`${API_URL}/ledger/transactions`, {
                params: { limit, offset }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching transactions:', error);
            throw error;
        }
    },

    getWallet: async () => {
        try {
            const response = await axios.get(`${API_URL}/wallet`);
            return response.data;
        } catch (error) {
            console.error('Error fetching wallet:', error);
            throw error;
        }
    }
};
