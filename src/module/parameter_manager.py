"""
파라미터 관리 라이브러리
FEA 시뮬레이션을 위한 파라미터 범위 정의, 샘플링, 최적화를 위한 boundary 조정 기능 제공
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C


class SamplingStrategy(Enum):
    """샘플링 전략"""
    RANDOM = "random"
    GRID = "grid"
    LHS = "lhs"  # Latin Hypercube Sampling
    SOBOL = "sobol"  # Sobol sequence
    UNIFORM = "uniform"


@dataclass
class ParameterBound:
    """단일 파라미터의 범위 정의"""
    name: str
    min_value: float
    max_value: float
    current_value: Optional[float] = None
    unit: str = ""
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.min_value >= self.max_value:
            raise ValueError(f"Parameter {self.name}: min_value ({self.min_value}) must be less than max_value ({self.max_value})")
        
        if self.current_value is None:
            self.current_value = (self.min_value + self.max_value) / 2.0
    
    def clip(self, value: float) -> float:
        """값을 범위 내로 제한"""
        return np.clip(value, self.min_value, self.max_value)
    
    def normalize(self, value: float) -> float:
        """값을 [0, 1] 범위로 정규화"""
        return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize(self, normalized_value: float) -> float:
        """정규화된 값을 원래 범위로 변환"""
        return self.min_value + normalized_value * (self.max_value - self.min_value)


class ParameterSpace:
    """파라미터 공간 정의 및 관리"""
    
    def __init__(self, parameters: Optional[Dict[str, ParameterBound]] = None):
        """
        Args:
            parameters: 파라미터 이름을 키로 하는 ParameterBound 딕셔너리
        """
        self.parameters: Dict[str, ParameterBound] = parameters or {}
        self.parameter_names = list(self.parameters.keys())
    
    def add_parameter(self, name: str, min_value: float, max_value: float, 
                     current_value: Optional[float] = None, unit: str = ""):
        """파라미터 추가"""
        self.parameters[name] = ParameterBound(
            name=name, 
            min_value=min_value, 
            max_value=max_value,
            current_value=current_value,
            unit=unit
        )
        self.parameter_names = list(self.parameters.keys())
    
    def get_current_values(self) -> Dict[str, float]:
        """현재 파라미터 값들을 딕셔너리로 반환"""
        return {name: param.current_value for name, param in self.parameters.items()}
    
    def set_current_values(self, values: Dict[str, float]):
        """현재 파라미터 값들 설정"""
        for name, value in values.items():
            if name in self.parameters:
                self.parameters[name].current_value = self.parameters[name].clip(value)
            else:
                logging.warning(f"Parameter {name} not found in parameter space")
    
    def update_boundaries(self, new_bounds: Dict[str, Tuple[float, float]]):
        """파라미터 범위 동적 업데이트"""
        for name, (min_val, max_val) in new_bounds.items():
            if name in self.parameters:
                self.parameters[name].min_value = min_val
                self.parameters[name].max_value = max_val
                # 현재 값이 새 범위를 벗어나면 조정
                self.parameters[name].current_value = self.parameters[name].clip(
                    self.parameters[name].current_value
                )
            else:
                logging.warning(f"Parameter {name} not found in parameter space")
    
    def shrink_boundaries(self, factor: float = 0.9, center: Optional[Dict[str, float]] = None):
        """범위를 축소 (최적화 후 탐색 공간 축소용)"""
        if center is None:
            center = self.get_current_values()
        
        for name, param in self.parameters.items():
            if name in center:
                center_val = center[name]
                width = param.max_value - param.min_value
                new_width = width * factor
                param.min_value = center_val - new_width / 2
                param.max_value = center_val + new_width / 2
                param.current_value = param.clip(param.current_value)
    
    def to_dict(self) -> Dict[str, float]:
        """현재 값을 딕셔너리로 반환 (기존 create_input_parameter와 호환)"""
        return self.get_current_values()


class ParameterSampler:
    """파라미터 샘플링 전략"""
    
    def __init__(self, parameter_space: ParameterSpace):
        self.parameter_space = parameter_space
    
    def sample(self, n_samples: int, strategy: SamplingStrategy = SamplingStrategy.LHS,
              seed: Optional[int] = None) -> List[Dict[str, float]]:
        """
        파라미터 공간에서 샘플 생성
        
        Args:
            n_samples: 샘플 개수
            strategy: 샘플링 전략
            seed: 랜덤 시드
            
        Returns:
            파라미터 딕셔너리 리스트
        """
        if seed is not None:
            np.random.seed(seed)
        
        n_params = len(self.parameter_space.parameters)
        param_names = self.parameter_space.parameter_names
        
        if strategy == SamplingStrategy.RANDOM:
            samples = np.random.random((n_samples, n_params))
        elif strategy == SamplingStrategy.UNIFORM:
            samples = np.linspace(0, 1, n_samples).reshape(-1, 1)
            if n_params > 1:
                samples = np.tile(samples, (1, n_params))
        elif strategy == SamplingStrategy.LHS:
            sampler = qmc.LatinHypercube(d=n_params, seed=seed)
            samples = sampler.random(n=n_samples)
        elif strategy == SamplingStrategy.SOBOL:
            sampler = qmc.Sobol(d=n_params, seed=seed)
            samples = sampler.random(n=n_samples)
        elif strategy == SamplingStrategy.GRID:
            # 간단한 그리드 샘플링 (각 차원당 sqrt(n_samples)개)
            n_per_dim = int(np.ceil(n_samples ** (1.0 / n_params)))
            grid = np.meshgrid(*[np.linspace(0, 1, n_per_dim) for _ in range(n_params)])
            samples = np.column_stack([g.ravel() for g in grid])[:n_samples]
        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")
        
        # 정규화된 샘플을 실제 값으로 변환
        result = []
        for sample in samples:
            param_dict = {}
            for i, name in enumerate(param_names):
                param = self.parameter_space.parameters[name]
                param_dict[name] = param.denormalize(sample[i])
            result.append(param_dict)
        
        return result


class ParameterOptimizer:
    """파라미터 최적화를 위한 boundary 조정"""
    
    def __init__(self, parameter_space: ParameterSpace):
        self.parameter_space = parameter_space
        self.history: List[Dict] = []  # 시뮬레이션 결과 히스토리
    
    def add_result(self, parameters: Dict[str, float], 
                   outputs: Dict[str, float], 
                   target_outputs: Optional[Dict[str, float]] = None):
        """
        시뮬레이션 결과 추가
        
        Args:
            parameters: 입력 파라미터
            outputs: 시뮬레이션 출력 (예: 효율, 손실 등)
            target_outputs: 목표 출력 값
        """
        record = {
            'parameters': parameters.copy(),
            'outputs': outputs.copy(),
            'target_outputs': target_outputs.copy() if target_outputs else None
        }
        self.history.append(record)
    
    def adjust_boundaries(self, 
                         target_outputs: Dict[str, float],
                         tolerance: Dict[str, float],
                         shrink_factor: float = 0.8,
                         method: str = "best_performance"):
        """
        목표 출력에 기반하여 boundary 조정
        
        Args:
            target_outputs: 목표 출력 값들
            tolerance: 각 출력에 대한 허용 오차
            shrink_factor: 범위 축소 비율
            method: 조정 방법 ("best_performance", "regression", "constraint")
        """
        if len(self.history) == 0:
            logging.warning("No simulation history available for boundary adjustment")
            return
        
        if method == "best_performance":
            self._adjust_by_best_performance(target_outputs, tolerance, shrink_factor)
        elif method == "regression":
            self._adjust_by_regression(target_outputs, tolerance, shrink_factor)
        elif method == "constraint":
            self._adjust_by_constraint(target_outputs, tolerance)
        else:
            raise ValueError(f"Unknown adjustment method: {method}")
    
    def _adjust_by_best_performance(self, target_outputs: Dict[str, float],
                                   tolerance: Dict[str, float], shrink_factor: float):
        """최고 성능을 보인 파라미터 주변으로 범위 축소"""
        # 목표에 가장 가까운 결과 찾기
        best_idx = self._find_best_result(target_outputs, tolerance)
        if best_idx is None:
            logging.warning("No satisfactory result found, keeping current boundaries")
            return
        
        best_params = self.history[best_idx]['parameters']
        self.parameter_space.shrink_boundaries(factor=shrink_factor, center=best_params)
        logging.info(f"Boundaries adjusted around best parameters: {best_params}")
    
    def _adjust_by_regression(self, target_outputs: Dict[str, float],
                             tolerance: Dict[str, float], shrink_factor: float):
        """회귀 모델을 사용하여 목표 달성 가능성이 높은 영역으로 범위 조정"""
        if len(self.history) < 5:
            logging.warning("Not enough data for regression-based adjustment, using best_performance")
            self._adjust_by_best_performance(target_outputs, tolerance, shrink_factor)
            return
        
        # 데이터 준비
        X = np.array([[r['parameters'][name] for name in self.parameter_space.parameter_names] 
                      for r in self.history])
        
        # 각 출력에 대해 회귀 모델 학습 및 최적 파라미터 예측
        predicted_params = {}
        for output_name, target_value in target_outputs.items():
            y = np.array([r['outputs'].get(output_name, 0) for r in self.history])
            
            # Gaussian Process 회귀
            kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
            gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
            gp.fit(X, y)
            
            # 목표 값에 가장 가까운 파라미터 찾기 (간단한 그리드 서치)
            # 실제로는 더 정교한 최적화 알고리즘 사용 가능
            best_params_for_output = self._optimize_for_target(gp, target_value)
            predicted_params[output_name] = best_params_for_output
        
        # 모든 출력에 대한 평균 파라미터 사용
        if predicted_params:
            avg_params = {}
            for name in self.parameter_space.parameter_names:
                avg_params[name] = np.mean([predicted_params[out].get(name, 0) 
                                          for out in predicted_params.keys()])
            self.parameter_space.shrink_boundaries(factor=shrink_factor, center=avg_params)
            logging.info(f"Boundaries adjusted using regression model around: {avg_params}")
    
    def _adjust_by_constraint(self, target_outputs: Dict[str, float],
                            tolerance: Dict[str, float]):
        """제약 조건을 만족하는 파라미터 영역으로 범위 조정"""
        # 제약 조건을 만족하는 결과들 필터링
        valid_results = []
        for record in self.history:
            if self._check_constraints(record['outputs'], target_outputs, tolerance):
                valid_results.append(record['parameters'])
        
        if not valid_results:
            logging.warning("No results satisfy constraints, keeping current boundaries")
            return
        
        # 유효한 파라미터들의 범위 계산
        new_bounds = {}
        for name in self.parameter_space.parameter_names:
            values = [r[name] for r in valid_results if name in r]
            if values:
                margin = (max(values) - min(values)) * 0.1  # 10% 마진
                new_bounds[name] = (max(min(values) - margin, self.parameter_space.parameters[name].min_value),
                                  min(max(values) + margin, self.parameter_space.parameters[name].max_value))
        
        if new_bounds:
            self.parameter_space.update_boundaries(new_bounds)
            logging.info(f"Boundaries adjusted to constraint-satisfying region: {new_bounds}")
    
    def _find_best_result(self, target_outputs: Dict[str, float],
                         tolerance: Dict[str, float]) -> Optional[int]:
        """목표에 가장 가까운 결과의 인덱스 반환"""
        best_idx = None
        best_score = float('inf')
        
        for idx, record in enumerate(self.history):
            score = self._calculate_error_score(record['outputs'], target_outputs, tolerance)
            if score < best_score:
                best_score = score
                best_idx = idx
        
        return best_idx
    
    def _calculate_error_score(self, outputs: Dict[str, float],
                              target_outputs: Dict[str, float],
                              tolerance: Dict[str, float]) -> float:
        """출력과 목표 간의 오차 점수 계산"""
        total_error = 0.0
        for key, target in target_outputs.items():
            if key in outputs:
                error = abs(outputs[key] - target) / (tolerance.get(key, 1.0) + 1e-10)
                total_error += error
        return total_error
    
    def _check_constraints(self, outputs: Dict[str, float],
                          target_outputs: Dict[str, float],
                          tolerance: Dict[str, float]) -> bool:
        """출력이 제약 조건을 만족하는지 확인"""
        for key, target in target_outputs.items():
            if key in outputs:
                if abs(outputs[key] - target) > tolerance.get(key, float('inf')):
                    return False
        return True
    
    def _optimize_for_target(self, model: GaussianProcessRegressor,
                            target_value: float) -> Dict[str, float]:
        """회귀 모델을 사용하여 목표 값에 가장 가까운 파라미터 찾기"""
        # 간단한 그리드 서치 (실제로는 scipy.optimize 사용 권장)
        n_samples = 100
        sampler = ParameterSampler(self.parameter_space)
        candidates = sampler.sample(n_samples, SamplingStrategy.LHS)
        
        best_params = None
        best_error = float('inf')
        
        for params in candidates:
            X_test = np.array([[params[name] for name in self.parameter_space.parameter_names]])
            pred, std = model.predict(X_test, return_std=True)
            error = abs(pred[0] - target_value) - std[0]  # 불확실성 고려
            if error < best_error:
                best_error = error
                best_params = params
        
        return best_params or self.parameter_space.get_current_values()
    
    def get_history_dataframe(self) -> pd.DataFrame:
        """히스토리를 DataFrame으로 반환"""
        records = []
        for record in self.history:
            row = {}
            row.update({f'param_{k}': v for k, v in record['parameters'].items()})
            row.update({f'output_{k}': v for k, v in record['outputs'].items()})
            if record['target_outputs']:
                row.update({f'target_{k}': v for k, v in record['target_outputs'].items()})
            records.append(row)
        return pd.DataFrame(records)


class SimulationParameterManager:
    """시뮬레이션 파라미터 전체 생명주기 관리"""
    
    def __init__(self, parameter_space: ParameterSpace):
        self.parameter_space = parameter_space
        self.sampler = ParameterSampler(parameter_space)
        self.optimizer = ParameterOptimizer(parameter_space)
    
    def get_next_parameters(self, n_samples: int = 1,
                           strategy: SamplingStrategy = SamplingStrategy.LHS) -> List[Dict[str, float]]:
        """다음 시뮬레이션을 위한 파라미터 샘플 생성"""
        return self.sampler.sample(n_samples, strategy)
    
    def record_simulation_result(self, parameters: Dict[str, float],
                                outputs: Dict[str, float],
                                target_outputs: Optional[Dict[str, float]] = None):
        """시뮬레이션 결과 기록"""
        self.optimizer.add_result(parameters, outputs, target_outputs)
    
    def optimize_boundaries(self, target_outputs: Dict[str, float],
                          tolerance: Dict[str, float],
                          shrink_factor: float = 0.8,
                          method: str = "best_performance"):
        """파라미터 범위 최적화"""
        self.optimizer.adjust_boundaries(target_outputs, tolerance, shrink_factor, method)
    
    def get_current_parameters(self) -> Dict[str, float]:
        """현재 파라미터 값 반환"""
        return self.parameter_space.get_current_values()
    
    def get_history(self) -> pd.DataFrame:
        """시뮬레이션 히스토리 반환"""
        return self.optimizer.get_history_dataframe()

