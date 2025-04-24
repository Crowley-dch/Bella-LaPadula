# Bell-LaPadula
a system for storing subjects and objects based on the Bell-LaPadula model

# Bell-LaPadula Model Implementation

This is a Python-based implementation of the **Bell-LaPadula (BLP)** model. The project demonstrates a simplified system for access control between subjects and objects with enforced information flow restrictions based on security labels.

## 📜 Overview
The Bell-LaPadula model is designed to maintain the confidentiality of information. It enforces two main rules:

- **No Read Up (NRU)** — a subject cannot read data at a higher security level.
- **No Write Down (NWD)** — a subject cannot write data to a lower security level.

This system is implemented with:
- A socket-based client-server architecture
- A GUI interface for user interaction (using `tkinter`)
- Support for label modification with tranquility principle enforcement
- Custom unit tests

---

## 🚀 Getting Started

### Requirements
- Python 3.8+
- No external libraries required (uses built-in modules)

### Running the Project
1. **Start the server:**
   ```bash
   python server.py
   ```

2. **Start the client (in another terminal):**
   ```bash
   python client.py
   ```

3. Interact via the graphical interface:
   - Add subjects and objects
   - Set security labels
   - Perform read/write operations
   - View current access control state

---

## 🧪 Running Tests
Run unit tests using:
```bash
python test.py
```



