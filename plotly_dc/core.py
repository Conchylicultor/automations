import dataclasses

import pandas


@dataclasses.dataclass
class Visualizable:

    @property
    def df(self) -> pandas.DataFrame:
        return pandas.DataFrame({k: getattr(self, k) for k in self._df_fields})

    # @property
    # def _df_fields(self) -> list[str]:
    #     return
