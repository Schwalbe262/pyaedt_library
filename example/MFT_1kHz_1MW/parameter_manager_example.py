"""
ParameterManager 사용 예시
기존 Simulation 클래스와 통합하는 방법을 보여줍니다.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from module.parameter_manager import (
    ParameterSpace, 
    ParameterSampler, 
    ParameterOptimizer,
    SimulationParameterManager,
    SamplingStrategy
)


class SimulationWithParameterManager:
    """
    ParameterManager를 사용하는 Simulation 클래스 예시
    """
    
    def __init__(self, parameter_space: ParameterSpace):
        self.parameter_manager = SimulationParameterManager(parameter_space)
        # 기존 Simulation 클래스의 다른 속성들...
        self.maxwell_design = None  # 실제로는 기존 코드에서 초기화
    
    def create_input_parameter(self):
        """
        ParameterManager를 사용하여 input_parameter 생성
        기존 create_input_parameter 메서드를 대체
        """
        # 현재 파라미터 값 가져오기
        input_parameter = self.parameter_manager.get_current_parameters()
        
        logging.info(f"input_parameter : {input_parameter}")
        logging.info("input_parameter : " + ",".join(str(float(v)) for v in input_parameter.values()))
        
        return input_parameter
    
    def run_single_simulation(self, parameters: dict):
        """
        단일 시뮬레이션 실행
        
        Args:
            parameters: 시뮬레이션에 사용할 파라미터 딕셔너리
            
        Returns:
            시뮬레이션 출력 딕셔너리 (예: 효율, 손실 등)
        """
        # 파라미터 설정
        self.parameter_manager.parameter_space.set_current_values(parameters)
        input_parameter = self.create_input_parameter()
        
        # 기존 set_variable 로직 실행
        # self.set_variable(input_parameter)
        
        # 시뮬레이션 실행
        # outputs = self.run_maxwell_simulation()
        
        # 예시 출력 (실제로는 시뮬레이션 결과)
        outputs = {
            'efficiency': 0.95,  # 예시 값
            'loss': 100.0,       # 예시 값
        }
        
        return outputs
    
    def run_optimization_loop(self, 
                             target_outputs: dict,
                             tolerance: dict,
                             n_iterations: int = 5,
                             n_samples_per_iteration: int = 10):
        """
        최적화 루프 실행
        
        Args:
            target_outputs: 목표 출력 값들 (예: {'efficiency': 0.98, 'loss': 80.0})
            tolerance: 각 출력에 대한 허용 오차 (예: {'efficiency': 0.01, 'loss': 10.0})
            n_iterations: 최적화 반복 횟수
            n_samples_per_iteration: 각 반복당 샘플 개수
        """
        for iteration in range(n_iterations):
            logging.info(f"\n=== Iteration {iteration + 1}/{n_iterations} ===")
            
            # 현재 파라미터 범위에서 샘플 생성
            parameter_samples = self.parameter_manager.get_next_parameters(
                n_samples=n_samples_per_iteration,
                strategy=SamplingStrategy.LHS
            )
            
            # 각 샘플에 대해 시뮬레이션 실행
            for i, params in enumerate(parameter_samples):
                logging.info(f"Running simulation {i+1}/{n_samples_per_iteration} with parameters: {params}")
                
                outputs = self.run_single_simulation(params)
                
                # 결과 기록
                self.parameter_manager.record_simulation_result(
                    parameters=params,
                    outputs=outputs,
                    target_outputs=target_outputs
                )
                
                logging.info(f"Outputs: {outputs}")
            
            # 목표 달성 여부 확인
            history = self.parameter_manager.get_history()
            if len(history) > 0:
                # 제약 조건을 만족하는 결과가 있는지 확인
                best_result = self._check_target_achievement(history, target_outputs, tolerance)
                if best_result:
                    logging.info(f"Target achieved! Best parameters: {best_result}")
                    break
            
            # Boundary 조정
            if iteration < n_iterations - 1:  # 마지막 반복이 아니면
                logging.info("Adjusting parameter boundaries...")
                self.parameter_manager.optimize_boundaries(
                    target_outputs=target_outputs,
                    tolerance=tolerance,
                    shrink_factor=0.8,
                    method="best_performance"  # 또는 "regression", "constraint"
                )
        
        return self.parameter_manager.get_history()
    
    def _check_target_achievement(self, history: 'pd.DataFrame',
                                 target_outputs: dict, tolerance: dict) -> Optional[dict]:
        """목표 달성 여부 확인"""
        for _, row in history.iterrows():
            satisfied = True
            for key, target in target_outputs.items():
                output_col = f'output_{key}'
                if output_col in row:
                    if abs(row[output_col] - target) > tolerance.get(key, float('inf')):
                        satisfied = False
                        break
            if satisfied:
                # 만족하는 파라미터 반환
                params = {col.replace('param_', ''): row[col] 
                         for col in row.index if col.startswith('param_')}
                return params
        return None


# 사용 예시
if __name__ == "__main__":
    # 1. 파라미터 공간 정의
    parameter_space = ParameterSpace()
    parameter_space.add_parameter("N1", min_value=5, max_value=20, current_value=10, unit="turns")
    parameter_space.add_parameter("N1_layer", min_value=1, max_value=3, current_value=2, unit="layers")
    parameter_space.add_parameter("w1", min_value=50e-3, max_value=200e-3, current_value=100e-3, unit="m")
    parameter_space.add_parameter("l1", min_value=50e-3, max_value=200e-3, current_value=100e-3, unit="m")
    # ... 필요한 모든 파라미터 추가
    
    # 2. SimulationWithParameterManager 초기화
    sim = SimulationWithParameterManager(parameter_space)
    
    # 3. 단일 시뮬레이션 실행 (기존 방식과 호환)
    current_params = sim.create_input_parameter()
    print("Current parameters:", current_params)
    
    # 4. 최적화 루프 실행
    target_outputs = {
        'efficiency': 0.98,
        'loss': 80.0
    }
    tolerance = {
        'efficiency': 0.01,
        'loss': 10.0
    }
    
    history = sim.run_optimization_loop(
        target_outputs=target_outputs,
        tolerance=tolerance,
        n_iterations=5,
        n_samples_per_iteration=10
    )
    
    print("\nFinal history:")
    print(history)

