import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

class PostProcessing:

    def __init__(self, design) :
        self.design = design
        
    def detect_peak(self, freq=None, data=None, prominence=30) :
        peaks_prom, properties = find_peaks(data, prominence=prominence)

        if freq is not None :
            peak_freqs_prom = freq[peaks_prom].values
            peak_vals_prom = data[peaks_prom].values
            return peak_freqs_prom, peak_vals_prom
        
        elif freq is None :
            peak_vals_prom = data[peaks_prom].values
            return peak_vals_prom
    

    def detect_zero_crossing(self, freq=None, data=None) :

        sign_data = np.sign(data)
        zero_crossing_indices = np.where(np.diff(sign_data))[0]
        
        zeros = []
        for idx in zero_crossing_indices:

            x1, x2 = freq[idx], freq[idx+1]
            y1, y2 = data[idx], data[idx+1]
            if y2 - y1 == 0:
                # 두 점의 y값이 동일하면 선형 보간 불가능하므로, 중간값 사용 (예외 처리)
                x_zero = (x1 + x2) / 2.0
            else:
                x_zero = x1 - y1 * (x2 - x1) / (y2 - y1)
            zeros.append(x_zero)
        
        return np.array(zeros)



    def detect_resonant(self, freq=None, peak=None, freq_zero=None, tolerance=5):
        filtered_freq = []
        filtered_peak = []
        
        for f, p in zip(freq, peak):
            # freq_zero 리스트에 있는 모든 값 중 하나라도 f와의 상대 오차가 tolerance% 이내라면
            if any(abs(f - fz) / f * 100 <= tolerance for fz in freq_zero):
                # np.float64를 파이썬 float로 변환하여 추가
                filtered_freq.append(float(f))
                filtered_peak.append(float(p))
        
        return filtered_freq, filtered_peak
    

    def get_frequency_data(self, target_freq, freq_data, param_data):
        """
        주어진 target_freq에 대해, freq_data에서 가장 가까운 주파수를 찾고,
        그 인덱스에 해당하는 param_data의 값을 반환합니다.
        
        Parameters:
            target_freq (float): 찾고자 하는 타겟 주파수 (예: 50)
            freq_data (list or array-like): 주파수 값들이 저장된 리스트 (예: [45, 49.5, 51, 52, ...])
            param_data (list or array-like): 주파수에 대응하는 파라미터 데이터 리스트
        
        Returns:
            closest_param: target_freq에 가장 가까운 주파수에 해당하는 파라미터 값
        """
        # numpy 배열로 변환 (float 형식)
        freq_array = np.array(freq_data, dtype=float)
        
        # 각 주파수와 target_freq 간의 절대 차이 계산
        differences = np.abs(freq_array - target_freq)
        
        # 차이가 가장 작은 인덱스 찾기
        closest_index = differences.argmin()
        
        # 해당 인덱스의 param_data 값을 반환 (파이썬의 일반 타입으로)
        return param_data[closest_index]

    def _convert_frequency(self, data, column, multiplier):
        idx = data.columns.get_loc(column)
        new_freq = data[column] * multiplier
        data.drop(columns=[column], inplace=True)
        data.insert(idx, "Freq [Hz]", new_freq)
        return data

    def data_preprocessing(self, data) :

        if "Freq [kHz]" in data.columns:
            data = self._convert_frequency(data, "Freq [kHz]", 1e3)
        elif "Freq [MHz]" in data.columns:
            data = self._convert_frequency(data, "Freq [MHz]", 1e6)
        elif "Freq [GHz]" in data.columns:
            data = self._convert_frequency(data, "Freq [GHz]", 1e9)

        # "Freq [Hz]" 컬럼의 위치 찾기
        idx = data.columns.get_loc("Freq [Hz]")

        # "Freq [Hz]" 컬럼부터 오른쪽에 있는 모든 컬럼만 선택
        data = data.iloc[:, idx:]

        return data

    def get_convergence_report(self, setup_name="Setup1", name=None) :
        report_file = self.design.export_convergence(setup_name=setup_name, variation_string="", file_path=None)
        df = self._extract_data_from_last_line(report_file)
        if name:
            df.columns = [f"{col}{name}" for col in df.columns]
        return df

    def _extract_data_from_last_line(self, filename):
        with open(filename, 'r') as file:
            lines = file.readlines()
        last_data_line = ""
        for line in reversed(lines):
            if line.strip():
                last_data_line = line
                break
        parts = last_data_line.split('|')
        data = {
            'Pass Number': [parts[0].strip()],
            'Tetrahedra': [parts[1].strip()],
            'Total Energy': [parts[2].strip()],
            'Energy Error': [parts[3].strip()],
            'Delta Energy': [parts[4].strip()]
        }
        return pd.DataFrame(data)
        
