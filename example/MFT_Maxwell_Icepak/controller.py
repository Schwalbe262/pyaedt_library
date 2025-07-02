import subprocess
import time

interval_seconds = 6 * 3600  # 3시간 = 10800초

# time.sleep(2*3600)

itr = 10

while True:
    # 모든 작업 종료

    print("모든 작업 종료(scancel) 실행 중...")
    subprocess.run(["scancel", "-u", "r1jae262", "--signal=kill"])
    print("rm rf")
    subprocess.run(["rm", "-rf", "simulation"])

    subprocess.run(["rm", "-rf", "error"])
    subprocess.run(["rm", "-rf", "log"])
    subprocess.run(["rm", "-rf", "simul_log"])
    subprocess.run(["mkdir", "simul_log"])
    subprocess.run(["rm", "-rf", "simulation_log"])

    subprocess.run(["rm", "-rf", "batch.log"])
    subprocess.run(["rm", "-rf", "info.log"])
    subprocess.run(["rm", "-rf", "log.csv"])
    subprocess.run(["rm", "-rf", "log.txt"])
    subprocess.run(["rm", "-rf", "run_debug.log"])


    time.sleep(10)
    
    for i in range(itr):
        print(f"{i+1}번째 simulation.sh 제출 (sbatch) 실행 중...")
        subprocess.run(["sbatch", "simulation1.sh"])
        time.sleep(5)
        subprocess.run(["squeue", "-u", "r1jae262"])
        time.sleep(60)

    for i in range(itr):
        print(f"{i+1}번째 simulation2.sh 제출 (sbatch) 실행 중...")
        subprocess.run(["sbatch", "simulation2.sh"])
        time.sleep(5)
        subprocess.run(["squeue", "-u", "r1jae262"])
        time.sleep(60)
    
    # 3시간 대기
    print(f"6시간 대기 중... ({interval_seconds}초)")
    time.sleep(interval_seconds)
