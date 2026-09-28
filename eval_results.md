# Batch Evaluation Results

Mode: LIVE (Gemini)
Logs evaluated: 16 (leave-one-out scoring, corpus size 15 per log)

## Summary table

| Log | Ground truth | LLM calls | Canned | Skipped |
|---|---|---|---|---|
| cuda_oom_01.log | CUDA out-of-memory (known/recurring) | 0 | 6 | 6 |
| cuda_oom_02.log | CUDA out-of-memory (known/recurring) | 0 | 6 | 6 |
| cuda_oom_03.log | CUDA out-of-memory (known/recurring) | 0 | 6 | 6 |
| healthy_01.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_02.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_03.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_04.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_05.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_06.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_07.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_08.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_09.log | healthy (no failure) | 0 | 0 | 17 |
| healthy_10.log | healthy (no failure) | 0 | 0 | 17 |
| keyerror_novel_01.log | pandas merge KeyError (novel) | 5 | 2 | 3 |
| timeout_novel_01.log | network read timeout (novel) | 5 | 2 | 1 |
| valueerror_novel_01.log | unknown | 5 | 2 | 3 |

**Totals: 15 LLM calls, 24 canned, 195 skipped across 16 logs.**

## LLM explanations (hand-code correctness against ground truth)

### keyerror_novel_01.log — ground truth: pandas merge KeyError (novel)

**Line 3** (rarity 1.0): `🔧 Merging external feature table on 'user_id'...`

> This failure was likely caused by an Out-Of-Memory (OOM) crash due to duplicate `user_id` key creation during a many-to-many join, or a `FileNotFoundError` if the external dataset path is inaccessible in the hidden test evaluation environment. To fix this, ensure the external feature table is strictly deduplicated on `user_id` before merging, downcast data types to optimize memory usage, and verify that the external dataset is correctly attached to the Kaggle notebook settings.

Correct root cause? (y/n): ____

**Line 5** (rarity 1.0): `KeyError                                  Traceback (most recent call last)`

> This error typically occurs when your inference code attempts to access a DataFrame column or dictionary key—such as a target variable or hardcoded feature name—that is missing or named differently in Kaggle's hidden private test set. To fix this, audit your preprocessing and test-prediction pipeline to ensure you are not referencing training-only columns (like labels) and add defensive checks (e.g., using `df.get()` or verifying `if col in df.columns`) before accessing specific keys.

Correct root cause? (y/n): ____

**Line 7** (rarity 1.0): `----> 22 merged = train_df.merge(ext_features, on='user_id', how='left')`

> This failure was likely caused by an Out-Of-Memory (OOM) error from duplicate `user_id` keys in `ext_features` creating a combinatorial row explosion during the merge, or a `KeyError` if `user_id` is missing in the submission environment. To fix this, enforce key uniqueness by running `ext_features = ext_features.drop_duplicates(subset=['user_id'])` before merging and verify that `user_id` exists with matching data types in both DataFrames.

Correct root cause? (y/n): ____

**Line 8** (rarity 1.0): `KeyError: 'user_id'`

> This error likely occurred because the hidden test set evaluated during submission is missing the `'user_id'` column, uses a slightly different column name, or the column was inadvertently dropped during a preprocessing step prior to inference. To fix this, audit your preprocessing pipeline to ensure columns aren't dropped before downstream merges/indexing, and add a defensive check (e.g., `if 'user_id' in df.columns:`) or explicit schema validation before referencing the column.

Correct root cause? (y/n): ____

**Line 9** (rarity 1.0): `❌ Feature merge failed: column 'user_id' not found in external_features.csv`

> This error likely occurred because `external_features.csv` was recently re-saved or updated with a different column header naming convention (e.g., `userId` or `id` instead of `user_id`), causing your merge operation to fail on the missing key. To fix this, inspect `pd.read_csv('external_features.csv').columns` in your notebook to verify the exact header names and update your code's `on=` merge parameter or column renaming logic accordingly.

Correct root cause? (y/n): ____

### timeout_novel_01.log — ground truth: network read timeout (novel)

**Line 1** (rarity 1.0): `🌐 Downloading external embeddings from remote cache...`

> This log indicates that your code or an underlying library attempted to fetch pre-trained embeddings over the network at runtime, which causes the notebook to hang or fail because Kaggle disables internet access during submission scoring. To fix this, download the required embedding files in advance, upload them as a Kaggle Dataset, and update your script to load the embeddings directly from `/kaggle/input/<your-dataset-name>` instead of a remote cache.

Correct root cause? (y/n): ____

**Line 3** (rarity 1.0): `ConnectionError                          Traceback (most recent call last)`

