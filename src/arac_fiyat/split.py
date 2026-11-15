"""Train/test bölmesi ve çapraz doğrulama (CV) katlamaları.

Kural (docs/PROGRESS.md, dal 3): A'da ilan tarihi ve ilan no yok. Bu yüzden
"muhtemelen aynı araç" grubu (cleaning.GROUP_KEY) kimlik yerine geçer:
- holdout: GroupShuffleSplit (aynı grup hem train'de hem testte olamaz),
- CV: GroupKFold(shuffle=True) yalnızca train içinde.
Grup anahtarı yaklaşıktır; gerçek yeniden ilan sızıntısını garanti engellemez.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from arac_fiyat.cleaning import GROUP_KEY
from arac_fiyat.config import RANDOM_STATE

TEST_SIZE = 0.2  # grupların yaklaşık %20'si teste
N_FOLDS = 5


def group_labels(df: pd.DataFrame) -> np.ndarray:
    """Her satıra GROUP_KEY grubunun tam sayı etiketini verir (boş değerler de bir grup)."""
    return df.groupby(GROUP_KEY, dropna=False, sort=False).ngroup().to_numpy()


def holdout_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Veriyi grup bazlı train/test olarak böler; iki parçanın indeksi sıfırdan başlar."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, groups=group_labels(df)))
    train = df.iloc[train_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)
    return train, test


def cv_folds(train: pd.DataFrame) -> list[tuple[np.ndarray, np.ndarray]]:
    """Train içinde grup bazlı CV katlamalarını (train_idx, val_idx) listesi olarak döndürür."""
    cv = GroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    return list(cv.split(train, groups=group_labels(train)))


def count_shared_groups(a: pd.DataFrame, b: pd.DataFrame) -> int:
    """İki parçada ortak olan GROUP_KEY grubu sayısı (doğru bölmede 0 olmalı)."""
    return len(group_keys(a) & group_keys(b))


def group_keys(df: pd.DataFrame) -> set[tuple]:
    """GROUP_KEY değerlerini küme olarak döndürür; boş değerler '<boş>' olarak eşleşir."""
    keys = df[GROUP_KEY].astype(object).fillna("<boş>")
    return set(keys.itertuples(index=False, name=None))
