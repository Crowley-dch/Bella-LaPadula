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
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS temp_levels (
                sid TEXT PRIMARY KEY,
                original_level INTEGER,
                temp_level INTEGER
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

    def set_subject_level(self, sid, new_level):
        self.cursor.execute("SELECT level FROM subjects WHERE id = ?", (sid,))
        row = self.cursor.fetchone()
        if not row:
            raise KeyError(f"Unknown subject '{sid}'")
        old_level = row[0]
        if new_level < old_level:
            raise TranquilityViolation(f"Cannot lower level of '{sid}'")
        self.cursor.execute("UPDATE subjects SET level = ? WHERE id = ?", (new_level, sid))
        self.db.commit()
        return f"Level of '{sid}' changed to {ClearanceLevel.names[new_level]}"

    def override_level(self, sid, new_level):
        """Temporarily override subject's clearance level"""
        self.cursor.execute("SELECT level FROM subjects WHERE id = ?", (sid,))
        row = self.cursor.fetchone()
        if not row:
            raise KeyError(f"Unknown subject '{sid}'")

        original_level = row[0]

        if new_level >= original_level:
            raise ValueError("Can only override to lower level")

        # Check if already has temporary level
        self.cursor.execute("SELECT 1 FROM temp_levels WHERE sid = ?", (sid,))
        if self.cursor.fetchone():
            self.cursor.execute("UPDATE temp_levels SET temp_level = ? WHERE sid = ?",
                                (new_level, sid))
        else:
            self.cursor.execute("INSERT INTO temp_levels (sid, original_level, temp_level) VALUES (?, ?, ?)",
                                (sid, original_level, new_level))
        self.db.commit()
        return f"Subject '{sid}' temporary level set to {ClearanceLevel.names[new_level]}"

    def restore_level(self, sid):
        """Restore subject's original clearance level"""
        self.cursor.execute("DELETE FROM temp_levels WHERE sid = ?", (sid,))
        self.db.commit()
        return f"Subject '{sid}' restored to original level"

    def read(self, sid, oid):
        s_level = self._get_subject_level(sid)
        o_level = self._get_object_level(oid)
        if s_level < o_level:
            raise AccessDenied(
                f"{sid} ({ClearanceLevel.names[s_level]}) cannot read {oid} ({ClearanceLevel.names[o_level]})")
        return {'object': oid, 'level': {'level': o_level}}

    def write(self, sid, oid):
        s_level = self._get_subject_level(sid)
        o_level = self._get_object_level(oid)
        if s_level > o_level:
            raise AccessDenied(
                f"{sid} ({ClearanceLevel.names[s_level]}) cannot write to {oid} ({ClearanceLevel.names[o_level]})")
        return f"{sid} wrote to {oid}."

    def _get_subject_level(self, sid):
        """Get current level (temporary if exists, otherwise original)"""
        self.cursor.execute("SELECT temp_level FROM temp_levels WHERE sid = ?", (sid,))
        row = self.cursor.fetchone()
        if row:
            return row[0]

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

    def list_subjects(self):
        self.cursor.execute("""
            SELECT s.id, s.level, t.temp_level 
            FROM subjects s
            LEFT JOIN temp_levels t ON s.id = t.sid
        """)
        results = {}
        for row in self.cursor.fetchall():
            sid, original_level, temp_level = row
            info = {
                'original_level': ClearanceLevel.names[original_level],
                'current_level': ClearanceLevel.names[temp_level if temp_level is not None else original_level]
            }
            if temp_level is not None:
                info['temporary_level'] = ClearanceLevel.names[temp_level]
            results[sid] = info
        return results

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
                elif action == 'set_level':
                    result = kernel.set_subject_level(params['id'], params['level'])
                elif action == 'override_level':
                    result = kernel.override_level(params['sid'], params['level'])
                elif action == 'restore_level':
                    result = kernel.restore_level(params['sid'])
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