> This error occurs because Kaggle disables internet access during the scoring phase of code competitions, causing any runtime network requests—such as downloading Hugging Face models, pretrained weights, or packages—to fail. To resolve this, pre-download all required models and assets, upload them as a private Kaggle Dataset, and update your code to load them locally using offline paths (e.g., setting `local_files_only=True` in Hugging Face).

Correct root cause? (y/n): ____

**Line 5** (rarity 1.0): `----> 6 resp = requests.get(url, timeout=120)`

> This failure likely occurred because Kaggle code competition evaluation environments run with internet access disabled, causing `requests.get()` to throw a network or connection error when trying to fetch external resources. To fix this, download the required external file or dependency beforehand, attach it to your notebook as a local Kaggle Dataset, and update the code to read from disk instead of making an HTTP request.

Correct root cause? (y/n): ____

**Line 6** (rarity 1.0): `requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='cache.example.com', port=443): Read timed out. (read timeout=120)`

> This error was likely caused by your script attempting to dynamically download external assets or model weights from `cache.example.com` during execution, which timed out due to remote server unresponsiveness or because Kaggle disables internet access during code competition evaluation runs. To fix this, pre-download all required remote assets, attach them to your notebook as a Kaggle Dataset, and update your code to load the files directly from the local filesystem instead of making HTTP requests.

Correct root cause? (y/n): ____

**Line 7** (rarity 1.0): `❌ Aborting: could not fetch external embeddings after 120s`

> This failure occurs because Kaggle disables internet access during submission evaluation, causing any runtime network calls to external APIs or remote servers for embeddings to time out. To fix this, pre-download or pre-compute the embeddings, upload them as a Kaggle Dataset, and update your notebook to load the files locally from `/kaggle/input/` instead of fetching them over the network.

Correct root cause? (y/n): ____

### valueerror_novel_01.log — ground truth: unknown

**Line 3** (rarity 1.0): `🏋️‍♂️ Fitting StandardScaler on training features...`

> This issue likely occurred because your submission pipeline executed full retraining logic—specifically refitting a `StandardScaler` dynamically—during inference, which can easily trigger an Out-Of-Memory (OOM) error or notebook timeout on Kaggle's hidden test set. To fix this, fit and serialize the `StandardScaler` (e.g., using `joblib` or `pickle`) during your offline training step, then update your inference code to simply load the scaler and call `.transform()` instead of fitting a new one.

Correct root cause? (y/n): ____

**Line 5** (rarity 1.0): `ValueError                                Traceback (most recent call last)`

> This failure was likely caused by an unhandled `ValueError` during hidden test set evaluation, commonly triggered by unexpected data dimensions, unseen categorical values, missing columns, or empty input batches. To fix this, wrap your test preprocessing and inference pipeline in a `try-except` block with fallback predictions, and locally test your code against edge cases like empty DataFrames or single-row submissions.

Correct root cause? (y/n): ____

**Line 7** (rarity 1.0): `----> 14 X_test_scaled = scaler.transform(X_test)`

> This error likely occurred because the hidden test dataset (`X_test`) contains unhandled missing values (NaNs/Infs) or has a different feature count/column order compared to the training data used to fit the `scaler`. To fix this, ensure missing values are imputed and column alignment (e.g., `X_test[train_features]`) is enforced on `X_test` before calling `scaler.transform()`.

Correct root cause? (y/n): ____

**Line 8** (rarity 1.0): `ValueError: X has 24 features, but StandardScaler is expecting 23 features as input.`

> This error likely occurred because the Kaggle hidden test set contains an extra column (such as an un-dropped ID variable or unexpected metadata) or because a feature engineering step generated a different number of columns during inference than during training. To fix this, explicitly align the test set columns to match the exact features used during training—for example, by filtering the test DataFrame with `X_test = X_test[scaler.feature_names_in_]` right before calling `scaler.transform()`.

Correct root cause? (y/n): ____

**Line 9** (rarity 1.0): `❌ Scaling failed: feature count mismatch between train (23) and test (24) sets`

> This failure was likely caused by inconsistent preprocessing on the hidden test set—such as using `pd.get_dummies()` separately on test data where an unseen categorical value generated an extra column, or failing to drop an extra column (e.g., an ID or metadata field) during test-time inference. To fix this, fit your encoders and scalers strictly on the training set (e.g., using Scikit-Learn's `OneHotEncoder` with `handle_unknown='ignore'`) and explicitly align test columns to training features using `test_df = test_df.reindex(columns=train_features, fill_value=0)` before scaling.

Correct root cause? (y/n): ____
