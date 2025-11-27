from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError

def verify_log_data():
    pubkey_hex = "83a850469cbcb348c5bdf62b1c120edd444c90d1e200ef934c91a2f10f40450d"
    signature_hex = "4e738dc290a4116174feeaf8ccd1a9b9236ae133562870ae5a7719b13990d37332e1b358263f82cb0074a9194ecb5b3fd0a62bdf102aa727fbd8198e621b8604"
    payload = 'POST:/api/proposals/submit:1764247835:{"affected_parties":["Citizens","Law enforcement"],"author":"83a850469cbcb348c5bdf62b1c120edd444c90d1e200ef934c91a2f10f40450d","category":"HIGH_IMPACT","context":{},"description":"Implement city-wide facial recognition to reduce crime by 40%. Includes 24/7 monitoring and centralized database.","domain":"SECURITY","submitter_id":"DAO_Rep_1","title":"Mandatory Biometric Surveillance for Public Safety"}'

    print(f"Payload length: {len(payload)}")
    print(f"Payload: {payload}")

    try:
        verify_key = VerifyKey(pubkey_hex, encoder=HexEncoder)
        verify_key.verify(payload.encode('utf-8'), bytes.fromhex(signature_hex))
        print("✅ SUCCESS: Signature is VALID for this payload.")
    except BadSignatureError:
        print("❌ FAILURE: Signature is INVALID for this payload.")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    verify_log_data()
