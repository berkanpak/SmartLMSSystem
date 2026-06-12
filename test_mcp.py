import subprocess
import sys
import json
import time
import threading

p = subprocess.Popen(
    [sys.executable, '-m', 'smart_lms.server'],
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

def read_out():
    while True:
        line = p.stdout.readline()
        if not line: break
        print('STDOUT:', repr(line))
        sys.stdout.flush()

def read_err():
    while True:
        line = p.stderr.readline()
        if not line: break
        print('STDERR:', repr(line))
        sys.stdout.flush()

threading.Thread(target=read_out, daemon=True).start()
threading.Thread(target=read_err, daemon=True).start()

init_req = {
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'test', 'version': '1.0'}
    }
}
p.stdin.write(json.dumps(init_req) + '\n')
p.stdin.flush()
time.sleep(0.5)

notif = {
    'jsonrpc': '2.0',
    'method': 'notifications/initialized'
}
p.stdin.write(json.dumps(notif) + '\n')
p.stdin.flush()
time.sleep(0.5)

tools_req = {
    'jsonrpc': '2.0',
    'id': 2,
    'method': 'tools/list'
}
p.stdin.write(json.dumps(tools_req) + '\n')
p.stdin.flush()

time.sleep(2)
p.terminate()
