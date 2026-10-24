import tempfile
import unittest
from pathlib import Path
from audit_ledger import AuditLedger

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"audit.sqlite"
        self.ledger=AuditLedger(self.path)
        self.evidence="a"*64
        self.payload={"kind":"roi_motion","frames":83}

    def test_prepare_and_verify(self):
        self.ledger.prepare(self.evidence,self.payload)
        self.assertTrue(self.ledger.verify())

    def test_idempotent_prepare(self):
        self.assertEqual(self.ledger.prepare(self.evidence,self.payload,"fixed"),
                         self.ledger.prepare(self.evidence,self.payload,"fixed"))
        with self.ledger.db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM audit_events").fetchone()[0],1)

    def test_operation_collision(self):
        self.ledger.prepare(self.evidence,self.payload,"fixed")
        with self.assertRaises(ValueError):
            self.ledger.prepare(self.evidence,{"frames":84},"fixed")

    def test_ready_dry_run_no_network(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        self.ledger.transition(op,"pending","ready","approved_synthetic")
        result=self.ledger.dry_run(op)
        self.assertFalse(result["executed"])
        self.assertFalse(result["network_called"])
        self.assertTrue(self.ledger.verify())

    def test_pending_denied(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        with self.assertRaises(PermissionError): self.ledger.dry_run(op)

    def test_rejected_denied(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        self.ledger.transition(op,"pending","rejected","owner_rejected_synthetic")
        with self.assertRaises(PermissionError): self.ledger.dry_run(op)

    def test_duplicate_transition_denied(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        self.ledger.transition(op,"pending","ready","approved_synthetic")
        with self.assertRaises(PermissionError):
            self.ledger.transition(op,"pending","ready","approved_synthetic")

    def test_restart_persistence(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        self.ledger.transition(op,"pending","ready","approved_synthetic")
        restarted=AuditLedger(self.path)
        self.assertTrue(restarted.verify())
        self.assertEqual(restarted.dry_run(op)["operation_id"],op)

    def test_unknown_dispatch_requires_manual_resolution(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        self.ledger.transition(op,"pending","ready","approved_synthetic")
        self.ledger.transition(op,"ready","dispatched_unknown","simulated_dispatch_uncertain")
        restarted=AuditLedger(self.path)
        self.assertEqual(restarted.unresolved(),[(op,"dispatched_unknown")])
        with self.assertRaises(PermissionError): restarted.dry_run(op)
        restarted.transition(op,"dispatched_unknown","resolved_manual","manual_reconciled")
        self.assertEqual(restarted.unresolved(),[])

    def test_tamper_detected(self):
        op=self.ledger.prepare(self.evidence,self.payload)
        with self.ledger.db() as db:
            db.execute("UPDATE audit_events SET event='changed' WHERE operation_id=?",(op,))
        self.assertFalse(self.ledger.verify())

    def test_invalid_evidence(self):
        with self.assertRaises(ValueError): self.ledger.prepare("bad",self.payload)

if __name__=="__main__": unittest.main()
