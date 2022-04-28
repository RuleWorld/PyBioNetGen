import ctypes, os, sys, subprocess
import numpy as np
import bionetgen


class RESULT(ctypes.Structure):
    _fields_ = [
        ("status", ctypes.c_int),
        ("n_observables", ctypes.c_int),
        ("n_species", ctypes.c_int),
        ("n_tpts", ctypes.c_int),
        ("obs_name_len", ctypes.c_int),
        ("spcs_name_len", ctypes.c_int),
        ("observables", ctypes.POINTER(ctypes.c_double)),
        ("species", ctypes.POINTER(ctypes.c_double)),
        ("obs_names", ctypes.POINTER(ctypes.c_char)),
        ("spcs_names", ctypes.POINTER(ctypes.c_char)),
    ]


class CSimulator:
    def __init__(self, lib_path, num_params=None, num_spec_init=None):
        self.return_type = RESULT
        self.lib = ctypes.CDLL(lib_path)
        self.lib.simulate.restype = ctypes.c_void_p
        self.num_params = num_params
        self.num_spec_init = num_spec_init

    def set_species_init(self, arr):
        assert len(arr) == self.num_spec_init
        self.species_init = np.array(arr, dtype=np.float64)

    def set_parameters(self, arr):
        assert len(arr) == self.num_params
        self.parameters = np.array(arr, dtype=np.float64)

    def simulate(self, t_start=0, t_end=100, n_steps=100):
        del_t = (t_end - t_start) / float(n_steps)
        timepoints = np.arange(t_start, t_end + 1, del_t)
        ntpts = len(timepoints)
        self.result = self.return_type.from_address(
            self.lib.simulate(
                ntpts,
                ctypes.c_void_p(timepoints.ctypes.data),
                self.num_spec_init,
                ctypes.c_void_p(self.species_init.ctypes.data),
                self.num_params,
                ctypes.c_void_p(self.parameters.ctypes.data),
            )
        )

        obs_names = ctypes.cast(
            self.result.obs_names,
            ctypes.POINTER(ctypes.c_char * self.result.obs_name_len),
        )[0].value.decode()
        obs_names = obs_names.split(":")[:-1]

        spcs_names = ctypes.cast(
            self.result.spcs_names,
            ctypes.POINTER(ctypes.c_char * self.result.spcs_name_len),
        )[0].value.decode()
        spcs_names = spcs_names.split(":")[:-1]

        buffer_as_ctypes_arr_obs = ctypes.cast(
            self.result.observables,
            ctypes.POINTER(ctypes.c_double * ntpts * self.result.n_observables),
        )[0]
        observables = np.frombuffer(buffer_as_ctypes_arr_obs, np.float64)
        fmt = ["f8"] * len(obs_names)
        obs_all = np.reshape(observables, (self.result.n_observables, ntpts))
        obs_all = np.core.records.fromarrays(obs_all, names=obs_names, formats=fmt)

        buffer_as_ctypes_arr_spc = ctypes.cast(
            self.result.species,
            ctypes.POINTER(ctypes.c_double * ntpts * self.result.n_species),
        )[0]
        species = np.frombuffer(buffer_as_ctypes_arr_spc, np.float64)
        fmt = ["f8"] * len(spcs_names)
        spcs_all = np.reshape(species, (self.result.n_species, ntpts))
        spcs_all = np.core.records.fromarrays(spcs_all, names=spcs_names, formats=fmt)

        self.lib.free_result(ctypes.byref(self.result))
        del self.result

        return (obs_all, spcs_all)


class BNGSim:
    def __init__(self, model, generate_network=False):
        # let's load the model first
        if isinstance(model, str):
            # load model file
            self.model = bionetgen.bngmodel(model, generate_network=generate_network)
        elif isinstance(model, bionetgen.bngmodel):
            # loaded model
            self.model = model
        else:
            print(f"model format not recognized: {model}")
        # run and get CPY file
        # make sure we don't have actions
        self.model.actions.clear_actions()
        self.model.actions.add_action("generate_network", {"overwrite": 1})
        self.model.actions.add_action("writeCPYfile", {})
        # for now run and write the .c file in the current folder
        bionetgen.run(self.model, out=os.path.abspath(os.getcwd()))
        # compile CPY file
        c_file = f"{self.model.model_name}_cvode_py.c"
        obj_file = f"{self.model.model_name}_cvode_py.o"
        lib_file = f"{self.model.model_name}_cvode_py.so"
        subprocess.call(
            [
                "gcc",
                "-fPIC",
                "-I/home/boltzmann/apps/cvode-2.6.0/cvode_lib/include/",
                "-c",
                f"{c_file}",
            ]
        )
        subprocess.call(
            [
                "gcc",
                f"{obj_file}",
                "--shared",
                "-fPIC",
                "-L/home/boltzmann/apps/cvode-2.6.0/cvode_lib/lib/",
                "-lsundials_cvode",
                "-lsundials_nvecserial",
                "-o",
                f"{lib_file}",
            ]
        )
        # use CSimulator under the hood
        n_param = len(
            list(filter(lambda x: not x.startswith("_"), list(self.model.parameters)))
        )
        self.csim = CSimulator(
            os.path.abspath(lib_file),
            num_params=n_param,
            num_spec_init=len(self.model.species),
        )

    def __str__(self):
        return f"C/Python Simulator, params: {self.model.parameters} \ninit species: {self.model.species}"

    def __repr__(self):
        return str(self)

    def simulate(self, t_start=0, t_end=10, n_steps=10):
        # set parameters and initial species values
        spcs = []
        for spc_name in self.model.species:
            try:
                count = float(self.model.species[spc_name].count)
                spcs.append(count)
            except:
                p_name = self.model.species[spc_name].count
                count = float(self.model.parameters[p_name].value)
                spcs.append(count)
        self.csim.set_species_init(spcs)
        params = list(filter(lambda x: not x.startswith("_"), self.model.parameters))
        params = [float(self.model.parameters[p].value) for p in params]
        self.csim.set_parameters(params)
        # now that we have CSimulator setup correctly, run the simulation
        obs_all, spcs_all = self.csim.simulate(t_start, t_end, n_steps)
        # return our results
        return (obs_all, spcs_all)


if __name__ == "__main__":
    sim = BNGSim(os.path.abspath(sys.argv[1]), generate_network=True)
    print("calling simulate")
    observables, species = sim.simulate(0, 1, 10)
    print(f"observables: ")
    print(observables[:10])
    print(f"species: ")
    print(species[:10])
    # import IPython;IPython.embed()
