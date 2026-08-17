import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    @unittest.skipUnless(
        shutil.which("pwsh") and shutil.which("sh"),
        "PowerShell and a POSIX shell are required for entrypoint parity testing",
    )
    def test_shell_and_powershell_generate_equivalent_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            home.mkdir()
            common = ["verify", "--profile", "home", "--home", str(home), "--json"]
            shell = subprocess.run(
                ["sh", str(ROOT / "installer" / "install.sh"), *common],
                check=False,
                capture_output=True,
                text=True,
            )
            powershell = subprocess.run(
                ["pwsh", "-NoProfile", "-File", str(ROOT / "installer" / "install.ps1"), *common],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(shell.returncode, powershell.returncode)
            self.assertEqual(json.loads(shell.stdout), json.loads(powershell.stdout))


if __name__ == "__main__":
    unittest.main()
