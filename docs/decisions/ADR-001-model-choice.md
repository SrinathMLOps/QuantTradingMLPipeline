# ADR-001: Start with XGBoost Before LSTM

## Status
Accepted

## Context
We need to choose an initial model for cryptocurrency price forecasting. The main candidates are:
1. XGBoost (gradient boosting)
2. LSTM (deep learning)
3. Prophet (time series)

## Decision
We will start with XGBoost and add LSTM later for comparison.

## Rationale

### Why XGBoost First?

**Pros:**
- Faster training (minutes vs hours)
- Works well with tabular features
- Better interpretability (feature importance)
- Easier to debug and tune
- Lower computational requirements
- Proven track record in financial forecasting
- Handles missing data well

**Cons:**
- May not capture complex temporal patterns as well as LSTM
- Requires manual feature engineering

### Why Not LSTM First?

**LSTM Challenges:**
- Longer training time (hours)
- Requires more data
- Harder to debug
- More hyperparameters to tune
- Needs GPU for reasonable performance
- Black box model

**LSTM Benefits (for later):**
- Can learn temporal patterns automatically
- May capture long-term dependencies better
- Good for sequence-to-sequence tasks

## Implementation Plan

### Phase 1: XGBoost (Weeks 1-4)
1. Build feature engineering pipeline
2. Train baseline XGBoost model
3. Optimize hyperparameters
4. Deploy to production
5. Establish performance baseline

### Phase 2: LSTM (Weeks 5-8)
1. Prepare sequence data
2. Build LSTM architecture
3. Train and compare with XGBoost
4. A/B test in production
5. Choose best model or ensemble

## Consequences

### Positive
- Faster time to production
- Lower infrastructure costs initially
- Easier to explain to stakeholders
- Can iterate quickly
- Good baseline for comparison

### Negative
- May need to rebuild features for LSTM
- Might miss some temporal patterns initially
- Will need to add GPU support later

## Alternatives Considered

### Prophet
- Pros: Designed for time series, handles seasonality
- Cons: Less flexible, not as accurate for financial data

### Ensemble from Start
- Pros: Best of both worlds
- Cons: Too complex for MVP, harder to debug

## References
- [XGBoost Paper](https://arxiv.org/abs/1603.02754)
- [LSTM for Time Series](https://arxiv.org/abs/1506.00019)
- [Kaggle Financial Forecasting Solutions](https://www.kaggle.com/competitions)

## Review Date
End of Week 4 - Evaluate XGBoost performance and decide on LSTM timeline
