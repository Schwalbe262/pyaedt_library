import subprocess
import psutil
import time
import os
import csv
from datetime import datetime

import pandas as pd

class Scheduler :

    def __init__(
            self,
            max_processes = 5,
            max_runtime = 300,
            start_interval = 3,
            interval = 10,
            script_name = None,
            conda_env = None,
            log_file = "process_log.csv"
    ):
        self.max_processes = max_processes
        self.max_runtime = max_runtime
        self.start_interval = start_interval
        self.interval = interval
        self.script_name = script_name
        self.conda_env = conda_env
        self.log_file = log_file

        self.iter = 0


        # 실행 중인 프로세스 추적 리스트
        self.active_processes = []

        # delete existing log file
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

        # make new log file
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["PID", "aedt_PID", "Start Time", "Status", "CPU_usage", "RAM_usage"])


    
    def _start_process(self) :

        script_path = os.path.join(os.getcwd(), self.script_name)
        process = subprocess.Popen(
            f'conda run -n {self.conda_env} python {script_path}',
            shell=False,
            stdout=subprocess.DEVNULL,  # 출력을 콘솔에 표시하지 않음
            stderr=subprocess.DEVNULL
        )

        pid = process.pid
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "START"

        return pid, start_time, status


    def _is_my_process_alive(self, pid):

        # 0:시뮬레이션 종료, 1:시뮬레이션 중, 2:이상동작

        try:
            proc = psutil.Process(pid)  # `conda run` 실행 프로세스
            child_procs = proc.children(recursive=True)  # 실제 실행된 프로세스 찾기

            if not child_procs: # child process 없는 경우
                print("no child process")
                return 2, 0, 0, 0

            # find ansysedt process
            ansys_edt = self._find_ansys_edt(pid)
            
            if ansys_edt == 0 : # child process는 있으나 ansysedt 안열린 경우 -> 다시실행해야함
                print("no aedt")
                return 2, 0, 0, 0
            

            ansys_edt_child = ansys_edt.children(recursive=True)

            process_check_itr = 0
            for i in range(3) :
                non_ansyscl_processes = [child for child in ansys_edt_child if child.name().lower() != "ansyscl.exe"]
                if non_ansyscl_processes : process_check_itr += 1
                time.sleep(0.5)

            if process_check_itr > 0 :
                cpu_usage = proc.cpu_percent(interval=0.5)
                mem_usage = proc.memory_info().rss / (1024 * 1024)
                for child in proc.children(recursive=True):
                    cpu_usage += child.cpu_percent(interval=None) 
                    mem_usage += child.memory_info().rss / (1024 * 1024)
                return 1, int(ansys_edt.pid), cpu_usage, mem_usage
            else:
                print("no simulation running")
                return 0, 0, 0, 0
            
        except psutil.NoSuchProcess:
            return 2, 0, 0, 0
        
    def _find_ansys_edt(self, pid) :

        proc = psutil.Process(pid)  # `conda run` 실행 프로세스
        child_procs = proc.children(recursive=True)  # 실제 실행된 프로세스 찾기

        for child in child_procs:
                try:
                    proc_name = child.name().lower()
                    if "ansysedt.exe" in proc_name:  # Ansys 관련 프로세스 필터링
                        ansys_edt = child
                        return ansys_edt
                except psutil.NoSuchProcess:
                    return 0


    


    def run_simulation(self, n_iter=1000) :

        start_flag = True
        
        while(self.iter < n_iter) :

            df = pd.read_csv(self.log_file)

            for i in range(self.max_processes) :

                if start_flag == True :

                    pid, start_time, status = self._start_process()
                    df.loc[i] = [pid, 0, start_time, status, 0, 0]
                    time.sleep(self.start_interval)

                    if i == self.max_processes-1 : 
                        start_flag = False

                else :

                    log = df.iloc[i]

                    pid = log["PID"]
                    start_time = log["Start Time"]
                    start_time_strp = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                    status = log["Status"]

                    current_time = datetime.now()
                    current_time_strf = current_time.strftime('%Y-%m-%d %H:%M:%S')

                    excution_time = (current_time - start_time_strp).total_seconds()

                    if excution_time > 60 :

                        running, ansys_pid, cpu_usage, mem_usage = self._is_my_process_alive(pid)


                        if running == 1 : # 시뮬레이션이 잘 돌고있는 상태
                            df.loc[i] = [pid, ansys_pid, current_time_strf, "RUNNING", cpu_usage, mem_usage]

                        elif running == 0  : # 시뮬레이션이 끝난 상태
                            print(f"process {self.iter} complete")
                            self.iter = self.iter + 1
                            df.loc[i] = [pid, ansys_pid, current_time_strf, "PENDING", cpu_usage, mem_usage]

                        elif running == 0 : # 시뮬레이션 이상 동작
                            df.loc[i] = [pid, ansys_pid, current_time_strf, "PENDING", cpu_usage, mem_usage]
                            proc = psutil.Process(pid)
                            proc.kill()

                        elif excution_time > self.max_runtime : # 시뮬레이션이 지정한시간 이상으로 실행되는 경우 (강제종료)
                            df.loc[i] = [pid, ansys_pid, current_time_strf, "PENDING", cpu_usage, mem_usage]
                            proc = psutil.Process(pid)
                            proc.kill()

                        elif status == "PENDING" and excution_time > self.interval : # pending 상태에서 대기시간 지난 케이스
                            pid, start_time, status = self._start_process()
                            df.loc[i] = [pid, ansys_pid, current_time_strf, "START", 0, 0]

                
                    # time.sleep(1)
                    # print(f"{i} : {pid} / {status} / {cpu_usage} / {mem_usage} / ")


            attempts = 0
            max_attempts = 5
            while True:
                try:
                    df.to_csv(self.log_file, index=False)
                    break  # 저장 성공하면 루프 탈출
                except Exception as e:
                    attempts += 1
                    print(f"CSV 기록 오류 발생: {e}. 재시도 {attempts}/{max_attempts}...")
                    if attempts >= max_attempts:
                        raise e  # 최대 재시도 횟수를 넘으면 예외 발생
                    time.sleep(1)  # 1초 후 재시도
