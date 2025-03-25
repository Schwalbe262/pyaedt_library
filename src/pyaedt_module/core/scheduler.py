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
                writer.writerow(["PID", "Start Time", "Status"])


    
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
        status = "RUN"

        return pid, start_time, status


    def _is_my_process_alive(self, pid):
        try:
            proc = psutil.Process(pid)  # `conda run` 실행 프로세스
            child_procs = proc.children(recursive=True)  # 실제 실행된 프로세스 찾기

            if not child_procs:
                return False, 0, 0

            # 실제 실행 중인 Ansys 관련 프로세스 찾기
            ansys_proc = None
            for child in child_procs:
                try:
                    proc_name = child.name().lower()
                    if "ansys" in proc_name or "hfss" in proc_name:  # Ansys 관련 프로세스 필터링
                        ansys_proc = child
                        break
                except psutil.NoSuchProcess:
                    continue  # 프로세스가 종료되었을 경우 무시

            if ansys_proc is None:
                return False, 0, 0

            cpu_usage = ansys_proc.cpu_percent(interval=0.5)
            mem_usage = ansys_proc.memory_info().rss / (1024 * 1024)
            return True, cpu_usage, mem_usage

        except psutil.NoSuchProcess:
            return False, 0, 0
    


    def run_simulation(self, n_iter=1000) :

        start_flag = True
        
        while(self.iter < n_iter) :

            df = pd.read_csv(self.log_file)

            for i in range(self.max_processes) :

                if start_flag == True :

                    pid, start_time, status = self._start_process()
                    df.loc[i] = [pid, start_time, status]
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

                    running, cpu_usage, mem_usage = self._is_my_process_alive(pid)


                    if running == False and status == "RUN" : # run이 끝난 것 감지한 케이스
                        df.loc[i] = [pid, current_time_strf, "PENDING"]
                        self.iter = self.iter + 1
                        print(self.iter)
                    elif status == "PENDING" and excution_time > self.interval : # pending 상태에서 대기시간 지난 케이스
                        pid, start_time, status = self._start_process()
                        df.loc[i] = [pid, current_time_strf, status]

                
                    time.sleep(1)
                    # print(f"{i} : {pid} / {status} / {cpu_usage} / {mem_usage} / ")

            df.to_csv(self.log_file, index=False)
