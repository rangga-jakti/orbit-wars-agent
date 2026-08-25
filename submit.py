from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
api.competition_submit('main.py', 'fix: iterative intercept prediction', 'orbit-wars')
print('Submit berhasil!')