import matplotlib.pyplot as plt
import simplejson

## wfse data

with open ("wfse_size.txt") as wfse_file:
    data = simplejson.load(wfse_file)

wfse_size = data['wfse_size']

wfse_product_size = data['pa_size_wfse']

wfse_pa_cart_size = data['cart_product_size_wfse']

wfse_product_dur = data['product_duration_wfse']

wfse_edges = data['wfse_edges']


### ts data:

with open ("ts_size.txt") as ts_file:
    data = simplejson.load(ts_file)

ts_size= data['ts_size']

ts_product_size=  data['pa_size_ts']

ts_pa_cart_size=  data['cart_product_size_ts']

ts_product_dur= data['product_duration_ts']

ts_edges = data['ts_edges']


fig2, ax2 = plt.subplots()
# fig3, ax3 = plt.subplots()


# ax3.plot(wfse_size, pa_construct, 'go',label='pa_construction', linewidth=3)

# ax3.set_xlabel('WFSE size', fontsize=16)
# ax3.set_ylabel('PA construction duration (ms)', fontsize=16)

ax2.plot(wfse_size, wfse_product_size, 'c-', label = '3-way PA w.r.t. WFSE', linewidth=3)
ax2.plot(wfse_size, wfse_pa_cart_size, 'r-', label = 'Cartesian product w.r.t. WFSE', linewidth=3)
ax2.plot(ts_size, ts_product_size,'b-', label = '3-way PA w.r.t. TS', linewidth=2)
ax2.plot(ts_size, ts_pa_cart_size,'g-', label = 'Cartesian product w.r.t. WFSE', linewidth=3)


ax2.set_xlabel('Model Size', fontsize=16)
ax2.set_ylabel('PA size', fontsize=16)

plt.grid(b=True)
ax2.legend(fontsize=13)
plt.show()

fig, axs = plt.subplots(2)
# plt.grid(b=True)
# fig.suptitle('PA construction wrt model size')
axs[0].plot(wfse_edges, wfse_product_dur, 'go',label='pa_construction', linewidth=3)
axs[0].grid()

# axs[0].set_xlabel('WFSE Size', fontsize=16)
# axs[0].set_ylabel('PA construction (ms)', fontsize=16)
plt.grid()

axs[1].plot(ts_edges, ts_product_dur, 'bo',label='pa_construction', linewidth=3)
axs[1].grid()


# axs.set_xlabel('Model Size', fontsize=16)
# axs.set_ylabel('PA construction (ms)', fontsize=16)
fig.text(0.5, 0.02, 'Model size', ha='center',fontsize=16)
fig.text(0.04, 0.5, 'PA construction (ms)', va='center', rotation='vertical',fontsize=16)

plt.grid()
plt.show()
