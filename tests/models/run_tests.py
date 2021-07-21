import bionetgen as bng
import glob

models = glob.glob("*.bngl")
total = len(models)
succ = []
fail = []
success = 0
fails = 0
for model in models:
    try:
        m = bng.bngmodel(model)
        success += 1
        succ.append(model)
        # mname = model.replace(".bngl","")
        # with open("{}_loaded.bngl".format(mname), 'w') as f:
        #     f.write(str(m))
    except:
        print("can't do model {}".format(model))
        fails += 1
        fail.append(model)

print("succ: {}".format(success))
print(sorted(succ))
print("fail: {}".format(fails))
print(sorted(fail))
