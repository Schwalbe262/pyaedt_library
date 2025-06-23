import subprocess
import time
import logging
import os
import platform

logging.basicConfig(filename='run_debug.log', level=logging.DEBUG)

script_name = "run_simulation.py"
script_path = os.path.join(os.getcwd(), script_name)

os_name = platform.system()
if os_name == "Windows":
    num_processes = 10 # number of subprocess
else :
    num_processes = 32 # number of subprocess


processes = []

log_dir = './simul_log'
os.makedirs(log_dir, exist_ok=True)

for i in range(num_processes):

    file_path = "simulog_num.txt"

    # 파일이 존재하지 않으면 생성
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("1")

    # 읽기/쓰기 모드로 파일 열기
    with open(file_path, "r+", encoding="utf-8") as file:

            # 파일에서 값 읽기
            content = int(file.read().strip())
            content += 1

            # 파일 포인터를 처음으로 되돌리고, 파일 내용 초기화 후 새 값 쓰기
            file.seek(0)
            file.truncate()
            file.write(str(content))

    log_file = open(f'./simul_log/process_{content}.log', 'w')
    p = subprocess.Popen(
        f'python {script_path}',
        shell=True,
        stdout=log_file,
        stderr=subprocess.STDOUT
    )
    processes.append((p, log_file))
    time.sleep(10)

for idx, (p, log_file) in enumerate(processes):
    p.wait()
    log_file.write(f"\nProcess {idx} finished with return code {p.returncode}\n")
    log_file.close()
