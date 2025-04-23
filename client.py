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
        self.root.title("BLP Client")

        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)
        buttons = [
            ("Add Subject", self.add_subject),
            ("Add Object", self.add_object),
            ("Set Label", self.set_label),
            ("Read", self.do_read),
            ("Write", self.do_write),
            ("List Subjects", self.list_subjects),
            ("List Objects", self.list_objects),
            ("Exit", self.root.quit)
        ]
        for text, cmd in buttons:
            b = tk.Button(frame, text=text, width=20, command=cmd)
            b.pack(pady=2)

    def prompt_label(self, title):
        level = simpledialog.askinteger(title, "Level (0-Unclass,1-Conf,2-Sec,3-Top):")
        if level is None: return None
        cats = simpledialog.askstring(title, "Categories (comma-separated):")
        cat_list = [c.strip() for c in cats.split(',')] if cats else []
        return level, cat_list

    def add_subject(self):
        sid = simpledialog.askstring("Add Subject", "Subject ID:")
        if not sid: return
        res = self.prompt_label("Subject Label")
        if not res: return
        level, cats = res
        resp = self.client.send('add_subject', {'id': sid, 'level': level, 'categories': cats})
        self.show_response(resp)

    def add_object(self):
        oid = simpledialog.askstring("Add Object", "Object ID:")
        if not oid: return
        res = self.prompt_label("Object Label")
        if not res: return
        level, cats = res
        resp = self.client.send('add_object', {'id': oid, 'level': level, 'categories': cats})
        self.show_response(resp)

    def set_label(self):
        sid = simpledialog.askstring("Set Label", "Subject ID:")
        if not sid: return
        res = self.prompt_label("New Label")
        if not res: return
        level, cats = res
        resp = self.client.send('set_label', {'id': sid, 'level': level, 'categories': cats})
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
            text = '\n'.join(f"{k}: {v}" for k, v in items.items()) or 'None'
            messagebox.showinfo("Subjects", text)
        else:
            self.show_response(resp)

    def list_objects(self):
        resp = self.client.send('list_objects')
        if resp['status'] == 'ok':
            items = resp['result']
            text = '\n'.join(f"{k}: {v}" for k, v in items.items()) or 'None'
            messagebox.showinfo("Objects", text)
        else:
            self.show_response(resp)

    def show_response(self, resp):
        if resp['status'] == 'ok':
            messagebox.showinfo("OK", resp['result'])
        else:
            messagebox.showerror("Error", resp.get('error', 'Unknown error'))

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    gui = ClientGUI()
    gui.run()
