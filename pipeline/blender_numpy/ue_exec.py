"""Run Python inside the running Unreal Editor via PythonScriptPlugin remote execution.
Usage: python ue_exec.py script.py [args...]   (args are exposed as sys.argv in the editor)
       python ue_exec.py -c "print(1)"
       python ue_exec.py --ping"""
import sys, os, time, json
sys.path.insert(0, r"E:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution as rex


def _receive_message(self, expected_type):
    """Read until the bytes form one complete JSON message (the stock reader stops at the
    first short TCP chunk, which truncates big results)."""
    data = b""
    while True:
        part = self._command_channel_socket.recv(rex.DEFAULT_RECEIVE_BUFFER_SIZE)
        if not part:
            break
        data += part
        try:
            json.loads(data.decode("utf-8"))
            break
        except ValueError:
            continue
    message = rex._RemoteExecutionMessage(None, None)
    if data and message.from_json_bytes(data) and message.passes_receive_filter(self._node_id) \
            and message.type_ == expected_type:
        return message
    raise RuntimeError("Remote party failed to send a valid response!")


rex._RemoteExecutionCommandConnection._receive_message = _receive_message


def main():
    args = sys.argv[1:]
    cfg = rex.RemoteExecutionConfig()
    re = rex.RemoteExecution(cfg)
    re.start()
    try:
        t0 = time.time()
        while not re.remote_nodes and time.time() - t0 < 20:
            time.sleep(0.25)
        if not re.remote_nodes:
            print("NO_EDITOR: no remote nodes found"); sys.exit(2)
        node = re.remote_nodes[0]
        if args and args[0] == "--ping":
            print("NODE", json.dumps(node)); return
        re.open_command_connection(node["node_id"])
        if args[0] == "-c":
            code = args[1]
        else:
            path = os.path.abspath(args[0])
            code = (f"import sys; sys.argv = {[path] + args[1:]!r}\n"
                    f"exec(compile(open({path!r}, encoding='utf-8').read(), {path!r}, 'exec'), "
                    f"{{'__name__': '__main__', '__file__': {path!r}}})")
        res = re.run_command(code, unattended=True, exec_mode=rex.MODE_EXEC_FILE)
        for o in res.get("output", []):
            print(o.get("output", "").rstrip())
        if not res.get("success"):
            print("REMOTE_FAILED:", res.get("result")); sys.exit(1)
    finally:
        re.stop()

main()
