"""Model preparation and the list of models to compare.

How the forecast works (two simple steps):

    1. Baseline: every rent grows by the average growth seen in the training years.
    2. Machine learning: the model learns how much FASTER or SLOWER each municipality grows
       than the Portugal average (the target `target_local_growth`).

    predicted rent next year = rent today x (1 + average growth + model correction)
"""
import numpy as np
from sklearn.ensemble import (AdaBoostRegressor, BaggingRegressor, GradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

NUMERIC_FEATURES = [
    "rent_m2",            # rent today, €/m²
    "rent_growth_1y",     # rent growth over the last 12 months
    "rent_vs_region",     # rent today / median rent of the region
    "growth_vs_region",   # last-year growth minus the region's growth
    "log_new_leases",     # size of the rental market (log of new contracts)
    "leases_per_1000",    # new contracts per 1,000 residents
    "share_age_65_plus",  # share of residents aged 65+
]
# log_population was also a candidate, but it is 0.96 correlated with log_new_leases,
# so I removed it in the feature selection step (notebook 02, section 3.4).
CATEGORICAL_FEATURES = ["area"]  # Lisbon metro / Porto metro / Rest of Portugal
TARGET = "target_local_growth"
RANDOM_STATE = 0


class FeaturePreparer:
    """Fill missing values (mean), normalise numbers (MinMaxScaler) and one-hot encode `area`.

    Everything is fitted on the TRAINING data only, then applied to train and test,
    so no information from the test year leaks into the model.
    """

    def fit(self, train):
        self.imputer = SimpleImputer(strategy="mean").fit(train[NUMERIC_FEATURES])
        self.normalizer = MinMaxScaler().fit(self.imputer.transform(train[NUMERIC_FEATURES]))
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(train[CATEGORICAL_FEATURES])
        return self

    def transform(self, df):
        numbers = self.normalizer.transform(self.imputer.transform(df[NUMERIC_FEATURES]))
        categories = self.encoder.transform(df[CATEGORICAL_FEATURES])
        return np.hstack([numbers, categories])

    def feature_names(self):
        return NUMERIC_FEATURES + list(self.encoder.get_feature_names_out(CATEGORICAL_FEATURES))


def candidate_models():
    """The regression models seen in class, with simple starting settings."""
    return {
        "Linear regression": LinearRegression(),
        "KNN": KNeighborsRegressor(n_neighbors=10),
        "Decision tree": DecisionTreeRegressor(max_depth=5, random_state=RANDOM_STATE),
        "Bagging": BaggingRegressor(DecisionTreeRegressor(max_depth=5), n_estimators=100, random_state=RANDOM_STATE),
        "Random forest": RandomForestRegressor(n_estimators=100, max_depth=5, random_state=RANDOM_STATE, n_jobs=-1),
        "AdaBoost": AdaBoostRegressor(DecisionTreeRegressor(max_depth=3), n_estimators=100, random_state=RANDOM_STATE),
        "Gradient boosting": GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=RANDOM_STATE),
    }


def predict_rent(model, X, rows, average_growth):
    """Turn the model's correction into a growth rate and a rent for next year."""
    growth = average_growth + model.predict(X)
    return growth, rows["rent_m2"].to_numpy() * (1 + growth)
