import socket
import threading
import json

# Bell–LaPadula model core classes
class ClearanceLevel:
    UNCLASSIFIED = 0
    CONFIDENTIAL = 1
    SECRET = 2
    TOP_SECRET = 3

    names = {
        UNCLASSIFIED: 'Unclassified',
        CONFIDENTIAL: 'Confidential',
        SECRET: 'Secret',
        TOP_SECRET: 'Top Secret',
    }

class Label:
    def __init__(self, level, categories=None):
        self.level = level
        self.categories = set(categories) if categories else set()

    def dominates(self, other):
        return (self.level >= other.level and
                self.categories.issuperset(other.categories))

    def to_dict(self):
        return {'level': self.level, 'categories': list(self.categories)}

class AccessDenied(Exception): pass
class TranquilityViolation(Exception): pass

class SecurityKernel:
    def __init__(self):
        self.subjects = {}  # subj_id -> Label
        self.objects = {}   # obj_id -> Label

    def add_subject(self, sid, label):
        self.subjects[sid] = label
        return f"Subject '{sid}' added."

    def add_object(self, oid, label):
        self.objects[oid] = label
        return f"Object '{oid}' added."

    def set_subject_label(self, sid, new_label):
        old = self.subjects.get(sid)
        if old is None:
            raise KeyError(f"Unknown subject '{sid}'")
        if not new_label.dominates(old):
            raise TranquilityViolation(f"Cannot lower label of '{sid}'")
        self.subjects[sid] = new_label
        return f"Label of '{sid}' changed."

    def read(self, sid, oid):
        s = self.subjects.get(sid)
        o = self.objects.get(oid)
        if s is None or o is None:
            raise KeyError("Unknown subject or object")
        if not s.dominates(o):
            raise AccessDenied(f"{sid} cannot read {oid}")
        return {'object': oid, 'label': o.to_dict()}

    def write(self, sid, oid):
        s = self.subjects.get(sid)
        o = self.objects.get(oid)
        if s is None or o is None:
            raise KeyError("Unknown subject or object")
        if not (o.level >= s.level and o.categories == s.categories):
            raise AccessDenied(f"{sid} cannot write to {oid}")
        return f"{sid} wrote to {oid}."

    def list_subjects(self):
        return {sid: lbl.to_dict() for sid, lbl in self.subjects.items()}

    def list_objects(self):
        return {oid: lbl.to_dict() for oid, lbl in self.objects.items()}

def handle_client(conn, addr, kernel):
    print(f"Connection from {addr}")
    with conn:
        file = conn.makefile('r')
        while True:
            line = file.readline()
            if not line:
                break
            try:
                cmd = json.loads(line)
                action = cmd.get('action')
                params = cmd.get('params', {})
                # Dispatch
                if action == 'add_subject':
                    lbl = Label(params['level'], params.get('categories'))
                    result = kernel.add_subject(params['id'], lbl)
                elif action == 'add_object':
                    lbl = Label(params['level'], params.get('categories'))
                    result = kernel.add_object(params['id'], lbl)
                elif action == 'set_label':
                    lbl = Label(params['level'], params.get('categories'))
                    result = kernel.set_subject_label(params['id'], lbl)
                elif action == 'read':
                    result = kernel.read(params['subj_id'], params['obj_id'])
                elif action == 'write':
                    result = kernel.write(params['subj_id'], params['obj_id'])
                elif action == 'list_subjects':
                    result = kernel.list_subjects()
                elif action == 'list_objects':
                    result = kernel.list_objects()
                else:
                    raise ValueError(f"Unknown action '{action}'")
                response = {'status': 'ok', 'result': result}
            except Exception as e:
                response = {'status': 'error', 'error': str(e)}
            conn.sendall((json.dumps(response) + '\n').encode())
    print(f"Disconnected {addr}")

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = 5010
    kernel = SecurityKernel()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr, kernel), daemon=True).start()
