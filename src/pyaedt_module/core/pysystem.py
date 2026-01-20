from ansys.aedt.core.internal.aedt_versions import aedt_versions
import re


class pySystem:

    def __init__(self):
        self.installed_versions = aedt_versions.installed_versions

    def get_installed_versions(self, ascending=False):

        """
        installed_keys 예: ['2025.2AWP', '2025.2', '2024.2', '2024.1']
        결과 (ascending=True): ['2024.1', '2024.2', '2025.1', '2025.2']
        결과 (ascending=False): ['2025.2', '2025.1', '2024.2', '2024.1']
        """
        out = []
        for k in self.installed_versions.keys():
            k = k.strip()
            if re.fullmatch(r"\d{4}\.\d+", k):
                out.append(k)

        # 오름차순 또는 내림차순 정렬
        return sorted(out, key=lambda v: tuple(map(int, v.split("."))), reverse=not ascending)