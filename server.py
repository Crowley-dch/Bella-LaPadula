import socket
import threading
import json
import sqlite3


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


class AccessDenied(Exception): pass


class TranquilityViolation(Exception): pass


class SecurityKernel:
    def __init__(self, db_path="security.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.db.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id TEXT PRIMARY KEY,
                level INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id TEXT PRIMARY KEY,
                level INTEGER
            )
        """)
        self.db.commit()

    def add_subject(self, sid, level):
        self.cursor.execute("INSERT OR REPLACE INTO subjects (id, level) VALUES (?, ?)", (sid, level))
        self.db.commit()
        return f"Subject '{sid}' added with level {ClearanceLevel.names[level]}"

    def add_object(self, oid, level):
        self.cursor.execute("INSERT OR REPLACE INTO objects (id, level) VALUES (?, ?)", (oid, level))
        self.db.commit()
        return f"Object '{oid}' added with level {ClearanceLevel.names[level]}"

    def read(self, sid, oid):
        s_level = self._get_subject_level(sid)
        o_level = self._get_object_level(oid)

        if s_level < o_level:
            self._set_subject_level(sid, o_level)
            return {
                'object': oid,
                'level': {'level': o_level},
                'notice': f"Subject '{sid}' level was automatically raised to {ClearanceLevel.names[o_level]}"
            }

        return {'object': oid, 'level': {'level': o_level}}

    def write(self, sid, oid):
        s_level = self._get_subject_level(sid)
        o_level = self._get_object_level(oid)

        if s_level > o_level:
            self._set_subject_level(sid, o_level)
            return {
                'result': f"{sid} wrote to {oid}.",
                'notice': f"Subject '{sid}' level was automatically lowered to {ClearanceLevel.names[o_level]}"
            }

        return f"{sid} wrote to {oid}."

    def _get_subject_level(self, sid):
        self.cursor.execute("SELECT level FROM subjects WHERE id = ?", (sid,))
        row = self.cursor.fetchone()
        if row is None:
            raise KeyError(f"Unknown subject '{sid}'")
        return row[0]

    def _get_object_level(self, oid):
        self.cursor.execute("SELECT level FROM objects WHERE id = ?", (oid,))
        row = self.cursor.fetchone()
        if row is None:
            raise KeyError(f"Unknown object '{oid}'")
        return row[0]

    def _set_subject_level(self, sid, new_level):
        self.cursor.execute("UPDATE subjects SET level = ? WHERE id = ?", (new_level, sid))
        self.db.commit()
        return new_level

    def list_subjects(self):
        self.cursor.execute("SELECT id, level FROM subjects")
        return {row[0]: {'level': ClearanceLevel.names[row[1]]} for row in self.cursor.fetchall()}

    def list_objects(self):
        self.cursor.execute("SELECT id, level FROM objects")
        return {row[0]: {'level': ClearanceLevel.names[row[1]]} for row in self.cursor.fetchall()}


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


def start_server():
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


if __name__ == '__main__':
    start_server()