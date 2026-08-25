from kaggle_environments import make
results = []
for seed in [0,1,2,3,4,5,6,7]:
    env=make('orbit_wars',configuration={'seed':seed},debug=False)
    env.run(['agent.py','random'])
    obs=env.steps[-1][0].observation
    p0=len([p for p in obs.get('planets',[]) if p[1]==0])
    p1=len([p for p in obs.get('planets',[]) if p[1]==1])
    win = 'WIN' if p0>p1 else 'LOSE' if p0<p1 else 'DRAW'
    results.append(win)
    print('seed='+str(seed)+'  mine='+str(p0)+'  enemy='+str(p1)+'  '+win)
print('Win rate vs random: '+str(results.count('WIN'))+'/'+str(len(results)))