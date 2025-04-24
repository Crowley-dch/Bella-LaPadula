import socket
import threading
import json


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
    def __init__(self, level):
        self.level = level

    def dominates(self, other):
        return self.level >= other.level

    def to_dict(self):
        return {'level': self.level}


class AccessDenied(Exception): pass


class TranquilityViolation(Exception): pass


class SecurityKernel:
    def __init__(self):
        self.subjects = {}
        self.objects = {}

    def add_subject(self, sid, level):
        self.subjects[sid] = Label(level)
        return f"Subject '{sid}' added with level {ClearanceLevel.names[level]}"

    def add_object(self, oid, level):
        self.objects[oid] = Label(level)
        return f"Object '{oid}' added with level {ClearanceLevel.names[level]}"

    def set_subject_level(self, sid, new_level):
        old = self.subjects.get(sid)
        if old is None:
            raise KeyError(f"Unknown subject '{sid}'")
        if new_level < old.level:
            raise TranquilityViolation(f"Cannot lower level of '{sid}'")
        self.subjects[sid] = Label(new_level)
        return f"Level of '{sid}' changed to {ClearanceLevel.names[new_level]}"

    def read(self, sid, oid):
        s = self.subjects.get(sid)
        o = self.objects.get(oid)
        if s is None or o is None:
            raise KeyError("Unknown subject or object")
        if not s.dominates(o):
            raise AccessDenied(
                f"{sid} ({ClearanceLevel.names[s.level]}) cannot read {oid} ({ClearanceLevel.names[o.level]})"
            )
        return {'object': oid, 'level': o.to_dict()}

    def write(self, sid, oid):
        s = self.subjects.get(sid)
        o = self.objects.get(oid)
        if s is None or o is None:
            raise KeyError("Unknown subject or object")
        if o.level < s.level:
            raise AccessDenied(
                f"{sid} ({ClearanceLevel.names[s.level]}) cannot write to {oid} ({ClearanceLevel.names[o.level]})"
            )
        return f"{sid} wrote to {oid}."

    def list_subjects(self):
        return {sid: {'level': ClearanceLevel.names[lbl.level]}
                for sid, lbl in self.subjects.items()}

    def list_objects(self):
        return {oid: {'level': ClearanceLevel.names[lbl.level]}
                for oid, lbl in self.objects.items()}


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

                if action == 'add_subject':
                    result = kernel.add_subject(params['id'], params['level'])
                elif action == 'add_object':
                    result = kernel.add_object(params['id'], params['level'])
                elif action == 'set_level':
                    result = kernel.set_subject_level(params['id'], params['level'])
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