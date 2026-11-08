"""Minimal SolidCraft MCP client (JSON-RPC 2.0 over stdio, standard library only).

Spawns `solidcraft-cli mcp --connect 127.0.0.1:<port> --allow-path <dir>...`
and talks to the running SolidCraft app (`solidcraft --control 7878`).
One app instance holds one shared design state: use one client at a time.
"""
import json
import subprocess


class SolidCraftError(Exception):
    """Tool error (result.isError), JSON-RPC error, or unparsable reply."""


class SolidCraft:
    def __init__(self, port=7878, allow_paths=()):
        cmd = ["solidcraft-cli", "mcp", "--connect", f"127.0.0.1:{port}"]
        for p in allow_paths or ():
            cmd += ["--allow-path", str(p)]
        self._p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, text=True)
        self._id = 0
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "station-case-tools", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self._p.stdin.write(json.dumps(msg) + "\n")
        self._p.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            line = self._p.stdout.readline()
            if not line:
                raise SolidCraftError("solidcraft-cli closed the connection")
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("id") == self._id:
                if "error" in r:
                    raise SolidCraftError(r["error"].get("message", str(r["error"])))
                return r.get("result", {})

    def call(self, tool, args=None):
        """Call an MCP tool; return its parsed JSON (or raw text if not JSON)."""
        res = self._rpc("tools/call", {"name": tool, "arguments": args or {}})
        text = "\n".join(c.get("text", "") for c in res.get("content", [])
                         if c.get("type") == "text")
        if res.get("isError"):
            raise SolidCraftError(text or f"{tool} failed")
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}

    def execute(self, command, params=None):
        return self.call("execute", {"command": command, "params": params or {}})

    def batch(self, commands):
        return self.call("batch", {"commands": commands})

    def inspect(self, **kw):
        return self.call("inspect_design", kw)

    def open(self, path):
        """Open a design; refuses to discard unsaved changes."""
        if self.inspect().get("dirty"):
            raise SolidCraftError("current design has unsaved changes; save it first")
        return self.call("open", {"path": str(path)})

    def measure(self):
        return self.call("measure")

    def timeline(self):
        return self.inspect().get("timeline", [])

    def close(self):
        try:
            self._p.stdin.close()
            self._p.wait(timeout=5)
        except Exception:
            self._p.kill()
