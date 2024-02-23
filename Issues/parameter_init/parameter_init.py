import  bionetgen

parameter = bionetgen.modelapi.structs.Parameter("A0", "10")
print(parameter.gen_string())