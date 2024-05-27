# Statbot Intent Detector

This package retrieves the latest versions of the Statbot metadata and database, uses these to build the intent detector models, then runs an evaluation of these models and outputs the results.

## Preparation

Create a `.env` file in the root directory containing the following:

	STATBOT_REPO=[URL of current Statbot Data repository]

Followed by the Statbot Database connection information:	

	DB_HOST=
	DB_PORT=
	DB_SCHEMA=
	DB_PASS=
	DB_USERNAME=
	DB_DATABASE=
	
(The Statbot Data repository is currently hosted at `https://github.com/statistikZH/statbotData`)

## Running the Evaluation

Build and run the Docker container to retrieve the data, build the model and see the evaluation results:

	$ docker build -t statbot-intent-detector-evaluation .
	$ docker run --gpus all statbot-intent-detector-evaluation
	
Note: Requires a minimum CUDA version of 11.8

The results should match the following, excepting minor deviations:

### Language Detector Results
|          |dev: English|dev: German|dev: Overall|test: English|test: German|test: Overall|crosseval: English | crosseval: German |crosseval: Overall |
|----------|-----------:|----------:|-----------:|------------:|-----------:|------------:|-------------------|-------------------|-------------------|
|langdetect|      0.9524|          1|      0.9818|            1|           1|            1|0.9950 (+/- 0.0617)|1.0000 (+/- 0.0000)|0.9978 (+/- 0.0200)|
|langid    |      1.0000|          1|      1.0000|            1|           1|            1|0.9950 (+/- 0.0665)|1.0000 (+/- 0.0000)|0.9978 (+/- 0.0196)|
|rocchio   |      1.0000|          1|      1.0000|            1|           1|            1|1.0000 (+/- 0.0000)|1.0000 (+/- 0.0000)|1.0000 (+/- 0.0000)|
|ensemble  |      1.0000|          1|      1.0000|            1|           1|            1|1.0000 (+/- 0.0000)|1.0000 (+/- 0.0000)|1.0000 (+/- 0.0000)|

### Table Classifier Results
|          |dev: English|dev: German|dev: Overall|test: English|test: German|test: Overall|crosseval: English | crosseval: German |crosseval: Overall |
|----------|-----------:|----------:|-----------:|------------:|-----------:|------------:|-------------------|-------------------|-------------------|
|bm25 (r@1)|      0.9524|     0.9706|      0.9636|       0.9024|      0.9322|         0.92|0.9389 (+/- 0.1312)|0.8977 (+/- 0.1477)|0.9151 (+/- 0.1108)|
|bm25 (r@3)|      1.0000|     1.0000|      1.0000|       1.0000|      0.9661|         0.98|0.9995 (+/- 0.0521)|0.9836 (+/- 0.0670)|0.9902 (+/- 0.0337)|
|bm25 (r@5)|      1.0000|     1.0000|      1.0000|       1.0000|      0.9831|         0.99|1.0000 (+/- 0.0000)|0.9884 (+/- 0.0717)|0.9930 (+/- 0.0365)|
|bert (r@1)|      0.9048|     0.9412|      0.9273|       0.9268|      0.9322|         0.93|0.9444 (+/- 0.2172)|0.8795 (+/- 0.2129)|0.9071 (+/- 0.1245)|
|bert (r@3)|      1.0000|     1.0000|      1.0000|       1.0000|      0.9661|         0.98|0.9915 (+/- 0.1092)|0.9779 (+/- 0.1029)|0.9840 (+/- 0.0709)|
|bert (r@5)|      1.0000|     1.0000|      1.0000|       1.0000|      0.9831|         0.99|0.9966 (+/- 0.0591)|0.9878 (+/- 0.1032)|0.9916 (+/- 0.0568)|