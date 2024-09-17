import os
import time
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate
from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)
path_to_data = os.path.join(project_dir, 'data')
from influence_function_kernel import kernel

np.random.seed(42)

def get_kernels(mesh, material, load, point, n_samples):
    kernels = np.zeros((n_samples, len(mesh)))
    for i in range(n_samples):
        m = material[0][i], material[1][i], material[2][i]
        l = load[0][i]
        p = point[0][i], point[1][i]
        for j,e in enumerate(mesh):
            kernels[i][j] = kernel(e, m, l, p)
    return kernels

def integrate_kernels(branch_vars, trunk_vars, lower_bound, upper_bound):
    integrals = []
    errors = []
    durations = []
    n = len(branch_vars)
    q = len(trunk_vars)
    material = branch_vars
    load = trunk_vars[:,0]
    point = trunk_vars[:, 1:]
    for i in tqdm(range(n), colour='GREEN'):
        for j in range(q):
            m = material[i]
            l = load[j]
            p = point[j]
            start = time.perf_counter_ns()
            integral, error = integrate.quad(lambda ζ: ζ*kernel(ζ, m, l, p), lower_bound, upper_bound, complex_func=True)
            end = time.perf_counter_ns()
            duration = (end - start)/1e6
            # print(integral, error)
            # print(f"Integration took: {duration:.2f} ms")
            integrals.append(integral)
            errors.append(error)
            durations.append(duration)
    integrals = np.array(integrals).reshape(len(branch_vars), len(trunk_vars))
    return np.array(integrals), np.array(errors), np.array(durations)

# ------- All SI units ----------
# Dataset size
N = 50 # Branch
q = 25 # Trunk

# ---------------------------------- Material data (E, ν, ρ) ------------------------
E_mean, E_std = 360e6, 36e6 # Soil is ~360 MPa, Concrete is 30 GPa (took 10% std). There is a very wide range, so I'm just doing soil for now and adding concrete later
ν_min, ν_max = 0.2, 0.5
ρ_mean, ρ_std = 2e3, 5e2 
E = np.random.normal(E_mean, E_std, N)
ν = np.random.uniform(ν_min, ν_max, N)
ρ = np.random.normal(ρ_mean, ρ_std, N) # Normal distribution centered around soil density (around 2e3 kg/m3)
m_params = (E,ν,ρ)

# --------------------------------- Load data (in this case only ω) ------------------------
ρ_steel = 7.85e3
h = 78 # Example tower in Amanda Oliveira et al. (Fix wind turbine)
g = 9.81
p_0 = ρ_steel*g*h
s_1 = 0
s_2 = 12.5
ω_min, ω_max = 0, 100
ω = np.random.uniform(ω_min, ω_max, N)
l_params = (ω,)
# ------------------------------ Point data (r, z) --------------------------------
r_0, z_0 = 0.1, 0.1
d = 20 # length of square centered at the origin where the trunk will be trained (space domain, must define a bound)
r = np.random.uniform(r_0, d, N)
z = np.random.uniform(z_0, d, N)
p = (r,z)

features = np.asarray(m_params + l_params + p).T
branch_features = features[:,:3]
trunk_features = features[:,3:]
# ---------------------------- Computing kernel for plot -----------------------------------
start, end = 0, 10
n_mesh = 300
ζ = np.linspace(start, end, n_mesh)
u_star = get_kernels(ζ, m_params, l_params, p, N)

# ---------------------------- Integrating ------------------------------------------------
l_bound = start
u_bound = np.inf
integrals, errors, durations = integrate_kernels(branch_features, trunk_features, l_bound, u_bound)

print('-----------------------------------------------------------------------')
print(f"Runtime for integration: {durations.mean():.2f} ±  {durations.std():.2f} ms")
print('-----------------------------------------------------------------------')

labels = integrals

# ------------------------------ Plots -------------------------------------------------------
# ω_test = ω[np.argmin(ω)]
# print(f'ω min. = {ω_test:.3f} Hz')
# print(f'p_0 = {p_0:.3E} N')

# plt.plot(ζ, np.abs(u_star[np.argmin(ω)]))
# plt.xlabel(r"$ζ$")
# plt.ylabel(r"$u^*_{zz}$")
# plt.ylim([-1e-3, 1e1])
# plt.tight_layout()
# plt.show()

#-------------------------------- Split training and test set -----------------------------
test_size = 0.2
train_rows = int(N * (1 - test_size))
test_rows = N - train_rows           

train_cols = int(q * (1 - test_size))
test_cols = q - train_cols           

u_train, u_test, G_train, G_test = train_test_split(branch_features, labels, test_size=test_size, random_state=42)

train_data = (u_train, G_train)
test_data = (u_test, G_test)

train_shapes = '\n'.join([str(i.shape) for i in train_data]) 
test_shapes = '\n'.join([str(i.shape) for i in test_data])

print(f"Train sizes (u, G): \n{train_shapes}, \nTest sizes (u, G): \n{test_shapes}")

# ----------------------------- Saving data -------------------------------------
G_train = G_train.reshape(-1,1)
G_test = G_test.reshape(-1,1)

# --- Save dataset ---
if __name__ == '__main__':
    np.savez(os.path.join(path_to_data, 'iss_dataset.npz'), X=features, y=labels)
    np.savez(os.path.join(path_to_data, 'iss_train.npz'), X_branch=u_train, X_trunk=trunk_features, y=G_train)
    np.savez(os.path.join(path_to_data, 'iss_test.npz'), X_branch=u_test, X_trunk=trunk_features, y=G_test)