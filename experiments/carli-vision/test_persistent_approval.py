import concurrent.futures, tempfile, unittest
from pathlib import Path
from persistent_approval import PersistentApproval, mcp_dry_run

class PersistentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test.sqlite"
        self.now=1000
        self.gate=PersistentApproval(self.path,clock=lambda:self.now)
        self.payload={"kind":"roi_motion","count":83}
        self.token=self.gate.prepare("synthetic-owner","record_observation",self.payload)

    def approve(self,gate=None,token=None,owner="synthetic-owner",action="record_observation",payload=None):
        return (gate or self.gate).approve(token or self.token,owner,action,self.payload if payload is None else payload)

    def test_single_use(self):
        self.assertEqual(self.approve()["status"],"approved_once")
        with self.assertRaises(PermissionError): self.approve()

    def test_restart_persistence(self):
        self.approve()
        with self.assertRaises(PermissionError):
            self.approve(gate=PersistentApproval(self.path,clock=lambda:self.now))

    def test_parallel_one_winner(self):
        def attempt(_):
            try:
                self.approve(gate=PersistentApproval(self.path,clock=lambda:self.now))
                return True
            except PermissionError: return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt,range(12))),1)

    def test_wrong_owner(self):
        with self.assertRaises(PermissionError): self.approve(owner="wrong")

    def test_tampered_payload(self):
        with self.assertRaises(PermissionError): self.approve(payload={"kind":"roi_motion","count":84})

    def test_tampered_action(self):
        with self.assertRaises(PermissionError): self.approve(action="delete_observation")

    def test_expired(self):
        self.now=1060
        with self.assertRaises(PermissionError): self.approve()

    def test_rejected(self):
        self.gate.reject(self.token,"synthetic-owner")
        with self.assertRaises(PermissionError): self.approve()

    def test_dry_run(self):
        result=mcp_dry_run(self.approve())
        self.assertFalse(result["executed"])
        self.assertFalse(result["network_called"])

    def test_dry_run_denies_pending(self):
        with self.assertRaises(PermissionError): mcp_dry_run({"status":"pending","mcp_tool_invoked":False})

    def test_dry_run_denies_other_action(self):
        token=self.gate.prepare("synthetic-owner","delete_observation",{})
        with self.assertRaises(PermissionError):
            mcp_dry_run(self.approve(token=token,action="delete_observation",payload={}))

if __name__=="__main__": unittest.main()
