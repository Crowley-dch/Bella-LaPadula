import socket
import json
import tkinter as tk
from tkinter import simpledialog, messagebox


class Client:
    def __init__(self, host='localhost', port=5010):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.file = self.sock.makefile('r')

    def send(self, action, params=None):
        cmd = {'action': action, 'params': params or {}}
        self.sock.sendall((json.dumps(cmd) + '\n').encode())
        resp = self.file.readline()
        return json.loads(resp)


class ClientGUI:
    def __init__(self):
        self.client = Client()
        self.root = tk.Tk()
        self.root.title("BLP Model with Access Override")

        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # Level names for display
        self.level_names = {
            0: 'Unclassified',
            1: 'Confidential',
            2: 'Secret',
            3: 'Top Secret'
        }

        buttons = [
            ("Add Subject", self.add_subject),
            ("Add Object", self.add_object),
            ("Set Level", self.set_level),
            ("Override Level", self.override_level),
            ("Restore Level", self.restore_level),
            ("Read", self.do_read),
            ("Write", self.do_write),
            ("List Subjects", self.list_subjects),
            ("List Objects", self.list_objects),
            ("Exit", self.root.quit)
        ]
        for text, cmd in buttons:
            b = tk.Button(frame, text=text, width=20, command=cmd)
            b.pack(pady=2)

    def prompt_level(self, title):
        return simpledialog.askinteger(
            title,
            "Level:\n0 - Unclassified\n1 - Confidential\n2 - Secret\n3 - Top Secret",
            minvalue=0,
            maxvalue=3
        )

    def add_subject(self):
        sid = simpledialog.askstring("Add Subject", "Subject ID:")
        if not sid: return
        level = self.prompt_level("Subject Level")
        if level is None: return
        resp = self.client.send('add_subject', {'id': sid, 'level': level})
        self.show_response(resp)

    def add_object(self):
        oid = simpledialog.askstring("Add Object", "Object ID:")
        if not oid: return
        level = self.prompt_level("Object Level")
        if level is None: return
        resp = self.client.send('add_object', {'id': oid, 'level': level})
        self.show_response(resp)

    def set_level(self):
        sid = simpledialog.askstring("Set Level", "Subject ID:")
        if not sid: return
        level = self.prompt_level("New Level")
        if level is None: return
        resp = self.client.send('set_level', {'id': sid, 'level': level})
        self.show_response(resp)

    def override_level(self):
        sid = simpledialog.askstring("Override Level", "Subject ID:")
        if not sid: return
        level = self.prompt_level("Temporary Level (must be lower than current)")
        if level is None: return
        resp = self.client.send('override_level', {'sid': sid, 'level': level})
        self.show_response(resp)

    def restore_level(self):
        sid = simpledialog.askstring("Restore Level", "Subject ID:")
        if not sid: return
        resp = self.client.send('restore_level', {'sid': sid})
        self.show_response(resp)

    def do_read(self):
        sid = simpledialog.askstring("Read", "Subject ID:")
        oid = simpledialog.askstring("Read", "Object ID:")
        if not sid or not oid: return
        resp = self.client.send('read', {'subj_id': sid, 'obj_id': oid})
        self.show_response(resp)

    def do_write(self):
        sid = simpledialog.askstring("Write", "Subject ID:")
        oid = simpledialog.askstring("Write", "Object ID:")
        if not sid or not oid: return
        resp = self.client.send('write', {'subj_id': sid, 'obj_id': oid})
        self.show_response(resp)

    def list_subjects(self):
        resp = self.client.send('list_subjects')
        if resp['status'] == 'ok':
            items = resp['result']
            text = ""
            for sid, info in items.items():
                text += f"{sid}: Original={info['original_level']}, Current={info['current_level']}"
                if 'temporary_level' in info:
                    text += f" (Temporary: {info['temporary_level']})"
                text += "\n"
            messagebox.showinfo("Subjects", text or "None")
        else:
            self.show_response(resp)

    def list_objects(self):
        resp = self.client.send('list_objects')
        if resp['status'] == 'ok':
            items = resp['result']
            text = '\n'.join(f"{k}: {v['level']}" for k, v in items.items()) or 'None'
            messagebox.showinfo("Objects", text)
        else:
            self.show_response(resp)

    def show_response(self, resp):
        if resp['status'] == 'ok':
            messagebox.showinfo("OK", str(resp['result']))
        else:
            messagebox.showerror("Error", resp.get('error', 'Unknown error'))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    gui = ClientGUI()
    gui.run()