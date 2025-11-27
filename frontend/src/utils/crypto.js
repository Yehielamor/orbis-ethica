/**
 * Crypto Utilities for Orbis Ethica
 * Uses TweetNaCl (loaded via CDN as window.nacl)
 */

const KEY_STORAGE_KEY = 'orbis_identity_v1';

export const cryptoUtils = {
    /**
     * Get or create a keypair for the current user.
     * Persists to localStorage.
     */
    getOrCreateIdentity: () => {
        const stored = localStorage.getItem(KEY_STORAGE_KEY);
        if (stored) {
            try {
                const data = JSON.parse(stored);
                return {
                    publicKey: data.publicKey,
                    secretKey: nacl.util.decodeBase64(data.secretKey) // Decode from storage format
                };
            } catch (e) {
                console.error("Failed to load identity", e);
            }
        }
        return cryptoUtils.generateIdentity();
    },

    /**
     * Generate a new Ed25519 keypair and save to storage.
     */
    generateIdentity: () => {
        const keyPair = nacl.sign.keyPair();
        const publicKeyHex = nacl.util.encodeHex(keyPair.publicKey);
        const secretKeyBase64 = nacl.util.encodeBase64(keyPair.secretKey);

        const identity = {
            publicKey: publicKeyHex,
            secretKey: secretKeyBase64
        };

        localStorage.setItem(KEY_STORAGE_KEY, JSON.stringify(identity));

        return {
            publicKey: publicKeyHex,
            secretKey: keyPair.secretKey
        };
    },

    /**
     * Sign a request payload.
     * Returns headers object.
     */
    signRequest: (method, path, body, identity) => {
        const timestamp = Math.floor(Date.now() / 1000).toString();

        // Canonicalize body (same as backend)
        // If body is empty/null, use empty string? No, backend expects JSON usually.
        // If body is object, stringify with sorted keys.
        let bodyStr = "";
        if (body) {
            // Simple canonicalization: JSON.stringify is usually sufficient for simple objects
            // but strictly we should sort keys. 
            // For this MVP, we rely on standard JSON.stringify behavior matching Python's default
            // provided keys are inserted in order or we sort them.
            // Let's do a basic sort.
            const sortedKeys = Object.keys(body).sort();
            const sortedObj = {};
            sortedKeys.forEach(k => sortedObj[k] = body[k]);
            bodyStr = JSON.stringify(sortedObj);
        }

        const payload = `${method.toUpperCase()}:${path}:${timestamp}:${bodyStr}`;
        const payloadBytes = nacl.util.decodeUTF8(payload);

        const signatureBytes = nacl.sign.detached(payloadBytes, identity.secretKey);
        const signatureHex = nacl.util.encodeHex(signatureBytes);

        return {
            'X-Pubkey': identity.publicKey,
            'X-Timestamp': timestamp,
            'X-Signature': signatureHex
        };
    }
};
