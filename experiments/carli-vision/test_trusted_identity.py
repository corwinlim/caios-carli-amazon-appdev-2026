import unittest
from trusted_identity import IdentityDenied, mint_test_token, verify_owner_token

KEY = b"offline-demo-key-not-for-production"
NOW = 10000

class TrustedIdentityTests(unittest.TestCase):
    def token(self, **overrides):
        args = dict(subject="owner-a", pet_ids=["pika"], scopes=["care:propose"],
                    issued_at=NOW-60, expires_at=NOW+60)
        args.update(overrides)
        return mint_test_token(KEY, **args)

    def verify(self, token, **overrides):
        args = dict(secret=KEY, pet_id="pika", scope="care:propose", now=NOW)
        args.update(overrides)
        return verify_owner_token(token, **args)

    def test_valid(self):
        self.assertEqual(self.verify(self.token())["verified_owner_id"], "owner-a")

    def test_wrong_secret(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(), secret=b"wrong")

    def test_tampered_token(self):
        t = self.token()
        with self.assertRaises(IdentityDenied):
            self.verify(t[:-2] + ("A" if t[-2] != "A" else "B") + t[-1])

    def test_expired(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(expires_at=NOW))

    def test_future_issued(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(issued_at=NOW+1))

    def test_other_pet(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(), pet_id="other-pet")

    def test_missing_scope(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(), scope="care:execute")

    def test_revoked(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(), revoked_subjects={"owner-a"})

    def test_wrong_audience(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(audience="other"))

    def test_wrong_issuer(self):
        with self.assertRaises(IdentityDenied):
            self.verify(self.token(issuer="other"))

    def test_malformed(self):
        for token in ("", "a", "a.b.c", "a.b"):
            with self.subTest(token=token), self.assertRaises(IdentityDenied):
                self.verify(token)

if __name__ == "__main__":
    unittest.main()
